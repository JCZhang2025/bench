# OCR Table Extraction Summary

- Normalized metric rows: **5**
- Validation issues: **1**

## Best F1 By Dataset

| Dataset | Best method | F1 |
|---|---:|---:|
| ChemTable | TableFormer | 84.2 |
| PubMed QA | GraphNet | 88.6 |

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|---|---|---:|---:|---|
| GraphNet | PubMed QA | 91.2 | 88.6 | best |
| TreeCRF | PubMed QA | 89.5 | 86.9 | baseline |
| GraphNet | ChemTable | 84.7 | 81.3 | cross-domain |
| TableFormer | ChemTable | 87.8 | 84.2 | best |
| Rule Parser | ChemTable | 71.0 | 68.4 | weak baseline |

## Audit Notes

- `excluded_non_table_text`: Words outside the table bounding box were excluded from normalized metrics.
