import json
import csv
import os
from collections import defaultdict

# Load input data
with os.environ['ORIGINAL_WORDS_JSON'] as f:
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

# Sort words by position (top to bottom, left to right)
table_words.sort(key=lambda w: (w['bbox'][1], w['bbox'][0]))

# Reconstruct table structure
rows = defaultdict(list)
cols = defaultdict(list)

# Group words into rows and columns
for word in table_words:
    x1, y1, x2, y2 = word['bbox']
    # Find closest row based on y-coordinate
    row_key = None
    min_dist = float('inf')
    for r_key in rows:
        row_y = rows[r_key][0]['bbox'][1]
        dist = abs(y1 - row_y)
        if dist < min_dist and dist < 20:  # 20px threshold
            min_dist = dist
            row_key = r_key
    
    if row_key is None:
        row_key = len(rows)
        rows[row_key] = []
    
    rows[row_key].append(word)
    cols[len(cols)].append(word)

# Sort words within each row by x-coordinate
for row_key in rows:
    rows[row_key].sort(key=lambda w: w['bbox'][0])

# Reconstruct cells
cells = []
for row_idx, row_words in rows.items():
    col_idx = 0
    while col_idx < len(row_words):
        word = row_words[col_idx]
        x1, y1, x2, y2 = word['bbox']
        
        # Check for column span
        col_span = 1
        while col_idx + col_span < len(row_words):
            next_word = row_words[col_idx + col_span]
            next_x1 = next_word['bbox'][0]
            if next_x1 - x2 < 10:  # 10px threshold for column span
                col_span += 1
                x2 = max(x2, next_word['bbox'][2])
            else:
                break
        
        # Check for row span (simplified)
        row_span = 1
        for next_row_idx in range(row_idx + 1, len(rows)):
            next_row_words = rows[next_row_idx]
            if col_idx < len(next_row_words):
                next_word = next_row_words[col_idx]
                next_y1 = next_word['bbox'][1]
                if next_y1 - y2 < 10:  # 10px threshold for row span
                    row_span += 1
                    y2 = max(y2, next_word['bbox'][3])
                else:
                    break
        
        # Determine if header (simplified)
        is_header = row_idx == 0 or any('method' in word['text'].lower() for word in row_words)
        
        # Combine text for multi-column cells
        cell_text = ' '.join([w['text'] for w in row_words[col_idx:col_idx+col_span]])
        
        cells.append({
            'row_id': row_idx,
            'col_id': col_idx,
            'row_span': row_span,
            'col_span': col_span,
            'is_header': is_header,
            'text': cell_text.strip()
        })
        
        col_idx += col_span

# Write cells CSV
with open(os.environ['OUTPUT_CELLS_CSV'], 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['row_id', 'col_id', 'row_span', 'col_span', 'is_header', 'text'])
    writer.writeheader()
    writer.writerows(cells)

# Extract metrics (simplified)
metrics = []
for cell in cells:
    if not cell['is_header'] and cell['text']:
        text = cell['text'].lower()
        if 'method' in text or 'dataset' in text or 'accuracy' in text or 'f1' in text:
            # Simple parsing - in real implementation would need more sophisticated logic
            parts = text.split(',')
            if len(parts) >= 4:
                metrics.append({
                    'method': parts[0].strip(),
                    'dataset': parts[1].strip(),
                    'accuracy': parts[2].strip(),
                    'f1': parts[3].strip(),
                    'notes': ','.join(parts[4:]).strip() if len(parts) > 4 else ''
                })

# Write metrics CSV
with open(os.environ['OUTPUT_METRICS_CSV'], 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['method', 'dataset', 'accuracy', 'f1', 'notes'])
    writer.writeheader()
    writer.writerows(metrics)

# Audit data
audit = {
    'row_count': len(metrics),
    'best_by_dataset': {},
    'issues': []
}

# Find best method by F1 for each dataset
dataset_methods = defaultdict(list)
for metric in metrics:
    try:
        f1 = float(metric['f1'])
        dataset_methods[metric['dataset']].append((metric['method'], f1))
    except ValueError:
        audit['issues'].append(f"Invalid F1 value: {metric['f1']}")

for dataset, methods in dataset_methods.items():
    best_method = max(methods, key=lambda x: x[1])
    audit['best_by_dataset'][dataset] = {
        'method': best_method[0],
        'f1': best_method[1]
    }

# Write audit JSON
with open(os.environ['OUTPUT_AUDIT_JSON'], 'w') as f:
    json.dump(audit, f, indent=2)

# Generate summary
summary = """# Table Extraction Summary

## Overview
- Total metric rows extracted: {row_count}
- Best performing methods by dataset:

{best_methods}

## Issues Found
{issues}
""".format(
    row_count=audit['row_count'],
    best_methods="\n".join([f"- {dataset}: {data['method']} (F1: {data['f1']})" 
                          for dataset, data in audit['best_by_dataset'].items()]),
    issues="\n".join([f"- {issue}" for issue in audit['issues']]) if audit['issues'] else "None"
)

# Write summary
with open(os.environ['SUMMARY_MD'], 'w') as f:
    f.write(summary)