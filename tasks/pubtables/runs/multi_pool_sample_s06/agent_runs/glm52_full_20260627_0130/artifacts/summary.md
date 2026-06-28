# PubTables Reconstruction Summary

- **Reconstructed cells:** 37
- **Header rows detected:** 1
- **Normalized metric rows:** 5
- **Extraction issues:** 5

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|--------|---------|----------|----|-------|
| GraphNet | PubMed |  |  | best |
| TreeCRF | PubMed |  |  | baseline |
| GraphNet | ChemTable |  |  | cross-domain |
| TableFormer | ChemTable |  |  | best |
| Rule | ChemTable |  |  | weak |

## Best Method by Dataset (F1)

- **PubMed:** GraphNet (F1=)
- **ChemTable:** GraphNet (F1=)

## Audit Issues

- Row 2: no numeric accuracy or f1 value found
- Row 3: no numeric accuracy or f1 value found
- Row 4: no numeric accuracy or f1 value found
- Row 5: no numeric accuracy or f1 value found
- Row 6: no numeric accuracy or f1 value found

## Notes

Caption and footnote words outside the table bounding box were excluded from metric rows. Cells were reconstructed from OCR word bounding boxes using row clustering by vertical center proximity and column boundary detection from word x-edges.