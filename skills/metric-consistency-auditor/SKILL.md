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
