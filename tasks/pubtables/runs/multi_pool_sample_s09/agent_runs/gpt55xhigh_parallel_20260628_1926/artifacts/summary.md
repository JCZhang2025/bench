# Extracted Table Metrics

Normalized metric rows: **5**.

## Best Method By Dataset

- **ChemTable**: TableFormer with F1 `84.2` and accuracy `87.8`.
- **PubMed QA**: GraphNet with F1 `88.6` and accuracy `91.2`.

## Audit Notes

- Excluded 15 caption/footnote or out-of-table word(s) outside the table bounding box.

## Normalized Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|---|---|---:|---:|---|
| GraphNet | PubMed QA | 91.2 | 88.6 | best |
| TreeCRF | PubMed QA | 89.5 | 86.9 | baseline |
| GraphNet | ChemTable | 84.7 | 81.3 | cross-domain |
| TableFormer | ChemTable | 87.8 | 84.2 | best |
| Rule Parser | ChemTable | 71 | 68.4 | weak baseline |
