#!/usr/bin/env python3
"""
Reconstruct a PubTables-style OCR table from word boxes, normalize metric rows,
audit the extracted values, and write the required artifacts.

Required environment variables:
  ORIGINAL_WORDS_JSON
  OUTPUT_CELLS_CSV
  OUTPUT_METRICS_CSV
  OUTPUT_AUDIT_JSON
  SUMMARY_MD
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class Word:
    text: str
    bbox: Tuple[float, float, float, float]
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class Row:
    words: List[Word]
    y_center: float


@dataclass
class ColBand:
    left: float
    right: float
    center: float


@dataclass
class Cell:
    row_id: int
    col_id: int
    row_span: int
    col_span: int
    is_header: bool
    text: str
    bbox: Tuple[float, float, float, float]


def as_bbox(value: Any) -> Optional[Tuple[float, float, float, float]]:
    """Return bbox as x1,y1,x2,y2 from common OCR bbox encodings."""
    if value is None:
        return None

    if isinstance(value, dict):
        keys_xyxy = ("x1", "y1", "x2", "y2")
        keys_ltrb = ("left", "top", "right", "bottom")
        keys_xywh = ("x", "y", "w", "h")
        keys_width_height = ("x", "y", "width", "height")

        if all(k in value for k in keys_xyxy):
            return tuple(float(value[k]) for k in keys_xyxy)  # type: ignore[return-value]
        if all(k in value for k in keys_ltrb):
            return tuple(float(value[k]) for k in keys_ltrb)  # type: ignore[return-value]
        if all(k in value for k in keys_xywh):
            x, y, w, h = (float(value[k]) for k in keys_xywh)
            return (x, y, x + w, y + h)
        if all(k in value for k in keys_width_height):
            x = float(value["x"])
            y = float(value["y"])
            return (x, y, x + float(value["width"]), y + float(value["height"]))

    if isinstance(value, (list, tuple)) and len(value) == 4:
        vals = tuple(float(v) for v in value)
        x0, y0, a, b = vals
        if a > x0 and b > y0:
            return vals
        return (x0, y0, x0 + a, y0 + b)

    if isinstance(value, (list, tuple)) and len(value) == 8:
        xs = [float(value[i]) for i in range(0, 8, 2)]
        ys = [float(value[i]) for i in range(1, 8, 2)]
        return (min(xs), min(ys), max(xs), max(ys))

    return None


def bbox_area(b: Tuple[float, float, float, float]) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def bbox_union(boxes: Sequence[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def bbox_overlap(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return bbox_area((x1, y1, x2, y2))


def center_inside(bbox: Tuple[float, float, float, float], region: Tuple[float, float, float, float]) -> bool:
    x = (bbox[0] + bbox[2]) / 2.0
    y = (bbox[1] + bbox[3]) / 2.0
    return region[0] <= x <= region[2] and region[1] <= y <= region[3]


def walk_json(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk_json(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_json(value)


def find_text(item: Dict[str, Any]) -> Optional[str]:
    for key in ("text", "word", "token", "value", "content", "ocr_text"):
        if key in item and item[key] is not None:
            text = str(item[key]).strip()
            if text:
                return text
    return None


def find_bbox_in_item(item: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
    for key in ("bbox", "box", "bounds", "bounding_box", "rect"):
        if key in item:
            bbox = as_bbox(item[key])
            if bbox:
                return bbox

    bbox = as_bbox(item)
    if bbox:
        return bbox

    return None


def extract_words(data: Any) -> List[Word]:
    words: List[Word] = []

    for item in walk_json(data):
        if not isinstance(item, dict):
            continue

        text = find_text(item)
        bbox = find_bbox_in_item(item)
        if not text or not bbox:
            continue

        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            continue

        words.append(
            Word(
                text=text,
                bbox=bbox,
                x_center=(bbox[0] + bbox[2]) / 2.0,
                y_center=(bbox[1] + bbox[3]) / 2.0,
                width=bbox[2] - bbox[0],
                height=bbox[3] - bbox[1],
            )
        )

    # De-duplicate records that appear through nested schema traversal.
    seen = set()
    unique: List[Word] = []
    for word in words:
        key = (word.text, tuple(round(v, 3) for v in word.bbox))
        if key not in seen:
            unique.append(word)
            seen.add(key)

    return unique


def extract_table_bbox(data: Any, words: Sequence[Word]) -> Tuple[Optional[Tuple[float, float, float, float]], List[str]]:
    issues: List[str] = []
    candidates: List[Tuple[str, Tuple[float, float, float, float]]] = []

    tableish_keys = {
        "table_bbox",
        "table_box",
        "table_bounds",
        "table_bounding_box",
        "table_region",
        "table",
        "tables",
    }

    def collect_named(obj: Any, parent_key: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_l = str(key).lower()
                if key_l in tableish_keys or ("table" in key_l and any(s in key_l for s in ("bbox", "box", "bound", "region"))):
                    bbox = as_bbox(value)
                    if bbox:
                        candidates.append((key_l, bbox))
                    elif isinstance(value, dict):
                        inner = find_bbox_in_item(value)
                        if inner:
                            candidates.append((key_l, inner))
                    elif isinstance(value, list):
                        for elem in value:
                            if isinstance(elem, dict):
                                inner = find_bbox_in_item(elem)
                                if inner:
                                    candidates.append((key_l, inner))
                collect_named(value, key_l)
        elif isinstance(obj, list):
            for value in obj:
                collect_named(value, parent_key)

    collect_named(data)

    valid = [b for _, b in candidates if b[2] > b[0] and b[3] > b[1]]
    if valid:
        # Prefer the candidate that contains the most OCR words while excluding outside prose.
        scored = []
        for bbox in valid:
            count = sum(1 for w in words if center_inside(w.bbox, bbox) or bbox_overlap(w.bbox, bbox) / max(bbox_area(w.bbox), 1.0) >= 0.6)
            area = bbox_area(bbox)
            scored.append((count, -area, bbox))
        scored.sort(reverse=True)
        return scored[0][2], issues

    if words:
        issues.append("missing_table_bbox: no explicit table bounding box found; using all OCR words")
        return bbox_union([w.bbox for w in words]), issues

    issues.append("missing_table_bbox: no explicit table bounding box found and no OCR words were available")
    return None, issues


def filter_table_words(words: Sequence[Word], table_bbox: Optional[Tuple[float, float, float, float]]) -> Tuple[List[Word], int, List[str]]:
    if not table_bbox:
        return list(words), 0, ["ambiguous_structure: table bbox unavailable; no geometry-based noise exclusion possible"]

    kept: List[Word] = []
    excluded = 0
    border_kept = 0

    for word in words:
        overlap_ratio = bbox_overlap(word.bbox, table_bbox) / max(bbox_area(word.bbox), 1.0)
        if center_inside(word.bbox, table_bbox):
            kept.append(word)
        elif overlap_ratio >= 0.6:
            kept.append(word)
            border_kept += 1
        else:
            excluded += 1

    issues: List[str] = []
    if excluded:
        issues.append(f"excluded_non_table_text: {excluded} OCR words outside the table bounding box were excluded")
    if border_kept:
        issues.append(f"ambiguous_structure: {border_kept} border-overlap words were kept because overlap ratio was at least 0.60")

    return kept, excluded, issues


def group_rows(words: Sequence[Word]) -> List[Row]:
    if not words:
        return []

    heights = [w.height for w in words if w.height > 0]
    median_height = statistics.median(heights) if heights else 8.0
    tolerance = max(2.0, median_height * 0.65)

    rows: List[Row] = []
    for word in sorted(words, key=lambda w: (w.y_center, w.x_center)):
        placed = False
        for row in rows:
            if abs(word.y_center - row.y_center) <= tolerance:
                row.words.append(word)
                row.y_center = statistics.mean(w.y_center for w in row.words)
                placed = True
                break
        if not placed:
            rows.append(Row(words=[word], y_center=word.y_center))

    rows.sort(key=lambda r: r.y_center)
    for row in rows:
        row.words.sort(key=lambda w: w.x_center)

    return rows


def infer_columns(rows: Sequence[Row]) -> List[ColBand]:
    if not rows:
        return []

    tokens = [w for row in rows for w in row.words]
    widths = [w.width for w in tokens if w.width > 0]
    median_width = statistics.median(widths) if widths else 20.0

    # Use row-internal word gaps to infer column breaks. This preserves multi-word cells.
    gaps: List[float] = []
    for row in rows:
        ws = sorted(row.words, key=lambda w: w.bbox[0])
        for left, right in zip(ws, ws[1:]):
            gap = right.bbox[0] - left.bbox[2]
            if gap > 0:
                gaps.append(gap)

    if gaps:
        median_gap = statistics.median(gaps)
        large_gaps = [g for g in gaps if g > max(median_gap * 1.8, median_width * 0.9)]
        threshold = max(median_width * 1.25, statistics.median(large_gaps) * 0.55 if large_gaps else median_gap * 2.2)
    else:
        threshold = median_width * 1.75

    break_positions: List[float] = []
    for row in rows:
        ws = sorted(row.words, key=lambda w: w.bbox[0])
        for left, right in zip(ws, ws[1:]):
            gap = right.bbox[0] - left.bbox[2]
            if gap >= threshold:
                break_positions.append((left.bbox[2] + right.bbox[0]) / 2.0)

    if not break_positions:
        x1 = min(w.bbox[0] for w in tokens)
        x2 = max(w.bbox[2] for w in tokens)
        return [ColBand(left=x1, right=x2, center=(x1 + x2) / 2.0)]

    break_positions.sort()
    cluster_tol = max(median_width, threshold * 0.35)
    clusters: List[List[float]] = []
    for pos in break_positions:
        if not clusters or abs(pos - statistics.mean(clusters[-1])) > cluster_tol:
            clusters.append([pos])
        else:
            clusters[-1].append(pos)

    breaks = [statistics.median(cluster) for cluster in clusters]
    table_left = min(w.bbox[0] for w in tokens)
    table_right = max(w.bbox[2] for w in tokens)

    edges = [table_left] + breaks + [table_right]
    bands: List[ColBand] = []
    for left, right in zip(edges, edges[1:]):
        if right > left:
            bands.append(ColBand(left=left, right=right, center=(left + right) / 2.0))

    return bands


def column_for_word(word: Word, bands: Sequence[ColBand]) -> int:
    if not bands:
        return 0

    best_idx = 0
    best_overlap = -1.0
    for idx, band in enumerate(bands):
        overlap = max(0.0, min(word.bbox[2], band.right) - max(word.bbox[0], band.left))
        if band.left <= word.x_center <= band.right:
            overlap += word.width
        if overlap > best_overlap:
            best_idx = idx
            best_overlap = overlap

    return best_idx


def join_tokens(words: Sequence[Word]) -> str:
    parts: List[str] = []
    no_space_before = set(".,;:%)]}")
    no_space_after = set("([{")

    for word in sorted(words, key=lambda w: w.bbox[0]):
        token = word.text.strip()
        if not token:
            continue
        if not parts:
            parts.append(token)
        elif token in no_space_before or token.startswith("%"):
            parts[-1] = parts[-1] + token
        elif parts[-1] and parts[-1][-1] in no_space_after:
            parts[-1] = parts[-1] + token
        else:
            parts.append(token)

    return " ".join(parts).strip()


def build_cells(rows: Sequence[Row], bands: Sequence[ColBand]) -> List[Cell]:
    cells: List[Cell] = []

    for row_idx, row in enumerate(rows):
        buckets: Dict[int, List[Word]] = {}
        for word in row.words:
            col_idx = column_for_word(word, bands)
            buckets.setdefault(col_idx, []).append(word)

        for col_idx in sorted(buckets):
            ws = buckets[col_idx]
            text = join_tokens(ws)
            if not text:
                continue

            cell_bbox = bbox_union([w.bbox for w in ws])

            # Conservative col span: only span multiple columns if the OCR cell text visually covers them.
            covered = [
                idx for idx, band in enumerate(bands)
                if max(0.0, min(cell_bbox[2], band.right) - max(cell_bbox[0], band.left)) >= (band.right - band.left) * 0.45
            ]
            if covered:
                col_id = min(covered)
                col_span = max(covered) - min(covered) + 1
            else:
                col_id = col_idx
                col_span = 1

            cells.append(
                Cell(
                    row_id=row_idx,
                    col_id=col_id,
                    row_span=1,
                    col_span=max(1, col_span),
                    is_header=False,
                    text=text,
                    bbox=cell_bbox,
                )
            )

    return cells


def parse_number(text: str) -> Optional[float]:
    if text is None:
        return None

    s = str(text).strip()
    if not s or s in {"-", "–", "—", "NA", "N/A", "n/a"}:
        return None

    s = s.replace(",", "")
    s = re.sub(r"^[^\d+\-.]+", "", s)
    s = re.sub(r"[^\d.%+\-]+$", "", s)
    s = s.replace("%", "")

    match = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def is_numeric_like(text: str) -> bool:
    return parse_number(text) is not None


def detect_header_rows(cells: Sequence[Cell], num_rows: int) -> Tuple[int, List[str]]:
    issues: List[str] = []
    if num_rows == 0:
        return 0, issues

    by_row: Dict[int, List[Cell]] = {}
    for cell in cells:
        by_row.setdefault(cell.row_id, []).append(cell)

    header_count = 0
    seen_body = False
    for row_id in range(num_rows):
        row_cells = by_row.get(row_id, [])
        if not row_cells:
            continue

        texts = [c.text for c in row_cells]
        numeric_ratio = sum(1 for t in texts if is_numeric_like(t)) / max(len(texts), 1)
        joined = " ".join(texts).lower()
        has_metric_header = bool(re.search(r"\b(method|dataset|accuracy|acc|f1|score|note|notes)\b", joined))

        if not seen_body and (has_metric_header or numeric_ratio < 0.5):
            header_count += 1
        else:
            seen_body = True

    if header_count == 0 and num_rows > 1:
        header_count = 1
        issues.append("ambiguous_structure: no clear header band detected; first row treated as header")

    for cell in cells:
        cell.is_header = cell.row_id < header_count

    # Infer simple vertical row spans for header side cells missing from lower header bands.
    header_by_row: Dict[int, List[Cell]] = {}
    for cell in cells:
        if cell.is_header:
            header_by_row.setdefault(cell.row_id, []).append(cell)

    for cell in cells:
        if not cell.is_header:
            continue
        span = 1
        for next_row in range(cell.row_id + 1, header_count):
            lower_same_col = [
                c for c in header_by_row.get(next_row, [])
                if c.col_id <= cell.col_id < c.col_id + c.col_span
            ]
            if lower_same_col:
                break
            span += 1
        cell.row_span = span

    return header_count, issues


def header_map(cells: Sequence[Cell]) -> Dict[int, str]:
    headers: Dict[int, List[str]] = {}
    for cell in cells:
        if not cell.is_header:
            continue
        for col in range(cell.col_id, cell.col_id + cell.col_span):
            headers.setdefault(col, []).append(cell.text)

    return {col: " ".join(parts).strip().lower() for col, parts in headers.items()}


def canonical_column_roles(headers: Dict[int, str], max_col: int) -> Dict[str, Optional[int]]:
    roles: Dict[str, Optional[int]] = {
        "method": None,
        "dataset": None,
        "accuracy": None,
        "f1": None,
        "notes": None,
    }

    patterns = {
        "method": r"\b(method|model|approach|system|algorithm)\b",
        "dataset": r"\b(dataset|data set|corpus|benchmark|split)\b",
        "accuracy": r"\b(accuracy|acc\.?|top[- ]?1)\b",
        "f1": r"\b(f1|f[- ]?measure|f[- ]?score)\b",
        "notes": r"\b(notes?|remark|comment|setting|variant)\b",
    }

    for role, pattern in patterns.items():
        for col, text in headers.items():
            if re.search(pattern, text, flags=re.I):
                roles[role] = col
                break

    # Positional fallback for the requested metric schema.
    ordered_cols = list(range(max_col + 1))
    fallback = {
        "method": 0,
        "dataset": 1,
        "accuracy": 2,
        "f1": 3,
        "notes": 4,
    }
    for role, idx in fallback.items():
        if roles[role] is None and idx < len(ordered_cols):
            roles[role] = ordered_cols[idx]

    return roles


def normalize_metrics(cells: Sequence[Cell]) -> Tuple[List[Dict[str, str]], List[str]]:
    issues: List[str] = []
    if not cells:
        return [], ["ambiguous_structure: no reconstructed cells available for metric normalization"]

    max_col = max(c.col_id + c.col_span - 1 for c in cells)
    headers = header_map(cells)
    roles = canonical_column_roles(headers, max_col)

    missing_roles = [role for role, col in roles.items() if col is None]
    for role in missing_roles:
        issues.append(f"missing_required_column: could not map required field '{role}' to a reconstructed column")

    by_row: Dict[int, List[Cell]] = {}
    for cell in cells:
        if not cell.is_header:
            by_row.setdefault(cell.row_id, []).append(cell)

    metric_rows: List[Dict[str, str]] = []
    for row_id in sorted(by_row):
        row_cells = by_row[row_id]
        by_col: Dict[int, str] = {}
        for cell in row_cells:
            for col in range(cell.col_id, cell.col_id + cell.col_span):
                by_col[col] = cell.text

        row = {
            "method": by_col.get(roles["method"], "").strip() if roles["method"] is not None else "",
            "dataset": by_col.get(roles["dataset"], "").strip() if roles["dataset"] is not None else "",
            "accuracy": by_col.get(roles["accuracy"], "").strip() if roles["accuracy"] is not None else "",
            "f1": by_col.get(roles["f1"], "").strip() if roles["f1"] is not None else "",
            "notes": by_col.get(roles["notes"], "").strip() if roles["notes"] is not None else "",
        }

        if not any(row.values()):
            continue

        metric_rows.append(row)

    for idx, row in enumerate(metric_rows, start=1):
        if not row["method"]:
            issues.append(f"empty_required_text: row {idx} has empty method")
        if not row["dataset"]:
            issues.append(f"empty_required_text: row {idx} has empty dataset")
        if parse_number(row["accuracy"]) is None:
            issues.append(f"non_numeric_metric: row {idx} accuracy value '{row['accuracy']}' is not numeric")
        if parse_number(row["f1"]) is None:
            issues.append(f"non_numeric_metric: row {idx} f1 value '{row['f1']}' is not numeric")

    seen = set()
    for idx, row in enumerate(metric_rows, start=1):
        key = (row["method"], row["dataset"])
        if key in seen:
            issues.append(f"duplicate_record: duplicate method/dataset record at normalized row {idx}: {key[0]} / {key[1]}")
        seen.add(key)

    return metric_rows, issues


def compute_best_by_dataset(metric_rows: Sequence[Dict[str, str]]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    best: Dict[str, Dict[str, Any]] = {}
    issues: List[str] = []

    for row in metric_rows:
        dataset = row.get("dataset", "").strip()
        method = row.get("method", "").strip()
        f1 = parse_number(row.get("f1", ""))

        if not dataset or not method or f1 is None:
            continue

        if dataset not in best or f1 > best[dataset]["f1"]:
            best[dataset] = {
                "method": method,
                "f1": f1,
            }
        elif math.isclose(f1, best[dataset]["f1"]):
            current = best[dataset].setdefault("tied_methods", [best[dataset]["method"]])
            if method not in current:
                current.append(method)
            issues.append(f"inconsistent_group_best: dataset '{dataset}' has a tied best F1 score of {f1}")

    return best, issues


def write_cells_csv(path: Path, cells: Sequence[Cell]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["row_id", "col_id", "row_span", "col_span", "is_header", "text"],
        )
        writer.writeheader()
        for cell in sorted(cells, key=lambda c: (c.row_id, c.col_id)):
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


def write_metrics_csv(path: Path, metric_rows: Sequence[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["method", "dataset", "accuracy", "f1", "notes"],
        )
        writer.writeheader()
        for row in metric_rows:
            writer.writerow(
                {
                    "method": row.get("method", ""),
                    "dataset": row.get("dataset", ""),
                    "accuracy": row.get("accuracy", ""),
                    "f1": row.get("f1", ""),
                    "notes": row.get("notes", ""),
                }
            )


def write_audit_json(path: Path, row_count: int, best_by_dataset: Dict[str, Dict[str, Any]], issues: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "row_count": row_count,
        "best_by_dataset": best_by_dataset,
        "issues": list(issues),
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_summary_md(path: Path, metric_rows: Sequence[Dict[str, str]], best_by_dataset: Dict[str, Dict[str, Any]], issues: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# OCR Table Extraction Summary",
        "",
        f"- Normalized metric rows: {len(metric_rows)}.",
    ]

    if best_by_dataset:
        lines.append("- Best method by F1 for each dataset:")
        for dataset in sorted(best_by_dataset):
            best = best_by_dataset[dataset]
            if "tied_methods" in best:
                methods = ", ".join(best["tied_methods"])
                lines.append(f"  - {dataset}: {methods} tied at F1 {best['f1']}.")
            else:
                lines.append(f"  - {dataset}: {best['method']} with F1 {best['f1']}.")
    else:
        lines.append("- Best method by F1 could not be computed from the normalized rows.")

    if issues:
        lines.append("- Audit issues:")
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("- Audit issues: none found.")

    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def require_env(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return Path(value)


def main() -> None:
    input_json = require_env("ORIGINAL_WORDS_JSON")
    output_cells_csv = require_env("OUTPUT_CELLS_CSV")
    output_metrics_csv = require_env("OUTPUT_METRICS_CSV")
    output_audit_json = require_env("OUTPUT_AUDIT_JSON")
    summary_md = require_env("SUMMARY_MD")

    with input_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    issues: List[str] = []

    all_words = extract_words(data)
    table_bbox, bbox_issues = extract_table_bbox(data, all_words)
    issues.extend(bbox_issues)

    table_words, _, filter_issues = filter_table_words(all_words, table_bbox)
    issues.extend(filter_issues)

    rows = group_rows(table_words)
    columns = infer_columns(rows)
    cells = build_cells(rows, columns)

    _, header_issues = detect_header_rows(cells, len(rows))
    issues.extend(header_issues)

    metric_rows, metric_issues = normalize_metrics(cells)
    issues.extend(metric_issues)

    best_by_dataset, best_issues = compute_best_by_dataset(metric_rows)
    issues.extend(best_issues)

    # Preserve issue order while removing exact duplicates.
    deduped_issues = list(dict.fromkeys(issues))

    write_cells_csv(output_cells_csv, cells)
    write_metrics_csv(output_metrics_csv, metric_rows)
    write_audit_json(output_audit_json, len(metric_rows), best_by_dataset, deduped_issues)
    write_summary_md(summary_md, metric_rows, best_by_dataset, deduped_issues)


if __name__ == "__main__":
    main()
