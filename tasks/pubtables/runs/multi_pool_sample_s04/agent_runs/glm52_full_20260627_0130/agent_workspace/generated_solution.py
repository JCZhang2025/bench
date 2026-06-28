#!/usr/bin/env python3
import os, json, csv, re
from collections import defaultdict

INPUT = os.environ['ORIGINAL_WORDS_JSON']
CELLS_CSV = os.environ['OUTPUT_CELLS_CSV']
METRICS_CSV = os.environ['OUTPUT_METRICS_CSV']
AUDIT_JSON = os.environ['OUTPUT_AUDIT_JSON']
SUMMARY_MD = os.environ['SUMMARY_MD']

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

table_bbox = data.get('table_bbox') or data.get('table_bbox') or data.get('table', {}).get('bbox')
words = data.get('words') or data.get('page_words') or data.get('tokens') or []

def bbox_to_centers(w):
    b = w.get('bbox') or w.get('bounding_box') or w.get('box')
    if b and len(b) >= 4:
        x0, y0, x1, y1 = b[0], b[1], b[2], b[3]
    else:
        x0 = w.get('x0', w.get('left', 0)); y0 = w.get('y0', w.get('top', 0))
        x1 = w.get('x1', w.get('right', x0)); y1 = w.get('y1', w.get('bottom', y0))
    return x0, y0, x1, y1, (x0+x1)/2.0, (y0+y1)/2.0, max(x1-x0, 0.1), max(y1-y0, 0.1)

if table_bbox:
    tx0, ty0, tx1, ty1 = table_bbox[0], table_bbox[1], table_bbox[2], table_bbox[3]
else:
    xs0=[]; ys0=[]; xs1=[]; ys1=[]
    for w in words:
        x0,y0,x1,y1,_,_,_,_ = bbox_to_centers(w)
        xs0.append(x0); ys0.append(y0); xs1.append(x1); ys1.append(y1)
    tx0, ty0, tx1, ty1 = min(xs0), min(ys0), max(xs1), max(ys1)

parsed = []
for w in words:
    x0,y0,x1,y1,xc,yc,w_,h_ = bbox_to_centers(w)
    text = w.get('text','')
    if not text:
        continue
    inside = (xc >= tx0 and xc <= tx1 and yc >= ty0 and yc <= ty1)
    parsed.append({'text': text, 'x0':x0,'y0':y0,'x1':x1,'y1':y1,'xc':xc,'yc':yc,'w':w_,'h':h_,'inside':inside})

table_words = [p for p in parsed if p['inside']]
table_words.sort(key=lambda p: (p['yc'], p['xc']))

if not table_words:
    table_words = parsed[:]
    table_words.sort(key=lambda p: (p['yc'], p['xc']))

heights = [p['h'] for p in table_words]
median_h = sorted(heights)[len(heights)//2] if heights else 10.0
row_tol = max(median_h * 0.6, 3.0)

rows = []
for p in table_words:
    placed = False
    for r in rows:
        if abs(p['yc'] - r['center']) < row_tol:
            r['words'].append(p)
            r['center'] = sum(q['yc'] for q in r['words']) / len(r['words'])
            placed = True
            break
    if not placed:
        rows.append({'center': p['yc'], 'words': [p]})
rows.sort(key=lambda r: r['center'])
for r in rows:
    r['words'].sort(key=lambda p: p['xc'])

all_x_centers = [p['xc'] for p in table_words]
if all_x_centers:
    sorted_x = sorted(all_x_centers)
    gaps = [(sorted_x[i+1]-sorted_x[i], sorted_x[i], sorted_x[i+1]) for i in range(len(sorted_x)-1)]
    big_gaps = [g for g in gaps if g[0] > median_h * 2.5]
    boundaries = [tx0] + [(g[1]+g[2])/2.0 for g in big_gaps] + [tx1]
    col_ranges = [(boundaries[i], boundaries[i+1]) for i in range(len(boundaries)-1)]
else:
    col_ranges = [(tx0, tx1)]

if len(col_ranges) < 2:
    xs = sorted(set([p['xc'] for p in table_words]))
    if len(xs) >= 2:
        midpoints = [(xs[i]+xs[i+1])/2.0 for i in range(len(xs)-1)]
        boundaries = [tx0] + midpoints + [tx1]
        col_ranges = [(boundaries[i], boundaries[i+1]) for i in range(len(boundaries)-1)]

def assign_col(p):
    best_i = 0; best_overlap = -1
    for i, (cl, cr) in enumerate(col_ranges):
        ov = min(p['x1'], cr) - max(p['x0'], cl)
        if ov > best_overlap:
            best_overlap = ov; best_i = i
    return best_i

cells = []
for ri, r in enumerate(rows):
    col_buckets = defaultdict(list)
    for p in r['words']:
        ci = assign_col(p)
        col_buckets[ci].append(p)
    for ci, tokens in col_buckets.items():
        tokens.sort(key=lambda p: p['xc'])
        text = ' '.join(t['text'] for t in tokens)
        is_header = 1 if ri == 0 else 0
        cells.append({'row_id': ri, 'col_id': ci, 'row_span': 1, 'col_span': 1, 'is_header': is_header, 'text': text})

cells.sort(key=lambda c: (c['row_id'], c['col_id']))

os.makedirs(os.path.dirname(CELLS_CSV), exist_ok=True)
with open(CELLS_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['row_id','col_id','row_span','col_span','is_header','text'])
    w.writeheader()
    for c in cells:
        w.writerow(c)

header_row = [c for c in cells if c['row_id'] == 0]
header_row.sort(key=lambda c: c['col_id'])
header_texts = [c['text'].strip().lower() for c in header_row]

def find_col_idx(name_candidates):
    for i, ht in enumerate(header_texts):
        for cand in name_candidates:
            if cand in ht:
                return i
    return None

method_col = find_col_idx(['method','model','approach'])
dataset_col = find_col_idx(['dataset','data','corpus'])
accuracy_col = find_col_idx(['accuracy','acc'])
f1_col = find_col_idx(['f1','f-score','fscore'])
notes_col = find_col_idx(['note','comment','remark'])

if method_col is None: method_col = 0
if dataset_col is None: dataset_col = 1 if len(header_texts)>1 else 0
if accuracy_col is None: accuracy_col = 2 if len(header_texts)>2 else None
if f1_col is None: f1_col = 3 if len(header_texts)>3 else None
if notes_col is None: notes_col = 4 if len(header_texts)>4 else None

body_cells = [c for c in cells if c['row_id'] > 0]
row_groups = defaultdict(dict)
for c in body_cells:
    row_groups[c['row_id']][c['col_id']] = c['text']

metrics = []
for rid in sorted(row_groups.keys()):
    rg = row_groups[rid]
    method = rg.get(method_col, '').strip()
    dataset = rg.get(dataset_col, '').strip()
    accuracy = rg.get(accuracy_col, '').strip() if accuracy_col is not None else ''
    f1 = rg.get(f1_col, '').strip() if f1_col is not None else ''
    notes = rg.get(notes_col, '').strip() if notes_col is not None else ''
    if not method and not dataset and not accuracy and not f1:
        continue
    metrics.append({'method': method, 'dataset': dataset, 'accuracy': accuracy, 'f1': f1, 'notes': notes})

def parse_num(s):
    if not s:
        return None
    s2 = s.strip().replace('%','').replace(',','').replace(' ','')
    try:
        return float(s2)
    except:
        m = re.search(r'-?\d+\.?\d*', s2)
        if m:
            return float(m.group())
        return None

for m in metrics:
    m['_acc_num'] = parse_num(m['accuracy'])
    m['_f1_num'] = parse_num(m['f1'])

with open(METRICS_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['method','dataset','accuracy','f1','notes'])
    w.writeheader()
    for m in metrics:
        w.writerow({'method': m['method'], 'dataset': m['dataset'], 'accuracy': m['accuracy'], 'f1': m['f1'], 'notes': m['notes']})

issues = []
required_cols = ['method','dataset','accuracy','f1','notes']
for col in required_cols:
    if col not in ['method','dataset','accuracy','f1','notes']:
        issues.append({'category':'missing_required_column','detail':f'Column {col} missing'})

for i, m in enumerate(metrics):
    if m['_acc_num'] is None and m['accuracy']:
        issues.append({'category':'non_numeric_metric','detail':f'Row {i+1} accuracy not numeric: {m["accuracy"]}'})
    if m['_f1_num'] is None and m['f1']:
        issues.append({'category':'non_numeric_metric','detail':f'Row {i+1} f1 not numeric: {m["f1"]}'})
    if not m['method']:
        issues.append({'category':'empty_required_text','detail':f'Row {i+1} method is empty'})
    if not m['dataset']:
        issues.append({'category':'empty_required_text','detail':f'Row {i+1} dataset is empty'})

seen = set()
for i, m in enumerate(metrics):
    key = (m['method'], m['dataset'])
    if key in seen:
        issues.append({'category':'duplicate_record','detail':f'Duplicate method/dataset: {key}'})
    seen.add(key)

best_by_dataset = {}
dataset_groups = defaultdict(list)
for m in metrics:
    if m['dataset']:
        dataset_groups[m['dataset']].append(m)
for ds, group in dataset_groups.items():
    valid = [g for g in group if g['_f1_num'] is not None]
    if valid:
        best = max(valid, key=lambda g: g['_f1_num'])
        best_by_dataset[ds] = {'method': best['method'], 'f1': best['_f1_num']}
    else:
        issues.append({'category':'inconsistent_group_best','detail':f'No valid f1 scores for dataset {ds}'})

outside_words = [p for p in parsed if not p['inside']]
if outside_words:
    issues.append({'category':'excluded_non_table_text','detail':f'{len(outside_words)} words outside table bbox excluded from metrics'})

audit = {
    'row_count': len(metrics),
    'best_by_dataset': best_by_dataset,
    'issues': issues
}
with open(AUDIT_JSON, 'w', encoding='utf-8') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

summary_lines = []
summary_lines.append('# PubTables Reconstruction Summary')
summary_lines.append('')
summary_lines.append(f'- Reconstructed cells: {len(cells)}')
summary_lines.append(f'- Normalized metric rows: {len(metrics)}')
summary_lines.append(f'- Audit issues found: {len(issues)}')
summary_lines.append('')
if best_by_dataset:
    summary_lines.append('## Best Method by F1 per Dataset')
    for ds, info in best_by_dataset.items():
        summary_lines.append(f'- **{ds}**: {info["method"]} (F1={info["f1"]})')
    summary_lines.append('')
if metrics:
    summary_lines.append('## Extracted Metrics')
    summary_lines.append('| Method | Dataset | Accuracy | F1 | Notes |')
    summary_lines.append('|--------|---------|----------|----|-------|')
    for m in metrics:
        summary_lines.append(f'| {m["method"]} | {m["dataset"]} | {m["accuracy"]} | {m["f1"]} | {m["notes"]} |')
    summary_lines.append('')
if issues:
    summary_lines.append('## Audit Issues')
    for iss in issues:
        summary_lines.append(f'- [{iss["category"]}] {iss["detail"]}')
    summary_lines.append('')
summary_lines.append('## Notes')
summary_lines.append('- Caption and footnote words outside the table bounding box were excluded from metric rows.')
summary_lines.append('- Row and column structure inferred from OCR word bounding boxes using coordinate clustering.')

with open(SUMMARY_MD, 'w', encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))

print(f'Cells: {len(cells)}, Metrics: {len(metrics)}, Issues: {len(issues)}')
