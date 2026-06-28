# Experiment Condition: multi_pool_sample_s02

One sampled skill from each pool, seed 2

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 2

## Skill Pools

### table_reconstruction
- table-ocr-structure-reconstructor

### metric_extraction_audit
- metric-consistency-auditor

### summary_reporting
- grounded-metric-summary

## Pool Samples

- table_reconstruction: table-ocr-structure-reconstructor
- metric_extraction_audit: metric-consistency-auditor
- summary_reporting: grounded-metric-summary

## Task

Given a local PubTables-style OCR word JSON file, reconstruct the table structure, normalize the metric rows, audit the extracted values, and write a short grounded Markdown summary.

The input JSON follows the PubTables-style word-box setup: it contains a table bounding box and page words with text plus bounding boxes. Some caption and footnote words are present outside the table bounding box. Use word positions to reconstruct rows, columns, header cells, row spans, and column spans. Exclude caption and footnote words from the normalized metric rows.

Required normalized metric fields:
- method
- dataset
- accuracy
- f1
- notes

For the audit, report the number of normalized metric rows, the best method by F1 score for each dataset, and any extraction or validation issues you find.

## Available Skills

- table-ocr-structure-reconstructor
- metric-consistency-auditor
- grounded-metric-summary

## Available Skill Documents

## Pool: table_reconstruction

### table-ocr-structure-reconstructor

```markdown
---
name: table-ocr-structure-reconstructor
description: Use when reconstructing structured tables from OCR word boxes, bounding boxes, table regions, row and column layout, header bands, spans, and normalized table artifacts.
---

# Table OCR Structure Reconstructor

Use this skill to turn OCR word-level JSON into a structured table without relying on image rendering or task-specific answers.

## Workflow

1. Load the OCR JSON and inspect the schema before transforming it.
2. Identify the table region from provided table bounds or from dense aligned word clusters.
3. Keep only words that belong to the table region; keep excluded caption or footnote text out of normalized rows.
4. Compute each word center, width, height, and baseline-like y position.
5. Group words into visual rows by y-center proximity using a tolerance derived from median word height.
6. Assign words to columns by x-center using supplied column hints when available, otherwise infer vertical bands from repeated x positions and gaps.
7. Merge adjacent words inside the same visual row and column into one cell, preserving left-to-right text order.
8. Separate header bands from body rows by position, alignment, and text role rather than by any expected answer.
9. Detect row spans and column spans from cell coverage across row and column bands.
10. Write both a structural cell inventory and a normalized data table.

## Output Rules

- Produce one structural row per non-empty reconstructed cell.
- Include row id, column id, row span, column span, header flag, and text for the cell inventory.
- Produce normalized metric rows only from body cells.
- Keep extraction assumptions in an audit artifact instead of hiding them in code.

## Leakage Guardrails

- Do not use oracle files, verifier code, target artifacts, expected row counts, or fixture-specific entity names.
- Do not hardcode numeric results or best-item conclusions.
- Treat the task prompt and input JSON as the only task-specific sources.
```

## Pool: metric_extraction_audit

### metric-consistency-auditor

```markdown
---
name: metric-consistency-auditor
description: Use when auditing normalized metric tables for schema consistency, numeric parsing, duplicate records, group-level best scores, and extraction issues.
---

# Metric Consistency Auditor

Use this skill after extraction and normalization to check whether the produced metric table is internally consistent.

## Audit Steps

1. Confirm all required columns are present.
2. Confirm numeric fields parse as numbers after stripping harmless formatting such as percent signs.
3. Confirm text fields are non-empty for each metric row.
4. Check for duplicate records at the intended entity and dataset grain.
5. Compute the best record per group using the requested score field and direction.
6. Compare audit counts against the produced artifact, not against hidden expected answers.
7. Write all assumptions and issues to a machine-readable audit file.

## Issue Categories

- missing_required_column
- non_numeric_metric
- empty_required_text
- duplicate_record
- inconsistent_group_best
- excluded_non_table_text
- ambiguous_structure

## Guardrails

- Do not use oracle artifacts, verifier source, or known expected values.
- Do not hardcode a target row count or target winner.
```

## Pool: summary_reporting

### grounded-metric-summary

```markdown
---
name: grounded-metric-summary
description: Use when writing concise Markdown summaries grounded only in extracted metric rows, audit findings, and computed group-level comparisons.
---

# Grounded Metric Summary

Use this skill to write the final human-readable summary after metrics and audit artifacts exist.

## Summary Procedure

1. Read the normalized metric rows.
2. Read the audit artifact.
3. State the number of normalized records from the produced data.
4. State the best item per requested group only after computing it from the metric rows.
5. Mention extraction or validation issues if the audit reports any.
6. Keep the summary short and avoid unsupported interpretation.

## Grounding Rules

- Every numeric value in the summary must appear in the extracted metrics or be computed directly from them.
- Every named entity in the summary must appear in the extracted metrics.
- Do not mention excluded caption or footnote text unless it is relevant to an audit issue.
- Do not invent recommendations beyond the extracted evidence.

## Guardrails

- Do not copy known answers from outside the produced artifacts.
- Do not use fixture-specific examples in the skill instructions.
```

## Condition Note

Provide exactly one deterministic random skill from each pool. Compare repeated sampled combinations against the all-candidates condition.

## Required Outputs

Save these artifacts:

- `OUTPUT_CELLS_CSV` -> `artifacts/table_cells.csv`: CSV columns row_id,col_id,row_span,col_span,is_header,text for every reconstructed non-empty table cell.
- `OUTPUT_METRICS_CSV` -> `artifacts/metrics.csv`: CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.
- `OUTPUT_AUDIT_JSON` -> `artifacts/audit.json`: JSON with row_count, best_by_dataset, and issues.
- `SUMMARY_MD` -> `artifacts/summary.md`: Short Markdown summary grounded in the extracted metrics and audit.

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
