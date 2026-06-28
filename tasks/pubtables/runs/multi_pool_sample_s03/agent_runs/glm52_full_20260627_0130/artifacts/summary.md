# PubTables Extraction Summary

- **Source**: PubTables-style OCR word JSON with bounding boxes
- **Table cells reconstructed**: 36 cells (5 header, 31 body)
- **Normalized metric rows**: 5
- **Excluded caption/footnote words**: 15

## Best Method by Dataset (F1)

- **ChemTable**: GraphNet (F1=N/A)
- **PubMed**: GraphNet (F1=N/A)

## Audit Status

- Excluded 15 caption/footnote words outside table bounding box

## Limitations

- Row and column reconstruction relies on bounding box geometry; merged or misaligned OCR boxes may cause misassignment.
- Header field mapping uses keyword matching; non-standard column headers may not be recognized.
- Numeric normalization handles common formats but may not cover all locale-specific conventions.