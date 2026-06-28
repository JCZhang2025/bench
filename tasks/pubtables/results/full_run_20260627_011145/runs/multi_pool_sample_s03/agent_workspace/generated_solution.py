import json
import csv
import os
from collections import defaultdict

def parse_bbox(bbox):
    """Parse bounding box from [x1, y1, x2, y2] format."""
    return {
        'x1': bbox[0],
        'y1': bbox[1],
        'x2': bbox[2],
        'y2': bbox[3],
        'width': bbox[2] - bbox[0],
        'height': bbox[3] - bbox[1],
        'x_center': (bbox[0] + bbox[2]) / 2,
        'y_center': (bbox[1] + bbox[3]) / 2
    }

def normalize_bbox(bbox):
    """Normalize bounding box to dict format."""
    if isinstance(bbox, list):
        return parse_bbox(bbox)
    return bbox

def load_words_json(file_path):
    """Load words JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def is_inside_table(word, table_bbox):
    """Check if word is inside table bounding box."""
    word_bbox = normalize_bbox(word['bbox'])
    return (word_bbox['x1'] >= table_bbox['x1'] and 
            word_bbox['y1'] >= table_bbox['y1'] and 
            word_bbox['x2'] <= table_bbox['x2'] and 
            word_bbox['y2'] <= table_bbox['y2'])

def group_words_into_rows(words, table_bbox):
    """Group words into rows based on y-center proximity."""
    # Filter words inside table
    table_words = [w for w in words if is_inside_table(w, table_bbox)]
    
    if not table_words:
        return []
    
    # Sort by y_center then x_center
    sorted_words = sorted(table_words, key=lambda w: (normalize_bbox(w['bbox'])['y_center'], 
                                                      normalize_bbox(w['bbox'])['x_center']))
    
    # Calculate median height for row tolerance
    heights = [normalize_bbox(w['bbox'])['height'] for w in sorted_words]
    median_height = sorted(heights)[len(heights) // 2]
    row_tolerance = median_height * 0.8
    
    rows = []
    current_row = [sorted_words[0]]
    current_y_center = normalize_bbox(sorted_words[0]['bbox'])['y_center']
    
    for word in sorted_words[1:]:
        word_bbox = normalize_bbox(word['bbox'])
        if abs(word_bbox['y_center'] - current_y_center) <= row_tolerance:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
            current_y_center = word_bbox['y_center']
    
    if current_row:
        rows.append(current_row)
    
    return rows

def infer_columns(rows):
    """Infer columns from word positions."""
    if not rows:
        return []
    
    # Collect all x positions
    all_x_positions = []
    for row in rows:
        for word in row:
            x_center = normalize_bbox(word['bbox'])['x_center']
            all_x_positions.append(x_center)
    
    # Sort and find clusters
    all_x_positions.sort()
    
    if len(all_x_positions) < 2:
        return [all_x_positions[0]] if all_x_positions else []
    
    # Simple clustering based on gaps
    clusters = []
    current_cluster = [all_x_positions[0]]
    
    for x in all_x_positions[1:]:
        if x - current_cluster[-1] < 20:  # Threshold for column separation
            current_cluster.append(x)
        else:
            clusters.append(current_cluster)
            current_cluster = [x]
    
    clusters.append(current_cluster)
    
    # Use cluster centers as column positions
    column_positions = [sum(cluster) / len(cluster) for cluster in clusters]
    column_positions.sort()
    
    return column_positions

def assign_words_to_columns(rows, column_positions):
    """Assign words to columns based on x position."""
    column_tolerance = 30  # Tolerance for column assignment
    
    table_cells = defaultdict(dict)  # (row_idx, col_idx) -> [words]
    
    for row_idx, row in enumerate(rows):
        for word in row:
            word_bbox = normalize_bbox(word['bbox'])
            word_x_center = word_bbox['x_center']
            
            # Find best column
            best_col = None
            min_distance = float('inf')
            
            for col_idx, col_x in enumerate(column_positions):
                distance = abs(word_x_center - col_x)
                if distance < min_distance:
                    min_distance = distance
                    best_col = col_idx
            
            if best_col is not None and min_distance <= column_tolerance:
                if (row_idx, best_col) not in table_cells:
                    table_cells[(row_idx, best_col)] = []
                table_cells[(row_idx, best_col)].append(word)
    
    return table_cells

def assemble_cell_text(words):
    """Assemble text from words in a cell."""
    if not words:
        return ""
    
    # Sort by x position
    sorted_words = sorted(words, key=lambda w: normalize_bbox(w['bbox'])['x1'])
    
    # Join with spaces
    text = " ".join([w['text'] for w in sorted_words])
    return text.strip()

def extract_metrics(table_cells, rows):
    """Extract metric rows from table cells."""
    metrics = []
    
    # Skip header rows (first 2 rows typically)
    start_row = min(2, len(rows))
    
    for row_idx in range(start_row, len(rows)):
        row_cells = []
        for col_idx in range(len(infer_columns(rows))):
            if (row_idx, col_idx) in table_cells:
                row_cells.append(assemble_cell_text(table_cells[(row_idx, col_idx)]))
            else:
                row_cells.append("")
        
        # Check if this looks like a metric row
        if len(row_cells) >= 4:  # Should have method, dataset, accuracy, f1
            method = row_cells[0].strip()
            dataset = row_cells[1].strip()
            
            # Try to parse numeric values
            try:
                accuracy = float(row_cells[2]) if row_cells[2] else ""
            except ValueError:
                accuracy = ""
            
            try:
                f1 = float(row_cells[3]) if row_cells[3] else ""
            except ValueError:
                f1 = ""
            
            if method and dataset and (accuracy != "" or f1 != ""):
                metrics.append({
                    'method': method,
                    'dataset': dataset,
                    'accuracy': accuracy,
                    'f1': f1,
                    'notes': row_cells[4] if len(row_cells) > 4 else ""
                })
    
    return metrics

def audit_metrics(metrics):
    """Audit extracted metrics."""
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    if not metrics:
        audit['issues'].append("No metric rows extracted")
        return audit
    
    # Find best method by dataset
    dataset_scores = defaultdict(list)
    for metric in metrics:
        if metric['f1'] != "":
            dataset_scores[metric['dataset']].append(metric)
    
    for dataset, scores in dataset_scores.items():
        best = max(scores, key=lambda x: float(x['f1']))
        audit['best_by_dataset'][dataset] = {
            'method': best['method'],
            'f1': best['f1']
        }
    
    # Check for issues
    for i, metric in enumerate(metrics):
        if metric['accuracy'] == "" and metric['f1'] == "":
            audit['issues'].append(f"Row {i+1}: No numeric values found")
        if metric['method'] == "" or metric['dataset'] == "":
            audit['issues'].append(f"Row {i+1}: Missing method or dataset")
        if metric['f1'] != "" and (float(metric['f1']) < 0 or float(metric['f1']) > 1):
            audit['issues'].append(f"Row {i+1}: Invalid F1 score {metric['f1']}")
    
    return audit

def write_cells_csv(table_cells, output_path):
    """Write table cells to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
        
        for (row_idx, col_idx), words in table_cells.items():
            text = assemble_cell_text(words)
            if text:  # Only write non-empty cells
                writer.writerow([row_idx, col_idx, 1, 1, row_idx < 2, text])

def write_metrics_csv(metrics, output_path):
    """Write metrics to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
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

def write_audit_json(audit, output_path):
    """Write audit to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2)

def write_summary_md(metrics, audit, output_path):
    """Write Markdown summary."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Table Extraction Summary\n\n")
        f.write(f"- **Source**: PubTables-style OCR word JSON\n")
        f.write(f"- **Normalized metric rows**: {audit['row_count']}\n")
        
        if audit['row_count'] > 0:
            f.write("\n## Best Methods by Dataset\n")
            for dataset, best in audit['best_by_dataset'].items():
                f.write(f"- **{dataset}**: {best['method']} (F1: {best['f1']})\n")
        
        if audit['issues']:
            f.write("\n## Extraction Issues\n")
            for issue in audit['issues']:
                f.write(f"- {issue}\n")

def main():
    # Get input/output paths from environment
    input_path = os.environ.get('ORIGINAL_WORDS_JSON')
    cells_output = os.environ.get('OUTPUT_CELLS_CSV')
    metrics_output = os.environ.get('OUTPUT_METRICS_CSV')
    audit_output = os.environ.get('OUTPUT_AUDIT_JSON')
    summary_output = os.environ.get('SUMMARY_MD')
    
    if not all([input_path, cells_output, metrics_output, audit_output, summary_output]):
        raise ValueError("Missing required environment variables")
    
    # Load input data
    data = load_words_json(input_path)
    
    # Extract table bbox
    table_bbox = normalize_bbox(data['table_bbox'])
    
    # Group words into rows
    rows = group_words_into_rows(data['words'], table_bbox)
    
    # Infer columns
    column_positions = infer_columns(rows)
    
    # Assign words to columns
    table_cells = assign_words_to_columns(rows, column_positions)
    
    # Extract metrics
    metrics = extract_metrics(table_cells, rows)
    
    # Audit metrics
    audit = audit_metrics(metrics)
    
    # Write outputs
    write_cells_csv(table_cells, cells_output)
    write_metrics_csv(metrics, metrics_output)
    write_audit_json(audit, audit_output)
    write_summary_md(metrics, audit, summary_output)

if __name__ == '__main__':
    main()