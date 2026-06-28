# PubTables OCR Metric Extraction Summary

Extracted 3 normalized metric row(s) from words inside the table bounding box.

## Best F1 by Dataset

| Dataset | Best method | F1 | Accuracy | Notes |
|---|---:|---:|---:|---|
| Method Dataset Evaluation score (%) Notes | GraphNet PubMed QA 91.2 88.6 best | 84.7 |  |  |

## Audit

- Could not identify the first data row from numeric metric cells.
- No row had exactly five reconstructed cells; inferred five columns by x-position clustering.
- Metric row 4 has a missing or unparseable F1 value.
- Metric row 5 has a missing or unparseable accuracy value.
- Metric row 7 has a missing or unparseable accuracy value.
- Metric row 1 could not be considered for best-by-dataset because F1 is unparseable.

## Normalized Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|---|---|---:|---:|---|
| GraphNet PubMed QA 91.2 88.6 best | Method Dataset Evaluation score (%) Notes | 89.5 |  |  |
| GraphNet PubMed QA 91.2 88.6 best | Method Dataset Evaluation score (%) Notes |  | 84.7 |  |
| TableFormer ChemTable 87.8 84.2 best | Method Dataset Evaluation score (%) Notes |  | 71 |  |
