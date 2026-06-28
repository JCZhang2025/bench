import json
import csv
import os
from collections import defaultdict
import re
import math

# Read environment variables
original_words_json = os.environ.get('ORIGINAL_WORDS_JSON')
output_cells_csv = os.environ.get('OUTPUT_CELLS_CSV')
output_metrics_csv = os.environ.get('OUTPUT_METRICS_CSV')
output_audit_json = os.environ.get('OUTPUT_AUDIT_JSON')
summary_md = os.environ.get('SUMMARY_MD')

# Load the original words JSON
with open(original_words_json, 'r') as f:
    data = json.load(f)

# Extract table bounding box
table_bbox = data['table_bbox']

# Extract words with their bounding boxes
words = data['words']

# Calculate centers and dimensions for each word
for word in words:
    bbox = word['bbox']
    word['x_center'] = (bbox[0] + bbox[2]) / 2
    word['y_center'] = (bbox[1] + bbox[3]) / 2
    word['width'] = bbox[2] - bbox[0]
    word['height'] = bbox[3] - bbox[1]

# Sort words by y_center, then by x_center
words_sorted = sorted(words, key=lambda w: (w['y_center'], w['x_center']))

# Estimate row tolerance from median token height
heights = [w['height'] for w in words_sorted]
median_height = sorted(heights)[len(heights) // 2]
row_tolerance = median_height * 0.8

# Group words into rows
rows = []
current_row = []
last_y = None

for word in words_sorted:
    if last_y is None or abs(word['y_center'] - last_y) <= row_tolerance:
        current_row.append(word)
    else:
        if current_row:
            rows.append(current_row)
        current_row = [word]
    last_y = word['y_center']

if current_row:
    rows.append(current_row)

# Sort rows by their average y position
rows = sorted(rows, key=lambda r: sum(w['y_center'] for w in r) / len(r))

# Estimate columns
# Find x clusters to determine column boundaries
x_positions = [w['x_center'] for w in words_sorted]
x_positions.sort()

column_boundaries = []
current_cluster = [x_positions[0]]

for x in x_positions[1:]:
    if x - current_cluster[-1] < median_height * 0.5:
        current_cluster.append(x)
    else:
        if len(current_cluster) > 1:
            column_boundaries.append((min(current_cluster), max(current_cluster)))
        current_cluster = [x]

if len(current_cluster) > 1:
    column_boundaries.append((min(current_cluster), max(current_cluster)))

# If no clear column boundaries found, create equal-width columns
if not column_boundaries:
    min_x = min(w['x_center'] for w in words_sorted)
    max_x = max(w['x_center'] for w in words_sorted)
    num_columns = 3  # Default to 3 columns
    column_width = (max_x - min_x) / num_columns
    column_boundaries = []
    for i in range(num_columns):
        start = min_x + i * column_width
        end = min_x + (i + 1) * column_width
        column_boundaries.append((start, end))

# Assign words to columns
for row in rows:
    for word in row:
        # Find the column that contains the word's center
        for i, (start, end) in enumerate(column_boundaries):
            if start <= word['x_center'] <= end:
                word['col_id'] = i
                break
        else:
            # If no column contains the center, find the closest one
            closest_col = min(range(len(column_boundaries)), 
                            key=lambda i: abs(word['x_center'] - (column_boundaries[i][0] + column_boundaries[i][1]) / 2))
            word['col_id'] = closest_col

# Create cells
cells = []
for row_idx, row in enumerate(rows):
    # Group words in the same row by column
    row_cells = defaultdict(list)
    for word in row:
        if 'col_id' in word:
            row_cells[word['col_id']].append(word)
    
    # Create cell entries
    for col_id in sorted(row_cells.keys()):
        words_in_cell = row_cells[col_id]
        # Sort words by x position
        words_in_cell = sorted(words_in_cell, key=lambda w: w['x_center'])
        
        # Join words with spaces
        cell_text = ' '.join([w['text'] for w in words_in_cell])
        
        # Determine if this is a header cell (simple heuristic: first row)
        is_header = row_idx == 0
        
        cells.append({
            'row_id': row_idx,
            'col_id': col_id,
            'row_span': 1,
            'col_span': 1,
            'is_header': is_header,
            'text': cell_text
        })

# Write cells to CSV
with open(output_cells_csv, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    writer.writeheader()
    writer.writerows(cells)

# Extract metric rows (non-header, non-empty cells)
metric_rows = []
for cell in cells:
    if not cell['is_header'] and cell['text'].strip():
        # Try to parse the text as a metric row
        # Look for patterns like "method, dataset, accuracy, f1, notes"
        parts = [p.strip() for p in cell['text'].split(',')]
        if len(parts) >= 4:
            method = parts[0]
            dataset = parts[1]
            accuracy = parts[2]
            f1 = parts[3]
            notes = ','.join(parts[4:]) if len(parts) > 4 else ''
            
            # Clean numeric values
            accuracy = re.sub(r'[^0-9.]', '', accuracy)
            f1 = re.sub(r'[^0-9.]', '', f1)
            
            if accuracy and f1:
                metric_rows.append({
                    'method': method,
                    'dataset': dataset,
                    'accuracy': accuracy,
                    'f1': f1,
                    'notes': notes
                })

# Write metrics to CSV
with open(output_metrics_csv, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['method', 'dataset', 'accuracy', 'f1', 'notes'])
    writer.writeheader()
    writer.writerows(metric_rows)

# Audit the metrics
audit = {
    'row_count': len(metric_rows),
    'best_by_dataset': {},
    'issues': []
}

# Find best method by F1 score for each dataset
dataset_methods = defaultdict(list)
for row in metric_rows:
    try:
        f1 = float(row['f1'])
        dataset_methods[row['dataset']].append((row['method'], f1))
    except ValueError:
        audit['issues'].append({
            'type': 'non_numeric_metric',
            'message': f'Non-numeric F1 value: {row["f1"]}'
        })

for dataset, methods in dataset_methods.items():
    best_method = max(methods, key=lambda x: x[1])
    audit['best_by_dataset'][dataset] = {
        'method': best_method[0],
        'f1': best_method[1]
    }

# Check for duplicate records
method_dataset_pairs = [(row['method'], row['dataset']) for row in metric_rows]
if len(method_dataset_pairs) != len(set(method_dataset_pairs)):
    audit['issues'].append({
        'type': 'duplicate_record',
        'message': 'Duplicate method-dataset pairs found'
    })

# Write audit JSON
with open(output_audit_json, 'w') as f:
    json.dump(audit, f, indent=2)

# Generate summary
summary = f"""# Table Extraction Summary

## Overview
- Total cells reconstructed: {len(cells)}
- Metric rows extracted: {audit['row_count']}

## Best Methods by Dataset
"""

for dataset, best in audit['best_by_dataset'].items():
    summary += f"- {dataset}: {best['method']} (F1: {best['f1']})\n"

if audit['issues']:
    summary += "\n## Issues Found\n"
    for issue in audit['issues']:
        summary += f"- {issue['type']}: {issue['message']}\n"
else:
    summary += "\n## No Issues Found\n"

summary += "\n## Processing Details\n"
summary += f"- Rows detected: {len(rows)}\n"
summary += f"- Columns detected: {len(column_boundaries)}\n"

# Write summary
with open(summary_md, 'w') as f:
    f.write(summary)
