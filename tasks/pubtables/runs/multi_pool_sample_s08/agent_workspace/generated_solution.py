import json
import csv
import os
from collections import defaultdict

# Read input JSON
with os.environ['ORIGINAL_WORDS_JSON'] as f:
    data = json.load(f)

# Extract table bbox and words
table_bbox = data['table_bbox']
words = data['words']

# Normalize word coordinates
for word in words:
    x1, y1, x2, y2 = word['bbox']
    word['x_center'] = (x1 + x2) / 2
    word['y_center'] = (y1 + y2) / 2
    word['width'] = x2 - x1
    word['height'] = y2 - y1

# Sort words by y_center, then x_center
words_sorted = sorted(words, key=lambda w: (w['y_center'], w['x_center']))

# Estimate row tolerance
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
            rows.append(sorted(current_row, key=lambda w: w['x_center']))
        current_row = [word]
    last_y = word['y_center']

if current_row:
    rows.append(sorted(current_row, key=lambda w: w['x_center']))

# Estimate columns
x_positions = [w['x_center'] for row in rows for w in row]
x_positions.sort()

# Simple column detection - find gaps larger than median word width
gaps = []
for i in range(1, len(x_positions)):
    gaps.append(x_positions[i] - x_positions[i-1])
median_gap = sorted(gaps)[len(gaps) // 2] if gaps else 0

column_boundaries = []
current_x = x_positions[0] if x_positions else 0

for x in x_positions:
    if x - current_x > median_gap * 1.5:
        column_boundaries.append((current_x, x))
        current_x = x
column_boundaries.append((current_x, x_positions[-1] if x_positions else current_x + 100))

# Assign words to columns
cells = defaultdict(lambda: defaultdict(list))

for row_idx, row in enumerate(rows):
    for word in row:
        # Find which column this word belongs to
        for col_idx, (col_start, col_end) in enumerate(column_boundaries):
            if col_start <= word['x_center'] <= col_end:
                cells[row_idx][col_idx].append(word)
                break

# Reconstruct cell text
cell_data = []
for row_idx in sorted(cells.keys()):
    for col_idx in sorted(cells[row_idx].keys()):
        words_in_cell = cells[row_idx][col_idx]
        if words_in_cell:
            # Sort by x position and join text
            sorted_words = sorted(words_in_cell, key=lambda w: w['x_center'])
            text = ' '.join([w['text'] for w in sorted_words])
            
            # Determine if header (simple heuristic: first row)
            is_header = row_idx == 0
            
            cell_data.append({
                'row_id': row_idx,
                'col_id': col_idx,
                'row_span': 1,
                'col_span': 1,
                'is_header': is_header,
                'text': text
            })

# Write cells CSV
with open(os.environ['OUTPUT_CELLS_CSV'], 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    writer.writeheader()
    writer.writerows(cell_data)

# Extract metrics (simplified - in real implementation would need more sophisticated parsing)
metrics = []
for cell in cell_data:
    if not cell['is_header'] and cell['text']:
        # Simple heuristic to identify metric rows
        text = cell['text'].lower()
        if any(metric in text for metric in ['accuracy', 'f1', 'method', 'dataset']):
            # Try to parse metric values (simplified)
            parts = text.split(',')
            if len(parts) >= 4:
                method = parts[0].strip()
                dataset = parts[1].strip()
                try:
                    accuracy = float(parts[2].strip())
                    f1 = float(parts[3].strip())
                    notes = parts[4].strip() if len(parts) > 4 else ''
                    metrics.append({
                        'method': method,
                        'dataset': dataset,
                        'accuracy': accuracy,
                        'f1': f1,
                        'notes': notes
                    })
                except ValueError:
                    continue

# Write metrics CSV
with open(os.environ['OUTPUT_METRICS_CSV'], 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['method', 'dataset', 'accuracy', 'f1', 'notes'])
    writer.writeheader()
    writer.writerows(metrics)

# Create audit
audit = {
    'row_count': len(metrics),
    'best_by_dataset': {},
    'issues': []
}

# Find best method by F1 for each dataset
dataset_methods = defaultdict(list)
for metric in metrics:
    dataset_methods[metric['dataset']].append(metric)

for dataset, method_list in dataset_methods.items():
    best_method = max(method_list, key=lambda m: m['f1'])
    audit['best_by_dataset'][dataset] = {
        'method': best_method['method'],
        'f1': best_method['f1']
    }

# Check for issues
if len(metrics) == 0:
    audit['issues'].append('No metric rows extracted')

# Write audit JSON
with open(os.environ['OUTPUT_AUDIT_JSON'], 'w') as f:
    json.dump(audit, f, indent=2)

# Write summary
with open(os.environ['SUMMARY_MD'], 'w') as f:
    f.write("""# Table Extraction Summary

- **Source**: PubTables-style OCR word JSON with table bounding box
- **Extracted Records**: {} normalized metric rows
- **Best Performance by Dataset":
""".format(len(metrics)))
    
    for dataset, best in audit['best_by_dataset'].items():
        f.write(f"  - {dataset}: {best['method']} (F1: {best['f1']:.3f})\n")
    
    if audit['issues']:
        f.write("\n**Issues Detected":\n")
        for issue in audit['issues']:
            f.write(f"- {issue}\n")
    else:
        f.write("\n**No extraction issues detected.**\n")