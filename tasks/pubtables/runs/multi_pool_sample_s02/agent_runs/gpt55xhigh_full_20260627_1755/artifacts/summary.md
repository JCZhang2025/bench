# OCR Table Extraction Summary

Normalized metric rows: **6**.

## Best F1 by Dataset

| Dataset | Best method | F1 |
|---|---:|---:|
| ChemTable | TableFormer | 87.8 |
| PubMed QA | GraphNet | 91.2 |

## Normalized Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|---|---|---:|---:|---|
|  |  |  | Accuracy |  |
| GraphNet | PubMed QA |  | 91.2 | best |
| TreeCRF | PubMed QA |  | 89.5 | baseline |
| GraphNet | ChemTable |  | 84.7 | cross-domain |
| TableFormer | ChemTable |  | 87.8 | best |
| Rule Parser | ChemTable |  | 71 | weak baseline |

## Audit Issues

- **excluded_non_table_text**: excluded_non_table_text: excluded 15 OCR words outside the table bounding box
- **empty_required_text**: {"category": "empty_required_text", "row": 0, "field": "method"}
- **empty_required_text**: {"category": "empty_required_text", "row": 0, "field": "dataset"}
- **non_numeric_metric**: {"category": "non_numeric_metric", "row": 0, "field": "accuracy", "value": ""}
- **non_numeric_metric**: {"category": "non_numeric_metric", "row": 0, "field": "f1", "value": "Accuracy"}
- **non_numeric_metric**: {"category": "non_numeric_metric", "row": 1, "field": "accuracy", "value": ""}
- **non_numeric_metric**: {"category": "non_numeric_metric", "row": 2, "field": "accuracy", "value": ""}
- **non_numeric_metric**: {"category": "non_numeric_metric", "row": 3, "field": "accuracy", "value": ""}
- **non_numeric_metric**: {"category": "non_numeric_metric", "row": 4, "field": "accuracy", "value": ""}
- **non_numeric_metric**: {"category": "non_numeric_metric", "row": 5, "field": "accuracy", "value": ""}
