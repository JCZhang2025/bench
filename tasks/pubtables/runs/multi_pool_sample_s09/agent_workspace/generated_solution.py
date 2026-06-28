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

# Extract table bounding box and words
table_bbox = data['table_bbox']
words = data['words']

# Separate table words from caption/footnote words
table_words = []
caption_footnote_words = []

for word in words:
    x1, y1, x2, y2 = word['bbox']
    # Check if word is within table bounding box
    if (x1 >= table_bbox[0] and y1 >= table_bbox[1] and 
        x2 <= table_bbox[2] and y2 <= table_bbox[3]):
        table_words.append(word)
    else:
        caption_footnote_words.append(word)

# Sort words by y-coordinate then x-coordinate
table_words.sort(key=lambda w: (w['bbox'][1], w['bbox'][0]))

# Group words into rows based on y-coordinate
rows = []
current_row = []
prev_y = None

for word in table_words:
    y1 = word['bbox'][1]
    if prev_y is None or abs(y1 - prev_y) < 10:  # Same row threshold
        current_row.append(word)
    else:
        rows.append(sorted(current_row, key=lambda w: w['bbox'][0]))
        current_row = [word]
    prev_y = y1

if current_row:
    rows.append(sorted(current_row, key=lambda w: w['bbox'][0]))

# Detect header rows (first 2 rows or rows with non-numeric text)
header_rows = []
for i, row in enumerate(rows[:3]):
    is_numeric = True
    for word in row:
        text = word['text'].strip()
        if not re.match(r'^[\d\s\.,%]+$', text):
            is_numeric = False
            break
    if not is_numeric:
        header_rows.append(i)

# Detect columns based on x-coordinates
column_x_coords = []
for row in rows:
    for word in row:
        x1 = word['bbox'][0]
        x2 = word['bbox'][2]
        column_x_coords.append(x1)
        column_x_coords.append(x2)

# Remove duplicates and sort
column_x_coords = sorted(list(set(column_x_coords)))

# Assign words to cells
cells = []
for row_idx, row in enumerate(rows):
    for col_idx, x_coord in enumerate(column_x_coords[:-1]):
        x1 = x_coord
        x2 = column_x_coords[col_idx + 1]
        
        # Find words in this cell
        cell_words = []
        for word in row:
            word_x1 = word['bbox'][0]
            word_x2 = word['bbox'][2]
            if word_x1 >= x1 and word_x2 <= x2:
                cell_words.append(word)
        
        if cell_words:
            # Combine text from all words in cell
            text = ' '.join([w['text'] for w in cell_words]).strip()
            
            # Determine if this is a header cell
            is_header = row_idx in header_rows
            
            # Calculate row span and col span (simplified)
            row_span = 1
            col_span = 1
            
            # Add to cells list
            cells.append({
                'row_id': row_idx,
                'col_id': col_idx,
                'row_span': row_span,
                'col_span': col_span,
                'is_header': is_header,
                'text': text
            })

# Extract metrics from non-header cells
metrics = []
for cell in cells:
    if not cell['is_header'] and cell['text']:
        text = cell['text'].strip()
        
        # Try to parse as metric
        # Look for method, dataset, accuracy, f1 patterns
        method_match = re.search(r'(\w+)', text)
        dataset_match = re.search(r'(\w+\s*\d*)', text)
        
        if method_match and dataset_match:
            # Extract numeric values
            numbers = re.findall(r'\d+\.?\d*%', text)
            
            if len(numbers) >= 2:
                accuracy = numbers[0].replace('%', '')
                f1 = numbers[1].replace('%', '')
                
                metrics.append({
                    'method': method_match.group(1),
                    'dataset': dataset_match.group(1),
                    'accuracy': accuracy,
                    'f1': f1,
                    'notes': text
                })

# Write table cells to CSV
with open(output_cells_csv, 'w', newline='') as f:
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

# Write metrics to CSV
with open(output_metrics_csv, 'w', newline='') as f:
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

# Create audit information
audit = {
    'row_count': len(metrics),
    'best_by_dataset': {},
    'issues': []
}

# Find best method by F1 score for each dataset
dataset_methods = defaultdict(list)
for metric in metrics:
    dataset_methods[metric['dataset']].append(metric)

for dataset, method_list in dataset_methods.items():
    best_method = max(method_list, key=lambda m: float(m['f1'].replace('%', '')))
    audit['best_by_dataset'][dataset] = {
        'method': best_method['method'],
        'f1': best_method['f1']
    }

# Check for issues
if len(metrics) == 0:
    audit['issues'].append('No metric rows extracted')

if len(header_rows) == 0:
    audit['issues'].append('No header rows detected')

# Write audit JSON
with open(output_audit_json, 'w') as f:
    json.dump(audit, f, indent=2)

# Write summary Markdown
with open(summary_md, 'w') as f:
    f.write("""# Table Extraction Summary

## Extraction Results
- Total table cells: {len(cells)}
- Header cells: {sum(1 for c in cells if c['is_header'])}
- Metric rows extracted: {len(metrics)}

## Metrics Overview
""")
    
    if metrics:
        f.write("\n| Method | Dataset | Accuracy | F1 Score |\n")
        f.write("|--------|---------|----------|----------|\n")
        for metric in metrics:
            f.write(f"| {metric['method']} | {metric['dataset']} | {metric['accuracy']}% | {metric['f1']}% |\n")
    
    f.write("\n## Best Performance by Dataset\n")
    for dataset, best in audit['best_by_dataset'].items():
        f.write(f"- {dataset}: {best['method']} (F1: {best['f1']}%)\n")
    
    if audit['issues']:
        f.write("\n## Issues Found\n")
        for issue in audit['issues']:
            f.write(f"- {issue}\n")
    
    f.write("\n---\nGenerated by PubTables extraction pipeline\n")