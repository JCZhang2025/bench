---
name: header-span-detector
description: Use when table headers include multiple header rows, grouped labels, row spans, column spans, or parent headers covering several child columns.
---

# Header Span Detector

Use this skill after row and column grouping to preserve table structure rather than flattening every header token.

## Header Band Detection

1. Treat the top aligned rows as candidate header bands until body-like numeric or repeated record rows begin.
2. Keep multiple header bands separate when they occupy different y positions.
3. Mark side labels as row-spanning only when they cover the vertical space of multiple header bands.
4. Mark parent labels as column-spanning when their horizontal coverage overlaps multiple child columns.

## Span Inference

- Compute the column coverage of each header cell from its x-range.
- A parent header spans the count of child columns it horizontally covers.
- A side header spans downward when it aligns with body columns but has no child header under it.
- Do not force spans when the geometry only supports a single column or row.

## Output Expectations

- Keep grouped headers in the structural cell inventory.
- Preserve child headers as separate cells.
- Record inferred `row_span` and `col_span` as integers.
- If a span is ambiguous, choose the conservative smaller span and list the ambiguity in the audit.

## Guardrails

- Do not hardcode header text from a particular fixture.
- Infer spans from position and table geometry.
