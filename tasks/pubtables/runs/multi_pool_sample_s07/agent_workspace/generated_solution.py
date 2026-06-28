import json
import csv
import os
from collections import defaultdict

def load_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_csv_file(filepath, data, fieldnames):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def save_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def save_markdown_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def filter_table_words(words, table_bbox):
    table_x1, table_y1, table_x2, table_y2 = table_bbox
    filtered_words = []
    
    for word in words:
        x1, y1, x2, y2 = word['bbox']
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        if (table_x1 <= center_x <= table_x2 and table_y1 <= center_y <= table_y2):
            filtered_words.append(word)
    
    return filtered_words

def reconstruct_table_cells(words, table_bbox):
    filtered_words = filter_table_words(words, table_bbox)
    
    if not filtered_words:
        return []
    
    words_sorted = sorted(filtered_words, key=lambda w: (w['bbox'][1], w['bbox'][0]))
    
    rows = defaultdict(list)
    row_heights = []
    
    for word in words_sorted:
        y1, y2 = word['bbox'][1], word['bbox'][3]
        row_found = False
        
        for i, row_y1 in enumerate(row_heights):
            row_y2 = row_y1 + 20
            if row_y1 <= y1 <= row_y2 or row_y1 <= y2 <= row_y2:
                rows[i].append(word)
                row_found = True
                break
        
        if not row_found:
            new_row_idx = len(row_heights)
            rows[new_row_idx] = [word]
            row_heights.append(y1)
    
    for row_idx in rows:
        rows[row_idx] = sorted(rows[row_idx], key=lambda w: w['bbox'][0])
    
    cells = []
    cell_id = 0
    
    for row_idx in sorted(rows.keys()):
        row_words = rows[row_idx]
        col_x = None
        
        for word in row_words:
            x1, x2 = word['bbox'][0], word['bbox'][2]
            
            if col_x is None or x1 > col_x + 5:
                col_id = len([c for c in cells if c['row_id'] == row_idx])
                
                is_header = row_idx == 0
                
                cell = {
                    'row_id': row_idx,
                    'col_id': col_id,
                    'row_span': 1,
                    'col_span': 1,
                    'is_header': is_header,
                    'text': word['text']
                }
                cells.append(cell)
                cell_id += 1
                col_x = x2
            else:
                last_cell = cells[-1]
                if last_cell['row_id'] == row_idx:
                    last_cell['col_span'] += 1
                    last_cell['text'] += ' ' + word['text']
                    col_x = x2
    
    return cells

def normalize_metrics(cells):
    metrics = []
    
    for cell in cells:
        if cell['is_header']:
            continue
        
        text = cell['text'].strip()
        parts = text.split(',')
        
        if len(parts) >= 4:
            method = parts[0].strip()
            dataset = parts[1].strip()
            accuracy = parts[2].strip()
            f1 = parts[3].strip()
            notes = parts[4].strip() if len(parts) > 4 else ''
            
            try:
                accuracy = float(accuracy)
                f1 = float(f1)
            except ValueError:
                continue
            
            metrics.append({
                'method': method,
                'dataset': dataset,
                'accuracy': accuracy,
                'f1': f1,
                'notes': notes
            })
    
    return metrics

def audit_metrics(metrics, cells):
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    if not metrics:
        audit['issues'].append('No metric rows extracted')
        return audit
    
    dataset_best = {}
    
    for metric in metrics:
        dataset = metric['dataset']
        f1 = metric['f1']
        
        if dataset not in dataset_best or f1 > dataset_best[dataset]['f1']:
            dataset_best[dataset] = metric
    
    audit['best_by_dataset'] = dataset_best
    
    if len(metrics) < 3:
        audit['issues'].append('Few metric rows extracted - possible incomplete table')
    
    return audit

def generate_summary(metrics, audit):
    summary = "# Table Extraction Summary\n\n"
    summary += f"Extracted {audit['row_count']} metric rows.\n\n"
    
    if audit['best_by_dataset']:
        summary += "Best method by dataset:\n"
        for dataset, best in audit['best_by_dataset'].items():
            summary += f"- {dataset}: {best['method']} (F1: {best['f1']:.3f})\n"
        summary += "\n"
    
    if audit['issues']:
        summary += "Issues found:\n"
        for issue in audit['issues']:
            summary += f"- {issue}\n"
    
    return summary

def main():
    input_path = os.environ.get('ORIGINAL_WORDS_JSON')
    cells_path = os.environ.get('OUTPUT_CELLS_CSV')
    metrics_path = os.environ.get('OUTPUT_METRICS_CSV')
    audit_path = os.environ.get('OUTPUT_AUDIT_JSON')
    summary_path = os.environ.get('SUMMARY_MD')
    
    data = load_json_file(input_path)
    table_bbox = data['table_bbox']
    words = data['words']
    
    cells = reconstruct_table_cells(words, table_bbox)
    save_csv_file(cells_path, cells, ['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    
    metrics = normalize_metrics(cells)
    save_csv_file(metrics_path, metrics, ['method', 'dataset', 'accuracy', 'f1', 'notes'])
    
    audit = audit_metrics(metrics, cells)
    save_json_file(audit_path, audit)
    
    summary = generate_summary(metrics, audit)
    save_markdown_file(summary_path, summary)

if __name__ == '__main__':
    main()