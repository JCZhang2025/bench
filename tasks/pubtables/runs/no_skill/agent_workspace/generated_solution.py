import json
import csv
import os
from collections import defaultdict

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_csv_file(data, file_path, fieldnames):
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_markdown_file(content, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_table_bbox(words_data):
    return words_data.get('table_bbox', {})

def is_inside_table(word, table_bbox):
    x1, y1, x2, y2 = table_bbox.get('x1', 0), table_bbox.get('y1', 0), table_bbox.get('x2', 0), table_bbox.get('y2', 0)
    word_x1, word_y1, word_x2, word_y2 = word.get('x1', 0), word.get('y1', 0), word.get('x2', 0), word.get('y2', 0)
    return word_x1 >= x1 and word_y1 >= y1 and word_x2 <= x2 and word_y2 <= y2

def reconstruct_table_cells(words_data, table_bbox):
    cells = []
    word_groups = defaultdict(list)
    
    for word in words_data.get('words', []):
        if is_inside_table(word, table_bbox):
            word_groups[(word['y1'], word['y2'])].append(word)
    
    sorted_rows = sorted(word_groups.keys(), key=lambda r: (r[0] + r[1]) / 2)
    
    for row_idx, row_key in enumerate(sorted_rows):
        row_words = sorted(word_groups[row_key], key=lambda w: w['x1'])
        
        if not row_words:
            continue
            
        col_start = row_words[0]['x1']
        col_end = row_words[-1]['x2']
        
        for col_idx, word in enumerate(row_words):
            if col_idx == 0 or word['x1'] > col_end + 5:
                col_start = word['x1']
                col_end = word['x2']
                col_span = 1
            else:
                col_end = max(col_end, word['x2'])
                col_span += 1
            
            text = word.get('text', '').strip()
            if text:
                cells.append({
                    'row_id': row_idx,
                    'col_id': col_idx,
                    'row_span': 1,
                    'col_span': col_span,
                    'is_header': row_idx == 0,
                    'text': text
                })
    
    return cells

def normalize_metrics(cells):
    metrics = []
    
    for cell in cells:
        if not cell['is_header'] and cell['text']:
            text = cell['text'].lower().strip()
            
            if 'method' in text or 'dataset' in text or 'accuracy' in text or 'f1' in text:
                continue
                
            parts = text.split(',')
            if len(parts) >= 3:
                method = parts[0].strip()
                dataset = parts[1].strip()
                
                accuracy = None
                f1 = None
                notes = ''
                
                for part in parts[2:]:
                    part = part.strip()
                    if 'accuracy' in part or 'acc' in part:
                        try:
                            acc_value = float(part.split('=')[-1].strip('%'))
                            accuracy = acc_value / 100 if acc_value > 1 else acc_value
                        except:
                            pass
                    elif 'f1' in part or 'f1-score' in part:
                        try:
                            f1_value = float(part.split('=')[-1].strip('%'))
                            f1 = f1_value / 100 if f1_value > 1 else f1_value
                        except:
                            pass
                    else:
                        notes += part + ' '
                
                if accuracy is not None or f1 is not None:
                    metrics.append({
                        'method': method,
                        'dataset': dataset,
                        'accuracy': accuracy,
                        'f1': f1,
                        'notes': notes.strip()
                    })
    
    return metrics

def audit_metrics(metrics):
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    dataset_methods = defaultdict(list)
    for metric in metrics:
        dataset_methods[metric['dataset']].append(metric)
    
    for dataset, method_list in dataset_methods.items():
        best_method = max(method_list, key=lambda m: m.get('f1', 0) or 0)
        audit['best_by_dataset'][dataset] = {
            'method': best_method['method'],
            'f1': best_method.get('f1', 0)
        }
    
    for metric in metrics:
        if metric.get('accuracy') is None and metric.get('f1') is None:
            audit['issues'].append(f'Missing both accuracy and F1 for {metric["method"]} on {metric["dataset"]}')
        if metric.get('accuracy') is not None and (metric['accuracy'] < 0 or metric['accuracy'] > 1):
            audit['issues'].append(f'Invalid accuracy value for {metric["method"]} on {metric["dataset"]}')
        if metric.get('f1') is not None and (metric['f1'] < 0 or metric['f1'] > 1):
            audit['issues'].append(f'Invalid F1 value for {metric["method"]} on {metric["dataset"]}')
    
    return audit

def generate_summary(metrics, audit):
    summary = "# Table Extraction Summary\n\n"
    summary += f"- Total metric rows extracted: {audit['row_count']}\n"
    summary += f"- Best performing methods by dataset:\n"
    
    for dataset, best in audit['best_by_dataset'].items():
        summary += f"  - {dataset}: {best['method']} (F1: {best['f1']:.3f})\n"
    
    if audit['issues']:
        summary += "\n- Extraction issues:\n"
        for issue in audit['issues']:
            summary += f"  - {issue}\n"
    else:
        summary += "\n- No extraction issues detected.\n"
    
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
    
    cells = reconstruct_table_cells(words_data, table_bbox)
    save_csv_file(cells, cells_path, ['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    
    metrics = normalize_metrics(cells)
    save_csv_file(metrics, metrics_path, ['method', 'dataset', 'accuracy', 'f1', 'notes'])
    
    audit = audit_metrics(metrics)
    save_json_file(audit, audit_path)
    
    summary = generate_summary(metrics, audit)
    save_markdown_file(summary, summary_path)

if __name__ == '__main__':
    main()