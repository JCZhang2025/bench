# PubTables OCR Metric Extraction Summary

- Normalized metric rows: 5
- Best method by F1:
  - ChemTable: TableFormer with F1 84.2, accuracy 87.8
  - PubMed QA: GraphNet with F1 88.6, accuracy 91.2
- Audit issues:
  - excluded_non_table_text: Words outside the table bounding box were excluded as caption/footnote candidates.
