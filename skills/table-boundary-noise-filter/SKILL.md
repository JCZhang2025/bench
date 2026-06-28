---
name: table-boundary-noise-filter
description: Use when OCR data contains table words mixed with captions, footnotes, page text, or other non-table noise that must be excluded before extraction.
---

# Table Boundary Noise Filter

Use this skill before reconstructing rows and columns when the OCR source includes text outside the table.

## Filtering Procedure

1. Read the table bounding box when one is provided.
2. For each word box, compute its center point and overlap with the table box.
3. Keep words whose center lies inside the table box.
4. For border cases, keep words with strong overlap and record the assumption in the audit.
5. Exclude caption, title, note, and footnote text that is outside the table region.
6. Preserve excluded text separately only if the task asks for provenance; do not mix it into metric rows.

## Quality Checks

- The first reconstructed row should come from the table region, not a caption above it.
- The last reconstructed row should come from the table region, not notes below it.
- Non-table prose should never become a normalized data record.
- If many words are excluded, summarize the reason in the audit artifact.

## Guardrails

- Do not identify excluded text by matching fixture-specific phrases.
- Use geometry and generic text role only.
