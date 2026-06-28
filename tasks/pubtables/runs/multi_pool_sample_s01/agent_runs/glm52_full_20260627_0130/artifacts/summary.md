# PubTables Reconstruction Summary

- **Reconstructed cells:** 35
- **Rows detected:** 7
- **Columns detected:** 7
- **Normalized metric rows:** 5
- **Audit issues:** 10

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|--------|---------|----------|----|-------|
| GraphNet | PubMed |  |  | best |
| TreeCRF | PubMed |  |  | baseline |
| GraphNet | ChemTable |  |  | cross-domain |
| TableFormer | ChemTable |  |  | best |
| Rule Parser | ChemTable |  |  | weak |

## Audit Issues

- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 0, 'field': 'accuracy', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 0, 'field': 'f1', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 1, 'field': 'accuracy', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 1, 'field': 'f1', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 2, 'field': 'accuracy', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 2, 'field': 'f1', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 3, 'field': 'accuracy', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 3, 'field': 'f1', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 4, 'field': 'accuracy', 'value': ''}
- non_numeric_metric: {'type': 'non_numeric_metric', 'row': 4, 'field': 'f1', 'value': ''}

## Notes

Caption and footnote words outside the table bounding box were excluded from metric rows. Row and column structure was inferred from OCR word bounding boxes using y-center clustering and x-gap analysis.
