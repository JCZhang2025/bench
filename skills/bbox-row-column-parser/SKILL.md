---
name: bbox-row-column-parser
description: Use when converting OCR tokens with bounding boxes into stable row groups, column groups, and cell text for noisy semi-structured tables.
---

# Bbox Row Column Parser

Use this skill when the main challenge is assigning OCR words to rows and columns from coordinates.

## Coordinate Normalization

1. For each token, compute `x_center`, `y_center`, `width`, and `height`.
2. Sort tokens by `y_center`, then by `x_center`.
3. Estimate a row tolerance from median token height. Increase tolerance only when adjacent rows would otherwise split the same baseline.
4. Estimate column bands from explicit hints, repeated x ranges, or large horizontal gaps.

## Row Grouping

- Group words into a row when their y-centers are close relative to token height.
- Recompute the row center after adding each token.
- Keep rows sorted from top to bottom.
- Do not merge vertically separated header rows just because their text is semantically related.

## Column Assignment

- Prefer provided column x-ranges when they exist.
- Otherwise infer columns from stable x clusters and repeated alignment across body rows.
- Assign a token to the column whose range contains its center.
- If a token crosses a boundary, choose the column with the largest horizontal overlap.

## Cell Text Assembly

- Within each row-column bucket, sort tokens by x position.
- Join adjacent words with spaces unless punctuation clearly attaches to a neighbor.
- Preserve original casing and symbols.
- Leave missing cells empty rather than shifting later cells left.

## Guardrails

- Do not use expected output values to tune row or column thresholds.
- Do not rely on a fixed number of rows, columns, or body records.
