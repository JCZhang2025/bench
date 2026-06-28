import os, json, csv, re, statistics
from collections import defaultdict

INPUT = os.environ['ORIGINAL_WORDS_JSON']
CELLS_OUT = os.environ['OUTPUT_CELLS_CSV']
METRICS_OUT = os.environ['OUTPUT_METRICS_CSV']
AUDIT_OUT = os.environ['OUTPUT_AUDIT_JSON']
SUMMARY_OUT = os.environ['SUMMARY_MD']

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

table_bbox = data.get('table_bbox') or data.get('table_bbox') or data.get('table_bounds')
words = data.get('words') or data.get('page_words') or []

def bbox_area(b):
    return max(0, b[2]-b[0]) * max(0, b[3]-b[1])

if table_bbox is None and words:
    xs0 = [w['bbox'][0] for w in words]
    ys0 = [w['bbox'][1] for w in words]
    xs1 = [w['bbox'][2] for w in words]
    ys1 = [w['bbox'][3] for w in words]
    table_bbox = [min(xs0), min(ys0), max(xs1), max(ys1)]

tx0, ty0, tx1, ty1 = table_bbox

def in_table(w):
    b = w['bbox']
    cx = (b[0]+b[2])/2
    cy = (b[1]+b[3])/2
    return (cx >= tx0 and cx <= tx1 and cy >= ty0 and cy <= ty1)

table_words = [w for w in words if in_table(w)]
excluded_words = [w for w in words if not in_table(w)]

for w in table_words:
    b = w['bbox']
    w['cx'] = (b[0]+b[2])/2
    w['cy'] = (b[1]+b[3])/2
    w['width'] = b[2]-b[0]
    w['height'] = b[3]-b[1]

if not table_words:
    rows = []
    cells = []
else:
    heights = [w['height'] for w in table_words if w['height'] > 0]
    med_h = statistics.median(heights) if heights else 10
    y_tol = med_h * 0.6

    sorted_by_y = sorted(table_words, key=lambda w: w['cy'])
    rows = []
    for w in sorted_by_y:
        placed = False
        for r in rows:
            if abs(w['cy'] - r['y_center']) <= y_tol:
                r['words'].append(w)
                r['y_center'] = sum(x['cy'] for x in r['words'])/len(r['words'])
                placed = True
                break
        if not placed:
            rows.append({'y_center': w['cy'], 'words': [w]})
    rows.sort(key=lambda r: r['y_center'])

    for ri, r in enumerate(rows):
        r['words'].sort(key=lambda w: w['cx'])
        r['row_id'] = ri

    all_x_centers = sorted([w['cx'] for w in table_words])
    col_boundaries = []
    if len(all_x_centers) >= 2:
        for i in range(len(all_x_centers)-1):
            col_boundaries.append((all_x_centers[i] + all_x_centers[i+1]) / 2)
    if not col_boundaries:
        col_boundaries = [(tx0 + tx1) / 2]

    def assign_col(cx):
        cid = 0
        for cb in col_boundaries:
            if cx > cb:
                cid += 1
            else:
                break
        return cid

    for r in rows:
        for w in r['words']:
            w['col_id'] = assign_col(w['cx'])

    cells = []
    for r in rows:
        row_cells = defaultdict(list)
        for w in r['words']:
            row_cells[w['col_id']].append(w)
        for col_id in sorted(row_cells.keys()):
            ws = sorted(row_cells[col_id], key=lambda w: w['cx'])
            text = ' '.join(w.get('text','') for w in ws).strip()
            text = re.sub(r'\s+', ' ', text)
            if text:
                cells.append({
                    'row_id': r['row_id'],
                    'col_id': col_id,
                    'row_span': 1,
                    'col_span': 1,
                    'is_header': 1 if r['row_id'] == 0 else 0,
                    'text': text
                })

    max_col = max((c['col_id'] for c in cells), default=0)
    for c in cells:
        if c['col_id'] == max_col and max_col > 0:
            c['col_span'] = 1

with open(CELLS_OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['row_id','col_id','row_span','col_span','is_header','text'])
    w.writeheader()
    for c in cells:
        w.writerow(c)

header_texts = [c['text'].lower().strip() for c in cells if c['is_header']]

def normalize_header(h):
    h = h.lower().strip()
    if h in ('method','model','approach','algorithm','name','technique'):
        return 'method'
    if h in ('dataset','data','corpus','benchmark','set'):
        return 'dataset'
    if h in ('accuracy','acc','acc.'):
        return 'accuracy'
    if h in ('f1','f1-score','f1 score','fmeasure','f-measure'):
        return 'f1'
    if h in ('notes','note','remarks','comment','comments'):
        return 'notes'
    return h

col_map = {}
for c in cells:
    if c['is_header']:
        col_map[c['col_id']] = normalize_header(c['text'])

if not col_map:
    body_cells = [c for c in cells if not c['is_header']]
    col_ids = sorted(set(c['col_id'] for c in body_cells))
    default_names = ['method','dataset','accuracy','f1','notes']
    for i, cid in enumerate(col_ids):
        if i < len(default_names):
            col_map[cid] = default_names[i]

def parse_number(s):
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    s = s.replace('%','').replace(',','').strip()
    try:
        val = float(s)
        return val
    except ValueError:
        return None

metric_rows = []
body_cells = [c for c in cells if not c['is_header']]
rows_by_id = defaultdict(dict)
for c in body_cells:
    rows_by_id[c['row_id']][c['col_id']] = c['text']

for rid in sorted(rows_by_id.keys()):
    row_data = rows_by_id[rid]
    mapped = {}
    for cid, txt in row_data.items():
        field = col_map.get(cid, normalize_header(txt) if cid in col_map else None)
        if field:
            mapped[field] = txt
    if not mapped:
        continue
    method = mapped.get('method','').strip()
    dataset = mapped.get('dataset','').strip()
    if not method and not dataset:
        continue
    acc = parse_number(mapped.get('accuracy'))
    f1 = parse_number(mapped.get('f1'))
    notes = mapped.get('notes','').strip()
    metric_rows.append({
        'method': method,
        'dataset': dataset,
        'accuracy': '' if acc is None else acc,
        'f1': '' if f1 is None else f1,
        'notes': notes
    })

with open(METRICS_OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['method','dataset','accuracy','f1','notes'])
    w.writeheader()
    for r in metric_rows:
        w.writerow(r)

issues = []
required_cols = ['method','dataset','accuracy','f1','notes']
for rc in required_cols:
    if rc not in col_map.values():
        issues.append({'type':'missing_required_column','detail':f'Column {rc} not found in header mapping'})

for i, r in enumerate(metric_rows):
    if not r['method']:
        issues.append({'type':'empty_required_text','detail':f'Row {i} has empty method'})
    if not r['dataset']:
        issues.append({'type':'empty_required_text','detail':f'Row {i} has empty dataset'})
    if r['accuracy'] == '':
        issues.append({'type':'non_numeric_metric','detail':f'Row {i} accuracy is empty or non-numeric'})
    if r['f1'] == '':
        issues.append({'type':'non_numeric_metric','detail':f'Row {i} f1 is empty or non-numeric'})

seen = set()
for i, r in enumerate(metric_rows):
    key = (r['method'], r['dataset'])
    if key in seen:
        issues.append({'type':'duplicate_record','detail':f'Duplicate method/dataset: {key}'})
    seen.add(key)

if excluded_words:
    issues.append({'type':'excluded_non_table_text','detail':f'{len(excluded_words)} words excluded as caption/footnote (outside table bbox)'})

best_by_dataset = {}
dataset_groups = defaultdict(list)
for r in metric_rows:
    if r['f1'] != '' and r['dataset']:
        dataset_groups[r['dataset']].append(r)

for ds, rows in dataset_groups.items():
    best = max(rows, key=lambda r: float(r['f1']))
    best_by_dataset[ds] = {'method': best['method'], 'f1': best['f1']}

audit = {
    'row_count': len(metric_rows),
    'best_by_dataset': best_by_dataset,
    'issues': issues,
    'header_mapping': col_map,
    'excluded_word_count': len(excluded_words),
    'table_word_count': len(table_words),
    'total_word_count': len(words)
}

with open(AUDIT_OUT, 'w', encoding='utf-8') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

summary_lines = []
summary_lines.append('# PubTables Reconstruction Summary')
summary_lines.append('')
summary_lines.append(f'- **Total words in input:** {len(words)}')
summary_lines.append(f'- **Table words retained:** {len(table_words)}')
summary_lines.append(f'- **Caption/footnote words excluded:** {len(excluded_words)}')
summary_lines.append(f'- **Reconstructed cells:** {len(cells)}')
summary_lines.append(f'- **Normalized metric rows:** {len(metric_rows)}')
summary_lines.append(f'- **Audit issues found:** {len(issues)}')
summary_lines.append('')
if best_by_dataset:
    summary_lines.append('## Best Method by Dataset (F1)')
    summary_lines.append('')
    summary_lines.append('| Dataset | Best Method | F1 |')
    summary_lines.append('|---------|-------------|----|')
    for ds, info in best_by_dataset.items():
        summary_lines.append(f'| {ds} | {info["method"]} | {info["f1"]} |')
    summary_lines.append('')
if metric_rows:
    summary_lines.append('## Extracted Metric Rows')
    summary_lines.append('')
    summary_lines.append('| Method | Dataset | Accuracy | F1 | Notes |')
    summary_lines.append('|--------|---------|----------|----|-------|')
    for r in metric_rows:
        summary_lines.append(f'| {r["method"]} | {r["dataset"]} | {r["accuracy"]} | {r["f1"]} | {r["notes"]} |')
    summary_lines.append('')
if issues:
    summary_lines.append('## Audit Issues')
    summary_lines.append('')
    for iss in issues:
        summary_lines.append(f'- **{iss["type"]}**: {iss["detail"]}')
    summary_lines.append('')
summary_lines.append('## Notes')
summary_lines.append('')
summary_lines.append('Table structure was reconstructed from OCR word bounding boxes using y-center proximity for row grouping and x-center gaps for column assignment. Caption and footnote words outside the table bounding box were excluded from metric rows. Numeric values were parsed after stripping formatting characters.')

with open(SUMMARY_OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))

print(f'Cells: {len(cells)}, Metrics: {len(metric_rows)}, Issues: {len(issues)}')
