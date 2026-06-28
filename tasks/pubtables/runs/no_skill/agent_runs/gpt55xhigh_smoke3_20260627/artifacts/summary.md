# Table Extraction Summary

Normalized metric rows: 6.

## Best F1 By Dataset

- ChemTable: TableFormer with F1 84.2 and accuracy 87.8.
- PubMed QA: GraphNet with F1 88.6 and accuracy 91.2.
- UNKNOWN:  with F1 1 and accuracy Accuracy.

## Audit Issues

- Excluded 15 word(s) outside the table bounding box as caption or footnote text.
- Missing inferred column for accuracy; used positional fallback where possible.
- Missing inferred column for f1; used positional fallback where possible.
- Row 1: missing dataset.
- Row 1: missing method.
- Row 1: missing or non-numeric accuracy value.
