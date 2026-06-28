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
