# OCR Table Extraction Summary

- Normalized metric rows: 5.
- Best method by F1 for each dataset:
  - GraphNet ChemTable 84.7 81.3 cross-domain: GraphNet ChemTable 84.7 81.3 cross-domain with F1 84.7.
  - GraphNet PubMed QA 91.2 88.6 best: GraphNet PubMed QA 91.2 88.6 best with F1 91.2.
  - Rule Parser ChemTable 71.0 68.4 weak baseline: Rule Parser ChemTable 71.0 68.4 weak baseline with F1 71.0.
  - TableFormer ChemTable 87.8 84.2 best: TableFormer ChemTable 87.8 84.2 best with F1 87.8.
  - TreeCRF PubMed QA 89.5 86.9 baseline: TreeCRF PubMed QA 89.5 86.9 baseline with F1 89.5.
- Audit issues:
  - excluded_non_table_text: 15 OCR words outside the table bounding box were excluded
