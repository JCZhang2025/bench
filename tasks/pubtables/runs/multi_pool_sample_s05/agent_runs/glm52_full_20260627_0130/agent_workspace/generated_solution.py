#!/usr/bin/env python3
import os, json, csv, re
from collections import defaultdict

INPUT = os.environ['ORIGINAL_WORDS_JSON']
OUT_CELLS = os.environ['OUTPUT_CELLS_CSV']
OUT_METRICS = os.environ['OUTPUT_METRICS_CSV']
OUT_AUDIT = os.environ['OUTPUT_AUDIT_JSON']
OUT_SUMMARY = os.environ['SUMMARY_MD']

for p in [OUT_CELLS, OUT_METRICS, OUT_AUDIT, OUT_SUMMARY]:
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

table_bbox = data.get('table_bbox') or data.get('table_bbox') or data.get('table_bounds')
words = data.get('words') or data.get('page_words') or data.get('word_boxes') or []

def box_area(b):
    return max(0, b[2]-b[0]) * max(0, b[3]-b[1])

def inside(word_box, tbl_box):
    if tbl_box is None:
        return True
    cx = (word_box[0] + word_box[2]) / 2
    cy = (word_box[1] + word_box[3]) / 2
    return tbl_box[0] <= cx <= tbl_box[2] and tbl_box[1] <= cy <= tbl_box[3]

tbl_words = []
for w in words:
    bbox = w.get('bbox') or w.get('bounding_box') or w.get('box')
    text = w.get('text', '')
    if bbox and text.strip() and inside(bbox, table_bbox):
        tbl_words.append({'text': text.strip(), 'bbox': bbox})

if not tbl_words and table_bbox is None:
    tbl_words = [{'text': w.get('text','').strip(), 'bbox': w.get('bbox') or w.get('bounding_box') or w.get('box')} for w in words if w.get('text','').strip()]

issues = []
if not tbl_words:
    issues.append('No words found inside table bounding box.')

# Cluster words into rows by y-center proximity
if tbl_words:
    ys = sorted([(w['bbox'][1] + w['bbox'][3]) / 2 for w in tbl_words])
    row_threshold = 12
    row_ys = []
    for y in ys:
        if not row_ys or abs(y - row_ys[-1]) > row_threshold:
            row_ys.append(y)
        else:
            row_ys[-1] = (row_ys[-1] + y) / 2

    def assign_row(y):
        best = 0
        best_dist = abs(y - row_ys[0])
        for i, ry in enumerate(row_ys):
            d = abs(y - ry)
            if d < best_dist:
                best_dist = d
                best = i
        return best

    for w in tbl_words:
        yc = (w['bbox'][1] + w['bbox'][3]) / 2
        w['row'] = assign_row(yc)

    # Cluster columns by x-center
    xs = sorted([(w['bbox'][0] + w['bbox'][2]) / 2 for w in tbl_words])
    col_threshold = 20
    col_xs = []
    for x in xs:
        if not col_xs or abs(x - col_xs[-1]) > col_threshold:
            col_xs.append(x)
        else:
            col_xs[-1] = (col_xs[-1] + x) / 2

    def assign_col(x):
        best = 0
        best_dist = abs(x - col_xs[0])
        for i, cx in enumerate(col_xs):
            d = abs(x - cx)
            if d < best_dist:
                best_dist = d
                best = i
        return best

    for w in tbl_words:
        xc = (w['bbox'][0] + w['bbox'][2]) / 2
        w['col'] = assign_col(xc)

    # Merge words in same cell
    cell_map = defaultdict(list)
    for w in tbl_words:
        cell_map[(w['row'], w['col'])].append(w)

    cells = []
    for (r, c), ws in sorted(cell_map.items()):
        ws_sorted = sorted(ws, key=lambda x: x['bbox'][0])
        text = ' '.join(w['text'] for w in ws_sorted)
        cells.append({'row_id': r, 'col_id': c, 'row_span': 1, 'col_span': 1, 'is_header': 1 if r == 0 else 0, 'text': text})
else:
    cells = []

# Write cells CSV
with open(OUT_CELLS, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['row_id','col_id','row_span','col_span','is_header','text'])
    writer.writeheader()
    for c in cells:
        writer.writerow(c)

# Build rows for metric extraction
rows_dict = defaultdict(dict)
for c in cells:
    rows_dict[c['row_id']][c['col_id']] = c['text']

sorted_rows = [rows_dict[r] for r in sorted(rows_dict.keys())]

# Identify header
header = {}
if sorted_rows:
    header = sorted_rows[0]

# Normalize header keys
header_norm = {}
for k, v in header.items():
    vl = v.lower().strip() if v else ''
    if 'method' in vl:
        header_norm[k] = 'method'
    elif 'dataset' in vl or 'data' in vl:
        header_norm[k] = 'dataset'
    elif 'acc' in vl:
        header_norm[k] = 'accuracy'
    elif 'f1' in vl or 'f-1' in vl or 'f 1' in vl:
        header_norm[k] = 'f1'
    elif 'note' in vl:
        header_norm[k] = 'notes'

# If header not recognized, try positional
if not header_norm and len(sorted_rows) > 0 and sorted_rows[0]:
    cols_sorted = sorted(header.keys())
    if len(cols_sorted) >= 4:
        header_norm = {cols_sorted[0]: 'method', cols_sorted[1]: 'dataset', cols_sorted[2]: 'accuracy', cols_sorted[3]: 'f1'}
        if len(cols_sorted) >= 5:
            header_norm[cols_sorted[4]] = 'notes'

metrics = []
for row in sorted_rows[1:]:
    if not row:
        continue
    rec = {'method': '', 'dataset': '', 'accuracy': '', 'f1': '', 'notes': ''}
    for col_id, val in row.items():
        field = header_norm.get(col_id)
        if field:
            rec[field] = val.strip() if val else ''
    # Skip rows that look like caption/footnote or are empty
    if not rec['method'] and not rec['dataset'] and not rec['accuracy'] and not rec['f1']:
        continue
    # Clean numeric fields
    def clean_num(s):
        if not s:
            return ''
        s = s.replace('%', '').replace(' ', '').strip()
        try:
            return str(float(s))
        except:
            return s
    rec['accuracy'] = clean_num(rec['accuracy'])
    rec['f1'] = clean_num(rec['f1'])
    metrics.append(rec)

# Write metrics CSV
with open(OUT_METRICS, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['method','dataset','accuracy','f1','notes'])
    writer.writeheader()
    for m in metrics:
        writer.writerow(m)

# Audit
best_by_dataset = {}
for m in metrics:
    ds = m['dataset'] or 'unknown'
    try:
        f1_val = float(m['f1'])
    except:
        f1_val = -1
    if ds not in best_by_dataset or f1_val > best_by_dataset[ds]['f1']:
        best_by_dataset[ds] = {'method': m['method'], 'f1': f1_val}

# Validation issues
for m in metrics:
    try:
        float(m['accuracy'])
    except:
        issues.append(f"Non-numeric accuracy for method={m['method']}, dataset={m['dataset']}: '{m['accuracy']}'")
    try:
        float(m['f1'])
    except:
        issues.append(f"Non-numeric f1 for method={m['method']}, dataset={m['dataset']}: '{m['f1']}'")

if not metrics:
    issues.append('No metric rows extracted.')

audit = {
    'row_count': len(metrics),
    'best_by_dataset': best_by_dataset,
    'issues': issues
}

with open(OUT_AUDIT, 'w', encoding='utf-8') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)

# Summary Markdown
lines = []
lines.append('# PubTables Reconstruction Summary')
lines.append('')
lines.append(f'- **Reconstructed cells:** {len(cells)}')
lines.append(f'- **Normalized metric rows:** {len(metrics)}')
lines.append(f'- **Datasets found:** {len(best_by_dataset)}')
lines.append(f'- **Issues detected:** {len(issues)}')
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
    lines.append('## Best Method by F1 per Dataset')
    lines.append('')
    for ds, info in best_by_dataset.items():
        lines.append(f'- **{ds}**: {info["method"]} (F1={info["f1"]})')
    lines.append('')
if issues:
    lines.append('## Audit Issues')
    lines.append('')
    for iss in issues:
        lines.append(f'- {iss}')
    lines.append('')
lines.append('## Notes')
lines.append('')
lines.append('Caption and footnote words outside the table bounding box were excluded from metric rows. Cells were reconstructed by clustering OCR word boxes into rows and columns using spatial proximity.')

with open(OUT_SUMMARY, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
