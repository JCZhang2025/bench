import json
import csv
import os
from collections import defaultdict
import re

def load_words_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_table_bounding_box(words_data):
    table_bbox = words_data.get('table_bbox', {})
    if not table_bbox:
        # Fallback: use the first word's bbox as table bbox
        if words_data.get('words'):
            first_word = words_data['words'][0]
            table_bbox = {
                'x0': first_word['bbox'][0],
                'y0': first_word['bbox'][1],
                'x1': first_word['bbox'][2],
                'y1': first_word['bbox'][3]
            }
    return table_bbox

def is_inside_table(word_bbox, table_bbox):
    x0, y0, x1, y1 = word_bbox
    return (x0 >= table_bbox['x0'] and y0 >= table_bbox['y0'] and 
            x1 <= table_bbox['x1'] and y1 <= table_bbox['y1'])

def reconstruct_table_cells(words_data, table_bbox):
    words = words_data.get('words', [])
    
    # Filter words inside table bbox
    table_words = [word for word in words if is_inside_table(word['bbox'], table_bbox)]
    
    # Sort words by y-coordinate (top to bottom) then x-coordinate (left to right)
    table_words.sort(key=lambda w: (w['bbox'][1], w['bbox'][0]))
    
    # Group words into rows based on y-coordinate proximity
    rows = []
    current_row = []
    current_y = None
    
    for word in table_words:
        y = word['bbox'][1]
        if current_y is None or abs(y - current_y) < 10:  # Same row threshold
            current_row.append(word)
            current_y = y
        else:
            rows.append(sorted(current_row, key=lambda w: w['bbox'][0]))
            current_row = [word]
            current_y = y
    
    if current_row:
        rows.append(sorted(current_row, key=lambda w: w['bbox'][0]))
    
    # Group words into columns within each row
    cells = []
    row_id = 0
    
    for row in rows:
        col_id = 0
        current_col = []
        current_x = None
        
        for word in row:
            x = word['bbox'][0]
            if current_x is None or abs(x - current_x) < 10:  # Same column threshold
                current_col.append(word)
                current_x = x
            else:
                # Merge words in the same column
                col_text = ' '.join([w['text'] for w in current_col])
                cells.append({
                    'row_id': row_id,
                    'col_id': col_id,
                    'row_span': 1,
                    'col_span': 1,
                    'is_header': row_id == 0,  # First row is header
                    'text': col_text.strip()
                })
                col_id += 1
                current_col = [word]
                current_x = x
        
        # Add last column in the row
        if current_col:
            col_text = ' '.join([w['text'] for w in current_col])
            cells.append({
                'row_id': row_id,
                'col_id': col_id,
                'row_span': 1,
                'col_span': 1,
                'is_header': row_id == 0,
                'text': col_text.strip()
            })
        
        row_id += 1
    
    return cells

def normalize_metrics(cells):
    metrics = []
    
    # Skip header row (row_id = 0)
    for cell in cells:
        if cell['row_id'] == 0:
            continue
        
        text = cell['text']
        
        # Extract method, dataset, accuracy, f1, and notes
        method_match = re.search(r'([A-Za-z0-9_]+)', text)
        dataset_match = re.search(r'([A-Za-z0-9_]+)', text)
        accuracy_match = re.search(r'([0-9.]+)%?', text)
        f1_match = re.search(r'([0-9.]+)%?', text)
        
        method = method_match.group(1) if method_match else ''
        dataset = dataset_match.group(1) if dataset_match else ''
        accuracy = float(accuracy_match.group(1)) / 100 if accuracy_match else None
        f1 = float(f1_match.group(1)) / 100 if f1_match else None
        notes = text.replace(method, '').replace(dataset, '').replace(str(accuracy), '').replace(str(f1), '').strip()
        
        if method and dataset and (accuracy is not None or f1 is not None):
            metrics.append({
                'method': method,
                'dataset': dataset,
                'accuracy': accuracy,
                'f1': f1,
                'notes': notes
            })
    
    return metrics

def audit_metrics(metrics):
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    if not metrics:
        audit['issues'].append('No metric rows found')
        return audit
    
    # Find best method by F1 score for each dataset
    dataset_methods = defaultdict(list)
    for metric in metrics:
        dataset_methods[metric['dataset']].append(metric)
    
    for dataset, methods in dataset_methods.items():
        best_method = max(methods, key=lambda m: m['f1'] if m['f1'] is not None else -1)
        audit['best_by_dataset'][dataset] = {
            'method': best_method['method'],
            'f1': best_method['f1']
        }
    
    # Check for issues
    for metric in metrics:
        if metric['accuracy'] is None and metric['f1'] is None:
            audit['issues'].append(f'Missing both accuracy and F1 for {metric["method"]} on {metric["dataset"]}')
        if metric['accuracy'] is not None and (metric['accuracy'] < 0 or metric['accuracy'] > 1):
            audit['issues'].append(f'Invalid accuracy value for {metric["method"]} on {metric["dataset"]}: {metric["accuracy"]}')
        if metric['f1'] is not None and (metric['f1'] < 0 or metric['f1'] > 1):
            audit['issues'].append(f'Invalid F1 value for {metric["method"]} on {metric["dataset"]}: {metric["f1"]}')
    
    return audit

def generate_summary(metrics, audit):
    summary = "# Table Extraction Summary\n\n"
    summary += f"- **Total metric rows extracted**: {audit['row_count']}\n"
    summary += f"- **Datasets found**: {len(audit['best_by_dataset'])}\n\n"
    
    if audit['best_by_dataset']:
        summary += "## Best Methods by Dataset\n\n"
        for dataset, best in audit['best_by_dataset'].items():
            summary += f"- **{dataset}**: {best['method']} (F1: {best['f1']:.2f})\n"
        summary += "\n"
    
    if audit['issues']:
        summary += "## Issues Found\n\n"
        for issue in audit['issues']:
            summary += f"- {issue}\n"
    else:
        summary += "## No Issues Found\n"
    
    return summary

def write_csv(data, file_path):
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def write_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def write_markdown(text, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

def main():
    # Load input data
    input_path = os.environ.get('ORIGINAL_WORDS_JSON')
    if not input_path:
        raise ValueError('ORIGINAL_WORDS_JSON environment variable not set')
    
    words_data = load_words_json(input_path)
    table_bbox = extract_table_bounding_box(words_data)
    
    # Reconstruct table cells
    cells = reconstruct_table_cells(words_data, table_bbox)
    
    # Normalize metrics
    metrics = normalize_metrics(cells)
    
    # Audit metrics
    audit = audit_metrics(metrics)
    
    # Generate summary
    summary = generate_summary(metrics, audit)
    
    # Write outputs
    output_dir = os.path.dirname(os.environ.get('OUTPUT_CELLS_CSV'))
    os.makedirs(output_dir, exist_ok=True)
    
    write_csv(cells, os.environ.get('OUTPUT_CELLS_CSV'))
    write_csv(metrics, os.environ.get('OUTPUT_METRICS_CSV'))
    write_json(audit, os.environ.get('OUTPUT_AUDIT_JSON'))
    write_markdown(summary, os.environ.get('SUMMARY_MD'))

if __name__ == '__main__':
    main()