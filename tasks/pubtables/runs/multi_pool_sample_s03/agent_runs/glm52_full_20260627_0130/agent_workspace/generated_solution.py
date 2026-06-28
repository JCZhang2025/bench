#!/usr/bin/env python3
import os, json, csv, re
from collections import defaultdict

INPUT = os.environ['ORIGINAL_WORDS_JSON']
CELLS_OUT = os.environ['OUTPUT_CELLS_CSV']
METRICS_OUT = os.environ['OUTPUT_METRICS_CSV']
AUDIT_OUT = os.environ['OUTPUT_AUDIT_JSON']
SUMMARY_OUT = os.environ['SUMMARY_MD']

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_bbox(word):
    for key in ('bbox', 'bounding_box', 'bounds', 'box'):
        if key in word:
            return word[key]
    if 'x0' in word:
        return [word['x0'], word['y0'], word['x1'], word['y1']]
    if 'left' in word:
        return [word['left'], word['top'], word['right'], word['bottom']]
    return None

def get_text(word):
    for key in ('text', 'token', 'word', 'content'):
        if key in word:
            return str(word[key])
    return ''

def get_table_bbox(data):
    for key in ('table_bbox', 'table_bounds', 'table_box', 'table_bounding_box'):
        if key in data:
            return data[key]
    if 'table' in data and isinstance(data['table'], dict):
        for key in ('bbox', 'bounding_box', 'bounds'):
            if key in data['table']:
                return data['table'][key]
    return None

def get_words(data):
    for key in ('words', 'tokens', 'page_words', 'ocr_words'):
        if key in data:
            return data[key]
    if isinstance(data, list):
        return data
    return []

def inside(bbox, table_bbox, margin=2):
    if not bbox or not table_bbox:
        return True
    return (bbox[0] >= table_bbox[0] - margin and
            bbox[1] >= table_bbox[1] - margin and
            bbox[2] <= table_bbox[2] + margin and
            bbox[3] <= table_bbox[3] + margin)

def center(bbox):
    return ((bbox[0]+bbox[2])/2.0, (bbox[1]+bbox[3])/2.0)

def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 1:
        return s[n//2]
    return (s[n//2-1]+s[n//2])/2.0

def group_rows(words):
    if not words:
        return []
    words_sorted = sorted(words, key=lambda w: (center(w['bbox'])[1], center(w['bbox'])[0]))
    heights = [w['bbox'][3]-w['bbox'][1] for w in words_sorted if w['bbox'][3] > w['bbox'][1]]
    med_h = median(heights) if heights else 10
    tol = max(med_h * 0.6, 5)
    rows = []
    for w in words_sorted:
        placed = False
        for row in rows:
            if abs(center(w['bbox'])[1] - row['y_center']) < tol:
                row['words'].append(w)
                ys = [center(x['bbox'])[1] for x in row['words']]
                row['y_center'] = sum(ys)/len(ys)
                placed = True
                break
        if not placed:
            rows.append({'words': [w], 'y_center': center(w['bbox'])[1]})
    rows.sort(key=lambda r: r['y_center'])
    return rows

def infer_columns(rows):
    all_centers = []
    for row in rows:
        for w in row['words']:
            all_centers.append(center(w['bbox'])[0])
    if not all_centers:
        return []
    all_centers.sort()
    gaps = []
    for i in range(1, len(all_centers)):
        gaps.append(all_centers[i]-all_centers[i-1])
    med_gap = median(gaps) if gaps else 10
    threshold = max(med_gap * 3, 20)
    clusters = []
    for c in all_centers:
        if clusters and c - clusters[-1][-1] < threshold:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    bands = []
    for cl in clusters:
        bands.append((min(cl), max(cl)))
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < threshold/2:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b[1]))
        else:
            merged.append(b)
    return merged

def assign_column(word_center_x, columns):
    best_idx = 0
    best_overlap = -1
    for i, (lo, hi) in enumerate(columns):
        if lo <= word_center_x <= hi:
            return i
        dist = 0
        if word_center_x < lo:
            dist = lo - word_center_x
        elif word_center_x > hi:
            dist = word_center_x - hi
        if best_overlap < 0 or dist < best_overlap:
            best_overlap = dist
            best_idx = i
    return best_idx

def assemble_text(cell_words):
    cell_words.sort(key=lambda w: center(w['bbox'])[0])
    parts = [w['text'] for w in cell_words]
    text = ' '.join(parts)
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_header_row(row, table_bbox, all_rows):
    if not all_rows:
        return False
    min_y = min(center(r['y_center'] if 'y_center' in r else 0) for r in [{}]) if False else min(r['y_center'] for r in all_rows)
    return abs(row['y_center'] - min_y) < 5 or row['y_center'] <= min_y + 15

def parse_number(s):
    if s is None or s == '':
        return None
    s = str(s).strip().replace('%', '').replace(',', '')
    if s == '' or s == '-' or s == 'N/A' or s.lower() == 'none':
        return None
    try:
        return float(s)
    except:
        return None

def normalize_method(text):
    t = text.strip()
    t = re.sub(r'\s*\[.*?\]\s*', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t

def normalize_dataset(text):
    t = text.strip()
    t = re.sub(r'\s+', ' ', t)
    return t

def main():
    data = load_json(INPUT)
    table_bbox = get_table_bbox(data)
    all_words = get_words(data)
    table_words = []
    excluded_words = []
    for w in all_words:
        bbox = get_bbox(w)
        text = get_text(w)
        if not text.strip():
            continue
        if bbox and table_bbox and not inside(bbox, table_bbox):
            excluded_words.append(text)
            continue
        table_words.append({'text': text, 'bbox': bbox})
    rows = group_rows(table_words)
    columns = infer_columns(rows)
    if not columns:
        columns = [(0, 1)]
    cells = []
    for r_idx, row in enumerate(rows):
        header = (r_idx == 0)
        col_buckets = defaultdict(list)
        for w in row['words']:
            cx = center(w['bbox'])[0]
            c_idx = assign_column(cx, columns)
            col_buckets[c_idx].append(w)
        for c_idx, cwords in sorted(col_buckets.items()):
            text = assemble_text(cwords)
            if text.strip():
                cells.append({
                    'row_id': r_idx,
                    'col_id': c_idx,
                    'row_span': 1,
                    'col_span': 1,
                    'is_header': header,
                    'text': text
                })
    with open(CELLS_OUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['row_id','col_id','row_span','col_span','is_header','text'])
        writer.writeheader()
        for cell in cells:
            writer.writerow(cell)
    header_cells = [c for c in cells if c['is_header']]
    body_cells = [c for c in cells if not c['is_header']]
    col_names = {}
    for c in header_cells:
        col_names[c['col_id']] = c['text'].strip().lower()
    body_by_row = defaultdict(dict)
    for c in body_cells:
        body_by_row[c['row_id']][c['col_id']] = c['text']
    metrics = []
    issues = []
    for r_idx in sorted(body_by_row.keys()):
        row_data = body_by_row[r_idx]
        method = ''
        dataset = ''
        accuracy = ''
        f1 = ''
        notes = ''
        for c_idx, text in row_data.items():
            col_name = col_names.get(c_idx, '')
            if 'method' in col_name or 'model' in col_name or 'approach' in col_name or 'system' in col_name:
                method = normalize_method(text)
            elif 'dataset' in col_name or 'data' in col_name or 'corpus' in col_name or 'benchmark' in col_name:
                dataset = normalize_dataset(text)
            elif 'acc' in col_name:
                accuracy = text.strip()
            elif 'f1' in col_name or 'f-score' in col_name or 'fscore' in col_name:
                f1 = text.strip()
            elif 'note' in col_name or 'remark' in col_name or 'comment' in col_name:
                notes = text.strip()
        if not method and not dataset and not accuracy and not f1:
            continue
        if not method:
            method = row_data.get(0, '')
            method = normalize_method(method) if method else ''
        if not dataset:
            for c_idx, text in row_data.items():
                col_name = col_names.get(c_idx, '')
                if c_idx not in col_names or col_name == '':
                    dataset = normalize_dataset(text)
                    break
        acc_val = parse_number(accuracy)
        f1_val = parse_number(f1)
        if accuracy and acc_val is None:
            issues.append(f'Row {r_idx}: accuracy value "{accuracy}" is non-numeric')
        if f1 and f1_val is None:
            issues.append(f'Row {r_idx}: f1 value "{f1}" is non-numeric')
        if not method:
            issues.append(f'Row {r_idx}: missing method field')
        if not dataset:
            issues.append(f'Row {r_idx}: missing dataset field')
        metrics.append({
            'method': method,
            'dataset': dataset,
            'accuracy': accuracy,
            'f1': f1,
            'notes': notes
        })
    with open(METRICS_OUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['method','dataset','accuracy','f1','notes'])
        writer.writeheader()
        for m in metrics:
            writer.writerow(m)
    best_by_dataset = {}
    for m in metrics:
        ds = m['dataset']
        f1_val = parse_number(m['f1'])
        if f1_val is not None:
            if ds not in best_by_dataset or f1_val > best_by_dataset[ds]['f1']:
                best_by_dataset[ds] = {'method': m['method'], 'f1': f1_val}
        else:
            if ds not in best_by_dataset:
                best_by_dataset[ds] = {'method': m['method'], 'f1': None}
    if excluded_words:
        issues.append(f'Excluded {len(excluded_words)} caption/footnote words outside table bounding box')
    if not metrics:
        issues.append('No metric rows extracted from table body')
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': best_by_dataset,
        'issues': issues
    }
    with open(AUDIT_OUT, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    lines = []
    lines.append('# PubTables Extraction Summary')
    lines.append('')
    lines.append('- **Source**: PubTables-style OCR word JSON with bounding boxes')
    lines.append(f'- **Table cells reconstructed**: {len(cells)} cells ({len(header_cells)} header, {len(body_cells)} body)')
    lines.append(f'- **Normalized metric rows**: {len(metrics)}')
    lines.append(f'- **Excluded caption/footnote words**: {len(excluded_words)}')
    lines.append('')
    lines.append('## Best Method by Dataset (F1)')
    lines.append('')
    if best_by_dataset:
        for ds in sorted(best_by_dataset.keys()):
            info = best_by_dataset[ds]
            f1_str = f"{info['f1']:.4f}" if info['f1'] is not None else 'N/A'
            lines.append(f'- **{ds}**: {info["method"]} (F1={f1_str})')
    else:
        lines.append('- No best method determined (no valid F1 scores found)')
    lines.append('')
    lines.append('## Audit Status')
    lines.append('')
    if issues:
        for issue in issues:
            lines.append(f'- {issue}')
    else:
        lines.append('- No extraction or validation issues detected')
    lines.append('')
    lines.append('## Limitations')
    lines.append('')
    lines.append('- Row and column reconstruction relies on bounding box geometry; merged or misaligned OCR boxes may cause misassignment.')
    lines.append('- Header field mapping uses keyword matching; non-standard column headers may not be recognized.')
    lines.append('- Numeric normalization handles common formats but may not cover all locale-specific conventions.')
    with open(SUMMARY_OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

if __name__ == '__main__':
    main()
