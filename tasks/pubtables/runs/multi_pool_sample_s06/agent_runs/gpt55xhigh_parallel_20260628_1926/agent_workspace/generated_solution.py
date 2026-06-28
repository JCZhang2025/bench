#!/usr/bin/env python3
"""
Reconstruct a PubTables-style OCR word table, normalize metric rows, audit them,
and write the required artifacts.

Inputs/outputs are read from these environment variables:
- ORIGINAL_WORDS_JSON
- OUTPUT_CELLS_CSV
- OUTPUT_METRICS_CSV
- OUTPUT_AUDIT_JSON
- SUMMARY_MD
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_PATHS = {
    "ORIGINAL_WORDS_JSON": r"E:\research\pilot_experiments\tasks\pubtables\data\original\table_words.json",
    "OUTPUT_CELLS_CSV": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s06\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\table_cells.csv",
    "OUTPUT_METRICS_CSV": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s06\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\metrics.csv",
    "OUTPUT_AUDIT_JSON": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s06\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\audit.json",
    "SUMMARY_MD": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s06\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\summary.md",
}


@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)


@dataclass
class Segment:
    row_id: int
    words: List[Word]

    @property
    def text(self) -> str:
        return " ".join(w.text for w in sorted(self.words, key=lambda w: w.x0)).strip()

    @property
    def x0(self) -> float:
        return min(w.x0 for w in self.words)

    @property
    def y0(self) -> float:
        return min(w.y0 for w in self.words)

    @property
    def x1(self) -> float:
        return max(w.x1 for w in self.words)

    @property
    def y1(self) -> float:
        return max(w.y1 for w in self.words)

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0


@dataclass
class Cell:
    row_id: int
    col_id: int
    row_span: int
    col_span: int
    is_header: bool
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


def path_for(name: str) -> str:
    return os.environ.get(name, DEFAULT_PATHS[name])


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def normalize_bbox(parts: Sequence[Any]) -> Optional[Tuple[float, float, float, float]]:
    if len(parts) != 4:
        return None
    try:
        vals = [float(v) for v in parts]
    except (TypeError, ValueError):
        return None
    x0, y0, x1, y1 = vals
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if not all(math.isfinite(v) for v in (x0, y0, x1, y1)):
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def bbox_from_obj(obj: Any) -> Optional[Tuple[float, float, float, float]]:
    if isinstance(obj, (list, tuple)):
        return normalize_bbox(obj)

    if not isinstance(obj, dict):
        return None

    for key in ("bbox", "box", "bounding_box", "bounds", "rect"):
        if key in obj:
            found = bbox_from_obj(obj[key])
            if found:
                return found

    keyed_sets = [
        ("x0", "y0", "x1", "y1"),
        ("xmin", "ymin", "xmax", "ymax"),
        ("left", "top", "right", "bottom"),
        ("l", "t", "r", "b"),
    ]
    for keys in keyed_sets:
        if all(k in obj for k in keys):
            return normalize_bbox([obj[k] for k in keys])

    size_sets = [
        ("x", "y", "w", "h"),
        ("x", "y", "width", "height"),
        ("left", "top", "width", "height"),
    ]
    for x_key, y_key, w_key, h_key in size_sets:
        if all(k in obj for k in (x_key, y_key, w_key, h_key)):
            try:
                x = float(obj[x_key])
                y = float(obj[y_key])
                w = float(obj[w_key])
                h = float(obj[h_key])
            except (TypeError, ValueError):
                continue
            return normalize_bbox([x, y, x + w, y + h])

    return None


def text_from_obj(obj: Dict[str, Any]) -> Optional[str]:
    for key in ("text", "word", "token", "value", "content", "ocr_text"):
        if key in obj and obj[key] is not None:
            text = str(obj[key]).strip()
            if text:
                return text
    return None


def collect_words(obj: Any) -> List[Word]:
    words: List[Word] = []
    seen = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            text = text_from_obj(node)
            bbox = bbox_from_obj(node)
            if text and bbox:
                rounded = tuple(round(v, 3) for v in bbox)
                key = (text, rounded)
                if key not in seen:
                    seen.add(key)
                    words.append(Word(text=text, x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(obj)
    return words


def find_table_bbox(obj: Any, words: List[Word]) -> Optional[Tuple[float, float, float, float]]:
    candidates: List[Tuple[int, float, Tuple[float, float, float, float]]] = []

    def area(b: Tuple[float, float, float, float]) -> float:
        return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])

    def score_path(path: Sequence[str]) -> int:
        joined = "/".join(path).lower()
        score = 0
        if "table_bbox" in joined or "table_bounding" in joined or "table_box" in joined:
            score += 10
        if "table" in joined:
            score += 6
        if joined.endswith("/bbox") or joined.endswith("/box") or joined.endswith("/bounding_box"):
            score += 2
        if "word" in joined or "token" in joined:
            score -= 8
        return score

    def walk(node: Any, path: List[str]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                lowered = key.lower()
                if lowered in {"table_bbox", "table_bounding_box", "table_box", "bbox", "box", "bounding_box", "bounds"}:
                    bbox = bbox_from_obj(value)
                    if bbox:
                        candidates.append((score_path(path + [key]), area(bbox), bbox))
                walk(value, path + [key])
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, path + [str(i)])

    walk(obj, [])

    strong = [c for c in candidates if c[0] > 0]
    if strong:
        strong.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return strong[0][2]

    if words:
        return (
            min(w.x0 for w in words),
            min(w.y0 for w in words),
            max(w.x1 for w in words),
            max(w.y1 for w in words),
        )
    return None


def inside_bbox(word: Word, bbox: Tuple[float, float, float, float], tolerance: float = 1.0) -> bool:
    x0, y0, x1, y1 = bbox
    return (x0 - tolerance) <= word.cx <= (x1 + tolerance) and (y0 - tolerance) <= word.cy <= (y1 + tolerance)


def cluster_rows(words: List[Word]) -> List[List[Word]]:
    if not words:
        return []

    heights = [w.height for w in words if w.height > 0]
    med_height = median(heights) if heights else 8.0
    threshold = max(2.0, med_height * 0.65)

    clusters: List[List[Word]] = []
    centers: List[float] = []

    for word in sorted(words, key=lambda w: (w.cy, w.x0)):
        assigned = False
        for idx, center in enumerate(centers):
            local_threshold = max(threshold, (word.height + median([w.height for w in clusters[idx]])) * 0.35)
            if abs(word.cy - center) <= local_threshold:
                clusters[idx].append(word)
                centers[idx] = sum(w.cy for w in clusters[idx]) / len(clusters[idx])
                assigned = True
                break
        if not assigned:
            clusters.append([word])
            centers.append(word.cy)

    ordered = sorted(clusters, key=lambda row: sum(w.cy for w in row) / len(row))
    return [sorted(row, key=lambda w: w.x0) for row in ordered]


def estimate_gap_threshold(rows: List[List[Word]]) -> float:
    gaps: List[float] = []
    heights: List[float] = []
    for row in rows:
        heights.extend(w.height for w in row if w.height > 0)
        ordered = sorted(row, key=lambda w: w.x0)
        for left, right in zip(ordered, ordered[1:]):
            gap = right.x0 - left.x1
            if gap > 0:
                gaps.append(gap)

    med_height = median(heights) if heights else 8.0
    if not gaps:
        return med_height * 1.5

    small_gaps = sorted(gaps)[: max(1, len(gaps) // 2)]
    baseline_gap = median(small_gaps)
    return max(med_height * 0.85, baseline_gap * 2.6, 3.0)


def row_segments(rows: List[List[Word]]) -> List[List[Segment]]:
    threshold = estimate_gap_threshold(rows)
    segmented_rows: List[List[Segment]] = []

    for row_id, row in enumerate(rows):
        ordered = sorted(row, key=lambda w: w.x0)
        if not ordered:
            segmented_rows.append([])
            continue

        groups: List[List[Word]] = [[ordered[0]]]
        for word in ordered[1:]:
            gap = word.x0 - groups[-1][-1].x1
            if gap > threshold:
                groups.append([word])
            else:
                groups[-1].append(word)

        segmented_rows.append([Segment(row_id=row_id, words=group) for group in groups])

    return segmented_rows


def parse_number(text: str) -> Optional[float]:
    if text is None:
        return None
    raw = str(text).strip()
    if not raw or raw in {"-", "--", "—", "–", "N/A", "NA", "n/a", "na"}:
        return None

    lowered = raw.lower()
    if re.search(r"[a-z]", lowered.replace("e", ""), flags=re.I):
        return None

    cleaned = raw.replace("%", "").replace(",", "").strip()
    cleaned = re.sub(r"^\((.*)\)$", r"\1", cleaned)
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None

    prefix = cleaned[: match.start()].strip()
    suffix = cleaned[match.end() :].strip()
    harmless = {"", "*", "†", "‡"}
    if prefix not in harmless or suffix not in harmless:
        if not re.fullmatch(r"[\s*†‡±+\-/().]*", prefix + suffix):
            return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def format_number(value: Optional[float]) -> str:
    if value is None:
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def first_data_row(segmented_rows: List[List[Segment]]) -> int:
    for row_id, segments in enumerate(segmented_rows):
        numeric_count = sum(1 for seg in segments if parse_number(seg.text) is not None)
        row_text = " ".join(seg.text for seg in segments).lower()
        headerish = bool(re.search(r"\b(method|model|dataset|data\s*set|accuracy|acc\.?|f1|note|remark)\b", row_text))
        if numeric_count >= 2 and not headerish:
            return row_id

    for row_id, segments in enumerate(segmented_rows):
        if sum(1 for seg in segments if parse_number(seg.text) is not None) >= 2:
            return row_id

    return 1 if len(segmented_rows) > 1 else 0


def choose_anchor_row(segmented_rows: List[List[Segment]], data_start: int) -> List[Segment]:
    candidates = segmented_rows[data_start:] or segmented_rows
    non_empty = [row for row in candidates if row]
    if not non_empty:
        return []
    return max(non_empty, key=lambda row: (len(row), sum(1 for seg in row if parse_number(seg.text) is not None)))


def build_column_bounds(anchor: List[Segment], table_bbox: Tuple[float, float, float, float]) -> List[float]:
    if not anchor:
        return [table_bbox[0], table_bbox[2]]

    ordered = sorted(anchor, key=lambda s: s.x0)
    bounds = [table_bbox[0]]
    for left, right in zip(ordered, ordered[1:]):
        bounds.append((left.x1 + right.x0) / 2.0)
    bounds.append(table_bbox[2])

    for i in range(1, len(bounds)):
        if bounds[i] <= bounds[i - 1]:
            bounds[i] = bounds[i - 1] + 1e-6
    return bounds


def assign_segment_columns(segment: Segment, bounds: List[float]) -> Tuple[int, int]:
    ncols = max(1, len(bounds) - 1)
    overlaps: List[Tuple[int, float]] = []
    for col in range(ncols):
        left, right = bounds[col], bounds[col + 1]
        overlap = max(0.0, min(segment.x1, right) - max(segment.x0, left))
        if overlap > 0:
            overlaps.append((col, overlap))

    if overlaps:
        meaningful = [col for col, overlap in overlaps if overlap >= max(1.0, segment.x1 - segment.x0) * 0.08]
        if meaningful:
            return min(meaningful), max(meaningful)

    centers = [(bounds[i] + bounds[i + 1]) / 2.0 for i in range(ncols)]
    nearest = min(range(ncols), key=lambda i: abs(segment.cx - centers[i]))
    return nearest, nearest


def make_cells(segmented_rows: List[List[Segment]], bounds: List[float], data_start: int) -> List[Cell]:
    merged: Dict[Tuple[int, int, int], Cell] = {}

    for row_id, segments in enumerate(segmented_rows):
        for segment in segments:
            text = segment.text
            if not text:
                continue
            col_start, col_end = assign_segment_columns(segment, bounds)
            key = (row_id, col_start, col_end)
            if key in merged:
                cell = merged[key]
                pieces = [cell.text, text]
                cell.text = " ".join(p for p in pieces if p).strip()
                cell.x0 = min(cell.x0, segment.x0)
                cell.y0 = min(cell.y0, segment.y0)
                cell.x1 = max(cell.x1, segment.x1)
                cell.y1 = max(cell.y1, segment.y1)
            else:
                merged[key] = Cell(
                    row_id=row_id,
                    col_id=col_start,
                    row_span=1,
                    col_span=col_end - col_start + 1,
                    is_header=row_id < data_start,
                    text=text,
                    x0=segment.x0,
                    y0=segment.y0,
                    x1=segment.x1,
                    y1=segment.y1,
                )

    return sorted(merged.values(), key=lambda c: (c.row_id, c.col_id, c.x0))


def cell_covers_col(cell: Cell, col: int) -> bool:
    return cell.col_id <= col < cell.col_id + cell.col_span


def row_cell_text(cells: List[Cell], row_id: int, col: int) -> str:
    parts = [c.text for c in cells if c.row_id == row_id and cell_covers_col(c, col)]
    return " ".join(parts).strip()


def map_columns(cells: List[Cell], ncols: int, data_start: int) -> Dict[str, Optional[int]]:
    header_texts = {col: [] for col in range(ncols)}
    for cell in cells:
        if cell.row_id < data_start:
            for col in range(cell.col_id, min(ncols, cell.col_id + cell.col_span)):
                header_texts[col].append(cell.text)

    combined = {col: " ".join(header_texts[col]).lower() for col in range(ncols)}

    patterns = {
        "method": r"\b(method|model|approach|system|algorithm|classifier)\b",
        "dataset": r"\b(data\s*set|dataset|benchmark|corpus|task)\b",
        "accuracy": r"\b(acc(?:uracy)?\.?|accuracy)\b",
        "f1": r"\b(f\s*1|f1|f-?score|f1-score)\b",
        "notes": r"\b(notes?|remarks?|comments?|settings?|details?)\b",
    }

    mapping: Dict[str, Optional[int]] = {field: None for field in patterns}
    for field, pattern in patterns.items():
        matches = [col for col, text in combined.items() if re.search(pattern, text)]
        if matches:
            mapping[field] = matches[0]

    numeric_counts = []
    text_counts = []
    max_row = max((c.row_id for c in cells), default=-1)
    for col in range(ncols):
        numeric = 0
        text = 0
        for row_id in range(data_start, max_row + 1):
            value = row_cell_text(cells, row_id, col)
            if not value:
                continue
            if parse_number(value) is not None:
                numeric += 1
            else:
                text += 1
        numeric_counts.append((col, numeric))
        text_counts.append((col, text))

    numeric_cols = [col for col, count in sorted(numeric_counts, key=lambda item: (-item[1], item[0])) if count > 0]
    text_cols = [col for col, count in sorted(text_counts, key=lambda item: (item[0])) if count > 0]

    if mapping["accuracy"] is None and numeric_cols:
        mapping["accuracy"] = numeric_cols[0]
    if mapping["f1"] is None:
        for col in numeric_cols:
            if col != mapping["accuracy"]:
                mapping["f1"] = col
                break

    used = {v for v in mapping.values() if v is not None}
    remaining_text = [col for col in text_cols if col not in used]

    if mapping["method"] is None and remaining_text:
        mapping["method"] = remaining_text[0]
        used.add(remaining_text[0])
    if mapping["dataset"] is None:
        remaining_text = [col for col in text_cols if col not in used]
        if remaining_text:
            mapping["dataset"] = remaining_text[0]
            used.add(remaining_text[0])
    if mapping["notes"] is None:
        remaining_text = [col for col in text_cols if col not in used]
        if remaining_text:
            mapping["notes"] = remaining_text[-1]

    return mapping


def infer_row_spans(cells: List[Cell], ncols: int, data_start: int, mapping: Dict[str, Optional[int]]) -> None:
    by_row: Dict[int, List[Cell]] = {}
    for cell in cells:
        by_row.setdefault(cell.row_id, []).append(cell)

    for cell in cells:
        if not cell.is_header:
            continue
        span = 1
        for row_id in range(cell.row_id + 1, data_start):
            has_overlap = any(
                any(cell_covers_col(other, col) for col in range(cell.col_id, cell.col_id + cell.col_span))
                for other in by_row.get(row_id, [])
            )
            if has_overlap:
                break
            span += 1
        cell.row_span = max(cell.row_span, span)

    carry_cols = [mapping.get("method"), mapping.get("dataset")]
    carry_cols = [col for col in carry_cols if col is not None]

    last_cell_by_col: Dict[int, Cell] = {}
    max_row = max((c.row_id for c in cells), default=-1)
    for row_id in range(data_start, max_row + 1):
        row = by_row.get(row_id, [])
        numeric_count = sum(1 for c in row if parse_number(c.text) is not None)
        metric_like = numeric_count >= 1
        for col in carry_cols:
            present = [c for c in row if cell_covers_col(c, col)]
            if present:
                last_cell_by_col[col] = present[0]
            elif metric_like and col in last_cell_by_col:
                last_cell_by_col[col].row_span += 1


def normalize_metrics(
    cells: List[Cell],
    data_start: int,
    mapping: Dict[str, Optional[int]],
) -> List[Dict[str, str]]:
    max_row = max((c.row_id for c in cells), default=-1)
    records: List[Dict[str, str]] = []
    carry: Dict[str, str] = {"method": "", "dataset": ""}

    for row_id in range(data_start, max_row + 1):
        row_values: Dict[str, str] = {}
        for field in ("method", "dataset", "accuracy", "f1", "notes"):
            col = mapping.get(field)
            row_values[field] = row_cell_text(cells, row_id, col) if col is not None else ""

        for field in ("method", "dataset"):
            if row_values[field]:
                carry[field] = row_values[field]
            else:
                row_values[field] = carry[field]

        accuracy_num = parse_number(row_values["accuracy"])
        f1_num = parse_number(row_values["f1"])

        if accuracy_num is None or f1_num is None:
            numeric_cells = []
            for cell in sorted([c for c in cells if c.row_id == row_id], key=lambda c: c.col_id):
                num = parse_number(cell.text)
                if num is not None:
                    numeric_cells.append((cell.col_id, num))
            if accuracy_num is None and numeric_cells:
                accuracy_num = numeric_cells[0][1]
            if f1_num is None:
                for col, num in numeric_cells:
                    if mapping.get("accuracy") is None or col != mapping.get("accuracy"):
                        if num != accuracy_num or len(numeric_cells) == 1:
                            f1_num = num
                            break

        has_metric = accuracy_num is not None or f1_num is not None
        if not has_metric:
            continue

        records.append(
            {
                "method": row_values["method"].strip(),
                "dataset": row_values["dataset"].strip(),
                "accuracy": format_number(accuracy_num),
                "f1": format_number(f1_num),
                "notes": row_values["notes"].strip(),
            }
        )

    return records


def audit_records(
    records: List[Dict[str, str]],
    outside_word_count: int,
    table_bbox_inferred: bool,
    mapping: Dict[str, Optional[int]],
) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    required = ["method", "dataset", "accuracy", "f1", "notes"]
    for field in required:
        if any(field not in row for row in records):
            issues.append({"category": "missing_required_column", "field": field})

    if outside_word_count:
        issues.append(
            {
                "category": "excluded_non_table_text",
                "message": "Words outside the table bounding box were excluded from metric normalization.",
                "word_count": outside_word_count,
            }
        )

    if table_bbox_inferred:
        issues.append(
            {
                "category": "ambiguous_structure",
                "message": "No explicit table bounding box was found; the table extent was inferred from word boxes.",
            }
        )

    for field, col in mapping.items():
        if col is None:
            issues.append(
                {
                    "category": "ambiguous_structure",
                    "message": f"Could not confidently map the {field!r} column; fallback extraction was used where possible.",
                    "field": field,
                }
            )

    seen_entity = {}
    for idx, row in enumerate(records):
        for field in ("method", "dataset", "notes"):
            if not str(row.get(field, "")).strip():
                issues.append({"category": "empty_required_text", "row": idx, "field": field})

        for field in ("accuracy", "f1"):
            value = parse_number(row.get(field, ""))
            if value is None:
                issues.append({"category": "non_numeric_metric", "row": idx, "field": field, "value": row.get(field, "")})
            elif value < 0 or value > 100:
                issues.append(
                    {
                        "category": "ambiguous_structure",
                        "row": idx,
                        "field": field,
                        "value": row.get(field, ""),
                        "message": "Metric value is outside the usual 0-100 range.",
                    }
                )

        key = (row.get("method", "").strip().lower(), row.get("dataset", "").strip().lower())
        if key in seen_entity:
            issues.append(
                {
                    "category": "duplicate_record",
                    "row": idx,
                    "previous_row": seen_entity[key],
                    "method": row.get("method", ""),
                    "dataset": row.get("dataset", ""),
                }
            )
        else:
            seen_entity[key] = idx

    best_by_dataset: Dict[str, Dict[str, str]] = {}
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in records:
        dataset = row.get("dataset", "").strip()
        f1 = parse_number(row.get("f1", ""))
        if dataset and f1 is not None:
            grouped.setdefault(dataset, []).append(row)

    for dataset, rows in grouped.items():
        best = max(
            rows,
            key=lambda r: (
                parse_number(r.get("f1", "")) if parse_number(r.get("f1", "")) is not None else -math.inf,
                parse_number(r.get("accuracy", "")) if parse_number(r.get("accuracy", "")) is not None else -math.inf,
                r.get("method", ""),
            ),
        )
        best_by_dataset[dataset] = {
            "method": best.get("method", ""),
            "f1": best.get("f1", ""),
            "accuracy": best.get("accuracy", ""),
            "notes": best.get("notes", ""),
        }

    return {"row_count": len(records), "best_by_dataset": best_by_dataset, "issues": issues}


def write_cells_csv(path: str, cells: List[Cell]) -> None:
    ensure_parent(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["row_id", "col_id", "row_span", "col_span", "is_header", "text"])
        writer.writeheader()
        for cell in cells:
            writer.writerow(
                {
                    "row_id": cell.row_id,
                    "col_id": cell.col_id,
                    "row_span": cell.row_span,
                    "col_span": cell.col_span,
                    "is_header": str(bool(cell.is_header)).lower(),
                    "text": cell.text,
                }
            )


def write_metrics_csv(path: str, records: List[Dict[str, str]]) -> None:
    ensure_parent(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "dataset", "accuracy", "f1", "notes"])
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in writer.fieldnames})


def write_audit_json(path: str, audit: Dict[str, Any]) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)


def write_summary(path: str, audit: Dict[str, Any]) -> None:
    ensure_parent(path)
    lines = [
        "# PubTables Metric Extraction Summary",
        "",
        f"Normalized metric rows: **{audit['row_count']}**.",
        "",
        "## Best Method by F1",
        "",
    ]

    if audit["best_by_dataset"]:
        lines.append("| Dataset | Method | F1 | Accuracy | Notes |")
        lines.append("|---|---:|---:|---:|---|")
        for dataset, best in sorted(audit["best_by_dataset"].items()):
            lines.append(
                f"| {dataset} | {best.get('method', '')} | {best.get('f1', '')} | "
                f"{best.get('accuracy', '')} | {best.get('notes', '')} |"
            )
    else:
        lines.append("No valid F1 values were available for dataset-level best-method selection.")

    lines.extend(["", "## Audit Issues", ""])

    if audit["issues"]:
        for issue in audit["issues"]:
            category = issue.get("category", "issue")
            message = issue.get("message")
            detail = message if message else json.dumps(issue, ensure_ascii=False, sort_keys=True)
            lines.append(f"- **{category}**: {detail}")
    else:
        lines.append("- No extraction or validation issues were found.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> None:
    input_path = path_for("ORIGINAL_WORDS_JSON")
    cells_csv = path_for("OUTPUT_CELLS_CSV")
    metrics_csv = path_for("OUTPUT_METRICS_CSV")
    audit_json = path_for("OUTPUT_AUDIT_JSON")
    summary_md = path_for("SUMMARY_MD")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_words = collect_words(data)
    explicit_bbox = find_table_bbox(data, all_words)
    table_bbox_inferred = False

    if explicit_bbox is None:
        table_words = all_words
        outside_words = []
        table_bbox_inferred = True
        table_bbox = (
            min(w.x0 for w in all_words),
            min(w.y0 for w in all_words),
            max(w.x1 for w in all_words),
            max(w.y1 for w in all_words),
        )
    else:
        table_bbox = explicit_bbox
        table_words = [w for w in all_words if inside_bbox(w, table_bbox)]
        outside_words = [w for w in all_words if not inside_bbox(w, table_bbox)]

    rows = cluster_rows(table_words)
    segmented = row_segments(rows)
    data_start = first_data_row(segmented)
    anchor = choose_anchor_row(segmented, data_start)
    bounds = build_column_bounds(anchor, table_bbox)
    ncols = max(1, len(bounds) - 1)

    cells = make_cells(segmented, bounds, data_start)
    mapping = map_columns(cells, ncols, data_start)
    infer_row_spans(cells, ncols, data_start, mapping)

    records = normalize_metrics(cells, data_start, mapping)
    audit = audit_records(
        records=records,
        outside_word_count=len(outside_words),
        table_bbox_inferred=table_bbox_inferred,
        mapping=mapping,
    )

    write_cells_csv(cells_csv, cells)
    write_metrics_csv(metrics_csv, records)
    write_audit_json(audit_json, audit)
    write_summary(summary_md, audit)


if __name__ == "__main__":
    main()
