# OCR Table Metric Extraction Summary

- Normalized metric rows: 5
- Datasets found: 5

## Best F1 by Dataset

| Dataset | Best method | F1 | Accuracy | Notes |
|---|---:|---:|---:|---|
| GraphNet ChemTable | GraphNet ChemTable | 81.3 | 84.7 | cross-domain |
| GraphNet PubMed QA | GraphNet PubMed QA | 88.6 | 91.2 | best |
| Rule Parser ChemTable | Rule Parser ChemTable | 68.4 | 71 | weak baseline |
| TableFormer ChemTable | TableFormer ChemTable | 84.2 | 87.8 | best |
| TreeCRF PubMed QA | TreeCRF PubMed QA | 86.9 | 89.5 | baseline |

## Audit Issues

- No extraction or validation issues found.

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|---|---|---:|---:|---|
| GraphNet PubMed QA | GraphNet PubMed QA | 91.2 | 88.6 | best |
| TreeCRF PubMed QA | TreeCRF PubMed QA | 89.5 | 86.9 | baseline |
| GraphNet ChemTable | GraphNet ChemTable | 84.7 | 81.3 | cross-domain |
| TableFormer ChemTable | TableFormer ChemTable | 87.8 | 84.2 | best |
| Rule Parser ChemTable | Rule Parser ChemTable | 71 | 68.4 | weak baseline |
