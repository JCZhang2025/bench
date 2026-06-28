#!/usr/bin/env python3
import csv
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

DEFAULTS = {
    "ORIGINAL_WORDS_JSON": r"E:\research\pilot_experiments\tasks\pubtables\data\original\table_words.json",
    "OUTPUT_CELLS_CSV": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s02\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\table_cells.csv",
    "OUTPUT_METRICS_CSV": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s02\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\metrics.csv",
    "OUTPUT_AUDIT_JSON": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s02\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\audit.json",
    "SUMMARY_MD": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s02\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\summary.md",
}

REQUIRED_FIELDS = ["method", "dataset", "accuracy", "f1", "notes"]
NUM_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


def path_from_env(name):
    return Path(os.environ.get(name, DEFAULTS[name]))


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def as_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return None


def median(values, default=0.0):
    vals = [v for v in values if v is not None and math.isfinite(v)]
    return statistics.median(vals) if vals else default


def clean_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_bbox(value):
    if value is None:
        return None

    if isinstance(value, dict):
        lower = {str(k).lower(): v for k, v in value.items()}

        for key in ("bbox", "bounding_box", "box", "bounds", "rect", "rectangle"):
            if key in lower and lower[key] is not value:
                bbox = normalize_bbox(lower[key])
                if bbox:
                    return bbox

        corner_sets = [
            ("x0", "y0", "x1", "y1"),
            ("xmin", "ymin", "xmax", "ymax"),
            ("left", "top", "right", "bottom"),
            ("l", "t", "r", "b"),
        ]
        size_sets = [
            ("x", "y", "w", "h"),
            ("x", "y", "width", "height"),
            ("left", "top", "width", "height"),
        ]

        for keys in corner_sets:
            if all(k in lower for k in keys):
                nums = [as_float(lower[k]) for k in keys]
                if all(n is not None for n in nums):
                    return ordered_bbox(nums[0], nums[1], nums[2], nums[3])

        for keys in size_sets:
            if all(k in lower for k in keys):
                x, y, w, h = [as_float(lower[k]) for k in keys]
                if all(n is not None for n in (x, y, w, h)):
                    return ordered_bbox(x, y, x + w, y + h)

        return None

    if isinstance(value, (list, tuple)):
        if len(value) == 4:
            nums = [as_float(v) for v in value]
            if all(n is not None for n in nums):
                x0, y0, a, b = nums
                if a <= x0 or b <= y0:
                    return ordered_bbox(x0, y0, x0 + a, y0 + b)
                return ordered_bbox(x0, y0, a, b)

        if len(value) >= 8:
            nums = [as_float(v) for v in value]
            if all(n is not None for n in nums):
                xs = nums[0::2]
                ys = nums[1::2]
                return ordered_bbox(min(xs), min(ys), max(xs), max(ys))

    return None


def ordered_bbox(x0, y0, x1, y1):
    left, right = sorted((float(x0), float(x1)))
    top, bottom = sorted((float(y0), float(y1)))
    if right <= left or bottom <= top:
        return None
    return (left, top, right, bottom)


def bbox_area(bbox):
    if not bbox:
        return 0.0
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def union_bbox(items, pad=0.0):
    boxes = [item["bbox"] if isinstance(item, dict) else item for item in items if item]
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes) - pad,
        min(b[1] for b in boxes) - pad,
        max(b[2] for b in boxes) + pad,
        max(b[3] for b in boxes) + pad,
    )


def bbox_overlap(a, b):
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def extract_text(obj):
    if not isinstance(obj, dict):
        return None
    for key in ("text", "word", "token", "value", "content", "str"):
        if key in obj and isinstance(obj[key], (str, int, float)):
            text = clean_text(obj[key])
            if text:
                return text
    return None


def extract_bbox_from_dict(obj):
    if not isinstance(obj, dict):
        return None
    lower = {str(k).lower(): v for k, v in obj.items()}

    for key in ("bbox", "bounding_box", "box", "bounds", "rect", "rectangle"):
        if key in lower:
            bbox = normalize_bbox(lower[key])
            if bbox:
                return bbox

    return normalize_bbox(obj)


def enrich_word(text, bbox, path=""):
    x0, y0, x1, y1 = bbox
    return {
        "text": clean_text(text),
        "bbox": bbox,
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "cx": (x0 + x1) / 2.0,
        "cy": (y0 + y1) / 2.0,
        "w": x1 - x0,
        "h": y1 - y0,
        "path": path,
    }


def collect_words(obj):
    words = []

    def visit(node, path):
        if isinstance(node, dict):
            text = extract_text(node)
            bbox = extract_bbox_from_dict(node)
            if text and bbox:
                words.append(enrich_word(text, bbox, "/".join(path)))
                return
            for key, val in node.items():
                visit(val, path + [str(key)])
        elif isinstance(node, list):
            for idx, val in enumerate(node):
                visit(val, path + [str(idx)])

    visit(obj, [])
    seen = set()
    unique = []
    for word in words:
        key = (
            word["text"],
            round(word["x0"], 3),
            round(word["y0"], 3),
            round(word["x1"], 3),
            round(word["y1"], 3),
        )
        if key not in seen:
            seen.add(key)
            unique.append(word)
    return unique


def add_issue(issues, category, message, **extra):
    item = {"category": category, "message": message}
    item.update(extra)
    if item not in issues:
        issues.append(item)


def collect_table_bbox_candidates(obj):
    candidates = []

    def visit(node, path):
        if isinstance(node, dict):
            path_text = "/".join(path).lower()
            for key, val in node.items():
                lk = str(key).lower()
                table_context = "table" in path_text or "table" in lk
                bbox_key = any(term in lk for term in ("bbox", "bounding_box", "bounds", "box", "region"))
                if table_context and bbox_key:
                    bbox = normalize_bbox(val)
                    if bbox:
                        candidates.append((bbox, "/".join(path + [str(key)])))

            if "table" in path_text and not (extract_text(node) and extract_bbox_from_dict(node)):
                bbox = extract_bbox_from_dict(node)
                if bbox:
                    candidates.append((bbox, "/".join(path)))

            for key, val in node.items():
                visit(val, path + [str(key)])

        elif isinstance(node, list):
            for idx, val in enumerate(node):
                visit(val, path + [str(idx)])

    visit(obj, [])
    deduped = []
    seen = set()
    for bbox, source in candidates:
        key = tuple(round(v, 3) for v in bbox)
        if key not in seen:
            seen.add(key)
            deduped.append((bbox, source))
    return deduped


def choose_table_bbox(obj, words, issues):
    candidates = collect_table_bbox_candidates(obj)
    if candidates:
        scored = []
        for bbox, source in candidates:
            inside = sum(1 for w in words if point_in_bbox(w["cx"], w["cy"], bbox, 0.0))
            area = bbox_area(bbox)
            scored.append((inside, -area, bbox, source))
        scored.sort(reverse=True)
        if scored[0][0] > 0:
            return scored[0][2], scored[0][3]

    inferred = infer_table_bbox(words)
    add_issue(
        issues,
        "ambiguous_structure",
        "No explicit table bounding box was confidently identified; inferred the table region from dense OCR rows.",
    )
    return inferred, "inferred_dense_rows"


def point_in_bbox(x, y, bbox, pad=0.0):
    return bbox[0] - pad <= x <= bbox[2] + pad and bbox[1] - pad <= y <= bbox[3] + pad


def infer_table_bbox(words):
    if not words:
        return None

    rows = group_rows(words)
    med_h = median([w["h"] for w in words], 10.0)
    blocks = []
    current = []

    for row in rows:
        dense = len(row["words"]) >= 2
        if not dense:
            if current:
                blocks.append(current)
                current = []
            continue

        if not current:
            current = [row]
        else:
            prev = current[-1]
            if abs(row["cy"] - prev["cy"]) <= med_h * 3.5:
                current.append(row)
            else:
                blocks.append(current)
                current = [row]

    if current:
        blocks.append(current)

    if blocks:
        best = max(blocks, key=lambda b: sum(len(r["words"]) for r in b) + len(b) * 5)
        block_words = [w for r in best for w in r["words"]]
        return union_bbox(block_words, pad=med_h * 0.5)

    return union_bbox(words, pad=med_h * 0.5)


def filter_table_words(words, table_bbox, issues):
    if not table_bbox:
        return [], words

    med_h = median([w["h"] for w in words], 10.0)
    pad = med_h * 0.25
    table_words = []
    excluded = []

    for word in words:
        overlap_fraction = bbox_overlap(word["bbox"], table_bbox) / max(bbox_area(word["bbox"]), 1.0)
        if point_in_bbox(word["cx"], word["cy"], table_bbox, pad) or overlap_fraction >= 0.5:
            table_words.append(word)
        else:
            excluded.append(word)

    if excluded:
        add_issue(
            issues,
            "excluded_non_table_text",
            "OCR words outside the table bounding box were excluded from normalized metric rows.",
            "word_count",
            len(excluded),
            sample_text=clean_text(" ".join(w["text"] for w in excluded[:12])),
        )

    return table_words, excluded


def group_rows(words):
    if not words:
        return []

    tol = max(2.0, median([w["h"] for w in words], 10.0) * 0.60)
    rows = []

    for word in sorted(words, key=lambda w: (w["cy"], w["x0"])):
        if rows and abs(word["cy"] - rows[-1]["cy"]) <= tol:
            rows[-1]["words"].append(word)
            rows[-1]["cy"] = median([w["cy"] for w in rows[-1]["words"]])
        else:
            rows.append({"words": [word], "cy": word["cy"]})

    for idx, row in enumerate(rows):
        row["row_id"] = idx
        row["words"].sort(key=lambda w: (w["x0"], w["y0"]))
        row["bbox"] = union_bbox(row["words"])
        row["text"] = clean_text(" ".join(w["text"] for w in row["words"]))

    return rows


def segment_row_by_gaps(row, gap_threshold):
    words = row["words"]
    if not words:
        return []

    segments = []
    current = [words[0]]
    for prev, word in zip(words, words[1:]):
        gap = word["x0"] - prev["x1"]
        if gap > gap_threshold:
            segments.append(words_to_segment(current, row["row_id"]))
            current = [word]
        else:
            current.append(word)
    segments.append(words_to_segment(current, row["row_id"]))
    return segments


def words_to_segment(words, row_id):
    bbox = union_bbox(words)
    return {
        "row_id": row_id,
        "words": list(words),
        "text": clean_text(" ".join(w["text"] for w in sorted(words, key=lambda w: w["x0"]))),
        "bbox": bbox,
        "x0": bbox[0],
        "x1": bbox[2],
        "cx": (bbox[0] + bbox[2]) / 2.0,
    }


def cluster_positions(items, tolerance):
    clusters = []
    for item in sorted(items, key=lambda i: i["x"]):
        if clusters and abs(item["x"] - clusters[-1]["center"]) <= tolerance:
            clusters[-1]["items"].append(item)
            clusters[-1]["center"] = median([i["x"] for i in clusters[-1]["items"]])
        else:
            clusters.append({"center": item["x"], "items": [item]})

    for cluster in clusters:
        cluster["rows"] = {i["row_id"] for i in cluster["items"]}
        cluster["support"] = len(cluster["rows"])
        cluster["texts"] = [i.get("text", "") for i in cluster["items"]]
    return clusters


def choose_column_centers(rows, table_words, table_bbox, issues, col_count):
    med_h = median([w["h"] for w in table_words], 10.0)
    char_w = median([w["w"] / max(len(w["text"]), 1) for w in table_words], 5.0)
    gap_threshold = max(4.0, min(max(med_h * 0.75, char_w * 2.2), med_h * 1.4))
    start_items = []

    for row in rows:
        for seg in segment_row_by_gaps(row, gap_threshold):
            start_items.append({"x": seg["x0"], "row_id": row["row_id"], "text": seg["text"]})

    clusters = cluster_positions(start_items, tolerance=max(2.0, char_w * 1.25, med_h * 0.35))
    if not clusters:
        add_issue(issues, "ambiguous_structure", "No column anchors were identified; used evenly spaced column bands.")
        return even_column_centers(table_bbox, col_count)

    min_support = 2 if len(rows) >= 3 else 1
    valid = [c for c in clusters if c["support"] >= min_support]
    if len(valid) < col_count:
        valid = clusters

    if len(valid) < col_count:
        add_issue(
            issues,
            "ambiguous_structure",
            "Fewer repeated column anchors were found than required metric fields; used evenly spaced fallback bands.",
            found_columns=len(valid),
            required_columns=col_count,
        )
        return even_column_centers(table_bbox, col_count)

    ranked = sorted(valid, key=lambda c: (-c["support"], c["center"]))
    pool = ranked[: min(16, len(ranked))]
    for c in (sorted(valid, key=lambda c: c["center"])[:2] + sorted(valid, key=lambda c: c["center"])[-2:]):
        if c not in pool:
            pool.append(c)
    pool = sorted(pool, key=lambda c: c["center"])

    row_start_map = defaultdict(list)
    for item in start_items:
        row_start_map[item["row_id"]].append(item["x"])

    min_gap = max(med_h * 1.6, char_w * 4.0)

    def semantic_bonus(cluster):
        text = " ".join(cluster["texts"]).lower()
        bonus = 0
        for pattern in (r"\bmethod\b", r"\bmodel\b", r"\bdataset\b", r"\bacc(?:uracy)?\.?\b", r"\bf\s*-?\s*1\b", r"\bnotes?\b"):
            if re.search(pattern, text):
                bonus += 6
        return bonus

    def combo_score(combo):
        centers = [c["center"] for c in combo]
        diffs = [b - a for a, b in zip(centers, centers[1:])]
        close_penalty = sum(max(0.0, min_gap - d) for d in diffs) * 2.5
        support_score = sum(c["support"] for c in combo) * 12.0
        semantic_score = sum(semantic_bonus(c) for c in combo)
        span_score = (centers[-1] - centers[0]) * 0.03

        match_score = 0.0
        tol = max(med_h, char_w * 3.0)
        for starts in row_start_map.values():
            matched = sum(1 for center in centers if any(abs(center - s) <= tol for s in starts))
            match_score += matched

        return support_score + semantic_score + span_score + match_score - close_penalty

    best_combo = max(combinations(pool, col_count), key=combo_score)
    centers = sorted(c["center"] for c in best_combo)

    inferred_counts = Counter(len(segment_row_by_gaps(row, gap_threshold)) for row in rows)
    if inferred_counts and col_count not in inferred_counts:
        add_issue(
            issues,
            "ambiguous_structure",
            "The required metric schema was used to set column count because visual row segment counts did not clearly agree.",
            required_columns=col_count,
            observed_segment_counts=dict(sorted(inferred_counts.items())),
        )

    return centers


def even_column_centers(table_bbox, col_count):
    if not table_bbox:
        return [float(i) for i in range(col_count)]
    x0, _, x1, _ = table_bbox
    width = max(1.0, x1 - x0)
    return [x0 + width * (i + 0.5) / col_count for i in range(col_count)]


def build_column_boundaries(centers, table_bbox, table_words):
    centers = sorted(centers)
    if table_bbox:
        left = table_bbox[0]
        right = table_bbox[2]
    else:
        left = min(w["x0"] for w in table_words)
        right = max(w["x1"] for w in table_words)

    pad = median([w["w"] for w in table_words], 10.0)
    boundaries = [left - pad]
    boundaries.extend((a + b) / 2.0 for a, b in zip(centers, centers[1:]))
    boundaries.append(right + pad)
    return boundaries


def column_for_x(x, boundaries):
    for idx in range(len(boundaries) - 1):
        if boundaries[idx] <= x < boundaries[idx + 1]:
            return idx
    return max(0, min(len(boundaries) - 2, len(boundaries) - 2))


def build_preliminary_cells(rows, boundaries):
    prelim_rows = []
    col_count = len(boundaries) - 1

    for row in rows:
        by_col = defaultdict(list)
        for word in row["words"]:
            by_col[column_for_x(word["cx"], boundaries)].append(word)

        cells = []
        for col_id in range(col_count):
            words = sorted(by_col.get(col_id, []), key=lambda w: (w["x0"], w["y0"]))
            if not words:
                continue
            bbox = union_bbox(words)
            cells.append({
                "row_id": row["row_id"],
                "col_id": col_id,
                "text": clean_text(" ".join(w["text"] for w in words)),
                "bbox": bbox,
                "cx": (bbox[0] + bbox[2]) / 2.0,
            })

        prelim_rows.append({"row_id": row["row_id"], "cells": cells, "text": row["text"]})

    return prelim_rows


def parse_number(text):
    match = NUM_RE.search(str(text or "").replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except Exception:
        return None


def metric_value_string(text):
    raw = str(text or "").replace(",", "")
    match = NUM_RE.search(raw)
    return match.group(0) if match else clean_text(text)


def detect_header_rows(prelim_rows, issues):
    first_body = None
    for row in prelim_rows:
        numeric_count = sum(1 for cell in row["cells"] if parse_number(cell["text"]) is not None)
        if numeric_count >= 2:
            first_body = row["row_id"]
            break

    if first_body is None:
        keyword_rows = []
        for row in prelim_rows:
            lower = row["text"].lower()
            if any(k in lower for k in ("method", "model", "dataset", "accuracy", " acc", "f1", "notes")):
                keyword_rows.append(row["row_id"])
        first_body = (max(keyword_rows) + 1) if keyword_rows else min(1, len(prelim_rows))
        add_issue(
            issues,
            "ambiguous_structure",
            "No body row with two numeric metric values was found; header/body split used keyword fallback.",
        )

    return set(range(first_body))


def build_structural_cells(prelim_rows, header_rows, col_centers):
    cells = []
    col_count = len(col_centers)

    for row in prelim_rows:
        nonempty = row["cells"]
        is_header = row["row_id"] in header_rows

        if is_header and 0 < len(nonempty) < col_count:
            sorted_cells = sorted(nonempty, key=lambda c: c["cx"])
            for idx, cell in enumerate(sorted_cells):
                left_limit = -float("inf") if idx == 0 else (sorted_cells[idx - 1]["cx"] + cell["cx"]) / 2.0
                right_limit = float("inf") if idx == len(sorted_cells) - 1 else (cell["cx"] + sorted_cells[idx + 1]["cx"]) / 2.0
                covered = [i for i, center in enumerate(col_centers) if left_limit <= center < right_limit]
                if not covered:
                    nearest = min(range(col_count), key=lambda i: abs(col_centers[i] - cell["cx"]))
                    covered = [nearest]
                col_id = min(covered)
                col_span = max(covered) - min(covered) + 1
                cells.append(make_struct_cell(cell, col_id, col_span, is_header))
        else:
            for cell in nonempty:
                cells.append(make_struct_cell(cell, cell["col_id"], 1, is_header))

    cells.sort(key=lambda c: (c["row_id"], c["col_id"], c["text"]))
    return cells


def make_struct_cell(cell, col_id, col_span, is_header):
    return {
        "row_id": cell["row_id"],
        "col_id": col_id,
        "row_span": 1,
        "col_span": col_span,
        "is_header": bool(is_header),
        "text": cell["text"],
    }


def keyword_score(text, field):
    text = " " + re.sub(r"[^a-z0-9]+", " ", str(text).lower()) + " "
    patterns = {
        "method": [r"\bmethod\b", r"\bmodel\b", r"\bapproach\b", r"\bsystem\b", r"\balgorithm\b", r"\bclassifier\b"],
        "dataset": [r"\bdataset\b", r"\bdata set\b", r"\bcorpus\b", r"\bbenchmark\b", r"\btask\b"],
        "accuracy": [r"\baccuracy\b", r"\bacc\b"],
        "f1": [r"\bf1\b", r"\bf 1\b", r"\bf score\b", r"\bfscore\b"],
        "notes": [r"\bnotes?\b", r"\bcomments?\b", r"\bremarks?\b", r"\bdetails?\b"],
    }
    return sum(1 for pat in patterns[field] if re.search(pat, text))


def map_headers_to_fields(struct_cells, header_rows, col_count, issues):
    header_text_by_col = [""] * col_count
    for cell in struct_cells:
        if cell["row_id"] not in header_rows:
            continue
        for col in range(cell["col_id"], min(col_count, cell["col_id"] + cell["col_span"])):
            header_text_by_col[col] = clean_text(header_text_by_col[col] + " " + cell["text"])

    candidates = []
    for field in REQUIRED_FIELDS:
        for col, text in enumerate(header_text_by_col):
            score = keyword_score(text, field)
            if score:
                candidates.append((score, -abs(REQUIRED_FIELDS.index(field) - col), field, col))

    field_to_col = {}
    used_cols = set()
    for _, _, field, col in sorted(candidates, reverse=True):
        if field not in field_to_col and col not in used_cols:
            field_to_col[field] = col
            used_cols.add(col)

    fallback_fields = []
    for idx, field in enumerate(REQUIRED_FIELDS):
        if field in field_to_col:
            continue
        unused = [col for col in range(col_count) if col not in used_cols]
        if not unused:
            fallback_col = min(idx, col_count - 1)
        else:
            fallback_col = min(unused, key=lambda col: abs(col - idx))
        field_to_col[field] = fallback_col
        used_cols.add(fallback_col)
        fallback_fields.append(field)

    if fallback_fields:
        add_issue(
            issues,
            "ambiguous_structure",
            "Some metric fields were mapped by ordinal fallback because header text was incomplete or ambiguous.",
            fields=fallback_fields,
        )

    return field_to_col


def normalize_metrics(prelim_rows, header_rows, field_to_col, struct_cells, issues):
    col_to_field = {col: field for field, col in field_to_col.items()}
    struct_lookup = {(cell["row_id"], cell["col_id"]): cell for cell in struct_cells}
    last_text = {}
    last_struct_cell = {}
    carried_fields = set()
    metrics = []

    for row in prelim_rows:
        row_id = row["row_id"]
        if row_id in header_rows:
            continue

        values = {field: "" for field in REQUIRED_FIELDS}
        direct = set()

        for cell in row["cells"]:
            field = col_to_field.get(cell["col_id"])
            if not field:
                continue
            values[field] = clean_text((values[field] + " " + cell["text"]).strip())
            if cell["text"].strip():
                direct.add(field)

        has_metric_value = parse_number(values["accuracy"]) is not None or parse_number(values["f1"]) is not None
        if not has_metric_value:
            continue

        for field in ("method", "dataset"):
            if values[field].strip():
                last_text[field] = values[field].strip()
                direct_col = field_to_col.get(field)
                if direct_col is not None and (row_id, direct_col) in struct_lookup:
                    last_struct_cell[field] = struct_lookup[(row_id, direct_col)]
            elif last_text.get(field):
                values[field] = last_text[field]
                prev = last_struct_cell.get(field)
                if prev:
                    prev["row_span"] = max(prev["row_span"], row_id - prev["row_id"] + 1)
                if field not in carried_fields:
                    add_issue(
                        issues,
                        "ambiguous_structure",
                        "A blank text field in a metric row was filled from the preceding row as an apparent row span.",
                        field=field,
                    )
                    carried_fields.add(field)

        metrics.append({
            "method": clean_text(values["method"]),
            "dataset": clean_text(values["dataset"]),
            "accuracy": metric_value_string(values["accuracy"]),
            "f1": metric_value_string(values["f1"]),
            "notes": clean_text(values["notes"]),
        })

    return metrics


def audit_metrics(metrics, issues):
    for idx, row in enumerate(metrics, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                add_issue(issues, "missing_required_column", "A normalized metric row is missing a required field.", row_index=idx, field=field)

        for field in ("method", "dataset"):
            if not clean_text(row.get(field, "")):
                add_issue(issues, "empty_required_text", "A required text field is empty.", row_index=idx, field=field)

        for field in ("accuracy", "f1"):
            if parse_number(row.get(field, "")) is None:
                add_issue(issues, "non_numeric_metric", "A metric field could not be parsed as numeric.", row_index=idx, field=field, value=row.get(field, ""))

    seen = {}
    for idx, row in enumerate(metrics, start=1):
        key = (clean_text(row.get("method", "")).lower(), clean_text(row.get("dataset", "")).lower())
        if key in seen:
            add_issue(
                issues,
                "duplicate_record",
                "Duplicate method and dataset record found.",
                first_row_index=seen[key],
                row_index=idx,
                method=row.get("method", ""),
                dataset=row.get("dataset", ""),
            )
        else:
            seen[key] = idx

    groups = defaultdict(list)
    for idx, row in enumerate(metrics, start=1):
        dataset = clean_text(row.get("dataset", ""))
        f1 = parse_number(row.get("f1", ""))
        if dataset and f1 is not None:
            groups[dataset].append((f1, idx, row))

    best_by_dataset = {}
    for dataset in sorted(groups):
        rows = groups[dataset]
        best_f1 = max(item[0] for item in rows)
        tied = [item for item in rows if item[0] == best_f1]
        best = sorted(tied, key=lambda item: (item[2].get("method", ""), item[1]))[0]
        best_by_dataset[dataset] = {
            "method": best[2].get("method", ""),
            "f1": best[2].get("f1", ""),
            "row_index": best[1],
        }
        if len(tied) > 1:
            add_issue(
                issues,
                "inconsistent_group_best",
                "Multiple methods tie for best F1 in a dataset.",
                dataset=dataset,
                f1=best[2].get("f1", ""),
                methods=sorted({item[2].get("method", "") for item in tied}),
            )

    datasets_with_no_best = sorted({
        clean_text(row.get("dataset", ""))
        for row in metrics
        if clean_text(row.get("dataset", "")) and clean_text(row.get("dataset", "")) not in best_by_dataset
    })
    for dataset in datasets_with_no_best:
        add_issue(
            issues,
            "inconsistent_group_best",
            "No parseable F1 value was available for this dataset.",
            dataset=dataset,
        )

    return {
        "row_count": len(metrics),
        "best_by_dataset": best_by_dataset,
        "issues": issues,
    }


def write_cells_csv(path, cells):
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["row_id", "col_id", "row_span", "col_span", "is_header", "text"])
        writer.writeheader()
        for cell in cells:
            writer.writerow({
                "row_id": cell["row_id"],
                "col_id": cell["col_id"],
                "row_span": cell["row_span"],
                "col_span": cell["col_span"],
                "is_header": "true" if cell["is_header"] else "false",
                "text": cell["text"],
            })


def write_metrics_csv(path, metrics):
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        for row in metrics:
            writer.writerow({field: row.get(field, "") for field in REQUIRED_FIELDS})


def write_audit_json(path, audit):
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(audit, fh, indent=2, ensure_ascii=False)


def write_summary(path, audit):
    ensure_parent(path)
    lines = [
        "# Metric Extraction Summary",
        "",
        f"- Normalized metric rows: {audit['row_count']}.",
    ]

    if audit["best_by_dataset"]:
        lines.append("- Best F1 by dataset:")
        for dataset, best in sorted(audit["best_by_dataset"].items()):
            lines.append(f"  - {dataset}: {best['method']} with F1 {best['f1']}.")
    else:
        lines.append("- Best F1 by dataset: none computed.")

    if audit["issues"]:
        counts = Counter(issue["category"] for issue in audit["issues"])
        issue_text = ", ".join(f"{category}: {counts[category]}" for category in sorted(counts))
        lines.append(f"- Audit issues reported: {len(audit['issues'])} ({issue_text}).")
    else:
        lines.append("- Audit issues reported: 0.")

    with path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    input_path = path_from_env("ORIGINAL_WORDS_JSON")
    cells_path = path_from_env("OUTPUT_CELLS_CSV")
    metrics_path = path_from_env("OUTPUT_METRICS_CSV")
    audit_path = path_from_env("OUTPUT_AUDIT_JSON")
    summary_path = path_from_env("SUMMARY_MD")

    issues = []

    with input_path.open("r", encoding="utf-8") as fh:
        source = json.load(fh)

    words = collect_words(source)
    if not words:
        add_issue(issues, "ambiguous_structure", "No OCR words with text and bounding boxes were found.")
        metrics = []
        cells = []
        audit = audit_metrics(metrics, issues)
        write_cells_csv(cells_path, cells)
        write_metrics_csv(metrics_path, metrics)
        write_audit_json(audit_path, audit)
        write_summary(summary_path, audit)
        return

    table_bbox, _ = choose_table_bbox(source, words, issues)
    table_words, _ = filter_table_words(words, table_bbox, issues)

    if not table_words:
        add_issue(issues, "ambiguous_structure", "No OCR words fell inside the selected table region.")
        metrics = []
        cells = []
        audit = audit_metrics(metrics, issues)
        write_cells_csv(cells_path, cells)
        write_metrics_csv(metrics_path, metrics)
        write_audit_json(audit_path, audit)
        write_summary(summary_path, audit)
        return

    rows = group_rows(table_words)
    col_count = len(REQUIRED_FIELDS)
    col_centers = choose_column_centers(rows, table_words, table_bbox, issues, col_count)
    boundaries = build_column_boundaries(col_centers, table_bbox, table_words)
    prelim_rows = build_preliminary_cells(rows, boundaries)
    header_rows = detect_header_rows(prelim_rows, issues)
    cells = build_structural_cells(prelim_rows, header_rows, col_centers)
    field_to_col = map_headers_to_fields(cells, header_rows, col_count, issues)
    metrics = normalize_metrics(prelim_rows, header_rows, field_to_col, cells, issues)
    audit = audit_metrics(metrics, issues)

    write_cells_csv(cells_path, cells)
    write_metrics_csv(metrics_path, metrics)
    write_audit_json(audit_path, audit)
    write_summary(summary_path, audit)


if __name__ == "__main__":
    main()
