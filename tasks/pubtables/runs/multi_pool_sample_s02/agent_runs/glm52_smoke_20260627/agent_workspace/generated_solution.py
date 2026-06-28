#!/usr/bin/env python3
import os, json, csv, re
from collections import defaultdict

INPUT = os.environ['ORIGINAL_WORDS_JSON']
CELLS_CSV = os.environ['OUTPUT_CELLS_CSV']
METRICS_CSV = os.environ['OUTPUT_METRICS_CSV']
AUDIT_JSON = os.environ['OUTPUT_AUDIT_JSON']
SUMMARY_MD = os.environ['SUMMARY_MD']

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_bbox(obj):
    for key in ('bbox','bounding_box','bounds','box'):
        if key in obj:
            return obj[key]
    return None

def bbox_vals(bbox):
    if isinstance(bbox, dict):
        x0 = bbox.get('x0', bbox.get('left', bbox.get('x', 0)))
        y0 = bbox.get('y0', bbox.get('top', bbox.get('y', 0)))
        x1 = bbox.get('x1', bbox.get('right', bbox.get('x2', x0)))
        y1 = bbox.get('y1', bbox.get('bottom', bbox.get('y2', y0)))
        return float(x0), float(y0), float(x1), float(y1)
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
    return 0.0, 0.0, 0.0, 0.0

def center(bbox):
    x0, y0, x1, y1 = bbox_vals(bbox)
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0, x1 - x0, y1 - y0

def extract_words(data):
    words = []
    if isinstance(data, dict):
        for key in ('words','page_words','ocr_words','text_words'):
            if key in data and isinstance(data[key], list):
                words = data[key]
                break
        if not words:
            for key in ('pages','page'):
                if key in data:
                    pages = data[key] if isinstance(data[key], list) else [data[key]]
                    for p in pages:
                        if isinstance(p, dict):
                            for wk in ('words','page_words','ocr_words','text_words'):
                                if wk in p and isinstance(p[wk], list):
                                    words.extend(p[wk])
    elif isinstance(data, list):
        words = data
    return words

def get_text(w):
    for k in ('text','word','content','value','string'):
        if k in w:
            return str(w[k])
    return ''

def get_table_bbox(data):
    for key in ('table_bbox','table_bounds','table_region','table_box','table'):
        if key in data:
            v = data[key]
            if isinstance(v, dict) and ('bbox' in v or 'bounding_box' in v or 'bounds' in v):
                return bbox_vals(get_bbox(v))
            return bbox_vals(v)
    return None

def main():
    data = load_json(INPUT)
    raw_words = extract_words(data)
    table_bbox = get_table_bbox(data)

    parsed = []
    for w in raw_words:
        if not isinstance(w, dict):
            continue
        text = get_text(w).strip()
        if not text:
            continue
        bbox = get_bbox(w)
        if bbox is None:
            continue
        cx, cy, wd, ht = center(bbox)
        parsed.append({'text': text, 'cx': cx, 'cy': cy, 'w': wd, 'h': ht, 'bbox': bbox_vals(bbox)})

    if table_bbox is not None:
        tx0, ty0, tx1, ty1 = table_bbox
        margin = 5.0
        table_words = [p for p in parsed if p['bbox'][0] >= tx0 - margin and p['bbox'][2] <= tx1 + margin and p['bbox'][1] >= ty0 - margin and p['bbox'][3] <= ty1 + margin]
    else:
        table_words = parsed

    if not table_words:
        table_words = parsed

    if not table_words:
        for path in [CELLS_CSV, METRICS_CSV]:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if path == CELLS_CSV:
                    writer.writerow(['row_id','col_id','row_span','col_span','is_header','text'])
                else:
                    writer.writerow(['method','dataset','accuracy','f1','notes'])
        audit = {'row_count': 0, 'best_by_dataset': {}, 'issues': ['no_table_words_found']}
        with open(AUDIT_JSON, 'w', encoding='utf-8') as f:
            json.dump(audit, f, indent=2)
        with open(SUMMARY_MD, 'w', encoding='utf-8') as f:
            f.write('# PubTables Reconstruction Summary\n\nNo table words found in input.\n')
        return

    heights = sorted([p['h'] for p in table_words if p['h'] > 0])
    median_h = heights[len(heights)//2] if heights else 10.0
    row_tol = max(median_h * 0.6, 3.0)

    sorted_by_y = sorted(table_words, key=lambda p: p['cy'])
    rows = []
    for w in sorted_by_y:
        placed = False
        for r in rows:
            if abs(r['y'] - w['cy']) <= row_tol:
                r['words'].append(w)
                r['y'] = sum(x['cy'] for x in r['words']) / len(r['words'])
                placed = True
                break
        if not placed:
            rows.append({'y': w['cy'], 'words': [w]})
    rows.sort(key=lambda r: r['y'])

    for r in rows:
        r['words'].sort(key=lambda w: w['cx'])

    all_x = sorted([w['cx'] for w in table_words])
    col_bands = []
    if all_x:
        gaps = []
        for i in range(1, len(all_x)):
            gaps.append((all_x[i] - all_x[i-1], i))
        big_gaps = sorted(gaps, key=lambda g: g[0], reverse=True)
        split_indices = sorted([g[1] for g in big_gaps[:7]])
        prev = 0
        for si in split_indices:
            band_xs = all_x[prev:si]
            if band_xs:
                col_bands.append((min(band_xs), max(band_xs)))
            prev = si
        band_xs = all_x[prev:]
        if band_xs:
            col_bands.append((min(band_xs), max(band_xs)))
        col_bands.sort()

    if not col_bands:
        col_bands = [(0, 99999)]

    def assign_col(cx):
        best_idx = 0
        best_dist = float('inf')
        for i, (lo, hi) in enumerate(col_bands):
            mid = (lo + hi) / 2.0
            d = abs(cx - mid)
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx

    cells = []
    for ri, r in enumerate(rows):
        col_words = defaultdict(list)
        for w in r['words']:
            ci = assign_col(w['cx'])
            col_words[ci].append(w)
        for ci, ws in col_words.items():
            ws.sort(key=lambda w: w['cx'])
            text = ' '.join(w['text'] for w in ws).strip()
            if text:
                cells.append({'row_id': ri, 'col_id': ci, 'row_span': 1, 'col_span': 1, 'is_header': 1 if ri == 0 else 0, 'text': text})

    cells.sort(key=lambda c: (c['row_id'], c['col_id']))

    with open(CELLS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['row_id','col_id','row_span','col_span','is_header','text'])
        for c in cells:
            writer.writerow([c['row_id'], c['col_id'], c['row_span'], c['col_span'], c['is_header'], c['text']])

    header_cells = [c for c in cells if c['is_header']]
    body_cells = [c for c in cells if not c['is_header']]

    col_names = {}
    if header_cells:
        for c in header_cells:
            col_names[c['col_id']] = c['text'].strip().lower()
    else:
        for c in cells[:8]:
            col_names[c['col_id']] = c['text'].strip().lower()

    rows_by_id = defaultdict(dict)
    for c in body_cells:
        rows_by_id[c['row_id']][c['col_id']] = c['text']

    def find_col(*candidates):
        for ci, name in col_names.items():
            for cand in candidates:
                if cand in name:
                    return ci
        return None

    method_ci = find_col('method')
    dataset_ci = find_col('dataset', 'data')
    acc_ci = find_col('acc')
    f1_ci = find_col('f1')
    notes_ci = find_col('note')

    if method_ci is None and body_cells:
        method_ci = min(col_names.keys()) if col_names else 0
    if dataset_ci is None and len(col_names) >= 2:
        sorted_cols = sorted(col_names.keys())
        dataset_ci = sorted_cols[1]
    if acc_ci is None and len(col_names) >= 3:
        sorted_cols = sorted(col_names.keys())
        acc_ci = sorted_cols[2]
    if f1_ci is None and len(col_names) >= 4:
        sorted_cols = sorted(col_names.keys())
        f1_ci = sorted_cols[3]
    if notes_ci is None and len(col_names) >= 5:
        sorted_cols = sorted(col_names.keys())
        notes_ci = sorted_cols[-1]

    def parse_num(s):
        if s is None:
            return None
        s = str(s).strip().replace('%','').replace(',','')
        try:
            return float(s)
        except:
            return None

    metrics = []
    for rid in sorted(rows_by_id.keys()):
        row = rows_by_id[rid]
        method = row.get(method_ci, '').strip() if method_ci is not None else ''
        dataset = row.get(dataset_ci, '').strip() if dataset_ci is not None else ''
        acc = parse_num(row.get(acc_ci)) if acc_ci is not None else None
        f1 = parse_num(row.get(f1_ci)) if f1_ci is not None else None
        notes = row.get(notes_ci, '').strip() if notes_ci is not None else ''
        if not method and not dataset:
            continue
        metrics.append({'method': method, 'dataset': dataset, 'accuracy': acc, 'f1': f1, 'notes': notes})

    with open(METRICS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['method','dataset','accuracy','f1','notes'])
        for m in metrics:
            writer.writerow([m['method'], m['dataset'], m['accuracy'] if m['accuracy'] is not None else '', m['f1'] if m['f1'] is not None else '', m['notes']])

    issues = []
    required_cols = ['method','dataset','accuracy','f1','notes']
    for rc in required_cols:
        if rc not in [col_names.get(k,'') for k in col_names]:
            issues.append(f'missing_or_unmapped_required_column:{rc}')

    for i, m in enumerate(metrics):
        if m['accuracy'] is None:
            issues.append(f'non_numeric_metric:accuracy:row:{i}')
        if m['f1'] is None:
            issues.append(f'non_numeric_metric:f1:row:{i}')
        if not m['method']:
            issues.append(f'empty_required_text:method:row:{i}')
        if not m['dataset']:
            issues.append(f'empty_required_text:dataset:row:{i}')

    seen = set()
    for i, m in enumerate(metrics):
        key = (m['method'], m['dataset'])
        if key in seen:
            issues.append(f'duplicate_record:row:{i}')
        seen.add(key)

    best_by_dataset = {}
    for ds in set(m['dataset'] for m in metrics if m['dataset']):
        ds_rows = [m for m in metrics if m['dataset'] == ds and m['f1'] is not None]
        if ds_rows:
            best = max(ds_rows, key=lambda m: m['f1'])
            best_by_dataset[ds] = {'method': best['method'], 'f1': best['f1']}

    audit = {
        'row_count': len(metrics),
        'best_by_dataset': best_by_dataset,
        'issues': issues,
        'header_columns': col_names,
        'total_cells': len(cells),
        'body_rows': len(rows_by_id)
    }

    with open(AUDIT_JSON, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)

    lines = ['# PubTables Reconstruction Summary', '']
    lines.append(f'**Reconstructed cells:** {len(cells)}  ')
    lines.append(f'**Normalized metric rows:** {len(metrics)}  ')
    lines.append(f'**Audit issues:** {len(issues)}')
    lines.append('')
    lines.append('## Best Method by Dataset (F1)')
    lines.append('')
    if best_by_dataset:
        lines.append('| Dataset | Best Method | F1 |')
        lines.append('|---------|-------------|----|')
        for ds, info in sorted(best_by_dataset.items()):
            lines.append(f'| {ds} | {info["method"]} | {info["f1"]} |')
    else:
        lines.append('No best methods determined.')
    lines.append('')
    lines.append('## Extracted Metrics')
    lines.append('')
    if metrics:
        lines.append('| Method | Dataset | Accuracy | F1 | Notes |')
        lines.append('|--------|---------|----------|----|-------|')
        for m in metrics:
            acc_s = f'{m["accuracy"]}' if m['accuracy'] is not None else ''
            f1_s = f'{m["f1"]}' if m['f1'] is not None else ''
            lines.append(f'| {m["method"]} | {m["dataset"]} | {acc_s} | {f1_s} | {m["notes"]} |')
    else:
        lines.append('No metric rows extracted.')
    lines.append('')
    if issues:
        lines.append('## Audit Issues')
        lines.append('')
        for iss in issues:
            lines.append(f'- {iss}')
        lines.append('')
    with open(SUMMARY_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

if __name__ == '__main__':
    main()
