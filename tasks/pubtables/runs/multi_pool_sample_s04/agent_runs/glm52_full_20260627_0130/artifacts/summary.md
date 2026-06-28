# PubTables Reconstruction Summary

- Reconstructed cells: 32
- Normalized metric rows: 6
- Audit issues found: 4

## Best Method by F1 per Dataset
- **PubMed QA**: GraphNet (F1=88.6)
- **ChemTable**: TableFormer (F1=84.2)

## Extracted Metrics
| Method | Dataset | Accuracy | F1 | Notes |
|--------|---------|----------|----|-------|
|  |  | Accuracy | F1 |  |
| GraphNet | PubMed QA | 91.2 | 88.6 | best |
| TreeCRF | PubMed QA | 89.5 | 86.9 | baseline |
| GraphNet | ChemTable | 84.7 | 81.3 | cross-domain |
| TableFormer | ChemTable | 87.8 | 84.2 | best |
| Rule Parser | ChemTable | 71.0 | 68.4 | weak baseline |

## Audit Issues
- [non_numeric_metric] Row 1 accuracy not numeric: Accuracy
- [empty_required_text] Row 1 method is empty
- [empty_required_text] Row 1 dataset is empty
- [excluded_non_table_text] 15 words outside table bbox excluded from metrics

## Notes
- Caption and footnote words outside the table bounding box were excluded from metric rows.
- Row and column structure inferred from OCR word bounding boxes using coordinate clustering.