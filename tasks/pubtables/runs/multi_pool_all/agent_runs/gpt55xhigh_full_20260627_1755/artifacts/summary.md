# OCR Table Extraction Summary

- Normalized metric rows: 6
- Best method by F1 score:
  - ChemTable: TableFormer (F1 84.2, accuracy 87.8)
  - PubMed QA: GraphNet (F1 88.6, accuracy 91.2)
- Audit issues:
  - empty_required_text: Empty required text field method
  - empty_required_text: Empty required text field dataset
  - non_numeric_metric: Metric field accuracy is not numeric
  - excluded_non_table_text: Words outside the table bounding box were excluded from normalized metric rows.
