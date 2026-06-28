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
