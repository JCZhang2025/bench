# PubTables Reconstruction Summary

**Reconstructed cells:** 36  
**Normalized metric rows:** 5  
**Audit issues:** 2

## Best Method by Dataset (F1)

| Dataset | Best Method | F1 |
|---------|-------------|----|
| ChemTable | TableFormer | 84.2 |
| PubMed | GraphNet | 88.6 |

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|--------|---------|----------|----|-------|
| GraphNet | PubMed | 91.2 | 88.6 | best |
| TreeCRF | PubMed | 89.5 | 86.9 | baseline |
| GraphNet | ChemTable | 84.7 | 81.3 | cross-domain |
| TableFormer | ChemTable | 87.8 | 84.2 | best |
| Rule | ChemTable | 71.0 | 68.4 | weak |

## Audit Issues

- missing_or_unmapped_required_column:accuracy
- missing_or_unmapped_required_column:f1
