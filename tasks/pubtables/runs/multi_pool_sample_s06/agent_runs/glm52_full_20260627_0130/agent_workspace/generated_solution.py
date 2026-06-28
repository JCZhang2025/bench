import os, json, csv, re
from collections import defaultdict

INPUT = os.environ['ORIGINAL_WORDS_JSON']
CELLS_CSV = os.environ['OUTPUT_CELLS_CSV']
METRICS_CSV = os.environ['OUTPUT_METRICS_CSV']
AUDIT_JSON = os.environ['OUTPUT_AUDIT_JSON']
SUMMARY_MD = os.environ['SUMMARY_MD']

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

table_bbox = data.get('table_bbox') or data.get('table_bbox') or data.get('table_bounds')
words = data.get('words') or data.get('page_words') or []

def bbox_area(b):
    return max(0, b[2]-b[0]) * max(0, b[3]-b[1])

def inside(word_bbox, table_bbox, tol=2):
    if not table_bbox or not word_bbox:
        return True
    return (word_bbox[0] >= table_bbox[0]-tol and
            word_bbox[1] >= table_bbox[1]-tol and
            word_bbox[2] <= table_bbox[2]+tol and
            word_bbox[3] <= table_bbox[3]+tol)

table_words = []
for w in words:
    bbox = w.get('bbox') or w.get('bounding_box') or w.get('box')
    text = w.get('text', '')
    if not text or not bbox:
        continue
    if inside(bbox, table_bbox):
        table_words.append({'text': text, 'bbox': [float(x) for x in bbox]})

table_words.sort(key=lambda w: (w['bbox'][1], w['bbox'][0]))

if not table_words:
    rows = []
else:
    rows = []
    current_row = [table_words[0]]
    for w in table_words[1:]:
        prev = current_row[-1]
        prev_cy = (prev['bbox'][1]+prev['bbox'][3])/2
        cur_cy = (w['bbox'][1]+w['bbox'][3])/2
        prev_h = prev['bbox'][3]-prev['bbox'][1]
        if abs(cur_cy - prev_cy) <= max(prev_h*0.6, 5):
            current_row.append(w)
        else:
            rows.append(current_row)
            current_row = [w]
    rows.append(current_row)

    for r in rows:
        r.sort(key=lambda w: w['bbox'][0])

x_edges = set()
for r in rows:
    for w in r:
        x_edges.add(w['bbox'][0])
        x_edges.add(w['bbox'][2])
x_edges = sorted(x_edges)

if len(x_edges) >= 2:
    col_boundaries = [x_edges[0]]
    for i in range(1, len(x_edges)):
        if x_edges[i] - col_boundaries[-1] > 3:
            col_boundaries.append(x_edges[i])
else:
    col_boundaries = x_edges[:]

def find_col_span(bbox):
    x0, _, x1, _ = bbox
    start = None
    end = None
    for i in range(len(col_boundaries)-1):
        cl = col_boundaries[i]
        cr = col_boundaries[i+1]
        if start is None and x0 <= (cl+cr)/2:
            start = i
        if x1 >= cl - 1:
            end = i
    if start is None:
        start = 0
    if end is None:
        end = len(col_boundaries)-2 if len(col_boundaries)>=2 else 0
    end = max(end, start)
    return start, end-start+1

cells = []
header_row_count = 0
if rows:
    first_row_text = ' '.join(w['text'] for w in rows[0]).lower()
    header_keywords = ['method', 'dataset', 'accuracy', 'f1', 'score', 'metric', 'model', 'approach']
    if any(k in first_row_text for k in header_keywords):
        header_row_count = 1

for ri, r in enumerate(rows):
    for w in r:
        col_id, col_span = find_col_span(w['bbox'])
        row_h = w['bbox'][3]-w['bbox'][1]
        row_span = 1
        cells.append({
            'row_id': ri,
            'col_id': col_id,
            'row_span': row_span,
            'col_span': col_span,
            'is_header': 1 if ri < header_row_count else 0,
            'text': w['text']
        })

with open(CELLS_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['row_id','col_id','row_span','col_span','is_header','text'])
    writer.writeheader()
    for c in cells:
        writer.writerow(c)

header_cells = [c for c in cells if c['is_header']]
if header_cells:
    header_cells.sort(key=lambda c: (c['row_id'], c['col_id']))
    col_names = {}
    for c in header_cells:
        cn = c['col_id']
        if cn not in col_names:
            col_names[cn] = c['text'].strip()
        else:
            col_names[cn] += ' ' + c['text'].strip()
    col_names = {k: re.sub(r'\s+', ' ', v).strip() for k, v in col_names.items()}
else:
    col_names = {}

non_header_cells = [c for c in cells if not c['is_header']]
row_groups = defaultdict(list)
for c in non_header_cells:
    row_groups[c['row_id']].append(c)

def normalize_col_name(name):
    n = name.lower().strip()
    if 'method' in n or 'model' in n or 'approach' in n:
        return 'method'
    if 'dataset' in n or 'data' in n or 'corpus' in n:
        return 'dataset'
    if 'acc' in n:
        return 'accuracy'
    if 'f1' in n or 'f-score' in n or 'fscore' in n:
        return 'f1'
    if 'note' in n:
        return 'notes'
    return None

col_map = {}
for cn, name in col_names.items():
    norm = normalize_col_name(name)
    if norm:
        col_map[cn] = norm

if not col_map and non_header_cells:
    sample_cols = sorted(set(c['col_id'] for c in non_header_cells))
    guesses = ['method','dataset','accuracy','f1','notes']
    for i, sc in enumerate(sample_cols):
        if i < len(guesses):
            col_map[sc] = guesses[i]

def parse_number(text):
    t = text.strip().replace('%','').replace(',','')
    t = re.sub(r'[^0-9.\-]', '', t)
    if t == '' or t == '-':
        return None
    try:
        val = float(t)
        if val > 1.0 and val <= 100.0:
            val = val / 100.0
        return val
    except:
        return None

metrics = []
issues = []

for ri in sorted(row_groups.keys()):
    rcells = row_groups[ri]
    row_data = {}
    for c in rcells:
        cn = c['col_id']
        if cn in col_map:
            field = col_map[cn]
            if field in row_data:
                row_data[field] += ' ' + c['text']
            else:
                row_data[field] = c['text']
    if 'method' not in row_data or not row_data['method'].strip():
        continue
    method = re.sub(r'\s+', ' ', row_data.get('method','')).strip()
    dataset = re.sub(r'\s+', ' ', row_data.get('dataset','')).strip() if row_data.get('dataset') else ''
    acc = parse_number(row_data.get('accuracy','')) if row_data.get('accuracy') else None
    f1 = parse_number(row_data.get('f1','')) if row_data.get('f1') else None
    notes = re.sub(r'\s+', ' ', row_data.get('notes','')).strip() if row_data.get('notes') else ''
    if acc is None and f1 is None:
        issues.append(f'Row {ri}: no numeric accuracy or f1 value found')
    metrics.append({
        'method': method,
        'dataset': dataset,
        'accuracy': f'{acc:.4f}' if acc is not None else '',
        'f1': f'{f1:.4f}' if f1 is not None else '',
        'notes': notes
    })

with open(METRICS_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['method','dataset','accuracy','f1','notes'])
    writer.writeheader()
    for m in metrics:
        writer.writerow(m)

best_by_dataset = {}
for m in metrics:
    ds = m['dataset'] if m['dataset'] else '(unspecified)'
    f1_val = None
    if m['f1']:
        try:
            f1_val = float(m['f1'])
        except:
            pass
    if ds not in best_by_dataset:
        best_by_dataset[ds] = {'method': m['method'], 'f1': m['f1'], 'f1_val': f1_val}
    else:
        cur = best_by_dataset[ds]
        if f1_val is not None and (cur.get('f1_val') is None or f1_val > cur['f1_val']):
            best_by_dataset[ds] = {'method': m['method'], 'f1': m['f1'], 'f1_val': f1_val}

for ds in best_by_dataset:
    if 'f1_val' in best_by_dataset[ds]:
        del best_by_dataset[ds]['f1_val']

if not metrics:
    issues.append('No metric rows extracted from table')
if not col_map:
    issues.append('Could not map header columns to required fields')

audit = {
    'row_count': len(metrics),
    'best_by_dataset': best_by_dataset,
    'issues': issues
}

with open(AUDIT_JSON, 'w', encoding='utf-8') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

lines = []
lines.append('# PubTables Reconstruction Summary')
lines.append('')
lines.append(f'- **Reconstructed cells:** {len(cells)}')
lines.append(f'- **Header rows detected:** {header_row_count}')
lines.append(f'- **Normalized metric rows:** {len(metrics)}')
lines.append(f'- **Extraction issues:** {len(issues)}')
lines.append('')
if metrics:
    lines.append('## Extracted Metrics')
    lines.append('')
    lines.append('| Method | Dataset | Accuracy | F1 | Notes |')
    lines.append('|--------|---------|----------|----|-------|')
    for m in metrics:
        lines.append(f"| {m['method']} | {m['dataset']} | {m['accuracy']} | {m['f1']} | {m['notes']} |")
    lines.append('')
if best_by_dataset:
    lines.append('## Best Method by Dataset (F1)')
    lines.append('')
    for ds, info in best_by_dataset.items():
        lines.append(f'- **{ds}:** {info["method"]} (F1={info["f1"]})')
    lines.append('')
if issues:
    lines.append('## Audit Issues')
    lines.append('')
    for iss in issues:
        lines.append(f'- {iss}')
    lines.append('')
lines.append('## Notes')
lines.append('')
lines.append('Caption and footnote words outside the table bounding box were excluded from metric rows. Cells were reconstructed from OCR word bounding boxes using row clustering by vertical center proximity and column boundary detection from word x-edges.')

with open(SUMMARY_MD, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
