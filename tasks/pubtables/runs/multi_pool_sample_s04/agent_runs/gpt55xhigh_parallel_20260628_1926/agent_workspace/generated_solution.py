import csv
import json
import math
import os
import re
from collections import defaultdict
from statistics import median


ORIGINAL_WORDS_JSON = os.environ["ORIGINAL_WORDS_JSON"]
OUTPUT_CELLS_CSV = os.environ["OUTPUT_CELLS_CSV"]
OUTPUT_METRICS_CSV = os.environ["OUTPUT_METRICS_CSV"]
OUTPUT_AUDIT_JSON = os.environ["OUTPUT_AUDIT_JSON"]
SUMMARY_MD = os.environ["SUMMARY_MD"]


FIELDNAMES_CELLS = ["row_id", "col_id", "row_span", "col_span", "is_header", "text"]
FIELDNAMES_METRICS = ["method", "dataset", "accuracy", "f1", "notes"]


def as_bbox(value):
    """Return bbox as [x0, y0, x1, y1] when possible."""
    if value is None:
        return None

    if isinstance(value, dict):
        keys1 = ("x0", "y0", "x1", "y1")
        keys2 = ("left", "top", "right", "bottom")
        keys3 = ("x", "y", "w", "h")
        keys4 = ("x", "y", "width", "height")

        if all(k in value for k in keys1):
            return [float(value[k]) for k in keys1]
        if all(k in value for k in keys2):
            return [float(value[k]) for k in keys2]
        if all(k in value for k in keys3):
            return [
                float(value["x"]),
                float(value["y"]),
                float(value["x"]) + float(value["w"]),
                float(value["y"]) + float(value["h"]),
            ]
        if all(k in value for k in keys4):
            return [
                float(value["x"]),
                float(value["y"]),
                float(value["x"]) + float(value["width"]),
                float(value["y"]) + float(value["height"]),
            ]

    if isinstance(value, (list, tuple)) and len(value) >= 4:
        vals = [float(v) for v in value[:4]]
        x0, y0, x1, y1 = vals
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        return [x0, y0, x1, y1]

    return None


def text_from_word(word):
    for key in ("text", "word", "token", "value", "ocr_text"):
        if key in word and word[key] is not None:
            return str(word[key])
    return ""


def bbox_from_word(word):
    for key in ("bbox", "box", "bounding_box", "bounds"):
        if key in word:
            bbox = as_bbox(word[key])
            if bbox:
                return bbox

    if all(k in word for k in ("x0", "y0", "x1", "y1")):
        return as_bbox(word)
    if all(k in word for k in ("left", "top", "right", "bottom")):
        return as_bbox(word)
    if all(k in word for k in ("x", "y", "w", "h")):
        return as_bbox(word)
    if all(k in word for k in ("x", "y", "width", "height")):
        return as_bbox(word)

    return None


def walk_json(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk_json(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_json(value)


def find_table_bbox(data, words):
    candidate_keys = (
        "table_bbox",
        "table_bounding_box",
        "table_box",
        "bbox",
        "bounding_box",
        "bounds",
    )

    candidates = []
    for obj in walk_json(data):
        if not isinstance(obj, dict):
            continue

        label = " ".join(str(obj.get(k, "")).lower() for k in ("type", "label", "name", "category"))
        for key in candidate_keys:
            if key in obj:
                bbox = as_bbox(obj[key])
                if bbox:
                    candidates.append((label, key, bbox))

    table_labeled = [bbox for label, _, bbox in candidates if "table" in label]
    if table_labeled:
        return largest_bbox(table_labeled)

    key_labeled = [bbox for _, key, bbox in candidates if "table" in key]
    if key_labeled:
        return largest_bbox(key_labeled)

    if words:
        x0 = min(w["bbox"][0] for w in words)
        y0 = min(w["bbox"][1] for w in words)
        x1 = max(w["bbox"][2] for w in words)
        y1 = max(w["bbox"][3] for w in words)
        return [x0, y0, x1, y1]

    raise ValueError("Could not find table bounding box or word boxes.")


def largest_bbox(bboxes):
    return max(bboxes, key=lambda b: max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1]))


def extract_words(data):
    words = []

    for obj in walk_json(data):
        if not isinstance(obj, dict):
            continue
        text = text_from_word(obj)
        bbox = bbox_from_word(obj)
        if text and bbox:
            words.append(
                {
                    "text": text.strip(),
                    "bbox": bbox,
                    "x_center": (bbox[0] + bbox[2]) / 2.0,
                    "y_center": (bbox[1] + bbox[3]) / 2.0,
                    "width": bbox[2] - bbox[0],
                    "height": bbox[3] - bbox[1],
                }
            )

    # Deduplicate in case the JSON has nested repeated word records.
    seen = set()
    unique = []
    for word in words:
        key = (
            word["text"],
            round(word["bbox"][0], 3),
            round(word["bbox"][1], 3),
            round(word["bbox"][2], 3),
            round(word["bbox"][3], 3),
        )
        if key not in seen:
            seen.add(key)
            unique.append(word)

    return unique


def inside_bbox(word, bbox, tolerance=1.5):
    x0, y0, x1, y1 = bbox
    return (
        x0 - tolerance <= word["x_center"] <= x1 + tolerance
        and y0 - tolerance <= word["y_center"] <= y1 + tolerance
    )


def group_rows(words):
    if not words:
        return []

    heights = [w["height"] for w in words if w["height"] > 0]
    med_height = median(heights) if heights else 10.0
    tolerance = max(2.0, med_height * 0.65)

    rows = []
    for word in sorted(words, key=lambda w: (w["y_center"], w["x_center"])):
        placed = False
        for row in rows:
            if abs(word["y_center"] - row["center"]) <= tolerance:
                row["words"].append(word)
                row["center"] = sum(w["y_center"] for w in row["words"]) / len(row["words"])
                placed = True
                break
        if not placed:
            rows.append({"center": word["y_center"], "words": [word]})

    rows.sort(key=lambda r: r["center"])
    return rows


def infer_column_boundaries(rows, table_bbox):
    left, _, right, _ = table_bbox

    row_gaps = []
    for row in rows:
        row_words = sorted(row["words"], key=lambda w: w["bbox"][0])
        for prev, curr in zip(row_words, row_words[1:]):
            gap = curr["bbox"][0] - prev["bbox"][2]
            if gap > 0:
                row_gaps.append(gap)

    if not row_gaps:
        return [left, right]

    typical_gap = median(row_gaps)
    large_gaps = []

    for row in rows:
        row_words = sorted(row["words"], key=lambda w: w["bbox"][0])
        for prev, curr in zip(row_words, row_words[1:]):
            gap = curr["bbox"][0] - prev["bbox"][2]
            if gap >= max(typical_gap * 2.5, 12.0):
                large_gaps.append((prev["bbox"][2] + curr["bbox"][0]) / 2.0)

    if not large_gaps:
        x_centers = sorted(w["x_center"] for r in rows for w in r["words"])
        clusters = []
        widths = [w["width"] for r in rows for w in r["words"] if w["width"] > 0]
        x_tol = max(8.0, (median(widths) if widths else 10.0) * 1.3)

        for x in x_centers:
            if not clusters or abs(x - clusters[-1][-1]) > x_tol:
                clusters.append([x])
            else:
                clusters[-1].append(x)

        centers = [sum(c) / len(c) for c in clusters]
        if len(centers) <= 1:
            return [left, right]
        return [left] + [(a + b) / 2.0 for a, b in zip(centers, centers[1:])] + [right]

    clusters = []
    for x in sorted(large_gaps):
        if not clusters or abs(x - clusters[-1][-1]) > 8.0:
            clusters.append([x])
        else:
            clusters[-1].append(x)

    cuts = [sum(c) / len(c) for c in clusters]
    cuts = [c for c in cuts if left < c < right]
    return [left] + cuts + [right]


def column_for_word(word, boundaries):
    best_col = 0
    best_overlap = -1.0
    wx0, _, wx1, _ = word["bbox"]

    for idx in range(len(boundaries) - 1):
        cx0, cx1 = boundaries[idx], boundaries[idx + 1]
        overlap = max(0.0, min(wx1, cx1) - max(wx0, cx0))
        if overlap > best_overlap:
            best_overlap = overlap
            best_col = idx

    if best_overlap > 0:
        return best_col

    x = word["x_center"]
    for idx in range(len(boundaries) - 1):
        if boundaries[idx] <= x <= boundaries[idx + 1]:
            return idx

    return min(range(len(boundaries) - 1), key=lambda i: abs(x - (boundaries[i] + boundaries[i + 1]) / 2.0))


def join_tokens(words):
    words = sorted(words, key=lambda w: (w["bbox"][0], w["bbox"][1]))
    out = ""
    no_space_before = set(".,;:%)]}")
    no_space_after = set("([{$")
    for word in words:
        token = word["text"]
        if not token:
            continue
        if not out:
            out = token
        elif token in no_space_before or out[-1] in no_space_after or token.startswith("%"):
            out += token
        else:
            out += " " + token
    return re.sub(r"\s+", " ", out).strip()


def reconstruct_cells(words, table_bbox):
    rows = group_rows(words)
    boundaries = infer_column_boundaries(rows, table_bbox)
    n_cols = max(1, len(boundaries) - 1)

    raw_cells = []
    for row_id, row in enumerate(rows):
        buckets = defaultdict(list)
        for word in row["words"]:
            col_id = column_for_word(word, boundaries)
            buckets[col_id].append(word)

        for col_id in range(n_cols):
            text = join_tokens(buckets.get(col_id, []))
            if text:
                raw_cells.append(
                    {
                        "row_id": row_id,
                        "col_id": col_id,
                        "row_span": 1,
                        "col_span": 1,
                        "is_header": False,
                        "text": text,
                    }
                )

    raw_cells = infer_spans(raw_cells, n_cols)
    mark_headers(raw_cells)
    return raw_cells, n_cols


def infer_spans(cells, n_cols):
    by_row = defaultdict(list)
    for cell in cells:
        by_row[cell["row_id"]].append(cell)

    adjusted = []
    for row_id in sorted(by_row):
        row_cells = sorted(by_row[row_id], key=lambda c: c["col_id"])
        if len(row_cells) == 1 and n_cols > 1:
            text = row_cells[0]["text"]
            lower = text.lower()
            if not any(k in lower for k in ("accuracy", "f1", "method", "dataset")):
                row_cells[0]["col_id"] = 0
                row_cells[0]["col_span"] = n_cols
        adjusted.extend(row_cells)

    return adjusted


def mark_headers(cells):
    header_keywords = ("method", "dataset", "accuracy", "acc", "f1", "score", "notes")
    max_header_row = -1

    for cell in cells:
        lower = normalize_header(cell["text"])
        if any(k in lower for k in header_keywords):
            max_header_row = max(max_header_row, cell["row_id"])

    if max_header_row < 0 and cells:
        max_header_row = min(c["row_id"] for c in cells)

    for cell in cells:
        cell["is_header"] = cell["row_id"] <= max_header_row


def normalize_header(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def header_to_field(text):
    normalized = normalize_header(text)

    if "method" in normalized or "model" in normalized or "approach" in normalized or "system" in normalized:
        return "method"
    if "dataset" in normalized or "data set" in normalized or "corpus" in normalized or "benchmark" in normalized:
        return "dataset"
    if "accuracy" in normalized or normalized in {"acc", "acc."} or " acc " in f" {normalized} ":
        return "accuracy"
    if "f1" in normalized or "f 1" in normalized or "f score" in normalized or "fscore" in normalized:
        return "f1"
    if "note" in normalized or "remark" in normalized or "comment" in normalized:
        return "notes"

    return None


def find_header_mapping(cells, n_cols):
    header_cells = [c for c in cells if c["is_header"]]
    mapping = {}
    for cell in sorted(header_cells, key=lambda c: (c["row_id"], c["col_id"])):
        field = header_to_field(cell["text"])
        if field:
            for col in range(cell["col_id"], min(n_cols, cell["col_id"] + cell["col_span"])):
                mapping[col] = field

    if not mapping:
        # Conservative fallback for common metric-table order.
        fallback = ["method", "dataset", "accuracy", "f1", "notes"]
        for col_id in range(min(n_cols, len(fallback))):
            mapping[col_id] = fallback[col_id]

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

    number = float(match.group(0))
    return number


def format_number(number):
    if number is None:
        return ""
    if math.isfinite(number) and abs(number - round(number)) < 1e-9:
        return str(int(round(number)))
    return f"{number:.6g}"


def normalize_metrics(cells, n_cols):
    mapping = find_header_mapping(cells, n_cols)
    issues = []

    by_row = defaultdict(dict)
    for cell in cells:
        if cell["is_header"]:
            continue
        for col in range(cell["col_id"], min(n_cols, cell["col_id"] + cell["col_span"])):
            field = mapping.get(col)
            if field:
                existing = by_row[cell["row_id"]].get(field, "")
                by_row[cell["row_id"]][field] = (existing + " " + cell["text"]).strip() if existing else cell["text"]

    metrics = []
    for row_id in sorted(by_row):
        row = by_row[row_id]
        metric = {
            "method": row.get("method", "").strip(),
            "dataset": row.get("dataset", "").strip(),
            "accuracy": row.get("accuracy", "").strip(),
            "f1": row.get("f1", "").strip(),
            "notes": row.get("notes", "").strip(),
        }

        if not any(metric.values()):
            continue

        if not metric["method"] or not metric["dataset"]:
            issues.append(
                {
                    "type": "missing_required_text",
                    "row_id": row_id,
                    "message": "Metric row is missing method or dataset.",
                    "row": metric,
                }
            )

        for field in ("accuracy", "f1"):
            number = parse_number(metric[field])
            if number is None:
                issues.append(
                    {
                        "type": "missing_numeric_value",
                        "row_id": row_id,
                        "field": field,
                        "message": f"Could not parse numeric {field}.",
                        "value": metric[field],
                    }
                )
            else:
                metric[field] = format_number(number)
                if number < 0 or number > 100:
                    issues.append(
                        {
                            "type": "numeric_range_warning",
                            "row_id": row_id,
                            "field": field,
                            "message": f"{field} is outside the expected 0-100 range.",
                            "value": metric[field],
                        }
                    )

        metrics.append(metric)

    return metrics, issues


def compute_best_by_dataset(metrics, issues):
    best = {}

    for idx, row in enumerate(metrics):
        dataset = row["dataset"]
        f1 = parse_number(row["f1"])

        if not dataset:
            continue
        if f1 is None:
            continue

        current = best.get(dataset)
        if current is None or f1 > current["f1_score"]:
            best[dataset] = {
                "method": row["method"],
                "f1": row["f1"],
                "f1_score": f1,
                "row_index": idx,
            }
        elif current is not None and f1 == current["f1_score"]:
            issues.append(
                {
                    "type": "best_f1_tie",
                    "dataset": dataset,
                    "message": "Multiple methods share the best F1 score for this dataset.",
                    "f1": row["f1"],
                }
            )

    return {
        dataset: {"method": item["method"], "f1": item["f1"], "row_index": item["row_index"]}
        for dataset, item in sorted(best.items())
    }


def write_cells_csv(path, cells):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES_CELLS)
        writer.writeheader()
        for cell in sorted(cells, key=lambda c: (c["row_id"], c["col_id"])):
            writer.writerow(
                {
                    "row_id": cell["row_id"],
                    "col_id": cell["col_id"],
                    "row_span": cell["row_span"],
                    "col_span": cell["col_span"],
                    "is_header": str(bool(cell["is_header"])).lower(),
                    "text": cell["text"],
                }
            )


def write_metrics_csv(path, metrics):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES_METRICS)
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)


def write_audit_json(path, audit):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)


def write_summary_md(path, audit):
    lines = [
        "# Metric Extraction Summary",
        "",
        f"- Normalized metric rows: {audit['row_count']}",
    ]

    if audit["best_by_dataset"]:
        lines.append("- Best method by F1:")
        for dataset, item in audit["best_by_dataset"].items():
            lines.append(f"  - {dataset}: {item['method']} (F1 {item['f1']})")
    else:
        lines.append("- Best method by F1: none computed because no parseable dataset/F1 pairs were found.")

    issue_count = len(audit["issues"])
    if issue_count:
        lines.append(f"- Extraction or validation issues: {issue_count} issue(s) reported in `audit.json`.")
    else:
        lines.append("- Extraction or validation issues: none reported.")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    with open(ORIGINAL_WORDS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_words = extract_words(data)
    table_bbox = find_table_bbox(data, all_words)
    table_words = [w for w in all_words if inside_bbox(w, table_bbox)]

    cells, n_cols = reconstruct_cells(table_words, table_bbox)
    metrics, issues = normalize_metrics(cells, n_cols)

    if not table_words:
        issues.append(
            {
                "type": "empty_table_bbox",
                "message": "No OCR words were found inside the detected table bounding box.",
            }
        )

    if not cells:
        issues.append(
            {
                "type": "empty_reconstructed_cells",
                "message": "No non-empty table cells were reconstructed.",
            }
        )

    best_by_dataset = compute_best_by_dataset(metrics, issues)

    audit = {
        "row_count": len(metrics),
        "best_by_dataset": best_by_dataset,
        "issues": issues,
    }

    write_cells_csv(OUTPUT_CELLS_CSV, cells)
    write_metrics_csv(OUTPUT_METRICS_CSV, metrics)
    write_audit_json(OUTPUT_AUDIT_JSON, audit)
    write_summary_md(SUMMARY_MD, audit)


if __name__ == "__main__":
    main()
