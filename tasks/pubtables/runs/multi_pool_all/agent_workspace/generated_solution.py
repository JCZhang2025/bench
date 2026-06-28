import json
import csv
import os
from collections import defaultdict

def load_json_file(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_csv_file(data, filepath, fieldnames):
    """Save data to CSV file."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def save_json_file(data, filepath):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_markdown_file(content, filepath):
    """Save content to Markdown file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def compute_word_centers(words):
    """Compute center coordinates for each word."""
    for word in words:
        bbox = word['bbox']
        word['x_center'] = (bbox[0] + bbox[2]) / 2
        word['y_center'] = (bbox[1] + bbox[3]) / 2
        word['width'] = bbox[2] - bbox[0]
        word['height'] = bbox[3] - bbox[1]
    return words

def filter_table_words(words, table_bbox):
    """Filter words that belong to the table region."""
    table_x1, table_y1, table_x2, table_y2 = table_bbox
    table_words = []
    
    for word in words:
        x_center = word['x_center']
        y_center = word['y_center']
        
        if table_x1 <= x_center <= table_x2 and table_y1 <= y_center <= table_y2:
            table_words.append(word)
    
    return table_words

def group_words_into_rows(words, tolerance_factor=1.5):
    """Group words into visual rows based on y-center proximity."""
    if not words:
        return []
    
    # Sort words by y_center
    sorted_words = sorted(words, key=lambda w: w['y_center'])
    
    # Calculate median height for tolerance
    heights = [w['height'] for w in sorted_words]
    median_height = sorted(heights)[len(heights) // 2]
    tolerance = median_height * tolerance_factor
    
    rows = []
    current_row = [sorted_words[0]]
    
    for word in sorted_words[1:]:
        if abs(word['y_center'] - current_row[-1]['y_center']) <= tolerance:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    if current_row:
        rows.append(current_row)
    
    return rows

def group_words_into_columns(rows):
    """Group words into columns based on x-center positions."""
    if not rows:
        return []
    
    # Collect all x positions
    all_x_positions = []
    for row in rows:
        for word in row:
            all_x_positions.append(word['x_center'])
    
    # Sort and find gaps to determine column boundaries
    all_x_positions.sort()
    
    # Simple column detection: find gaps larger than median word width
    if len(all_x_positions) < 2:
        # Single column case
        return [[row] for row in rows]
    
    widths = [all_x_positions[i+1] - all_x_positions[i] for i in range(len(all_x_positions)-1)]
    median_width = sorted(widths)[len(widths) // 2]
    
    column_boundaries = []
    current_boundary = all_x_positions[0]
    
    for i in range(len(all_x_positions)-1):
        if all_x_positions[i+1] - all_x_positions[i] > median_width:
            column_boundaries.append((current_boundary, all_x_positions[i]))
            current_boundary = all_x_positions[i+1]
    
    column_boundaries.append((current_boundary, all_x_positions[-1]))
    
    # Assign words to columns
    columns = [[] for _ in column_boundaries]
    
    for row in rows:
        row_columns = [[] for _ in column_boundaries]
        
        for word in row:
            x_center = word['x_center']
            
            # Find which column this word belongs to
            for i, (x1, x2) in enumerate(column_boundaries):
                if x1 <= x_center <= x2:
                    row_columns[i].append(word)
                    break
            
        # Add to columns
        for i, col_words in enumerate(row_columns):
            if col_words:
                columns[i].append(col_words)
    
    return columns

def reconstruct_cells(rows, columns):
    """Reconstruct table cells from rows and columns."""
    cells = []
    
    # Create a mapping of (row_idx, col_idx) to words
    cell_words = defaultdict(list)
    
    for row_idx, row in enumerate(rows):
        for col_idx, col_words in enumerate(columns[row_idx] if row_idx < len(columns) else []):
            for word in col_words:
                cell_words[(row_idx, col_idx)].append(word)
    
    # Create cell entries
    for (row_idx, col_idx), words in cell_words.items():
        if words:
            # Sort words by x position
            sorted_words = sorted(words, key=lambda w: w['x_center'])
            
            # Join text with spaces
            text = ' '.join([word['text'] for word in sorted_words])
            
            # Determine if header (simple heuristic: top rows)
            is_header = row_idx < 2  # First two rows considered header
            
            cell = {
                'row_id': row_idx,
                'col_id': col_idx,
                'row_span': 1,
                'col_span': 1,
                'is_header': is_header,
                'text': text.strip()
            }
            
            cells.append(cell)
    
    return cells

def normalize_metrics(cells):
    """Normalize metric rows from table cells."""
    metrics = []
    
    # Look for method, dataset, accuracy, f1 in body cells
    for cell in cells:
        if not cell['is_header'] and cell['text']:
            text = cell['text']
            
            # Simple parsing - look for numeric values
            parts = text.split()
            
            if len(parts) >= 2:
                # Try to extract method and dataset
                method = parts[0] if len(parts[0]) > 2 else ''
                dataset = parts[1] if len(parts[1]) > 2 else ''
                
                # Look for accuracy and f1 values
                accuracy = ''
                f1 = ''
                notes = ''
                
                for part in parts[2:]:
                    if '%' in part and not accuracy:
                        accuracy = part
                    elif '.' in part and len(part.split('.')[1]) <= 3 and not f1:
                        f1 = part
                    else:
                        notes = part if not notes else notes + ' ' + part
                
                if method and dataset and (accuracy or f1):
                    metrics.append({
                        'method': method,
                        'dataset': dataset,
                        'accuracy': accuracy,
                        'f1': f1,
                        'notes': notes
                    })
    
    return metrics

def audit_extraction(metrics, cells):
    """Audit the extraction process."""
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    # Find best method by F1 for each dataset
    for metric in metrics:
        dataset = metric['dataset']
        f1 = metric['f1']
        
        if dataset not in audit['best_by_dataset'] or f1 > audit['best_by_dataset'][dataset]['f1']:
            audit['best_by_dataset'][dataset] = {
                'method': metric['method'],
                'f1': f1
            }
    
    # Check for issues
    if len(metrics) == 0:
        audit['issues'].append('no_metric_rows_extracted')
    
    # Check for missing required fields
    for i, metric in enumerate(metrics):
        if not metric['method']:
            audit['issues'].append(f'missing_method_row_{i}')
        if not metric['dataset']:
            audit['issues'].append(f'missing_dataset_row_{i}')
        if not metric['accuracy'] and not metric['f1']:
            audit['issues'].append(f'missing_numeric_values_row_{i}')
    
    # Check for duplicate records
    seen = set()
    for i, metric in enumerate(metrics):
        key = (metric['method'], metric['dataset'])
        if key in seen:
            audit['issues'].append(f'duplicate_record_{metric["method"]}_{metric["dataset"]}')
        seen.add(key)
    
    return audit

def generate_summary(metrics, audit):
    """Generate a grounded Markdown summary."""
    summary = """# Table Extraction Summary

## Extraction Results
- Total normalized metric rows: {}

## Best Methods by Dataset
""".format(audit['row_count'])
    
    for dataset, best in audit['best_by_dataset'].items():
        summary += f"- {dataset}: {best['method']} (F1: {best['f1']})\n"
    
    summary += "\n## Audit Issues\n"
    
    if not audit['issues']:
        summary += "No extraction issues detected.\n"
    else:
        for issue in audit['issues']:
            summary += f"- {issue}\n"
    
    return summary

def main():
    # Load input data
    input_path = os.environ.get('ORIGINAL_WORDS_JSON')
    if not input_path:
        raise ValueError("ORIGINAL_WORDS_JSON environment variable not set")
    
    data = load_json_file(input_path)
    
    # Extract table bbox and words
    table_bbox = data['table_bbox']
    words = data['words']
    
    # Process words
    words = compute_word_centers(words)
    table_words = filter_table_words(words, table_bbox)
    
    # Reconstruct table structure
    rows = group_words_into_rows(table_words)
    columns = group_words_into_columns(rows)
    cells = reconstruct_cells(rows, columns)
    
    # Normalize metrics
    metrics = normalize_metrics(cells)
    
    # Audit extraction
    audit = audit_extraction(metrics, cells)
    
    # Generate summary
    summary = generate_summary(metrics, audit)
    
    # Save outputs
    output_dir = os.path.dirname(os.environ.get('OUTPUT_CELLS_CSV'))
    os.makedirs(output_dir, exist_ok=True)
    
    # Save cells CSV
    save_csv_file(cells, os.environ.get('OUTPUT_CELLS_CSV'), 
                  ['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    
    # Save metrics CSV
    save_csv_file(metrics, os.environ.get('OUTPUT_METRICS_CSV'), 
                  ['method', 'dataset', 'accuracy', 'f1', 'notes'])
    
    # Save audit JSON
    save_json_file(audit, os.environ.get('OUTPUT_AUDIT_JSON'))
    
    # Save summary Markdown
    save_markdown_file(summary, os.environ.get('SUMMARY_MD'))
    
    print("Processing completed successfully.")

if __name__ == '__main__':
    main()