# PubTables Reconstruction Summary

- Reconstructed cells: 35
- Normalized metric rows: 6
- Audit issues: 9

## Best Method by Dataset (F1)

No valid F1 scores found.

## Extracted Metrics

| Method | Dataset | Accuracy | F1 | Notes |
|--------|---------|----------|----|-------|
| unknown | unknown |  |  |  |
| GraphNet | PubMed | 91.2000 |  | best |
| TreeCRF | PubMed | 89.5000 |  | baseline |
| GraphNet | ChemTable | 84.7000 |  | cross-domain |
| TableFormer | ChemTable | 87.8000 |  | best |
| Rule Parser | ChemTable | 71.0000 |  | weak |

## Audit Issues

- **MISSING_METHOD**: Row has no method name
- **MISSING_DATASET**: Row has no dataset name
- **MISSING_ACCURACY**: Accuracy missing for unknown/unknown
- **MISSING_F1**: F1 missing for unknown/unknown
- **MISSING_F1**: F1 missing for GraphNet/PubMed
- **MISSING_F1**: F1 missing for TreeCRF/PubMed
- **MISSING_F1**: F1 missing for GraphNet/ChemTable
- **MISSING_F1**: F1 missing for TableFormer/ChemTable
- **MISSING_F1**: F1 missing for Rule Parser/ChemTable
