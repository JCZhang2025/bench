---
name: extraction-audit-summary
description: Use when reporting both table extraction results and audit limitations in a compact Markdown summary for benchmark artifacts.
---

# Extraction Audit Summary

Use this skill when the final summary needs to communicate what was extracted and how trustworthy the extraction is.

## Required Content

1. Briefly describe the extraction source type.
2. Summarize the number of normalized records from the generated metrics artifact.
3. Summarize the top record or best score per requested group when the task asks for it.
4. Include audit status, especially missing fields, ambiguous spans, non-numeric values, or excluded noise.
5. Keep limitations separate from results.

## Style

- Use Markdown bullets.
- Prefer precise, data-backed statements.
- Keep wording neutral.
- Avoid decorative charts unless explicitly requested.

## Guardrails

- Use only the current input, generated metrics, and generated audit.
- Do not include oracle-only values, verifier-only checks, or fixed expected answers.
