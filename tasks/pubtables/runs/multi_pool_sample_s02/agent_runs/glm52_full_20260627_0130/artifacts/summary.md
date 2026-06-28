# PubTables Reconstruction Summary

- **Total words in input:** 52
- **Table words retained:** 37
- **Caption/footnote words excluded:** 15
- **Reconstructed cells:** 37
- **Normalized metric rows:** 0
- **Audit issues found:** 3

## Audit Issues

- **missing_required_column**: Column accuracy not found in header mapping
- **missing_required_column**: Column f1 not found in header mapping
- **excluded_non_table_text**: 15 words excluded as caption/footnote (outside table bbox)

## Notes

Table structure was reconstructed from OCR word bounding boxes using y-center proximity for row grouping and x-center gaps for column assignment. Caption and footnote words outside the table bounding box were excluded from metric rows. Numeric values were parsed after stripping formatting characters.