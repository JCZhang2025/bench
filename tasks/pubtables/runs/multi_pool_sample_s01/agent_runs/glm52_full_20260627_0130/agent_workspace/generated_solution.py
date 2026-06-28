#!/usr/bin/env python3
import os, json, csv, re, statistics
from collections import defaultdict

INPUT = os.environ['ORIGINAL_WORDS_JSON']
CELLS_OUT = os.environ['OUTPUT_CELLS_CSV']
METRICS_OUT = os.environ['OUTPUT_METRICS_CSV']
AUDIT_OUT = os.environ['OUTPUT_AUDIT_JSON']
SUMMARY_OUT = os.environ['SUMMARY_MD']

for p in [CELLS_OUT, METRICS_OUT, AUDIT_OUT, SUMMARY_OUT]:
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)

with open(INPUT, 'r', encoding='utf-8') as f:
    raw = json.load(f)

# ---- Normalize input structure ----
table_bbox = None
words = []
if isinstance(raw, dict):
    for k in ('table_bbox', 'table_bbox', 'bbox'):
        if k in raw:
            table_bbox = raw[k]; break
    if 'words' in raw:
        words = raw['words']
    elif 'page_words' in raw:
        words = raw['page_words']
    elif 'tokens' in raw:
        words = raw['tokens']
elif isinstance(raw, list):
    words = raw

def to_list(v):
    if v is None: return None
    if isinstance(v, (list, tuple)): return list(v)
    if isinstance(v, dict):
        for kk in ('bbox','box','bounding_box','coordinates'):
            if kk in v: return to_list(v[kk])
    if isinstance(v, str):
        nums = re.findall(r'-?\d+\.?\d*', v)
        return [float(x) for x in nums]
    return None

def get_text(w):
    for k in ('text','word','token','content','value'):
        if k in w and isinstance(w[k], str): return w[k]
    return ''

def get_bbox(w):
    for k in ('bbox','box','bounding_box','coordinates'):
        if k in w: return to_list(w[k])
    return None

if table_bbox is None:
    table_bbox = [0, 0, 1e9, 1e9]
else:
    table_bbox = to_list(table_bbox) or [0, 0, 1e9, 1e9]

tx0, ty0, tx1, ty1 = table_bbox[0], table_bbox[1], table_bbox[2], table_bbox[3]

tokens = []
for w in words:
    if isinstance(w, str):
        continue
    t = get_text(w)
    if not t.strip():
        continue
    bb = get_bbox(w)
    if not bb or len(bb) < 4:
        continue
    x0, y0, x1, y1 = bb[0], bb[1], bb[2], bb[3]
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    # keep tokens whose center is inside table bbox
    if cx < tx0 or cx > tx1 or cy < ty0 or cy > ty1:
        continue
    tokens.append({'text': t, 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                   'cx': cx, 'cy': cy, 'w': x1 - x0, 'h': y1 - y0})

tokens.sort(key=lambda t: (t['cy'], t['cx']))

# ---- Row grouping ----
rows = []
if tokens:
    heights = [t['h'] for t in tokens if t['h'] > 0]
    med_h = statistics.median(heights) if heights else 10.0
    row_tol = med_h * 0.6
    for tok in tokens:
        placed = False
        for r in rows:
            if abs(tok['cy'] - r['center']) <= row_tol:
                r['tokens'].append(tok)
                r['center'] = sum(t['cy'] for t in r['tokens']) / len(r['tokens'])
                placed = True
                break
        if not placed:
            rows.append({'center': tok['cy'], 'tokens': [tok]})
    rows.sort(key=lambda r: r['center'])
    for r in rows:
        r['tokens'].sort(key=lambda t: t['cx'])

# ---- Column inference ----
all_x = []
for r in rows:
    for t in r['tokens']:
        all_x.append(t['cx'])

if all_x:
    all_x.sort()
    gaps = []
    for i in range(1, len(all_x)):
        gaps.append((all_x[i] - all_x[i-1], all_x[i-1], all_x[i]))
    med_gap = statistics.median([g[0] for g in gaps]) if gaps else 0
    big_gaps = [g for g in gaps if g[0] > max(med_gap * 2.5, med_h * 1.5)]
    boundaries = [tx0]
    for g in big_gaps:
        mid = (g[1] + g[2]) / 2.0
        if mid > boundaries[-1] + 1:
            boundaries.append(mid)
    boundaries.append(tx1)
    col_ranges = [(boundaries[i], boundaries[i+1]) for i in range(len(boundaries)-1)]
else:
    col_ranges = [(tx0, tx1)]

def assign_col(cx):
    best_i, best_ov = 0, -1
    for i, (c0, c1) in enumerate(col_ranges):
        if c0 <= cx <= c1:
            return i
        ov = min(cx, c1) - max(cx, c0)
        if ov > best_ov:
            best_ov = ov; best_i = i
    return best_i

# ---- Build cells ----
cells = []
for ri, r in enumerate(rows):
    buckets = defaultdict(list)
    for t in r['tokens']:
        buckets[assign_col(t['cx'])].append(t)
    for ci, toks in sorted(buckets.items()):
        toks.sort(key=lambda t: t['cx'])
        text = ' '.join(t['text'] for t in toks)
        text = re.sub(r'\s+([,.;:])', r'\1', text)
        is_header = (ri == 0)
        cells.append({
            'row_id': ri, 'col_id': ci, 'row_span': 1, 'col_span': 1,
            'is_header': is_header, 'text': text.strip()
        })

# ---- Write cells CSV ----
with open(CELLS_OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['row_id','col_id','row_span','col_span','is_header','text'])
    w.writeheader()
    for c in cells:
        w.writerow(c)

# ---- Normalize metrics ----
# Determine header labels
header_labels = {}
if cells:
    for c in cells:
        if c['is_header']:
            header_labels[c['col_id']] = c['text'].lower().strip()

# Map columns to roles by header text
method_col = dataset_col = acc_col = f1_col = notes_col = None
for ci, label in header_labels.items():
    if 'method' in label or 'model' in label or 'approach' in label:
        method_col = ci
    elif 'dataset' in label or 'data' in label or 'corpus' in label:
        dataset_col = ci
    elif 'acc' in label:
        acc_col = ci
    elif 'f1' in label or 'f-score' in label or 'fscore' in label:
        f1_col = ci
    elif 'note' in label or 'remark' in label or 'comment' in label:
        notes_col = ci

# Fallback: if no header match, try positional
body_cells = [c for c in cells if not c['is_header']]
if method_col is None and body_cells:
    all_cols = sorted(set(c['col_id'] for c in cells))
    if len(all_cols) >= 1: method_col = all_cols[0]
    if len(all_cols) >= 2: dataset_col = all_cols[1]
    if len(all_cols) >= 3: acc_col = all_cols[2]
    if len(all_cols) >= 4: f1_col = all_cols[3]
    if len(all_cols) >= 5: notes_col = all_cols[4]

# Group body cells by row
row_cells = defaultdict(dict)
for c in body_cells:
    row_cells[c['row_id']][c['col_id']] = c['text']

def parse_num(s):
    if s is None: return None
    s = s.strip().replace('%','').replace(',','')
    if not s: return None
    try:
        return float(s)
    except:
        m = re.search(r'-?\d+\.?\d*', s)
        return float(m.group()) if m else None

metrics = []
for ri in sorted(row_cells.keys()):
    rc = row_cells[ri]
    method = rc.get(method_col, '').strip() if method_col is not None else ''
    dataset = rc.get(dataset_col, '').strip() if dataset_col is not None else ''
    acc_raw = rc.get(acc_col, '') if acc_col is not None else ''
    f1_raw = rc.get(f1_col, '') if f1_col is not None else ''
    notes = rc.get(notes_col, '').strip() if notes_col is not None else ''
    if not method and not dataset and not acc_raw and not f1_raw:
        continue
    acc = parse_num(acc_raw)
    f1 = parse_num(f1_raw)
    metrics.append({
        'method': method, 'dataset': dataset,
        'accuracy': acc if acc is not None else '',
        'f1': f1 if f1 is not None else '',
        'notes': notes
    })

with open(METRICS_OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['method','dataset','accuracy','f1','notes'])
    w.writeheader()
    for m in metrics:
        w.writerow(m)

# ---- Audit ----
issues = []
required_cols = ['method','dataset','accuracy','f1','notes']
for col in required_cols:
    # check column presence in metrics output
    pass

# numeric parse check
for i, m in enumerate(metrics):
    if m['accuracy'] == '':
        issues.append({'type':'non_numeric_metric','row':i,'field':'accuracy','value':''})
    if m['f1'] == '':
        issues.append({'type':'non_numeric_metric','row':i,'field':'f1','value':''})
    if not m['method']:
        issues.append({'type':'empty_required_text','row':i,'field':'method'})
    if not m['dataset']:
        issues.append({'type':'empty_required_text','row':i,'field':'dataset'})

# duplicate check
seen = {}
for i, m in enumerate(metrics):
    key = (m['method'], m['dataset'])
    if key in seen:
        issues.append({'type':'duplicate_record','row':i,'key':list(key)})
    else:
        seen[key] = i

# best by dataset by f1
best_by_dataset = {}
dataset_groups = defaultdict(list)
for m in metrics:
    if m['dataset'] and m['f1'] != '':
        dataset_groups[m['dataset']].append(m)
for ds, group in dataset_groups.items():
    best = max(group, key=lambda x: float(x['f1']))
    best_by_dataset[ds] = {'method': best['method'], 'f1': float(best['f1'])}

audit = {
    'row_count': len(metrics),
    'best_by_dataset': best_by_dataset,
    'issues': issues
}
with open(AUDIT_OUT, 'w', encoding='utf-8') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

# ---- Summary Markdown ----
lines = []
lines.append('# PubTables Reconstruction Summary')
lines.append('')
lines.append(f'- **Reconstructed cells:** {len(cells)}')
lines.append(f'- **Rows detected:** {len(rows)}')
lines.append(f'- **Columns detected:** {len(col_ranges)}')
lines.append(f'- **Normalized metric rows:** {len(metrics)}')
lines.append(f'- **Audit issues:** {len(issues)}')
lines.append('')
if best_by_dataset:
    lines.append('## Best Method by Dataset (F1)')
    lines.append('')
    lines.append('| Dataset | Best Method | F1 |')
    lines.append('|---------|-------------|----|')
    for ds, info in sorted(best_by_dataset.items()):
        lines.append(f'| {ds} | {info["method"]} | {info["f1"]} |')
    lines.append('')
if metrics:
    lines.append('## Extracted Metrics')
    lines.append('')
    lines.append('| Method | Dataset | Accuracy | F1 | Notes |')
    lines.append('|--------|---------|----------|----|-------|')
    for m in metrics:
        lines.append(f'| {m["method"]} | {m["dataset"]} | {m["accuracy"]} | {m["f1"]} | {m["notes"]} |')
    lines.append('')
if issues:
    lines.append('## Audit Issues')
    lines.append('')
    for iss in issues:
        lines.append(f'- {iss["type"]}: {iss}')
    lines.append('')
lines.append('## Notes')
lines.append('')
lines.append('Caption and footnote words outside the table bounding box were excluded from metric rows. '
             'Row and column structure was inferred from OCR word bounding boxes using y-center clustering '
             'and x-gap analysis.')
lines.append('')
with open(SUMMARY_OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Done. Cells:', len(cells), 'Metrics:', len(metrics), 'Issues:', len(issues))
