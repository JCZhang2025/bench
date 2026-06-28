#!/usr/bin/env python3
"""
Reconstruct a PubTables-style OCR table from word bounding boxes and write:
- table_cells.csv
- metrics.csv
- audit.json
- summary.md

All paths are read from environment variables:
ORIGINAL_WORDS_JSON, OUTPUT_CELLS_CSV, OUTPUT_METRICS_CSV,
OUTPUT_AUDIT_JSON, SUMMARY_MD.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


BBox = Tuple[float, float, float, float]


ROLE_ALIASES = {
    "method": [
        "method",
        "model",
        "approach",
        "algorithm",
        "classifier",
        "system",
        "technique",
    ],
    "dataset": [
        "dataset",
        "data set",
        "benchmark",
        "corpus",
        "test set",
        "data",
    ],
    "accuracy": [
        "accuracy",
        "acc",
        "acc.",
        "top 1",
        "top1",
    ],
    "f1": [
        "f1",
        "f 1",
        "f1 score",
        "f score",
        "f-score",
        "macro f1",
        "micro f1",
    ],
    "notes": [
        "notes",
        "note",
        "remarks",
        "remark",
        "comments",
        "comment",
        "setting",
        "split",
        "details",
    ],
}


@dataclass
class Word:
    text: str
    bbox: BBox

    @property
    def x0(self) -> float:
        return self.bbox[0]

    @property
    def y0(self) -> float:
        return self.bbox[1]

    @property
    def x1(self) -> float:
        return self.bbox[2]

    @property
    def y1(self) -> float:
        return self.bbox[3]

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)


@dataclass
class RowGroup:
    row_id: int
    words: List[Word] = field(default_factory=list)
    center: float = 0.0

    def add(self, word: Word) -> None:
        self.words.append(word)
        self.center = statistics.mean(w.yc for w in self.words)


@dataclass
class Segment:
    row_id: int
    text: str
    words: List[Word]
    bbox: BBox

    @property
    def x0(self) -> float:
        return self.bbox[0]

    @property
    def y0(self) -> float:
        return self.bbox[1]

    @property
    def x1(self) -> float:
        return self.bbox[2]

    @property
    def y1(self) -> float:
        return self.bbox[3]

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2.0


def as_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def normalize_bbox(value: Any) -> Optional[BBox]:
    if isinstance(value, dict):
        lowered = {str(k).lower(): v for k, v in value.items()}

        for keys in (
            ("x0", "y0", "x1", "y1"),
            ("left", "top", "right", "bottom"),
            ("xmin", "ymin", "xmax", "ymax"),
        ):
            if all(k in lowered for k in keys):
                nums = [as_number(lowered[k]) for k in keys]
                if all(v is not None for v in nums):
                    x0, y0, x1, y1 = nums  # type: ignore[misc]
                    return make_xyxy(x0, y0, x1, y1)

        for keys in (("x", "y", "width", "height"), ("left", "top", "width", "height")):
            if all(k in lowered for k in keys):
                nums = [as_number(lowered[k]) for k in keys]
                if all(v is not None for v in nums):
                    x, y, w, h = nums  # type: ignore[misc]
                    return make_xyxy(x, y, x + w, y + h)

    if isinstance(value, (list, tuple)) and len(value) >= 4:
        nums = [as_number(v) for v in value[:4]]
        if all(v is not None for v in nums):
            x0, y0, x1, y1 = nums  # type: ignore[misc]
            return make_xyxy(x0, y0, x1, y1)

    return None


def make_xyxy(x0: float, y0: float, x1: float, y1: float) -> BBox:
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def bbox_area(bbox: BBox) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def overlap_1d(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def overlap_area(a: BBox, b: BBox) -> float:
    return overlap_1d(a[0], a[2], b[0], b[2]) * overlap_1d(a[1], a[3], b[1], b[3])


def center_inside(word: Word, bbox: BBox, pad: float = 1.0) -> bool:
    return (
        bbox[0] - pad <= word.xc <= bbox[2] + pad
        and bbox[1] - pad <= word.yc <= bbox[3] + pad
    )


def walk_json(obj: Any, path: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], Any]]:
    yield path, obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from walk_json(value, path + (str(key),))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from walk_json(value, path + (str(index),))


def extract_words(data: Any) -> List[Word]:
    words: List[Word] = []

    text_keys = ("text", "word", "token", "value", "ocr_text")
    bbox_keys = ("bbox", "bounding_box", "bounds", "box")

    for _, obj in walk_json(data):
        if not isinstance(obj, dict):
            continue

        text_value = None
        for key in text_keys:
            if key in obj and isinstance(obj[key], (str, int, float)):
                text_value = str(obj[key]).strip()
                break

        if not text_value:
            continue

        bbox = None
        for key in bbox_keys:
            if key in obj:
                bbox = normalize_bbox(obj[key])
                if bbox is not None:
                    break

        if bbox is None:
            bbox = normalize_bbox(obj)

        if bbox is not None and bbox_area(bbox) > 0:
            words.append(Word(text=text_value, bbox=bbox))

    seen = set()
    deduped: List[Word] = []
    for word in words:
        key = (
            word.text,
            round(word.x0, 3),
            round(word.y0, 3),
            round(word.x1, 3),
            round(word.y1, 3),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(word)

    return deduped


def find_table_bbox(data: Any, words: List[Word], issues: List[str]) -> BBox:
    candidates: List[Tuple[int, float, BBox, str]] = []

    for path, obj in walk_json(data):
        bbox = normalize_bbox(obj)
        if bbox is None or bbox_area(bbox) <= 0:
            continue

        path_text = ".".join(path).lower()
        score = 0
        if "table" in path_text:
            score += 100
        if "bbox" in path_text or "bound" in path_text or "box" in path_text:
            score += 20
        if "page" in path_text and "table" not in path_text:
            score -= 25
        if "word" in path_text or "token" in path_text:
            score -= 60
        if "cell" in path_text:
            score -= 30

        contained = sum(1 for word in words if center_inside(word, bbox, pad=1.0))
        if contained > 1:
            candidates.append((score, contained, bbox, path_text))

    if candidates:
        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
                -bbox_area(item[2]),
            ),
            reverse=True,
        )
        return candidates[0][2]

    if not words:
        issues.append("No OCR words were found in the input JSON.")
        return (0.0, 0.0, 0.0, 0.0)

    x0 = min(w.x0 for w in words)
    y0 = min(w.y0 for w in words)
    x1 = max(w.x1 for w in words)
    y1 = max(w.y1 for w in words)
    issues.append("No explicit table bounding box was detected; used the full word extent.")
    return (x0, y0, x1, y1)


def filter_table_words(words: List[Word], table_bbox: BBox, issues: List[str]) -> List[Word]:
    filtered = []
    excluded = 0

    for word in words:
        word_area = bbox_area(word.bbox)
        overlap_ratio = overlap_area(word.bbox, table_bbox) / word_area if word_area else 0.0
        if center_inside(word, table_bbox, pad=1.5) or overlap_ratio >= 0.5:
            filtered.append(word)
        else:
            excluded += 1

    if excluded:
        issues.append(
            f"Excluded {excluded} OCR words outside the detected table bounding box "
            "as caption or footnote noise."
        )

    if not filtered and words:
        issues.append("No words fell inside the detected table bounding box; used all OCR words.")
        return words

    return filtered


def median(values: Sequence[float], default: float = 0.0) -> float:
    clean = [v for v in values if math.isfinite(v)]
    return statistics.median(clean) if clean else default


def group_rows(words: List[Word]) -> List[RowGroup]:
    if not words:
        return []

    med_height = median([w.height for w in words], default=8.0)
    row_tolerance = max(1.5, med_height * 0.65)

    rows: List[RowGroup] = []
    for word in sorted(words, key=lambda w: (w.yc, w.xc)):
        if not rows or abs(word.yc - rows[-1].center) > row_tolerance:
            row = RowGroup(row_id=len(rows), words=[word], center=word.yc)
            rows.append(row)
        else:
            rows[-1].add(word)

    for index, row in enumerate(rows):
        row.row_id = index
        row.words.sort(key=lambda w: w.x0)

    return rows


def estimate_cell_gap(rows: List[RowGroup]) -> float:
    gaps: List[float] = []
    char_widths: List[float] = []
    heights: List[float] = []

    for row in rows:
        ordered = sorted(row.words, key=lambda w: w.x0)
        for word in ordered:
            heights.append(word.height)
            char_widths.append(word.width / max(1, len(word.text)))
        for left, right in zip(ordered, ordered[1:]):
            gap = right.x0 - left.x1
            if gap > 0:
                gaps.append(gap)

    med_char = median(char_widths, default=4.0)
    med_height = median(heights, default=8.0)
    base = max(4.0, med_char * 3.0, med_height * 0.55)

    if len(gaps) < 4:
        return base

    sorted_gaps = sorted(gaps)
    split_threshold = None
    best_ratio = 0.0

    for left, right in zip(sorted_gaps, sorted_gaps[1:]):
        if left <= 0:
            continue
        ratio = right / left
        if ratio > best_ratio and right > base:
            best_ratio = ratio
            split_threshold = (left + right) / 2.0

    if split_threshold is not None and best_ratio >= 1.8:
        return max(base, split_threshold)

    small_gaps = sorted_gaps[: max(1, len(sorted_gaps) // 2)]
    return max(base, median(small_gaps, default=base) * 3.0)


def join_tokens(words: List[Word]) -> str:
    parts = [w.text for w in sorted(words, key=lambda w: w.x0)]
    text = " ".join(parts)
    text = re.sub(r"\s+([,.;:%)\]\}])", r"\1", text)
    text = re.sub(r"([\(\[\{])\s+", r"\1", text)
    text = re.sub(r"\s+([/%])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_segments(rows: List[RowGroup], cell_gap: float) -> Dict[int, List[Segment]]:
    segments_by_row: Dict[int, List[Segment]] = {}

    for row in rows:
        ordered = sorted(row.words, key=lambda w: w.x0)
        if not ordered:
            segments_by_row[row.row_id] = []
            continue

        buckets: List[List[Word]] = [[ordered[0]]]
        for word in ordered[1:]:
            gap = word.x0 - buckets[-1][-1].x1
            if gap > cell_gap:
                buckets.append([word])
            else:
                buckets[-1].append(word)

        row_segments: List[Segment] = []
        for bucket in buckets:
            bbox = (
                min(w.x0 for w in bucket),
                min(w.y0 for w in bucket),
                max(w.x1 for w in bucket),
                max(w.y1 for w in bucket),
            )
            row_segments.append(
                Segment(
                    row_id=row.row_id,
                    text=join_tokens(bucket),
                    words=bucket,
                    bbox=bbox,
                )
            )

        segments_by_row[row.row_id] = row_segments

    return segments_by_row


def infer_column_bands(
    segments_by_row: Dict[int, List[Segment]], table_bbox: BBox, issues: List[str]
) -> Tuple[List[BBox], List[float]]:
    counts = [len(segs) for segs in segments_by_row.values() if len(segs) >= 2]
    if not counts:
        issues.append("Could not infer multiple table columns from OCR positions.")
        return [table_bbox], [(table_bbox[0] + table_bbox[2]) / 2.0]

    count_freq = Counter(counts)
    max_count = max(counts)
    target_count = max_count

    if max_count < 5:
        issues.append(
            f"Inferred only {max_count} table columns; expected metric fields may rely on fallback mapping."
        )
    elif max_count > 8:
        modal_count = count_freq.most_common(1)[0][0]
        target_count = modal_count
        issues.append(
            f"Maximum row segment count was {max_count}; used modal count {modal_count} for column bands."
        )

    reference_rows = [
        segs
        for segs in segments_by_row.values()
        if len(segs) == target_count
    ]

    if not reference_rows:
        reference_rows = [max(segments_by_row.values(), key=len)]

    centers: List[float] = []
    for col_id in range(target_count):
        values = []
        for segs in reference_rows:
            if col_id < len(segs):
                values.append(segs[col_id].xc)
        centers.append(median(values, default=table_bbox[0]))

    centers = sorted(centers)

    boundaries = [table_bbox[0]]
    for left, right in zip(centers, centers[1:]):
        boundaries.append((left + right) / 2.0)
    boundaries.append(table_bbox[2])

    bands: List[BBox] = []
    for col_id in range(target_count):
        bands.append((boundaries[col_id], table_bbox[1], boundaries[col_id + 1], table_bbox[3]))

    return bands, centers


def normalized_text(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.replace("-", " ")
    lowered = re.sub(r"[^a-z0-9.]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def role_score(text: str, role: str) -> int:
    norm = normalized_text(text)
    if not norm:
        return 0

    score = 0
    for alias in ROLE_ALIASES[role]:
        alias_norm = normalized_text(alias)
        if not alias_norm:
            continue
        if re.search(rf"(^| )({re.escape(alias_norm)})( |$)", norm):
            score = max(score, 10 + len(alias_norm))
        elif alias_norm in norm:
            score = max(score, 4 + len(alias_norm))
    return score


def parse_numeric(text: str) -> Optional[float]:
    if text is None:
        return None

    cleaned = str(text).strip()
    if not cleaned:
        return None

    if re.fullmatch(r"(?i)n/?a|na|--|-|none", cleaned):
        return None

    cleaned = cleaned.replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def format_number(value: Optional[float]) -> str:
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def detect_header_rows(segments_by_row: Dict[int, List[Segment]]) -> set:
    first_data_row: Optional[int] = None

    for row_id in sorted(segments_by_row):
        segs = segments_by_row[row_id]
        numeric_count = sum(1 for seg in segs if parse_numeric(seg.text) is not None)
        row_text = " ".join(seg.text for seg in segs)
        headerish = any(role_score(row_text, role) > 0 for role in ROLE_ALIASES)
        if numeric_count >= 2 and not headerish:
            first_data_row = row_id
            break

    if first_data_row is not None and first_data_row > 0:
        return set(range(first_data_row))

    header_rows = set()
    for row_id, segs in segments_by_row.items():
        row_text = " ".join(seg.text for seg in segs)
        if any(role_score(row_text, role) > 0 for role in ROLE_ALIASES):
            header_rows.add(row_id)

    if not header_rows and segments_by_row:
        return {min(segments_by_row)}

    return header_rows


def closest_col(x: float, centers: List[float]) -> int:
    return min(range(len(centers)), key=lambda idx: abs(x - centers[idx]))


def assign_segments_to_cells(
    segments_by_row: Dict[int, List[Segment]],
    bands: List[BBox],
    centers: List[float],
    header_rows: set,
) -> List[Dict[str, Any]]:
    cells: List[Dict[str, Any]] = []
    ncols = len(bands)

    for row_id in sorted(segments_by_row):
        segs = sorted(segments_by_row[row_id], key=lambda s: s.x0)
        anchors = [closest_col(seg.xc, centers) for seg in segs]

        used = set()
        adjusted = []
        for anchor in anchors:
            candidate = anchor
            while candidate in used and candidate + 1 < ncols:
                candidate += 1
            while candidate in used and candidate - 1 >= 0:
                candidate -= 1
            used.add(candidate)
            adjusted.append(candidate)

        for idx, seg in enumerate(segs):
            anchor = adjusted[idx]
            start = anchor
            end = anchor

            overlap_cols = []
            for col_id, band in enumerate(bands):
                x_overlap = overlap_1d(seg.x0, seg.x1, band[0], band[2])
                if x_overlap > 0 and x_overlap >= min(max(1.0, seg.x1 - seg.x0), band[2] - band[0]) * 0.15:
                    overlap_cols.append(col_id)

            if len(overlap_cols) > 1:
                start = min(overlap_cols)
                end = max(overlap_cols)

            if row_id in header_rows and len(segs) < ncols:
                prev_anchor = adjusted[idx - 1] if idx > 0 else None
                next_anchor = adjusted[idx + 1] if idx + 1 < len(adjusted) else None

                if prev_anchor is not None and next_anchor is not None and next_anchor - prev_anchor > 1:
                    start = prev_anchor + 1
                    end = next_anchor - 1
                elif idx == 0 and next_anchor is not None and next_anchor - anchor > 1:
                    start = 0 if anchor == 0 else anchor
                    end = next_anchor - 1
                elif idx == len(segs) - 1 and prev_anchor is not None and anchor - prev_anchor > 1:
                    start = prev_anchor + 1
                    end = anchor

            start = max(0, min(start, ncols - 1))
            end = max(start, min(end, ncols - 1))

            cells.append(
                {
                    "row_id": row_id,
                    "col_id": start,
                    "row_span": 1,
                    "col_span": end - start + 1,
                    "is_header": row_id in header_rows,
                    "text": seg.text,
                }
            )

    return cells


def infer_roles(
    cells: List[Dict[str, Any]],
    ncols: int,
    header_rows: set,
    issues: List[str],
) -> Dict[str, int]:
    header_text_by_col = defaultdict(list)

    for cell in cells:
        if not cell["is_header"]:
            continue
        for col_id in range(cell["col_id"], cell["col_id"] + cell["col_span"]):
            header_text_by_col[col_id].append(cell["text"])

    assignments: Dict[str, int] = {}
    used_cols = set()

    for role in ("method", "dataset", "accuracy", "f1", "notes"):
        scored = []
        for col_id in range(ncols):
            header_text = " ".join(header_text_by_col[col_id])
            score = role_score(header_text, role)
            if score:
                scored.append((score, -col_id, col_id))

        scored.sort(reverse=True)
        for _, _, col_id in scored:
            if col_id not in used_cols:
                assignments[role] = col_id
                used_cols.add(col_id)
                break

    body_rows = sorted({cell["row_id"] for cell in cells if not cell["is_header"]})
    body_text_by_col = defaultdict(list)
    for cell in cells:
        if cell["is_header"]:
            continue
        for col_id in range(cell["col_id"], cell["col_id"] + cell["col_span"]):
            body_text_by_col[col_id].append(cell["text"])

    numeric_cols = []
    for col_id in range(ncols):
        values = body_text_by_col[col_id]
        if values:
            numeric_count = sum(1 for text in values if parse_numeric(text) is not None)
            numeric_cols.append((numeric_count, col_id))

    numeric_cols = [col_id for count, col_id in sorted(numeric_cols, reverse=True) if count > 0]
    numeric_cols.sort()

    if "accuracy" not in assignments and numeric_cols:
        assignments["accuracy"] = numeric_cols[0]
        used_cols.add(numeric_cols[0])
        issues.append("Accuracy column was assigned by numeric-column fallback.")

    if "f1" not in assignments:
        candidates = [col for col in numeric_cols if col != assignments.get("accuracy")]
        if candidates:
            assignments["f1"] = candidates[0]
            used_cols.add(candidates[0])
            issues.append("F1 column was assigned by numeric-column fallback.")

    metric_left = min(
        [assignments[k] for k in ("accuracy", "f1") if k in assignments],
        default=ncols,
    )

    if "method" not in assignments:
        candidates = [col for col in range(metric_left) if col not in used_cols]
        if candidates:
            assignments["method"] = candidates[0]
            used_cols.add(candidates[0])
            issues.append("Method column was assigned by positional fallback.")

    if "dataset" not in assignments:
        candidates = [col for col in range(metric_left) if col not in used_cols]
        if candidates:
            assignments["dataset"] = candidates[0]
            used_cols.add(candidates[0])
            issues.append("Dataset column was assigned by positional fallback.")

    if "notes" not in assignments:
        f1_col = assignments.get("f1", -1)
        candidates = [col for col in range(f1_col + 1, ncols) if col not in used_cols]
        if candidates:
            assignments["notes"] = candidates[-1]
            used_cols.add(candidates[-1])
            issues.append("Notes column was assigned by positional fallback.")
        elif ncols:
            assignments["notes"] = ncols - 1
            issues.append("Notes column was assigned to the rightmost column by fallback.")

    missing = [role for role in ("method", "dataset", "accuracy", "f1", "notes") if role not in assignments]
    if missing:
        issues.append(f"Could not assign required columns: {', '.join(missing)}.")

    if not body_rows:
        issues.append("No non-header table rows were detected.")

    return assignments


def add_row_spans(cells: List[Dict[str, Any]], role_cols: Dict[str, int], header_rows: set) -> None:
    by_row = defaultdict(list)
    for cell in cells:
        by_row[cell["row_id"]].append(cell)

    row_ids = sorted(by_row)
    body_span_cols = {
        role_cols[role]
        for role in ("method", "dataset")
        if role in role_cols
    }

    for cell in cells:
        row_id = cell["row_id"]
        col_start = cell["col_id"]
        col_end = cell["col_id"] + cell["col_span"] - 1
        span_cols = set(range(col_start, col_end + 1))

        if cell["is_header"]:
            candidate_rows = [rid for rid in row_ids if rid > row_id and rid in header_rows]
        elif span_cols & body_span_cols:
            candidate_rows = [rid for rid in row_ids if rid > row_id and rid not in header_rows]
        else:
            continue

        row_span = 1
        for next_row_id in candidate_rows:
            blocked = False
            for other in by_row[next_row_id]:
                other_cols = set(range(other["col_id"], other["col_id"] + other["col_span"]))
                if span_cols & other_cols:
                    blocked = True
                    break
            if blocked:
                break
            row_span += 1

        cell["row_span"] = row_span


def cell_text_for_col(row_cells: List[Dict[str, Any]], col_id: Optional[int]) -> str:
    if col_id is None:
        return ""
    for cell in row_cells:
        start = cell["col_id"]
        end = start + cell["col_span"] - 1
        if start <= col_id <= end:
            return str(cell["text"]).strip()
    return ""


def normalize_metrics(
    cells: List[Dict[str, Any]],
    role_cols: Dict[str, int],
    issues: List[str],
) -> List[Dict[str, str]]:
    by_row = defaultdict(list)
    for cell in cells:
        by_row[cell["row_id"]].append(cell)

    metrics: List[Dict[str, str]] = []
    last_method = ""
    last_dataset = ""

    for row_id in sorted(by_row):
        row_cells = by_row[row_id]
        if any(cell["is_header"] for cell in row_cells):
            continue

        method = cell_text_for_col(row_cells, role_cols.get("method"))
        dataset = cell_text_for_col(row_cells, role_cols.get("dataset"))
        accuracy_text = cell_text_for_col(row_cells, role_cols.get("accuracy"))
        f1_text = cell_text_for_col(row_cells, role_cols.get("f1"))
        notes = cell_text_for_col(row_cells, role_cols.get("notes"))

        if method:
            last_method = method
        elif last_method:
            method = last_method
            issues.append(f"Filled missing method in row {row_id} from preceding row-span context.")

        if dataset:
            last_dataset = dataset
        elif last_dataset:
            dataset = last_dataset
            issues.append(f"Filled missing dataset in row {row_id} from preceding row-span context.")

        accuracy = parse_numeric(accuracy_text)
        f1 = parse_numeric(f1_text)

        if not any([method, dataset, accuracy_text, f1_text, notes]):
            continue

        if accuracy is None and f1 is None:
            issues.append(f"Skipped row {row_id} because no numeric accuracy or F1 value was found.")
            continue

        if not method:
            issues.append(f"Metric row {row_id} has no method value.")
        if not dataset:
            issues.append(f"Metric row {row_id} has no dataset value.")
        if accuracy_text and accuracy is None:
            issues.append(f"Accuracy value in row {row_id} is non-numeric: {accuracy_text!r}.")
        if f1_text and f1 is None:
            issues.append(f"F1 value in row {row_id} is non-numeric: {f1_text!r}.")

        metrics.append(
            {
                "method": method,
                "dataset": dataset,
                "accuracy": format_number(accuracy),
                "f1": format_number(f1),
                "notes": notes,
            }
        )

    return metrics


def audit_metrics(metrics: List[Dict[str, str]], issues: List[str]) -> Dict[str, Any]:
    by_dataset: Dict[str, List[Tuple[float, Dict[str, str]]]] = defaultdict(list)

    for row in metrics:
        dataset = row.get("dataset", "").strip()
        f1 = parse_numeric(row.get("f1", ""))
        if not dataset:
            issues.append(f"Metric row for method {row.get('method', '')!r} has empty dataset.")
            continue
        if f1 is None:
            issues.append(
                f"Metric row for dataset {dataset!r}, method {row.get('method', '')!r} has no numeric F1."
            )
            continue
        by_dataset[dataset].append((f1, row))

    best_by_dataset: Dict[str, Dict[str, Any]] = {}
    for dataset in sorted(by_dataset):
        values = by_dataset[dataset]
        values.sort(key=lambda item: (-item[0], item[1].get("method", "")))
        best_f1, best_row = values[0]

        tied = [row for f1, row in values if f1 == best_f1]
        if len(tied) > 1:
            methods = ", ".join(sorted(row.get("method", "") for row in tied))
            issues.append(f"Dataset {dataset!r} has a tie for best F1 among: {methods}.")

        best_by_dataset[dataset] = {
            "method": best_row.get("method", ""),
            "f1": best_f1,
            "accuracy": parse_numeric(best_row.get("accuracy", "")),
            "notes": best_row.get("notes", ""),
        }

    f1_values = [parse_numeric(row.get("f1", "")) for row in metrics]
    f1_values = [value for value in f1_values if value is not None]
    if f1_values and min(f1_values) <= 1 < max(f1_values):
        issues.append("F1 values appear to mix fractional and percentage scales.")

    accuracy_values = [parse_numeric(row.get("accuracy", "")) for row in metrics]
    accuracy_values = [value for value in accuracy_values if value is not None]
    if accuracy_values and min(accuracy_values) <= 1 < max(accuracy_values):
        issues.append("Accuracy values appear to mix fractional and percentage scales.")

    return {
        "row_count": len(metrics),
        "best_by_dataset": best_by_dataset,
        "issues": sorted(set(issues)),
    }


def write_cells_csv(path: str, cells: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["row_id", "col_id", "row_span", "col_span", "is_header", "text"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for cell in sorted(cells, key=lambda c: (c["row_id"], c["col_id"], c["text"])):
            writer.writerow({key: cell[key] for key in fieldnames})


def write_metrics_csv(path: str, metrics: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["method", "dataset", "accuracy", "f1", "notes"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_audit_json(path: str, audit: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False, sort_keys=True)


def write_summary_md(path: str, audit: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    lines = [
        "# Extraction Audit Summary",
        "",
        "- Source: PubTables-style OCR word JSON with table reconstruction from word bounding boxes.",
        f"- Normalized metric rows: {audit['row_count']}.",
    ]

    best_by_dataset = audit.get("best_by_dataset", {})
    if best_by_dataset:
        lines.append("- Best F1 by dataset:")
        for dataset in sorted(best_by_dataset):
            best = best_by_dataset[dataset]
            lines.append(
                f"  - {dataset}: {best.get('method', '')} "
                f"(F1 {format_number(parse_numeric(str(best.get('f1', ''))))})."
            )
    else:
        lines.append("- Best F1 by dataset: no dataset-level best record could be computed.")

    issues = audit.get("issues", [])
    if issues:
        lines.append("- Audit status: issues were found during extraction or validation.")
        lines.append("- Limitations:")
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("- Audit status: no extraction or validation issues were detected.")
        lines.append("- Limitations: none identified from the reconstructed table.")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    input_json = required_env("ORIGINAL_WORDS_JSON")
    output_cells_csv = required_env("OUTPUT_CELLS_CSV")
    output_metrics_csv = required_env("OUTPUT_METRICS_CSV")
    output_audit_json = required_env("OUTPUT_AUDIT_JSON")
    summary_md = required_env("SUMMARY_MD")

    issues: List[str] = []

    with open(input_json, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    words = extract_words(data)
    table_bbox = find_table_bbox(data, words, issues)
    table_words = filter_table_words(words, table_bbox, issues)

    rows = group_rows(table_words)
    cell_gap = estimate_cell_gap(rows)
    segments_by_row = make_segments(rows, cell_gap)

    bands, centers = infer_column_bands(segments_by_row, table_bbox, issues)
    header_rows = detect_header_rows(segments_by_row)
    cells = assign_segments_to_cells(segments_by_row, bands, centers, header_rows)

    role_cols = infer_roles(cells, len(bands), header_rows, issues)
    add_row_spans(cells, role_cols, header_rows)

    metrics = normalize_metrics(cells, role_cols, issues)
    audit = audit_metrics(metrics, issues)

    write_cells_csv(output_cells_csv, cells)
    write_metrics_csv(output_metrics_csv, metrics)
    write_audit_json(output_audit_json, audit)
    write_summary_md(summary_md, audit)


if __name__ == "__main__":
    main()
