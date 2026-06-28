import os
import json
import csv
import re
from collections import defaultdict


def load_input():
    path = os.environ['ORIGINAL_WORDS_JSON']
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_bbox(word):
    for key in ('bbox', 'bounding_box', 'boundingBox', 'box'):
        if key in word:
            return word[key]
    return None


def get_text(word):
    for key in ('text', 'content', 'value'):
        if key in word:
            return str(word[key])
    return ''


def bbox_area(bbox):
    if not bbox or len(bbox) < 4:
        return 0
    x0, y0, x1, y1 = bbox[0], bbox[1], bbox[2], bbox[3]
    return max(0, x1 - x0) * max(0, y1 - y0)


def center_y(bbox):
    return (bbox[1] + bbox[3]) / 2.0


def center_x(bbox):
    return (bbox[0] + bbox[2]) / 2.0


def extract_table_bbox(data):
    if isinstance(data, dict):
        for key in ('table_bbox', 'table_bounding_box', 'table_bbox', 'table'):
            if key in data and isinstance(data[key], (list, tuple)) and len(data[key]) >= 4:
                return data[key]
        if 'words' in data:
            return None
    return None


def extract_words(data):
    if isinstance(data, dict):
        if 'words' in data:
            return data['words']
        if 'page_words' in data:
            return data['page_words']
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and get_bbox(v[0]):
                return v
    if isinstance(data, list):
        return data
    return []


def in_table_bbox(bbox, table_bbox):
    if table_bbox is None:
        return True
    if not bbox or len(bbox) < 4:
        return False
    cx = center_x(bbox)
    cy = center_y(bbox)
    return (cx >= table_bbox[0] and cx <= table_bbox[2] and
            cy >= table_bbox[1] and cy <= table_bbox[3])


def cluster(values, threshold):
    if not values:
        return []
    vals = sorted(values)
    clusters = [[vals[0]]]
    for v in vals[1:]:
        if v - clusters[-1][-1] <= threshold:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [sum(c) / len(c) for c in clusters]


def assign_to_cluster(value, centers):
    best = 0
    best_dist = abs(value - centers[0])
    for i, c in enumerate(centers[1:], 1):
        d = abs(value - c)
        if d < best_dist:
            best_dist = d
            best = i
    return best


def reconstruct_cells(words, table_bbox):
    table_words = []
    for w in words:
        bbox = get_bbox(w)
        text = get_text(w).strip()
        if not text or not bbox or len(bbox) < 4:
            continue
        if not in_table_bbox(bbox, table_bbox):
            continue
        table_words.append({'text': text, 'bbox': bbox})
    
    if not table_words:
        return [], []
    
    ys = [center_y(w['bbox']) for w in table_words]
    xs = [center_x(w['bbox']) for w in table_words]
    
    y_range = max(ys) - min(ys) if ys else 1
    x_range = max(xs) - min(xs) if xs else 1
    
    y_thresh = max(y_range * 0.08, 5.0)
    x_thresh = max(x_range * 0.04, 3.0)
    
    row_centers = cluster(ys, y_thresh)
    col_centers = cluster(xs, x_thresh)
    
    row_centers.sort()
    col_centers.sort()
    
    cell_map = {}
    for w in table_words:
        r = assign_to_cluster(center_y(w['bbox']), row_centers)
        c = assign_to_cluster(center_x(w['bbox']), col_centers)
        if (r, c) not in cell_map:
            cell_map[(r, c)] = []
        cell_map[(r, c)].append(w)
    
    cells = []
    for (r, c), ws in sorted(cell_map.items()):
        ws_sorted = sorted(ws, key=lambda w: w['bbox'][0])
        text = ' '.join(w['text'] for w in ws_sorted).strip()
        if text:
            cells.append({
                'row_id': r,
                'col_id': c,
                'row_span': 1,
                'col_span': 1,
                'is_header': 1 if r == 0 else 0,
                'text': text
            })
    
    return cells, table_words


def parse_number(text):
    t = text.strip().replace('%', '').replace(' ', '')
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def normalize_metrics(cells):
    if not cells:
        return []
    
    max_row = max(c['row_id'] for c in cells)
    max_col = max(c['col_id'] for c in cells)
    
    grid = {}
    for c in cells:
        grid[(c['row_id'], c['col_id'])] = c['text']
    
    header_row = [grid.get((0, c), '') for c in range(max_col + 1)]
    
    def find_header_col(patterns):
        for i, h in enumerate(header_row):
            hl = h.lower().strip()
            for p in patterns:
                if p in hl:
                    return i
        return None
    
    method_col = find_header_col(['method', 'model', 'approach'])
    dataset_col = find_header_col(['dataset', 'data', 'corpus'])
    acc_col = find_header_col(['acc', 'accuracy'])
    f1_col = find_header_col(['f1', 'f-score', 'fscore'])
    notes_col = find_header_col(['note', 'comment', 'remark'])
    
    if method_col is None:
        method_col = 0
    if dataset_col is None:
        dataset_col = 1 if method_col == 0 else 0
    if acc_col is None:
        for i, h in enumerate(header_row):
            if i not in (method_col, dataset_col):
                acc_col = i
                break
    if f1_col is None and acc_col is not None:
        for i, h in enumerate(header_row):
            if i not in (method_col, dataset_col, acc_col):
                f1_col = i
                break
    
    metrics = []
    for r in range(1, max_row + 1):
        method = grid.get((r, method_col), '').strip() if method_col is not None else ''
        dataset = grid.get((r, dataset_col), '').strip() if dataset_col is not None else ''
        acc_text = grid.get((r, acc_col), '') if acc_col is not None else ''
        f1_text = grid.get((r, f1_col), '') if f1_col is not None else ''
        notes = grid.get((r, notes_col), '').strip() if notes_col is not None else ''
        
        if not method and not dataset and not acc_text and not f1_text:
            continue
        
        acc = parse_number(acc_text)
        f1 = parse_number(f1_text)
        
        metrics.append({
            'method': method,
            'dataset': dataset,
            'accuracy': acc if acc is not None else '',
            'f1': f1 if f1 is not None else '',
            'notes': notes
        })
    
    return metrics


def audit_metrics(metrics):
    issues = []
    
    for i, m in enumerate(metrics):
        if not m['method']:
            issues.append(f'Row {i+1}: missing method name')
        if not m['dataset']:
            issues.append(f'Row {i+1}: missing dataset name')
        if m['accuracy'] == '':
            issues.append(f'Row {i+1}: accuracy not parseable')
        if m['f1'] == '':
            issues.append(f'Row {i+1}: f1 not parseable')
        for field in ('accuracy', 'f1'):
            val = m[field]
            if val != '':
                try:
                    v = float(val)
                    if v < 0 or v > 100:
                        issues.append(f'Row {i+1}: {field} value {v} out of expected 0-100 range')
                except (ValueError, TypeError):
                    pass
    
    best_by_dataset = {}
    by_dataset = defaultdict(list)
    for m in metrics:
        ds = m['dataset']
        if ds:
            by_dataset[ds].append(m)
    
    for ds, rows in by_dataset.items():
        best = None
        best_f1 = -1
        for m in rows:
            if m['f1'] != '':
                try:
                    f1_val = float(m['f1'])
                    if f1_val > best_f1:
                        best_f1 = f1_val
                        best = m
                except (ValueError, TypeError):
                    pass
        if best:
            best_by_dataset[ds] = {
                'method': best['method'],
                'f1': best['f1'],
                'accuracy': best['accuracy']
            }
    
    return {
        'row_count': len(metrics),
        'best_by_dataset': best_by_dataset,
        'issues': issues
    }


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_summary(path, metrics, audit):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = ['# Table Reconstruction Summary', '']
    lines.append(f'Extracted **{audit["row_count"]}** normalized metric rows from the table.')
    lines.append('')
    if audit['best_by_dataset']:
        lines.append('## Best Method by Dataset (F1)')
        lines.append('')
        lines.append('| Dataset | Best Method | F1 | Accuracy |')
        lines.append('|---------|-------------|----|----------|')
        for ds, info in audit['best_by_dataset'].items():
            lines.append(f'| {ds} | {info["method"]} | {info["f1"]} | {info["accuracy"]} |')
        lines.append('')
    if audit['issues']:
        lines.append('## Audit Issues')
        lines.append('')
        for issue in audit['issues']:
            lines.append(f'- {issue}')
        lines.append('')
    if metrics:
        lines.append('## Extracted Metrics')
        lines.append('')
        lines.append('| Method | Dataset | Accuracy | F1 |')
        lines.append('|--------|---------|----------|----|')
        for m in metrics:
            lines.append(f'| {m["method"]} | {m["dataset"]} | {m["accuracy"]} | {m["f1"]} |')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    data = load_input()
    table_bbox = extract_table_bbox(data)
    words = extract_words(data)
    
    cells, table_words = reconstruct_cells(words, table_bbox)
    metrics = normalize_metrics(cells)
    audit = audit_metrics(metrics)
    
    write_csv(os.environ['OUTPUT_CELLS_CSV'], cells,
              ['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    write_csv(os.environ['OUTPUT_METRICS_CSV'], metrics,
              ['method', 'dataset', 'accuracy', 'f1', 'notes'])
    write_json(os.environ['OUTPUT_AUDIT_JSON'], audit)
    write_summary(os.environ['SUMMARY_MD'], metrics, audit)


if __name__ == '__main__':
    main()