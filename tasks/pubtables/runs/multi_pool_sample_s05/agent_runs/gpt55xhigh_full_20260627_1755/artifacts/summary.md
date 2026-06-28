# PubTables OCR Extraction Summary

- Normalized metric rows: **5**
- Datasets with valid F1 rankings: **2**

## Best Method by Dataset

| Dataset | Best method | F1 | Accuracy | Notes |
|---|---:|---:|---:|---|
| ChemTable | TableFormer | 84.2 | 87.8 |  |
| PubMed | GraphNet | 88.6 | 91.2 | QA |

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|---|---|---:|---:|---|
| GraphNet | PubMed | 91.2 | 88.6 | QA |
| TreeCRF | PubMed | 89.5 | 86.9 | QA |
| GraphNet | ChemTable | 84.7 | 81.3 |  |
| TableFormer | ChemTable | 87.8 | 84.2 |  |
| TableFormer | ChemTable | 71 | 68.4 | Rule \| Parser |

## Audit Issues

- Row 8 has missing or non-numeric accuracy: 'over table'.
- Row 8 has missing or non-numeric F1: 'cells.'.
- Dropped row without numeric metrics: method='Footnote:', dataset='are'.
