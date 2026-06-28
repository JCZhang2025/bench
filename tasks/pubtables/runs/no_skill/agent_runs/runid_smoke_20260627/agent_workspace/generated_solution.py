import json
import csv
import os
from collections import defaultdict

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_csv_file(file_path, data, fieldnames):
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def write_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def write_markdown_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_table_bbox(words_data):
    return words_data.get('table_bbox', [0, 0, 0, 0])

def filter_table_words(words_data, table_bbox):
    table_words = []
    for word in words_data.get('words', []):
        bbox = word.get('bbox', [0, 0, 0, 0])
        x1, y1, x2, y2 = bbox
        tx1, ty1, tx2, ty2 = table_bbox
        if x1 >= tx1 and y1 >= ty1 and x2 <= tx2 and y2 <= ty2:
            table_words.append(word)
    return table_words

def reconstruct_cells(table_words):
    cells = []
    word_positions = defaultdict(list)
    
    for word in table_words:
        bbox = word.get('bbox', [0, 0, 0, 0])
        x1, y1, x2, y2 = bbox
        word_positions[y1].append((x1, word))
    
    sorted_rows = sorted(word_positions.keys())
    
    for row_idx, y_pos in enumerate(sorted_rows):
        row_words = sorted(word_positions[y_pos], key=lambda x: x[0])
        
        if not row_words:
            continue
            
        col_start = row_words[0][0]
        current_col = 0
        current_text = []
        
        for x_pos, word in row_words:
            if x_pos - col_start > 10:
                if current_text:
                    cells.append({
                        'row_id': row_idx,
                        'col_id': current_col,
                        'row_span': 1,
                        'col_span': 1,
                        'is_header': row_idx == 0,
                        'text': ' '.join(current_text).strip()
                    })
                    current_col += 1
                    current_text = []
                    col_start = x_pos
            current_text.append(word.get('text', ''))
        
        if current_text:
            cells.append({
                'row_id': row_idx,
                'col_id': current_col,
                'row_span': 1,
                'col_span': 1,
                'is_header': row_idx == 0,
                'text': ' '.join(current_text).strip()
            })
    
    return cells

def normalize_metrics(cells):
    metrics = []
    
    for cell in cells:
        if cell['is_header']:
            continue
            
        text = cell['text'].strip()
        if not text:
            continue
            
        parts = text.split()
        if len(parts) < 4:
            continue
            
        method = parts[0]
        dataset = parts[1]
        
        try:
            accuracy = float(parts[2])
            f1 = float(parts[3])
            notes = ' '.join(parts[4:]) if len(parts) > 4 else ''
            
            metrics.append({
                'method': method,
                'dataset': dataset,
                'accuracy': accuracy,
                'f1': f1,
                'notes': notes
            })
        except (ValueError, IndexError):
            continue
    
    return metrics

def audit_metrics(metrics):
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    dataset_metrics = defaultdict(list)
    for metric in metrics:
        dataset_metrics[metric['dataset']].append(metric)
    
    for dataset, dataset_metric_list in dataset_metrics.items():
        best_metric = max(dataset_metric_list, key=lambda x: x['f1'])
        audit['best_by_dataset'][dataset] = {
            'method': best_metric['method'],
            'f1': best_metric['f1']
        }
    
    if len(metrics) == 0:
        audit['issues'].append('No metrics extracted')
    
    return audit

def generate_summary(metrics, audit):
    summary = "# Table Extraction Summary\n\n"
    summary += f"- Total metric rows extracted: {audit['row_count']}\n"
    summary += "- Best performing methods by dataset:\n"
    
    for dataset, best in audit['best_by_dataset'].items():
        summary += f"  - {dataset}: {best['method']} (F1: {best['f1']:.3f})\n"
    
    if audit['issues']:
        summary += "- Issues encountered:\n"
        for issue in audit['issues']:
            summary += f"  - {issue}\n"
    
    return summary

def main():
    input_path = os.environ.get('ORIGINAL_WORDS_JSON')
    cells_path = os.environ.get('OUTPUT_CELLS_CSV')
    metrics_path = os.environ.get('OUTPUT_METRICS_CSV')
    audit_path = os.environ.get('OUTPUT_AUDIT_JSON')
    summary_path = os.environ.get('SUMMARY_MD')
    
    if not all([input_path, cells_path, metrics_path, audit_path, summary_path]):
        raise ValueError("Missing required environment variables")
    
    words_data = load_json_file(input_path)
    table_bbox = extract_table_bbox(words_data)
    table_words = filter_table_words(words_data, table_bbox)
    
    cells = reconstruct_cells(table_words)
    metrics = normalize_metrics(cells)
    audit = audit_metrics(metrics)
    summary = generate_summary(metrics, audit)
    
    os.makedirs(os.path.dirname(cells_path), exist_ok=True)
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    os.makedirs(os.path.dirname(audit_path), exist_ok=True)
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    
    write_csv_file(cells_path, cells, ['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    write_csv_file(metrics_path, metrics, ['method', 'dataset', 'accuracy', 'f1', 'notes'])
    write_json_file(audit_path, audit)
    write_markdown_file(summary_path, summary)

if __name__ == '__main__':
    main()