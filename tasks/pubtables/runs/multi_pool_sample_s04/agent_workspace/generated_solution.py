import json
import csv
import os
from collections import defaultdict
import re

def normalize_text(text):
    """Clean and normalize text from OCR words"""
    if not text:
        return ""
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def parse_bbox(bbox):
    """Parse bounding box coordinates"""
    return [float(coord) for coord in bbox]

def compute_token_features(word):
    """Compute center coordinates and dimensions for a word"""
    bbox = parse_bbox(word['bbox'])
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    x_center = (x1 + x2) / 2
    y_center = (y1 + y2) / 2
    return {
        'x_center': x_center,
        'y_center': y_center,
        'width': width,
        'height': height,
        'text': word['text']
    }

def group_into_rows(words, height_tolerance_factor=1.5):
    """Group words into rows based on y-center coordinates"""
    if not words:
        return []
    
    # Sort by y_center
    sorted_words = sorted(words, key=lambda w: w['y_center'])
    
    # Calculate median height for tolerance
    heights = [w['height'] for w in sorted_words]
    median_height = sorted(heights)[len(heights) // 2]
    row_tolerance = median_height * height_tolerance_factor
    
    rows = []
    current_row = [sorted_words[0]]
    current_y_center = sorted_words[0]['y_center']
    
    for word in sorted_words[1:]:
        if abs(word['y_center'] - current_y_center) <= row_tolerance:
            current_row.append(word)
            # Update center to include this word
            current_y_center = (current_y_center * len(current_row) + word['y_center']) / (len(current_row) + 1)
        else:
            rows.append(current_row)
            current_row = [word]
            current_y_center = word['y_center']
    
    if current_row:
        rows.append(current_row)
    
    return rows

def infer_columns(rows):
    """Infer column boundaries from row data"""
    if not rows:
        return []
    
    # Collect all x centers
    all_x_centers = []
    for row in rows:
        for word in row:
            all_x_centers.append(word['x_center'])
    
    # Sort x centers
    all_x_centers.sort()
    
    # Find gaps between x centers
    gaps = []
    for i in range(1, len(all_x_centers)):
        gap = all_x_centers[i] - all_x_centers[i-1]
        gaps.append(gap)
    
    if not gaps:
        return []
    
    # Find significant gaps (larger than median gap)
    median_gap = sorted(gaps)[len(gaps) // 2]
    significant_gaps = [i for i, gap in enumerate(gaps) if gap > median_gap * 1.5]
    
    # Create column boundaries
    columns = []
    start_x = all_x_centers[0]
    
    for gap_idx in significant_gaps:
        boundary = (all_x_centers[gap_idx] + all_x_centers[gap_idx + 1]) / 2
        columns.append((start_x, boundary))
        start_x = boundary
    
    # Add last column
    if columns:
        columns.append((start_x, all_x_centers[-1]))
    else:
        # If no significant gaps, create single column
        columns.append((all_x_centers[0], all_x_centers[-1]))
    
    return columns

def assign_words_to_columns(row, columns):
    """Assign words in a row to columns based on x_center"""
    if not columns:
        return [row]
    
    row_columns = [[] for _ in columns]
    
    for word in row:
        x_center = word['x_center']
        best_col = 0
        max_overlap = 0
        
        for col_idx, (col_start, col_end) in enumerate(columns):
            # Calculate overlap
            if x_center >= col_start and x_center <= col_end:
                overlap = min(col_end - x_center, x_center - col_start)
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_col = col_idx
            
        row_columns[best_col].append(word)
    
    return row_columns

def assemble_cell_text(words):
    """Assemble text from words in a cell"""
    if not words:
        return ""
    
    # Sort by x position
    sorted_words = sorted(words, key=lambda w: w['x_center'])
    
    # Join with spaces, but be careful with punctuation
    text_parts = []
    for i, word in enumerate(sorted_words):
        if i > 0:
            # Check if previous word ends with punctuation
            prev_word = sorted_words[i-1]['text']
            if prev_word and prev_word[-1] in '.,;:!?':
                text_parts.append(word['text'])
            else:
                text_parts.append(' ' + word['text'])
        else:
            text_parts.append(word['text'])
    
    return ''.join(text_parts)

def is_header_cell(text, row_idx):
    """Determine if a cell is a header cell"""
    # Simple heuristic: first row is header, or text contains common header words
    if row_idx == 0:
        return True
    
    header_keywords = ['method', 'dataset', 'accuracy', 'f1', 'model', 'algorithm']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in header_keywords)

def extract_table_cells(words, table_bbox):
    """Extract table cells from OCR words"""
    # Filter words inside table bbox
    table_x1, table_y1, table_x2, table_y2 = parse_bbox(table_bbox)
    
    table_words = []
    for word in words:
        bbox = parse_bbox(word['bbox'])
        x1, y1, x2, y2 = bbox
        
        # Check if word is inside table (with small margin)
        if (x1 >= table_x1 - 5 and x2 <= table_x2 + 5 and 
            y1 >= table_y1 - 5 and y2 <= table_y2 + 5):
            table_words.append(word)
    
    if not table_words:
        return []
    
    # Compute features for each word
    word_features = [compute_token_features(word) for word in table_words]
    
    # Group into rows
    rows = group_into_rows(word_features)
    
    # Infer columns
    columns = infer_columns(rows)
    
    # Create cells
    cells = []
    for row_idx, row in enumerate(rows):
        row_columns = assign_words_to_columns(row, columns)
        
        for col_idx, col_words in enumerate(row_columns):
            text = assemble_cell_text(col_words)
            if text.strip():  # Only include non-empty cells
                is_header = is_header_cell(text, row_idx)
                cells.append({
                    'row_id': row_idx,
                    'col_id': col_idx,
                    'row_span': 1,
                    'col_span': 1,
                    'is_header': is_header,
                    'text': text
                })
    
    return cells

def normalize_metrics(cells):
    """Normalize table cells into metric rows"""
    # Find header row
    header_row = None
    for cell in cells:
        if cell['is_header'] and cell['row_id'] == 0:
            header_row = cell['col_id']
            break
    
    if header_row is None:
        return []
    
    # Map column indices to field names
    field_map = {}
    header_cells = [c for c in cells if c['row_id'] == 0]
    
    for cell in header_cells:
        if cell['col_id'] == header_row:
            field_map['method'] = cell['col_id']
        elif cell['col_id'] == header_row + 1:
            field_map['dataset'] = cell['col_id']
        elif cell['col_id'] == header_row + 2:
            field_map['accuracy'] = cell['col_id']
        elif cell['col_id'] == header_row + 3:
            field_map['f1'] = cell['col_id']
        elif cell['col_id'] == header_row + 4:
            field_map['notes'] = cell['col_id']
    
    # Extract metric rows
    metrics = []
    for row_id in range(1, max(c['row_id'] for c in cells) + 1):
        row_cells = [c for c in cells if c['row_id'] == row_id]
        
        if len(row_cells) >= 4:  # Need at least method, dataset, accuracy, f1
            metric = {
                'method': '',
                'dataset': '',
                'accuracy': '',
                'f1': '',
                'notes': ''
            }
            
            for cell in row_cells:
                col_id = cell['col_id']
                if col_id in field_map:
                    field = field_map[col_id]
                    if field == 'method':
                        metric['method'] = cell['text']
                    elif field == 'dataset':
                        metric['dataset'] = cell['text']
                    elif field == 'accuracy':
                        metric['accuracy'] = cell['text']
                    elif field == 'f1':
                        metric['f1'] = cell['text']
                    elif field == 'notes':
                        metric['notes'] = cell['text']
            
            # Only include if we have the required fields
            if metric['method'] and metric['dataset'] and metric['accuracy'] and metric['f1']:
                metrics.append(metric)
    
    return metrics

def parse_numeric_value(text):
    """Parse numeric value from text"""
    if not text:
        return None
    
    # Remove percent signs and other non-numeric characters
    text = re.sub(r'[^0-9.]', '', text)
    
    try:
        return float(text)
    except ValueError:
        return None

def audit_metrics(metrics):
    """Audit the normalized metrics"""
    audit = {
        'row_count': len(metrics),
        'best_by_dataset': {},
        'issues': []
    }
    
    # Check required columns
    required_columns = ['method', 'dataset', 'accuracy', 'f1', 'notes']
    for metric in metrics:
        for col in required_columns:
            if not metric.get(col, '').strip():
                audit['issues'].append({
                    'type': 'empty_required_text',
                    'field': col,
                    'row': metric
                })
    
    # Check numeric fields
    for metric in metrics:
        accuracy = parse_numeric_value(metric['accuracy'])
        f1 = parse_numeric_value(metric['f1'])
        
        if accuracy is None:
            audit['issues'].append({
                'type': 'non_numeric_metric',
                'field': 'accuracy',
                'value': metric['accuracy']
            })
        
        if f1 is None:
            audit['issues'].append({
                'type': 'non_numeric_metric',
                'field': 'f1',
                'value': metric['f1']
            })
    
    # Find best method by dataset
    dataset_methods = defaultdict(list)
    for metric in metrics:
        dataset = metric['dataset']
        f1 = parse_numeric_value(metric['f1'])
        if f1 is not None:
            dataset_methods[dataset].append((metric['method'], f1))
    
    for dataset, methods in dataset_methods.items():
        if methods:
            # Find method with highest F1
            best_method = max(methods, key=lambda x: x[1])
            audit['best_by_dataset'][dataset] = {
                'method': best_method[0],
                'f1': best_method[1]
            }
    
    # Check for duplicates
    seen = set()
    for metric in metrics:
        key = (metric['method'], metric['dataset'])
        if key in seen:
            audit['issues'].append({
                'type': 'duplicate_record',
                'method': metric['method'],
                'dataset': metric['dataset']
            })
        seen.add(key)
    
    return audit

def generate_summary(metrics, audit):
    """Generate a Markdown summary"""
    summary = """# Table Extraction Summary

## Overview
- Total metric rows extracted: {}
- Datasets found: {}
- Best methods by dataset:
""".format(
        audit['row_count'],
        len(audit['best_by_dataset'])
    )
    
    for dataset, best in audit['best_by_dataset'].items():
        summary += "\n- **{}**: {} (F1: {:.3f})".format(
            dataset, best['method'], best['f1']
        )
    
    if audit['issues']:
        summary += "\n\n## Issues Found\n"
        issue_types = defaultdict(int)
        for issue in audit['issues']:
            issue_types[issue['type']] += 1
        
        for issue_type, count in issue_types.items():
            summary += "- {}: {} occurrences\n".format(issue_type, count)
    else:
        summary += "\n\nNo extraction or validation issues found."
    
    return summary

def main():
    # Read input
    input_path = os.environ.get('ORIGINAL_WORDS_JSON')
    if not input_path:
        raise ValueError("ORIGINAL_WORDS_JSON environment variable not set")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract table cells
    cells = extract_table_cells(data['words'], data['table_bbox'])
    
    # Write cells CSV
    cells_path = os.environ.get('OUTPUT_CELLS_CSV')
    if cells_path:
        os.makedirs(os.path.dirname(cells_path), exist_ok=True)
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
    
    # Normalize metrics
    metrics = normalize_metrics(cells)
    
    # Write metrics CSV
    metrics_path = os.environ.get('OUTPUT_METRICS_CSV')
    if metrics_path:
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
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
    
    # Audit metrics
    audit = audit_metrics(metrics)
    
    # Write audit JSON
    audit_path = os.environ.get('OUTPUT_AUDIT_JSON')
    if audit_path:
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, 'w', encoding='utf-8') as f:
            json.dump(audit, f, indent=2, ensure_ascii=False)
    
    # Generate summary
    summary = generate_summary(metrics, audit)
    
    # Write summary
    summary_path = os.environ.get('SUMMARY_MD')
    if summary_path:
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

if __name__ == '__main__':
    main()