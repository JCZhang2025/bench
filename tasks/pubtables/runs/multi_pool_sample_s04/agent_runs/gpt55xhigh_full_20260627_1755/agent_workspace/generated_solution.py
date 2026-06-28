#!/usr/bin/env python3
import csv
import json
import math
import os
import re
from collections import defaultdict


REQUIRED_ENV = [
    "ORIGINAL_WORDS_JSON",
    "OUTPUT_CELLS_CSV",
    "OUTPUT_METRICS_CSV",
    "OUTPUT_AUDIT_JSON",
    "SUMMARY_MD",
]

REQUIRED_METRIC_FIELDS = ["method", "dataset", "accuracy", "f1", "notes"]


def as_bbox(value):
    if value is None:
        return None
    if isinstance(value, dict):
        keys = {k.lower(): k for k in value.keys()}
        if all(k in keys for k in ("x0", "y0", "x1", "y1")):
            return [
                float(value[keys["x0"]]),
                float(value[keys["y0"]]),
                float(value[keys["x1"]]),
                float(value[keys["y1"]]),
            ]
        if all(k in keys for k in ("left", "top", "right", "bottom")):
            return [
                float(value[keys["left"]]),
                float(value[keys["top"]]),
                float(value[keys["right"]]),
                float(value[keys["bottom"]]),
            ]
        if all(k in keys for k in ("x", "y", "w", "h")):
            x = float(value[keys["x"]])
            y = float(value[keys["y"]])
            w = float(value[keys["w"]])
            h = float(value[keys["h"]])
            return [x, y, x + w, y + h]
        if all(k in keys for k in ("x", "y", "width", "height")):
            x = float(value[keys["x"]])
            y = float(value[keys["y"]])
            w = float(value[keys["width"]])
            h = float(value[keys["height"]])
            return [x, y, x + w, y + h]
    if isinstance(value, (list, tuple)) and len(value) >= 4:
        vals = [float(v) for v in value[:4]]
        x0, y0, x1, y1 = vals
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        return [x0, y0, x1, y1]
    return None


def get_text(item):
    for key in ("text", "word", "token", "value", "content"):
        if key in item and item[key] is not None:
            return str(item[key])
    return ""


def find_words(obj):
    if isinstance(obj, dict):
        for key in ("words", "page_words", "tokens", "ocr_words"):
            if isinstance(obj.get(key), list):
                return obj[key]
        for value in obj.values():
            found = find_words(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        if obj and all(isinstance(x, dict) and get_text(x) for x in obj[: min(3, len(obj))]):
            return obj
        for value in obj:
            found = find_words(value)
            if found is not None:
                return found
    return None


def find_table_bbox(obj):
    candidates = []

    def walk(value, key_hint=""):
        if isinstance(value, dict):
            for key, child in value.items():
                low = key.lower()
                if "bbox" in low or "bounding" in low:
                    bbox = as_bbox(child)
                    if bbox and ("table" in low or "bbox" == low or "bounding_box" == low):
                        score = 2 if "table" in low else 1
                        candidates.append((score, bbox))
                if "table" in low and isinstance(child, dict):
                    for bkey in ("bbox", "bounding_box", "bounds"):
                        bbox = as_bbox(child.get(bkey))
                        if bbox:
                            candidates.append((3, bbox))
                walk(child, low)
        elif isinstance(value, list):
            bbox = as_bbox(value)
            if bbox and "table" in key_hint:
                candidates.append((3, bbox))
            else:
                for child in value:
                    walk(child, key_hint)

    walk(obj)
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return None


def bbox_area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def inside_bbox(inner, outer, pad=1.0):
    cx = (inner[0] + inner[2]) / 2.0
    cy = (inner[1] + inner[3]) / 2.0
    return outer[0] - pad <= cx <= outer[2] + pad and outer[1] - pad <= cy <= outer[3] + pad


def overlap_1d(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def median(values, default=0.0):
    vals = sorted(v for v in values if v is not None and not math.isnan(v))
    if not vals:
        return default
    mid = len(vals) // 2
    if len(vals) % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def normalize_word(raw):
    bbox = None
    for key in ("bbox", "bounding_box", "bounds"):
        if key in raw:
            bbox = as_bbox(raw[key])
            break
    if bbox is None:
        bbox = as_bbox(raw)
    text = get_text(raw).strip()
    if not text or bbox is None:
        return None
    return {
        "text": text,
        "bbox": bbox,
        "x0": bbox[0],
        "y0": bbox[1],
        "x1": bbox[2],
        "y1": bbox[3],
        "xc": (bbox[0] + bbox[2]) / 2.0,
        "yc": (bbox[1] + bbox[3]) / 2.0,
        "w": max(0.0, bbox[2] - bbox[0]),
        "h": max(0.0, bbox[3] - bbox[1]),
    }


def group_rows(words):
    heights = [w["h"] for w in words]
    tol = max(2.0, median(heights, 8.0) * 0.65)
    rows = []

    for word in sorted(words, key=lambda w: (w["yc"], w["x0"])):
        best_i = None
        best_dist = None
        for i, row in enumerate(rows):
            dist = abs(word["yc"] - row["center"])
            if dist <= tol and (best_dist is None or dist < best_dist):
                best_i = i
                best_dist = dist
        if best_i is None:
            rows.append({"center": word["yc"], "words": [word]})
        else:
            row = rows[best_i]
            row["words"].append(word)
            row["center"] = sum(w["yc"] for w in row["words"]) / len(row["words"])

    rows.sort(key=lambda r: r["center"])
    return rows


def infer_column_centers(rows):
    body_rows = rows[1:] if len(rows) > 1 else rows
    candidate_rows = sorted(body_rows, key=lambda r: len(r["words"]), reverse=True)
    if not candidate_rows:
        return []

    best = candidate_rows[0]
    words = sorted(best["words"], key=lambda w: w["x0"])
    heights = [w["h"] for r in rows for w in r["words"]]
    widths = [w["w"] for r in rows for w in r["words"]]
    gap_threshold = max(median(widths, 20.0) * 0.9, median(heights, 8.0) * 1.8, 12.0)

    cells = []
    current = []
    prev = None
    for word in words:
        if prev is not None and word["x0"] - prev["x1"] > gap_threshold:
            cells.append(current)
            current = []
        current.append(word)
        prev = word
    if current:
        cells.append(current)

    centers = []
    for cell_words in cells:
        x0 = min(w["x0"] for w in cell_words)
        x1 = max(w["x1"] for w in cell_words)
        centers.append((x0 + x1) / 2.0)

    all_x = [w["xc"] for r in rows for w in r["words"]]
    if len(centers) < 2:
        centers = sorted(set(round(x, 1) for x in all_x))

    return sorted(centers)


def infer_column_ranges(rows, table_bbox):
    centers = infer_column_centers(rows)
    if not centers:
        return []

    if len(centers) == 1:
        return [(table_bbox[0], table_bbox[2])]

    boundaries = [table_bbox[0]]
    for left, right in zip(centers, centers[1:]):
        boundaries.append((left + right) / 2.0)
    boundaries.append(table_bbox[2])

    ranges = []
    for i in range(len(boundaries) - 1):
        ranges.append((boundaries[i], boundaries[i + 1]))
    return ranges


def assign_col(word, col_ranges):
    best_i = 0
    best_score = -1.0
    for i, (x0, x1) in enumerate(col_ranges):
        score = overlap_1d(word["x0"], word["x1"], x0, x1)
        if x0 <= word["xc"] <= x1:
            score += max(1.0, word["w"])
        if score > best_score:
            best_i = i
            best_score = score
    return best_i


def join_tokens(tokens):
    parts = []
    attach_left = {".", ",", ";", ":", "%", ")", "]", "}", "±"}
    attach_right = {"(", "[", "{", "$"}
    for tok in tokens:
        text = tok["text"]
        if not parts:
            parts.append(text)
        elif text in attach_left or text.startswith("%"):
            parts[-1] += text
        elif parts[-1] in attach_right:
            parts[-1] += text
        elif re.fullmatch(r"[/\-–—]", text):
            parts[-1] += text
        else:
            parts.append(text)
    return " ".join(parts).strip()


def reconstruct_cells(words, table_bbox):
    rows = group_rows(words)
    col_ranges = infer_column_ranges(rows, table_bbox)
    cells = []

    for row_id, row in enumerate(rows):
        buckets = defaultdict(list)
        for word in sorted(row["words"], key=lambda w: w["x0"]):
            col_id = assign_col(word, col_ranges)
            buckets[col_id].append(word)

        for col_id in sorted(buckets):
            toks = sorted(buckets[col_id], key=lambda w: w["x0"])
            text = join_tokens(toks)
            if not text:
                continue
            x0 = min(w["x0"] for w in toks)
            x1 = max(w["x1"] for w in toks)
            row_span = 1
            col_span = 1

            if col_ranges:
                start = col_id
                end = col_id
                for i, (cx0, cx1) in enumerate(col_ranges):
                    if overlap_1d(x0, x1, cx0, cx1) > 0.35 * min(x1 - x0, cx1 - cx0):
                        start = min(start, i)
                        end = max(end, i)
                col_id = start
                col_span = max(1, end - start + 1)

            cells.append({
                "row_id": row_id,
                "col_id": col_id,
                "row_span": row_span,
                "col_span": col_span,
                "is_header": row_id == 0,
                "text": text,
            })

    return cells, rows, col_ranges


def norm_header(text):
    t = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    if t in {"acc", "accuracy", "accuracy score"}:
        return "accuracy"
    if t in {"f1", "f 1", "f1 score", "f measure", "f1score"}:
        return "f1"
    if "method" in t or "model" in t or "approach" in t or "system" in t:
        return "method"
    if "dataset" in t or "data set" in t or "corpus" in t or "benchmark" in t:
        return "dataset"
    if "note" in t or "remark" in t or "setting" in t or "comment" in t:
        return "notes"
    return ""


def detect_header_row(cells):
    by_row = defaultdict(list)
    for cell in cells:
        by_row[cell["row_id"]].append(cell)

    best_row = 0
    best_score = -1
    for row_id, row_cells in by_row.items():
        labels = [norm_header(c["text"]) for c in row_cells]
        score = len(set(x for x in labels if x))
        if score > best_score:
            best_row = row_id
            best_score = score

    return best_row


def header_mapping(cells, header_row):
    mapping = {}
    header_cells = [c for c in cells if c["row_id"] == header_row]
    for cell in header_cells:
        label = norm_header(cell["text"])
        if label:
            for col in range(cell["col_id"], cell["col_id"] + cell["col_span"]):
                mapping[col] = label

    if not mapping:
        ordered = sorted(header_cells, key=lambda c: c["col_id"])
        fallback = ["method", "dataset", "accuracy", "f1", "notes"]
        for cell, label in zip(ordered, fallback):
            mapping[cell["col_id"]] = label

    return mapping


def parse_number(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        return None
    return float(match.group(0))


def clean_metric_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_metrics(cells):
    header_row = detect_header_row(cells)
    mapping = header_mapping(cells, header_row)

    by_row_col = defaultdict(dict)
    for cell in cells:
        if cell["row_id"] <= header_row:
            continue
        for col in range(cell["col_id"], cell["col_id"] + cell["col_span"]):
            if col not in by_row_col[cell["row_id"]]:
                by_row_col[cell["row_id"]][col] = cell["text"]

    metrics = []
    carry = {"method": "", "dataset": ""}

    for row_id in sorted(by_row_col):
        row = {field: "" for field in REQUIRED_METRIC_FIELDS}
        extras = []

        for col_id, text in sorted(by_row_col[row_id].items()):
            field = mapping.get(col_id)
            if field in row:
                row[field] = clean_metric_text(text)
            elif text:
                extras.append(clean_metric_text(text))

        if extras:
            row["notes"] = clean_metric_text((row["notes"] + " " + " ".join(extras)).strip())

        for field in ("method", "dataset"):
            if row[field]:
                carry[field] = row[field]
            else:
                row[field] = carry[field]

        has_metric = parse_number(row["accuracy"]) is not None or parse_number(row["f1"]) is not None
        has_identity = bool(row["method"] or row["dataset"])
        if has_metric and has_identity:
            metrics.append(row)

    return metrics, header_row, mapping


def audit_metrics(metrics, raw_words, table_words):
    issues = []

    for col in REQUIRED_METRIC_FIELDS:
        if any(col not in row for row in metrics):
            issues.append({
                "category": "missing_required_column",
                "message": f"Required column missing from at least one row: {col}",
            })

    for i, row in enumerate(metrics):
        for field in ("method", "dataset"):
            if not clean_metric_text(row.get(field)):
                issues.append({
                    "category": "empty_required_text",
                    "row_index": i,
                    "field": field,
                    "message": f"Empty required text field: {field}",
                })
        for field in ("accuracy", "f1"):
            if parse_number(row.get(field)) is None:
                issues.append({
                    "category": "non_numeric_metric",
                    "row_index": i,
                    "field": field,
                    "value": row.get(field, ""),
                    "message": f"Metric field is not numeric: {field}",
                })

    seen = {}
    for i, row in enumerate(metrics):
        key = (
            clean_metric_text(row.get("method")).lower(),
            clean_metric_text(row.get("dataset")).lower(),
        )
        if key in seen:
            issues.append({
                "category": "duplicate_record",
                "row_index": i,
                "first_row_index": seen[key],
                "message": "Duplicate method/dataset record",
            })
        else:
            seen[key] = i

    best_by_dataset = {}
    grouped = defaultdict(list)
    for row in metrics:
        f1 = parse_number(row.get("f1"))
        if f1 is not None and clean_metric_text(row.get("dataset")):
            grouped[clean_metric_text(row["dataset"])].append((f1, row))

    for dataset, values in sorted(grouped.items()):
        best_f1, best_row = max(values, key=lambda item: item[0])
        best_by_dataset[dataset] = {
            "method": clean_metric_text(best_row.get("method")),
            "f1": best_f1,
            "accuracy": parse_number(best_row.get("accuracy")),
        }

    excluded_count = len(raw_words) - len(table_words)
    if excluded_count > 0:
        issues.append({
            "category": "excluded_non_table_text",
            "message": f"Excluded {excluded_count} OCR words outside the table bounding box as caption/footnote/non-table text.",
            "count": excluded_count,
        })

    if not metrics:
        issues.append({
            "category": "ambiguous_structure",
            "message": "No metric rows could be normalized from the reconstructed cells.",
        })

    return {
        "row_count": len(metrics),
        "best_by_dataset": best_by_dataset,
        "issues": issues,
    }


def write_cells_csv(path, cells):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["row_id", "col_id", "row_span", "col_span", "is_header", "text"],
        )
        writer.writeheader()
        for cell in sorted(cells, key=lambda c: (c["row_id"], c["col_id"], c["text"])):
            writer.writerow({
                "row_id": cell["row_id"],
                "col_id": cell["col_id"],
                "row_span": cell["row_span"],
                "col_span": cell["col_span"],
                "is_header": str(bool(cell["is_header"])).lower(),
                "text": cell["text"],
            })


def write_metrics_csv(path, metrics):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_METRIC_FIELDS)
        writer.writeheader()
        for row in metrics:
            writer.writerow({field: row.get(field, "") for field in REQUIRED_METRIC_FIELDS})


def write_audit_json(path, audit):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)


def write_summary_md(path, metrics, audit):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [
        "# OCR Table Extraction Summary",
        "",
        f"Normalized metric rows: **{audit['row_count']}**.",
        "",
        "## Best F1 by Dataset",
        "",
    ]

    if audit["best_by_dataset"]:
        lines.append("| Dataset | Best method | F1 | Accuracy |")
        lines.append("|---|---:|---:|---:|")
        for dataset, best in audit["best_by_dataset"].items():
            acc = "" if best.get("accuracy") is None else f"{best['accuracy']:g}"
            lines.append(
                f"| {dataset} | {best.get('method', '')} | {best.get('f1', 0):g} | {acc} |"
            )
    else:
        lines.append("No dataset-level F1 winners could be computed.")

    lines.extend(["", "## Validation Notes", ""])

    if audit["issues"]:
        for issue in audit["issues"]:
            lines.append(f"- `{issue['category']}`: {issue['message']}")
    else:
        lines.append("- No extraction or validation issues were detected.")

    lines.extend(["", "## Extracted Metrics", ""])

    if metrics:
        lines.append("| Method | Dataset | Accuracy | F1 | Notes |")
        lines.append("|---|---|---:|---:|---|")
        for row in metrics:
            lines.append(
                "| {method} | {dataset} | {accuracy} | {f1} | {notes} |".format(
                    method=row.get("method", ""),
                    dataset=row.get("dataset", ""),
                    accuracy=row.get("accuracy", ""),
                    f1=row.get("f1", ""),
                    notes=row.get("notes", ""),
                )
            )
    else:
        lines.append("No metric observations were extracted.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    env = {}
    missing = []
    for key in REQUIRED_ENV:
        value = os.environ.get(key)
        if not value:
            missing.append(key)
        env[key] = value

    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))

    with open(env["ORIGINAL_WORDS_JSON"], "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_word_items = find_words(data)
    if raw_word_items is None:
        raise RuntimeError("Could not locate OCR words list in input JSON.")

    raw_words = [w for w in (normalize_word(item) for item in raw_word_items) if w]
    if not raw_words:
        raise RuntimeError("No OCR words with usable text and bounding boxes were found.")

    table_bbox = find_table_bbox(data)
    if table_bbox is None:
        table_bbox = [
            min(w["x0"] for w in raw_words),
            min(w["y0"] for w in raw_words),
            max(w["x1"] for w in raw_words),
            max(w["y1"] for w in raw_words),
        ]

    table_words = [w for w in raw_words if inside_bbox(w["bbox"], table_bbox)]
    if not table_words:
        raise RuntimeError("No OCR words fell inside the table bounding box.")

    cells, rows, col_ranges = reconstruct_cells(table_words, table_bbox)
    metrics, header_row, mapping = normalize_metrics(cells)
    audit = audit_metrics(metrics, raw_words, table_words)

    write_cells_csv(env["OUTPUT_CELLS_CSV"], cells)
    write_metrics_csv(env["OUTPUT_METRICS_CSV"], metrics)
    write_audit_json(env["OUTPUT_AUDIT_JSON"], audit)
    write_summary_md(env["SUMMARY_MD"], metrics, audit)


if __name__ == "__main__":
    main()
