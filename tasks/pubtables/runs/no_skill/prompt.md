# Experiment Condition: no_skill

No-skill baseline

## Condition Metadata

- condition_type: baseline
- sample_seed: 

## Skill Pools

- none

## Pool Samples

- none

## Task

Given a local PubTables-style scientific table in HTML, extract the table structure, normalize the metric rows, audit the extracted values, and write a short grounded Markdown summary.

The input table has multi-row headers and span attributes. Treat header cells, row spans, and column spans as part of the table structure. Exclude caption text and footnotes from the normalized metric rows.

Required normalized metric fields:
- method
- dataset
- accuracy
- f1
- notes

For the audit, report the number of normalized metric rows, the best method by F1 score for each dataset, and any extraction or validation issues you find.

## Available Skills

- none

## Available Skill Documents

No external skill document is provided in this condition.

## Condition Note

No skill document is provided. This measures direct model behavior.

## Required Outputs

Save these artifacts:

- `OUTPUT_CELLS_CSV` -> `artifacts/table_cells.csv`: CSV columns row_id,col_id,row_span,col_span,is_header,text for every non-empty table cell.
- `OUTPUT_METRICS_CSV` -> `artifacts/metrics.csv`: CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.
- `OUTPUT_AUDIT_JSON` -> `artifacts/audit.json`: JSON with row_count, best_by_dataset, and issues.
- `SUMMARY_MD` -> `artifacts/summary.md`: Short Markdown summary grounded in the extracted metrics and audit.

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
