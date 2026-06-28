# PubTables Reconstruction Summary

- **Reconstructed cells:** 36
- **Normalized metric rows:** 5
- **Datasets found:** 2
- **Issues detected:** 10

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|--------|---------|----------|----|-------|
| GraphNet | PubMed |  |  | best |
| TreeCRF | PubMed |  |  | baseline |
| GraphNet | ChemTable |  |  |  |
| TableFormer | ChemTable |  |  | best |
| Rule | ChemTable |  |  | weak |

## Best Method by F1 per Dataset

- **PubMed**: GraphNet (F1=-1)
- **ChemTable**: GraphNet (F1=-1)

## Audit Issues

- Non-numeric accuracy for method=GraphNet, dataset=PubMed: ''
- Non-numeric f1 for method=GraphNet, dataset=PubMed: ''
- Non-numeric accuracy for method=TreeCRF, dataset=PubMed: ''
- Non-numeric f1 for method=TreeCRF, dataset=PubMed: ''
- Non-numeric accuracy for method=GraphNet, dataset=ChemTable: ''
- Non-numeric f1 for method=GraphNet, dataset=ChemTable: ''
- Non-numeric accuracy for method=TableFormer, dataset=ChemTable: ''
- Non-numeric f1 for method=TableFormer, dataset=ChemTable: ''
- Non-numeric accuracy for method=Rule, dataset=ChemTable: ''
- Non-numeric f1 for method=Rule, dataset=ChemTable: ''

## Notes

Caption and footnote words outside the table bounding box were excluded from metric rows. Cells were reconstructed by clustering OCR word boxes into rows and columns using spatial proximity.