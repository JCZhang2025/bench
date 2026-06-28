#!/usr/bin/env python3
"""
Reconstruct a PubTables-style OCR word-box table, extract normalized metrics,
audit the extraction, and write required artifacts.

Inputs/outputs are read from environment variables:
- ORIGINAL_WORDS_JSON
- OUTPUT_CELLS_CSV
- OUTPUT_METRICS_CSV
- OUTPUT_AUDIT_JSON
- SUMMARY_MD
"""

import csv
import json
import math
import os
import re
from collections import defaultdict


DEFAULTS = {
    "ORIGINAL_WORDS_JSON": r"E:\research\pilot_experiments\tasks\pubtables\data\original\table_words.json",
    "OUTPUT_CELLS_CSV": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s08\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\table_cells.csv",
    "OUTPUT_METRICS_CSV": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s08\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\metrics.csv",
    "OUTPUT_AUDIT_JSON": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s08\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\audit.json",
    "SUMMARY_MD": r"E:\research\pilot_experiments\tasks\pubtables\runs\multi_pool_sample_s08\agent_runs\gpt55xhigh_parallel_20260628_1926\artifacts\summary.md",
}


HEADER_SYNONYMS = {
    "method": {"method", "model", "approach", "system", "algorithm", "classifier"},
    "dataset": {"dataset", "data", "benchmark", "corpus", "set"},
    "accuracy": {"accuracy", "acc", "acc.", "top1", "top-1"},
    "f1": {"f1", "f1-score", "f1score", "f-score", "macro-f1", "micro-f1"},
    "notes": {"notes", "note", "remarks", "remark", "setting", "details"},
}


def env_path(name):
    return os.environ.get(name) or DEFAULTS[name]


def ensure_parent(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from flatten(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from flatten(item)


def as_bbox(value):
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


def find_bbox_in_record(record):
    for key in ("bbox", "bounding_box", "box", "rect", "rectangle"):
        if key in record:
            bbox = as_bbox(record[key])
            if bbox:
                return bbox

    lower = {k.lower(): k for k in record.keys()}
    for names in (
        ("x0", "y0", "x1", "y1"),
        ("left", "top", "right", "bottom"),
    ):
        if all(n in lower for n in names):
            return as_bbox({n: record[lower[n]] for n in names})

    if all(n in lower for n in ("x", "y", "width", "height")):
        return as_bbox({n: record[lower[n]] for n in ("x", "y", "width", "height")})

    return None


def extract_words(data):
    words = []
    for rec in flatten(data):
        text = None
        for key in ("text", "word", "token", "content", "value"):
            if key in rec and isinstance(rec[key], (str, int, float)):
                text = str(rec[key]).strip()
                break

        bbox = find_bbox_in_record(rec)
        if text and bbox:
            x0, y0, x1, y1 = bbox
            if x1 > x0 and y1 > y0:
                words.append(
                    {
                        "text": text,
                        "bbox": [x0, y0, x1, y1],
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "xc": (x0 + x1) / 2.0,
                        "yc": (y0 + y1) / 2.0,
                        "w": x1 - x0,
                        "h": y1 - y0,
                    }
                )
    return words


def candidate_table_bboxes(data):
    candidates = []
    for rec in flatten(data):
        keys = {str(k).lower(): k for k in rec.keys()}
        label_text = " ".join(str(rec[k]).lower() for k in rec.keys() if k in ("type", "label", "category", "name"))
        has_table_hint = "table" in label_text or any("table" in k for k in keys)

        for key in ("table_bbox", "table_bounding_box", "table_box", "bbox", "bounding_box", "box"):
            if key in rec:
                bbox = as_bbox(rec[key])
                if bbox and has_table_hint:
                    candidates.append(bbox)

        for key, value in rec.items():
            if "table" in str(key).lower():
                bbox = as_bbox(value)
                if bbox:
                    candidates.append(bbox)
                elif isinstance(value, dict):
                    nested = find_bbox_in_record(value)
                    if nested:
                        candidates.append(nested)

    return candidates


def bbox_area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def infer_table_bbox(data, words):
    candidates = candidate_table_bboxes(data)
    if candidates:
        word_union = [
            min(w["x0"] for w in words),
            min(w["y0"] for w in words),
            max(w["x1"] for w in words),
            max(w["y1"] for w in words),
        ]

        def score(b):
            inside = sum(1 for w in words if point_inside(w["xc"], w["yc"], b))
            area_penalty = bbox_area(b) / max(1.0, bbox_area(word_union))
            return (inside, -area_penalty)

        return sorted(candidates, key=score, reverse=True)[0]

    # Fallback: trim likely caption/footnote by taking the densest central block.
    xs0 = sorted(w["x0"] for w in words)
    ys0 = sorted(w["y0"] for w in words)
    xs1 = sorted(w["x1"] for w in words)
    ys1 = sorted(w["y1"] for w in words)
    return [
        percentile(xs0, 2),
        percentile(ys0, 8),
        percentile(xs1, 98),
        percentile(ys1, 92),
    ]


def point_inside(x, y, bbox, pad=0.5):
    return bbox[0] - pad <= x <= bbox[2] + pad and bbox[1] - pad <= y <= bbox[3] + pad


def percentile(values, pct):
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * pct / 100.0
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return values[lo]
    frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def median(values, default=0.0):
    values = sorted(values)
    if not values:
        return default
    n = len(values)
    mid = n // 2
    if n % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def group_rows(words):
    if not words:
        return []

    med_h = median([w["h"] for w in words], default=8.0)
    tolerance = max(3.0, med_h * 0.65)
    rows = []

    for word in sorted(words, key=lambda w: (w["yc"], w["x0"])):
        best = None
        best_dist = None
        for row in rows:
            dist = abs(word["yc"] - row["yc"])
            if dist <= tolerance and (best is None or dist < best_dist):
                best = row
                best_dist = dist

        if best is None:
            rows.append({"words": [word], "yc": word["yc"]})
        else:
            best["words"].append(word)
            best["yc"] = sum(w["yc"] for w in best["words"]) / len(best["words"])

    rows.sort(key=lambda r: r["yc"])
    for i, row in enumerate(rows):
        row["row_id"] = i
        row["words"].sort(key=lambda w: (w["x0"], w["yc"]))
        row["y0"] = min(w["y0"] for w in row["words"])
        row["y1"] = max(w["y1"] for w in row["words"])

    return rows


def infer_column_edges(rows, table_bbox):
    if not rows:
        return [table_bbox[0], table_bbox[2]]

    word_count_by_row = [len(r["words"]) for r in rows]
    likely_body_rows = sorted(rows, key=lambda r: len(r["words"]), reverse=True)[: max(1, min(6, len(rows)))]
    med_word_w = median([w["w"] for r in rows for w in r["words"]], default=20.0)
    gap_threshold = max(med_word_w * 1.2, 18.0)

    gap_votes = []
    for row in likely_body_rows:
        words = sorted(row["words"], key=lambda w: w["x0"])
        for left, right in zip(words, words[1:]):
            gap = right["x0"] - left["x1"]
            if gap >= gap_threshold:
                gap_votes.append((left["x1"] + right["x0"]) / 2.0)

    if not gap_votes:
        # Fallback to x-center clusters.
        centers = sorted(w["xc"] for r in rows for w in r["words"])
        breaks = []
        for a, b in zip(centers, centers[1:]):
            if b - a >= max(med_word_w * 1.5, 24.0):
                breaks.append((a + b) / 2.0)
        edges = [table_bbox[0]] + breaks + [table_bbox[2]]
        return clean_edges(edges, table_bbox)

    clusters = []
    for x in sorted(gap_votes):
        if not clusters or abs(x - clusters[-1]["center"]) > max(10.0, med_word_w * 0.5):
            clusters.append({"values": [x], "center": x})
        else:
            clusters[-1]["values"].append(x)
            clusters[-1]["center"] = sum(clusters[-1]["values"]) / len(clusters[-1]["values"])

    min_votes = 1 if len(rows) <= 3 else 2
    breaks = [c["center"] for c in clusters if len(c["values"]) >= min_votes]

    edges = [table_bbox[0]] + breaks + [table_bbox[2]]
    return clean_edges(edges, table_bbox)


def clean_edges(edges, table_bbox):
    left, right = table_bbox[0], table_bbox[2]
    cleaned = []
    for edge in sorted(edges):
        edge = max(left, min(right, edge))
        if not cleaned or abs(edge - cleaned[-1]) > 5.0:
            cleaned.append(edge)

    if len(cleaned) < 2:
        cleaned = [left, right]

    if cleaned[0] > left + 1:
        cleaned.insert(0, left)
    else:
        cleaned[0] = left

    if cleaned[-1] < right - 1:
        cleaned.append(right)
    else:
        cleaned[-1] = right

    return cleaned


def column_for_word(word, edges):
    best_idx = 0
    best_overlap = -1.0
    for idx in range(len(edges) - 1):
        overlap = max(0.0, min(word["x1"], edges[idx + 1]) - max(word["x0"], edges[idx]))
        if edges[idx] <= word["xc"] <= edges[idx + 1]:
            overlap += 1e-3
        if overlap > best_overlap:
            best_idx = idx
            best_overlap = overlap
    return best_idx


def join_tokens(tokens):
    tokens = [t for t in tokens if t]
    if not tokens:
        return ""

    text = tokens[0]
    no_space_before = {".", ",", ":", ";", "%", ")", "]", "}", "?", "!"}
    no_space_after = {"(", "[", "{", "/", "-"}
    for tok in tokens[1:]:
        if tok in no_space_before:
            text += tok
        elif text and text[-1] in no_space_after:
            text += tok
        elif tok.startswith(("/", "-", "%")):
            text += tok
        else:
            text += " " + tok
    return text.strip()


def build_cells(rows, edges):
    raw_cells = []
    for row in rows:
        buckets = defaultdict(list)
        for word in row["words"]:
            buckets[column_for_word(word, edges)].append(word)

        occupied_cols = sorted(buckets)
        for col in occupied_cols:
            words = sorted(buckets[col], key=lambda w: (w["x0"], w["yc"]))
            x0 = min(w["x0"] for w in words)
            x1 = max(w["x1"] for w in words)

            col_start = col
            col_end = col
            for idx in range(len(edges) - 1):
                overlap = max(0.0, min(x1, edges[idx + 1]) - max(x0, edges[idx]))
                width = max(1.0, edges[idx + 1] - edges[idx])
                if overlap / width >= 0.35:
                    col_start = min(col_start, idx)
                    col_end = max(col_end, idx)

            raw_cells.append(
                {
                    "row_id": row["row_id"],
                    "col_id": col_start,
                    "row_span": 1,
                    "col_span": max(1, col_end - col_start + 1),
                    "is_header": False,
                    "text": join_tokens([w["text"] for w in words]),
                    "x0": x0,
                    "x1": x1,
                    "y0": min(w["y0"] for w in words),
                    "y1": max(w["y1"] for w in words),
                }
            )

    mark_headers(raw_cells)
    raw_cells = infer_row_spans(raw_cells, len(rows))
    return sorted(raw_cells, key=lambda c: (c["row_id"], c["col_id"]))


def mark_headers(cells):
    header_rows = set()
    for cell in cells:
        lowered = normalize_label(cell["text"])
        if any(lowered in names or lowered.replace(" ", "") in names for names in HEADER_SYNONYMS.values()):
            header_rows.add(cell["row_id"])

    if not header_rows and cells:
        header_rows.add(min(c["row_id"] for c in cells))

    if header_rows:
        first_body = max(header_rows) + 1
        for cell in cells:
            if cell["row_id"] in header_rows or cell["row_id"] < first_body:
                cell["is_header"] = True


def infer_row_spans(cells, row_count):
    by_col = defaultdict(list)
    for cell in cells:
        by_col[cell["col_id"]].append(cell)

    for col_cells in by_col.values():
        col_cells.sort(key=lambda c: c["row_id"])
        for idx, cell in enumerate(col_cells):
            next_row = col_cells[idx + 1]["row_id"] if idx + 1 < len(col_cells) else row_count
            gap = next_row - cell["row_id"]
            if gap > 1 and cell["text"] and not cell["is_header"]:
                cell["row_span"] = gap

    return cells


def normalize_label(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.%\- ]+", " ", text.lower())).strip()


def parse_number(text):
    if text is None:
        return None
    cleaned = str(text).strip()
    if not cleaned or cleaned in {"-", "--", "n/a", "N/A", "NA"}:
        return None

    match = re.search(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?|[-+]?\.\d+", cleaned)
    if not match:
        return None

    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def header_mapping(cells):
    header_cells = [c for c in cells if c["is_header"]]
    if not header_cells:
        return {}

    scores = defaultdict(lambda: defaultdict(int))
    for cell in header_cells:
        label = normalize_label(cell["text"])
        compact = label.replace(" ", "")
        for field, names in HEADER_SYNONYMS.items():
            for name in names:
                ncompact = name.replace(" ", "")
                if label == name or compact == ncompact:
                    scores[cell["col_id"]][field] += 5
                elif name in label or ncompact in compact:
                    scores[cell["col_id"]][field] += 2

    mapping = {}
    used = set()
    for col, field_scores in scores.items():
        if not field_scores:
            continue
        field, score = max(field_scores.items(), key=lambda item: item[1])
        if score > 0 and field not in used:
            mapping[field] = col
            used.add(field)

    return mapping


def rows_to_matrix(cells):
    matrix = defaultdict(dict)
    for cell in cells:
        matrix[cell["row_id"]][cell["col_id"]] = cell["text"]
    return matrix


def infer_mapping_from_values(cells):
    matrix = rows_to_matrix(cells)
    cols = sorted({c["col_id"] for c in cells})
    data_rows = sorted(matrix)

    numeric_cols = []
    text_cols = []
    for col in cols:
        vals = [matrix[r].get(col, "") for r in data_rows]
        numeric_hits = sum(1 for v in vals if parse_number(v) is not None)
        text_hits = sum(1 for v in vals if v and parse_number(v) is None)
        if numeric_hits >= max(1, text_hits):
            numeric_cols.append(col)
        else:
            text_cols.append(col)

    mapping = {}
    if text_cols:
        mapping["method"] = text_cols[0]
    if len(text_cols) >= 2:
        mapping["dataset"] = text_cols[1]
    elif len(cols) >= 2:
        mapping["dataset"] = cols[1]

    if numeric_cols:
        mapping["accuracy"] = numeric_cols[0]
    if len(numeric_cols) >= 2:
        mapping["f1"] = numeric_cols[1]

    remaining = [c for c in cols if c not in set(mapping.values())]
    if remaining:
        mapping["notes"] = remaining[-1]

    return mapping


def normalize_metrics(cells):
    mapping = header_mapping(cells)
    if not all(k in mapping for k in ("method", "dataset", "accuracy", "f1")):
        fallback = infer_mapping_from_values([c for c in cells if not c["is_header"]])
        for key, value in fallback.items():
            mapping.setdefault(key, value)

    matrix = rows_to_matrix(cells)
    metrics = []
    issues = []

    for row_id in sorted(matrix):
        row_cells = [c for c in cells if c["row_id"] == row_id]
        if row_cells and all(c["is_header"] for c in row_cells):
            continue

        row = matrix[row_id]
        method = row.get(mapping.get("method"), "").strip()
        dataset = row.get(mapping.get("dataset"), "").strip()
        acc_text = row.get(mapping.get("accuracy"), "").strip()
        f1_text = row.get(mapping.get("f1"), "").strip()
        notes = row.get(mapping.get("notes"), "").strip() if "notes" in mapping else ""

        accuracy = parse_number(acc_text)
        f1 = parse_number(f1_text)

        if not any([method, dataset, acc_text, f1_text, notes]):
            continue

        # Skip non-metric rows that survived table cropping.
        if accuracy is None and f1 is None and not method:
            issues.append(f"row {row_id}: skipped row without method or numeric metrics")
            continue

        if not method:
            issues.append(f"row {row_id}: missing method")
        if not dataset:
            issues.append(f"row {row_id}: missing dataset")
        if accuracy is None:
            issues.append(f"row {row_id}: accuracy is missing or non-numeric ({acc_text!r})")
        if f1 is None:
            issues.append(f"row {row_id}: f1 is missing or non-numeric ({f1_text!r})")

        if accuracy is not None and not (0 <= accuracy <= 100):
            issues.append(f"row {row_id}: accuracy outside expected 0-100 range ({accuracy})")
        if f1 is not None and not (0 <= f1 <= 100):
            issues.append(f"row {row_id}: f1 outside expected 0-100 range ({f1})")

        metrics.append(
            {
                "method": method,
                "dataset": dataset,
                "accuracy": "" if accuracy is None else format_number(accuracy),
                "f1": "" if f1 is None else format_number(f1),
                "notes": notes,
                "_row_id": row_id,
                "_f1_num": f1,
            }
        )

    if not mapping:
        issues.append("no usable header mapping found; used positional fallback")
    else:
        missing = [k for k in ("method", "dataset", "accuracy", "f1") if k not in mapping]
        if missing:
            issues.append("missing mapped columns: " + ", ".join(missing))

    public_metrics = [{k: m[k] for k in ("method", "dataset", "accuracy", "f1", "notes")} for m in metrics]
    return public_metrics, metrics, issues, mapping


def format_number(value):
    if value is None:
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def audit_metrics(public_metrics, internal_metrics, issues):
    best_by_dataset = {}
    grouped = defaultdict(list)

    for metric, internal in zip(public_metrics, internal_metrics):
        dataset = metric["dataset"] or "UNKNOWN"
        grouped[dataset].append((metric, internal.get("_f1_num")))

    for dataset, rows in sorted(grouped.items()):
        numeric = [(m, f1) for m, f1 in rows if f1 is not None]
        if not numeric:
            best_by_dataset[dataset] = None
            issues.append(f"dataset {dataset}: no numeric F1 values available")
            continue

        best_metric, best_f1 = max(numeric, key=lambda item: item[1])
        best_by_dataset[dataset] = {
            "method": best_metric["method"],
            "f1": format_number(best_f1),
            "accuracy": best_metric["accuracy"],
            "notes": best_metric["notes"],
        }

    return {
        "row_count": len(public_metrics),
        "best_by_dataset": best_by_dataset,
        "issues": issues,
    }


def write_cells_csv(path, cells):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["row_id", "col_id", "row_span", "col_span", "is_header", "text"],
        )
        writer.writeheader()
        for cell in cells:
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
    ensure_parent(path)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "dataset", "accuracy", "f1", "notes"])
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)


def write_audit_json(path, audit):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)


def write_summary(path, metrics, audit):
    ensure_parent(path)

    lines = [
        "# OCR Table Metric Extraction Summary",
        "",
        f"- Normalized metric rows: {audit['row_count']}",
        f"- Datasets found: {len(audit['best_by_dataset'])}",
        "",
        "## Best F1 by Dataset",
        "",
    ]

    if audit["best_by_dataset"]:
        lines.append("| Dataset | Best method | F1 | Accuracy | Notes |")
        lines.append("|---|---:|---:|---:|---|")
        for dataset, best in audit["best_by_dataset"].items():
            if best is None:
                lines.append(f"| {escape_md(dataset)} |  |  |  | No numeric F1 values available |")
            else:
                lines.append(
                    "| {dataset} | {method} | {f1} | {accuracy} | {notes} |".format(
                        dataset=escape_md(dataset),
                        method=escape_md(best.get("method", "")),
                        f1=escape_md(best.get("f1", "")),
                        accuracy=escape_md(best.get("accuracy", "")),
                        notes=escape_md(best.get("notes", "")),
                    )
                )
    else:
        lines.append("No dataset-level best method could be computed.")

    lines.extend(["", "## Audit Issues", ""])
    if audit["issues"]:
        for issue in audit["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- No extraction or validation issues found.")

    lines.extend(["", "## Extracted Metrics", ""])
    if metrics:
        lines.append("| Method | Dataset | Accuracy | F1 | Notes |")
        lines.append("|---|---|---:|---:|---|")
        for row in metrics:
            lines.append(
                "| {method} | {dataset} | {accuracy} | {f1} | {notes} |".format(
                    method=escape_md(row["method"]),
                    dataset=escape_md(row["dataset"]),
                    accuracy=escape_md(row["accuracy"]),
                    f1=escape_md(row["f1"]),
                    notes=escape_md(row["notes"]),
                )
            )
    else:
        lines.append("No metric rows were extracted.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def escape_md(value):
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def main():
    input_path = env_path("ORIGINAL_WORDS_JSON")
    cells_path = env_path("OUTPUT_CELLS_CSV")
    metrics_path = env_path("OUTPUT_METRICS_CSV")
    audit_path = env_path("OUTPUT_AUDIT_JSON")
    summary_path = env_path("SUMMARY_MD")

    data = load_json(input_path)
    all_words = extract_words(data)
    if not all_words:
        raise RuntimeError("No OCR words with bounding boxes were found in the input JSON.")

    table_bbox = infer_table_bbox(data, all_words)
    table_words = [w for w in all_words if point_inside(w["xc"], w["yc"], table_bbox)]

    if not table_words:
        raise RuntimeError("No OCR words fell inside the inferred/provided table bounding box.")

    rows = group_rows(table_words)
    edges = infer_column_edges(rows, table_bbox)
    cells = build_cells(rows, edges)

    metrics, internal_metrics, extraction_issues, _mapping = normalize_metrics(cells)
    audit = audit_metrics(metrics, internal_metrics, extraction_issues)

    write_cells_csv(cells_path, cells)
    write_metrics_csv(metrics_path, metrics)
    write_audit_json(audit_path, audit)
    write_summary(summary_path, metrics, audit)


if __name__ == "__main__":
    main()
