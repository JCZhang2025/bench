# OCR Table Metric Extraction Summary

- Normalized metric rows: **6**
- Datasets with a best F1 method: **2**
- Validation issues: **4**

## Best Method by Dataset

| Dataset | Best method | F1 |
|---|---:|---:|
| ChemTable | TableFormer | 84.2 |
| PubMed QA | GraphNet | 88.6 |

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|---|---|---:|---:|---|
|  |  |  | 1 |  |
| GraphNet | PubMed QA | 91.2 | 88.6 | best |
| TreeCRF | PubMed QA | 89.5 | 86.9 | baseline |
| GraphNet | ChemTable | 84.7 | 81.3 | cross-domain |
| TableFormer | ChemTable | 87.8 | 84.2 | best |
| Rule Parser | ChemTable | 71 | 68.4 | weak baseline |

## Audit

- Row 1, column 2 has non-numeric accuracy: 'Accuracy'.
- Metric row 1 is missing method.
- Metric row 1 is missing dataset.
- Metric row 1 is missing numeric accuracy.
