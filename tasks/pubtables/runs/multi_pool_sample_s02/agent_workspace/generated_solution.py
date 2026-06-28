import json
import csv
import os
from collections import defaultdict
import math

# Load input JSON
with os.environ['ORIGINAL_WORDS_JSON'] as f:
    data = json.load(f)

# Extract table bounds and words
table_bbox = data['table_bbox']
words = data['words']

# Filter words inside table region
def is_inside_table(word_bbox, table_bbox):
    x1, y1, x2, y2 = word_bbox
    tx1, ty1, tx2, ty2 = table_bbox
    return x1 >= tx1 and y1 >= ty1 and x2 <= tx2 and y2 <= ty2
table_words = [w for w in words if is_inside_table(w['bbox'], table_bbox)]

# Compute word properties
for word in table_words:
    x1, y1, x2, y2 = word['bbox']
    word['center_x'] = (x1 + x2) / 2
    word['center_y'] = (y1 + y2) / 2
    word['width'] = x2 - x1
    word['height'] = y2 - y1

# Group words into visual rows
word_heights = [w['height'] for w in table_words]
median_height = sorted(word_heights)[len(word_heights) // 2]
row_tolerance = median_height * 0.5

rows = defaultdict(list)
for word in table_words:
    row_key = round(word['center_y'] / row_tolerance) * row_tolerance
    rows[row_key].append(word)

# Sort rows by y position
sorted_rows = sorted(rows.items(), key=lambda x: x[0])

# Assign words to columns
all_x_positions = sorted(set(w['center_x'] for w in table_words))
column_positions = []
current_col = [all_x_positions[0]]

for x in all_x_positions[1:]:
    if x - current_col[-1] > median_height:
        column_positions.append(current_col)
        current_col = [x]
    else:
        current_col.append(x)
column_positions.append(current_col)

# Normalize column positions
column_centers = [sum(col) / len(col) for col in column_positions]
column_tolerance = median_height * 0.3

# Create cells
cells = []
for row_idx, (row_y, row_words) in enumerate(sorted_rows):
    # Sort words by x position
    row_words_sorted = sorted(row_words, key=lambda w: w['center_x'])
    
    # Assign to columns
    col_idx = 0
    current_cell_text = []
    
    for word in row_words_sorted:
        # Find which column this word belongs to
        while col_idx < len(column_centers) and abs(word['center_x'] - column_centers[col_idx]) > column_tolerance:
            col_idx += 1
        
        if col_idx >= len(column_centers):
            # Start new cell for next row
            if current_cell_text:
                cells.append({
                    'row_id': row_idx,
                    'col_id': col_idx - 1,
                    'row_span': 1,
                    'col_span': 1,
                    'is_header': row_idx == 0,
                    'text': ' '.join(current_cell_text)
                })
                current_cell_text = []n            break
        
        # Check if we're continuing a cell or starting a new one
        if current_cell_text and abs(word['center_x'] - column_centers[col_idx]) > column_tolerance * 2:
            # New cell
            cells.append({
                'row_id': row_idx,
                'col_id': col_idx - 1,
                'row_span': 1,
                'col_span': 1,
                'is_header': row_idx == 0,
                'text': ' '.join(current_cell_text)
            })
            current_cell_text = [word['text']]
        else:
            current_cell_text.append(word['text'])
    
    # Add last cell in row
    if current_cell_text:
        cells.append({
            'row_id': row_idx,
            'col_id': len(column_centers) - 1,
            'row_span': 1,
            'col_span': 1,
            'is_header': row_idx == 0,
            'text': ' '.join(current_cell_text)
        })

# Write cells CSV
with open(os.environ['OUTPUT_CELLS_CSV'], 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    writer.writeheader()
    writer.writerows(cells)

# Extract normalized metrics
metrics = []
for cell in cells:
    if not cell['is_header'] and cell['text']:
        # Try to parse as metric row
        parts = cell['text'].split(',')
        if len(parts) >= 4:
            method = parts[0].strip()
            dataset = parts[1].strip()
            
            # Parse accuracy
            try:
                acc_str = parts[2].strip().replace('%', '')
                accuracy = float(acc_str) / 100 if '%' in parts[2] else float(acc_str)
            except:
                accuracy = None
            
            # Parse F1
            try:
                f1_str = parts[3].strip().replace('%', '')
                f1 = float(f1_str) / 100 if '%' in parts[3] else float(f1_str)
            except:
                f1 = None
            
            notes = parts[4].strip() if len(parts) > 4 else ''
            
            if accuracy is not None and f1 is not None:
                metrics.append({
                    'method': method,
                    'dataset': dataset,
                    'accuracy': accuracy,
                    'f1': f1,
                    'notes': notes
                })

# Write metrics CSV
with open(os.environ['OUTPUT_METRICS_CSV'], 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['method', 'dataset', 'accuracy', 'f1', 'notes'])
    writer.writeheader()
    writer.writerows(metrics)

# Audit metrics
audit = {
    'row_count': len(metrics),
    'best_by_dataset': {},
    'issues': []
}

# Find best method per dataset
datasets = set(m['dataset'] for m in metrics)
for dataset in datasets:
    dataset_metrics = [m for m in metrics if m['dataset'] == dataset]
    if dataset_metrics:
        best = max(dataset_metrics, key=lambda x: x['f1'])
        audit['best_by_dataset'][dataset] = {
            'method': best['method'],
            'f1': best['f1']
        }

# Check for issues
if len(metrics) == 0:
    audit['issues'].append('no_metric_rows_extracted')

for i, metric in enumerate(metrics):
    if metric['accuracy'] > 1.0 or metric['accuracy'] < 0.0:
        audit['issues'].append(f'invalid_accuracy_value_row_{i}')
    if metric['f1'] > 1.0 or metric['f1'] < 0.0:
        audit['issues'].append(f'invalid_f1_value_row_{i}')

# Write audit JSON
with open(os.environ['OUTPUT_AUDIT_JSON'], 'w') as f:
    json.dump(audit, f, indent=2)

# Generate summary
summary = f"""# PubTables Extraction Summary

## Table Structure
- Reconstructed {len(cells)} cells from {len(sorted_rows)} rows
- Header detected: {'Yes' if any(c['is_header'] for c in cells) else 'No'}

## Metrics
- Extracted {len(metrics)} metric rows
- Best performing methods:
"""

for dataset, best in audit['best_by_dataset'].items():
    summary += f"  - {dataset}: {best['method']} (F1: {best['f1']:.3f})\n"

if audit['issues']:
    summary += "\n## Issues\n"
    for issue in audit['issues']:
        summary += f"- {issue}\n"
else:
    summary += "\n## No Issues Detected\n"

summary += f"\n*Generated on {os.environ.get('DATE', 'unknown')}*"

# Write summary
with open(os.environ['SUMMARY_MD'], 'w') as f:
    f.write(summary)