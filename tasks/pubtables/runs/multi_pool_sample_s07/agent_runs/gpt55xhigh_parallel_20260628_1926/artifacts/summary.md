# PubTables Metric Extraction Summary

- Normalized metric rows: 5.
- Best F1 for PubMed QA: GraphNet with F1 88.6 and accuracy 91.2.
- Best F1 for Rule Parser ChemTable: TreeCRF with F1 68.4 and accuracy 71.
- Best F1 for TableFormer ChemTable: TreeCRF with F1 84.2 and accuracy 87.8.
- Audit issues:
  - Excluded 15 word boxes outside the table bounding box as caption, footnote, or page noise.
