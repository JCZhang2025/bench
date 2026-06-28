import json
import csv
import os
from collections import defaultdict
import re

def load_words_json(file_path):
    """Load the original words JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_table_bounds(words_data):
    """Extract the table bounding box from the words data."""
    table_bbox = words_data.get('table_bbox', {})
    if not table_bbox:
        # If no explicit table bbox, use the first word's bbox as fallback
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
    """Check if a word is inside the table bounding box."""
    if not table_bbox:
        return True
    
    x0, y0, x1, y1 = word_bbox
    return (x0 >= table_bbox['x0'] and y0 >= table_bbox['y0'] and 
            x1 <= table_bbox['x1'] and y1 <= table_bbox['y1'])

def reconstruct_table_cells(words_data, table_bbox):
    """Reconstruct table cells from words and their positions."""
    cells = []
    word_positions = []
    
    # Collect words inside the table
    for word in words_data.get('words', []):
        if is_inside_table(word['bbox'], table_bbox):
            word_positions.append({
                'text': word['text'],
                'bbox': word['bbox'],
                'x0': word['bbox'][0],
                'y0': word['bbox'][1],
                'x1': word['bbox'][2],
                'y1': word['bbox'][3]
            })
    
    if not word_positions:
        return cells
    
    # Sort words by vertical position (top to bottom), then horizontal (left to right)
    word_positions.sort(key=lambda w: (w['y0'], w['x0']))
    
    # Group words into rows based on vertical proximity
    rows = []
    current_row = [word_positions[0]]
    current_y = word_positions[0]['y0']
    
    for word in word_positions[1:]:
        # If word is in the same row (within 5 pixels vertically)
        if abs(word['y0'] - current_y) < 5:
            current_row.append(word)
        else:
            # Sort words in the row by horizontal position
            current_row.sort(key=lambda w: w['x0'])
            rows.append(current_row)
            current_row = [word]
            current_y = word['y0']
    
    # Add the last row
    if current_row:
        current_row.sort(key=lambda w: w['x0'])
        rows.append(current_row)
    
    # Reconstruct cells from rows
    for row_idx, row in enumerate(rows):
        col_idx = 0
        while col_idx < len(row):
            word = row[col_idx]
            
            # Check for column span (multiple words in the same row at similar y positions)
            col_span = 1
            while col_idx + col_span < len(row):
                next_word = row[col_idx + col_span]
                if abs(next_word['y0'] - word['y0']) < 5 and abs(next_word['y1'] - word['y1']) < 5:
                    col_span += 1
                else:
                    break
            
            # Check for row span (same column in next rows)
            row_span = 1
            for next_row in rows[row_idx + 1:]:
                if col_idx < len(next_row) and abs(next_row[col_idx]['x0'] - word['x0']) < 5:
                    row_span += 1
                else:
                    break
            
            # Determine if this is a header cell (first row or contains specific keywords)
            is_header = row_idx == 0 or any(
                keyword in word['text'].lower() 
                for keyword in ['method', 'dataset', 'accuracy', 'f1']
            )
            
            # Combine text for cells with span
            cell_text = ' '.join([w['text'] for w in row[col_idx:col_idx + col_span]])
            
            cells.append({
                'row_id': row_idx,
                'col_id': col_idx,
                'row_span': row_span,
                'col_span': col_span,
                'is_header': is_header,
                'text': cell_text.strip()
            })
            
            col_idx += col_span
    
    return cells

def normalize_metrics(cells):
    """Normalize metric rows from table cells."""
    metrics = []
    
    # Find header row to determine column mapping
    header_row = None
    for cell in cells:
        if cell['is_header'] and cell['row_id'] == 0:
            header_row = cell['row_id']
            break
    
    if header_row is None:
        return metrics
    
    # Map column positions to metric fields
    col_mapping = {}
    for cell in cells:
        if cell['row_id'] == header_row:
            col_mapping[cell['col_id']] = cell['text'].lower()
    
    # Extract metric rows (non-header rows)
    for cell in cells:
        if not cell['is_header'] and cell['row_id'] > 0:
            row_metrics = {}
            for col_id, field in col_mapping.items():
                # Find cell in the same row and column
                matching_cell = next(
                    (c for c in cells 
                     if c['row_id'] == cell['row_id'] and c['col_id'] == col_id),
                    None
                )
                if matching_cell:
                    row_metrics[field] = matching_cell['text']
            
            # Only include rows with required fields
            if all(field in row_metrics for field in ['method', 'dataset', 'accuracy', 'f1']):
                metrics.append({
                    'method': row_metrics['method'],
                    'dataset': row_metrics['dataset'],
                    'accuracy': row_metrics['accuracy'],
                    'f1': row_metrics['f1'],
                    'notes': row_metrics.get('notes', '')
                })
    
    return metrics

def audit_metrics(metrics, cells):
    """Audit the extracted metrics."""
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    if not metrics:
        audit['issues'].append('No metric rows extracted')
        return audit
    
    # Find best method by F1 score for each dataset
    dataset_scores = defaultdict(list)
    for metric in metrics:
        try:
            f1 = float(metric['f1'])
            dataset_scores[metric['dataset']].append((metric['method'], f1))
        except ValueError:
            audit['issues'].append(f"Invalid F1 score: {metric['f1']}")
    
    for dataset, scores in dataset_scores.items():
        if scores:
            best_method = max(scores, key=lambda x: x[1])
            audit['best_by_dataset'][dataset] = {
                'method': best_method[0],
                'f1': best_method[1]
            }
    
    # Check for extraction issues
    if len(metrics) < 3:
        audit['issues'].append('Low number of metric rows extracted')
    
    # Check for missing values
    for i, metric in enumerate(metrics):
        if not metric['method'] or not metric['dataset']:
            audit['issues'].append(f'Missing method or dataset in row {i+1}')
        
        try:
            accuracy = float(metric['accuracy'])
            if accuracy < 0 or accuracy > 1:
                audit['issues'].append(f'Invalid accuracy value: {metric['accuracy']}")
        except ValueError:
            audit['issues'].append(f'Invalid accuracy score: {metric['accuracy']}")
    
    return audit

def generate_summary(metrics, audit):
    """Generate a Markdown summary of the extracted metrics."""
    summary = """# Table Extraction Summary

## Overview
- Total metric rows extracted: {audit['row_count']}
- Issues found: {len(audit['issues'])}

## Best Methods by Dataset
"""
    
    if audit['best_by_dataset']:
        for dataset, info in audit['best_by_dataset'].items():
            summary += f"- {dataset}: {info['method']} (F1: {info['f1']:.3f})\n"
    else:
        summary += "No valid methods found.\n"
    
    summary += "\n## Issues\n"
    if audit['issues']:
        for issue in audit['issues']:
            summary += f"- {issue}\n"
    else:
        summary += "No issues detected.\n"
    
    if metrics:
        summary += "\n## Sample Metrics\n\n"
        summary += "| Method | Dataset | Accuracy | F1 | Notes |\n"
        summary += "|--------|---------|----------|----|-------|\n"
        for metric in metrics[:3]:  # Show first 3 metrics
            summary += f"| {metric['method']} | {metric['dataset']} | {metric['accuracy']} | {metric['f1']} | {metric['notes']} |\n"
    
    return summary

def main():
    # Load input data
    input_path = os.environ.get('ORIGINAL_WORDS_JSON')
    if not input_path:
        raise ValueError("ORIGINAL_WORDS_JSON environment variable not set")
    
    words_data = load_words_json(input_path)
    table_bbox = extract_table_bounds(words_data)
    
    # Reconstruct table cells
    cells = reconstruct_table_cells(words_data, table_bbox)
    
    # Normalize metrics
    metrics = normalize_metrics(cells)
    
    # Audit metrics
    audit = audit_metrics(metrics, cells)
    
    # Generate summary
    summary = generate_summary(metrics, audit)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(os.environ.get('OUTPUT_CELLS_CSV', ''))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write table cells CSV
    cells_path = os.environ.get('OUTPUT_CELLS_CSV')
    if cells_path:
        with open(cells_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
            for cell in cells:
                writer.writerow([
                    cell['row_id'],
                    cell['col_id'],
                    cell['row_span'],
                    cell['col_span'],
                    cell['is_header'],
                    cell['text']
                ])
    
    # Write metrics CSV
    metrics_path = os.environ.get('OUTPUT_METRICS_CSV')
    if metrics_path:
        with open(metrics_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['method', 'dataset', 'accuracy', 'f1', 'notes'])
            for metric in metrics:
                writer.writerow([
                    metric['method'],
                    metric['dataset'],
                    metric['accuracy'],
                    metric['f1'],
                    metric['notes']
                ])
    
    # Write audit JSON
    audit_path = os.environ.get('OUTPUT_AUDIT_JSON')
    if audit_path:
        with open(audit_path, 'w', encoding='utf-8') as f:
            json.dump(audit, f, indent=2)
    
    # Write summary Markdown
    summary_path = os.environ.get('SUMMARY_MD')
    if summary_path:
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

if __name__ == '__main__':
    main()