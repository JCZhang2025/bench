import csv
import json
import os
import re
from collections import defaultdict


ORIGINAL_WORDS_JSON = os.environ["ORIGINAL_WORDS_JSON"]
OUTPUT_CELLS_CSV = os.environ["OUTPUT_CELLS_CSV"]
OUTPUT_METRICS_CSV = os.environ["OUTPUT_METRICS_CSV"]
OUTPUT_AUDIT_JSON = os.environ["OUTPUT_AUDIT_JSON"]
SUMMARY_MD = os.environ["SUMMARY_MD"]


def ensure_parent(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def as_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def norm_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def bbox_from_any(obj):
    if obj is None:
        return None

    if isinstance(obj, dict):
        for key in ("bbox", "bounding_box", "box"):
            if key in obj:
                return bbox_from_any(obj[key])

        keys1 = ("x0", "y0", "x1", "y1")
        if all(k in obj for k in keys1):
            return [float(obj["x0"]), float(obj["y0"]), float(obj["x1"]), float(obj["y1"])]

        keys2 = ("left", "top", "right", "bottom")
        if all(k in obj for k in keys2):
            return [float(obj["left"]), float(obj["top"]), float(obj["right"]), float(obj["bottom"])]

        if all(k in obj for k in ("x", "y", "w", "h")):
            x, y, w, h = float(obj["x"]), float(obj["y"]), float(obj["w"]), float(obj["h"])
            return [x, y, x + w, y + h]

        if all(k in obj for k in ("x", "y", "width", "height")):
            x, y = float(obj["x"]), float(obj["y"])
            return [x, y, x + float(obj["width"]), y + float(obj["height"])]

    if isinstance(obj, (list, tuple)) and len(obj) >= 4:
        vals = [float(v) for v in obj[:4]]
        x0, y0, a, b = vals
        if a > x0 and b > y0:
            return [x0, y0, a, b]
        return [x0, y0, x0 + a, y0 + b]

    return None


def bbox_union(boxes):
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]


def bbox_center(b):
    return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)


def bbox_height(b):
    return max(0.0, b[3] - b[1])


def bbox_width(b):
    return max(0.0, b[2] - b[0])


def inside(inner, outer, pad=0.0):
    cx, cy = bbox_center(inner)
    return (
        outer[0] - pad <= cx <= outer[2] + pad
        and outer[1] - pad <= cy <= outer[3] + pad
    )


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_words(node):
    candidates = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            text = None
            for key in ("text", "token", "word", "value", "content"):
                if key in obj and isinstance(obj[key], (str, int, float)):
                    text = str(obj[key])
                    break

            box = bbox_from_any(obj)
            if text is not None and box is not None:
                candidates.append({"text": norm_text(text), "bbox": box, "path": path})

            for k, v in obj.items():
                walk(v, f"{path}.{k}" if path else str(k))

        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")

    walk(node)
    return [w for w in candidates if w["text"]]


def find_table_bbox(data, words):
    direct_keys = (
        "table_bbox",
        "table_bounding_box",
        "table_box",
        "bbox",
        "bounding_box",
        "box",
    )

    if isinstance(data, dict):
        for key in direct_keys:
            if key in data:
                box = bbox_from_any(data[key])
                if box and bbox_width(box) > 0 and bbox_height(box) > 0:
                    return box

        table_like = []
        stack = [data]
        while stack:
            obj = stack.pop()
            if isinstance(obj, dict):
                label = " ".join(str(k).lower() for k in obj.keys())
                if "table" in label:
                    box = bbox_from_any(obj)
                    if box and bbox_width(box) > 0 and bbox_height(box) > 0:
                        table_like.append(box)
                stack.extend(obj.values())
            elif isinstance(obj, list):
                stack.extend(obj)

        if table_like:
            return max(table_like, key=lambda b: bbox_width(b) * bbox_height(b))

    return bbox_union([w["bbox"] for w in words])


def median(vals, default=0.0):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return default
    n = len(vals)
    mid = n // 2
    if n % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def cluster_words_into_rows(words):
    if not words:
        return []

    heights = [bbox_height(w["bbox"]) for w in words]
    y_tol = max(3.0, median(heights, 8.0) * 0.65)

    sorted_words = sorted(words, key=lambda w: (bbox_center(w["bbox"])[1], w["bbox"][0]))
    rows = []

    for word in sorted_words:
        cy = bbox_center(word["bbox"])[1]
        best = None
        best_dist = None
        for row in rows:
            dist = abs(cy - row["cy"])
            if dist <= y_tol and (best_dist is None or dist < best_dist):
                best = row
                best_dist = dist

        if best is None:
            rows.append({"cy": cy, "words": [word]})
        else:
            best["words"].append(word)
            best["cy"] = median([bbox_center(w["bbox"])[1] for w in best["words"]])

    for row in rows:
        row["words"].sort(key=lambda w: w["bbox"][0])
        row["bbox"] = bbox_union([w["bbox"] for w in row["words"]])
        row["text"] = " ".join(w["text"] for w in row["words"])

    rows.sort(key=lambda r: r["cy"])
    return rows


def split_row_into_segments(row_words):
    if not row_words:
        return []

    row_words = sorted(row_words, key=lambda w: w["bbox"][0])
    widths = [bbox_width(w["bbox"]) for w in row_words]
    gaps = [
        row_words[i + 1]["bbox"][0] - row_words[i]["bbox"][2]
        for i in range(len(row_words) - 1)
    ]
    positive_gaps = [g for g in gaps if g > 0]
    gap_med = median(positive_gaps, 0.0)
    width_med = median(widths, 8.0)

    threshold = max(width_med * 1.2, gap_med * 2.4, 10.0)

    segments = []
    current = [row_words[0]]

    for i, gap in enumerate(gaps):
        if gap > threshold:
            segments.append(current)
            current = [row_words[i + 1]]
        else:
            current.append(row_words[i + 1])

    segments.append(current)

    out = []
    for seg in segments:
        box = bbox_union([w["bbox"] for w in seg])
        out.append({
            "text": " ".join(w["text"] for w in seg),
            "bbox": box,
            "cx": bbox_center(box)[0],
            "words": seg,
        })
    return out


def infer_column_centers(row_segments):
    points = []
    for segs in row_segments:
        for seg in segs:
            points.append(seg["cx"])

    if not points:
        return []

    points = sorted(points)
    if len(points) == 1:
        return points

    gaps = [points[i + 1] - points[i] for i in range(len(points) - 1)]
    positive = [g for g in gaps if g > 0]
    gap_med = median(positive, 20.0)
    tol = max(12.0, gap_med * 0.45)

    clusters = []
    for x in points:
        if not clusters or abs(x - clusters[-1]["center"]) > tol:
            clusters.append({"values": [x], "center": x})
        else:
            clusters[-1]["values"].append(x)
            clusters[-1]["center"] = median(clusters[-1]["values"])

    centers = [c["center"] for c in clusters]

    # If over-splitting occurred because multi-word cells were fragmented, favor
    # rows with the richest repeated structure as the column count anchor.
    counts = defaultdict(int)
    for segs in row_segments:
        counts[len(segs)] += 1
    if counts:
        likely_count = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
        if 1 < likely_count < len(centers):
            candidate_rows = [segs for segs in row_segments if len(segs) == likely_count]
            if candidate_rows:
                centers = []
                for col_index in range(likely_count):
                    vals = [segs[col_index]["cx"] for segs in candidate_rows]
                    centers.append(median(vals))

    return sorted(centers)


def nearest_col(cx, centers):
    if not centers:
        return 0
    return min(range(len(centers)), key=lambda i: abs(cx - centers[i]))


def column_boundaries(centers, table_bbox):
    if not centers:
        return [table_bbox[0], table_bbox[2]]

    bounds = [table_bbox[0]]
    for i in range(len(centers) - 1):
        bounds.append((centers[i] + centers[i + 1]) / 2.0)
    bounds.append(table_bbox[2])
    return bounds


def build_cells(rows, table_bbox):
    row_segments = [split_row_into_segments(r["words"]) for r in rows]
    centers = infer_column_centers(row_segments)
    if not centers:
        centers = [bbox_center(table_bbox)[0]]

    bounds = column_boundaries(centers, table_bbox)
    cells = []

    for row_id, (row, segs) in enumerate(zip(rows, row_segments)):
        used_cols = []
        for seg in segs:
            left, right = seg["bbox"][0], seg["bbox"][2]
            covered = [
                i for i in range(len(centers))
                if right >= bounds[i] and left <= bounds[i + 1]
            ]

            if not covered:
                covered = [nearest_col(seg["cx"], centers)]

            col_id = min(covered)
            col_span = max(covered) - col_id + 1

            # Very wide header/title cells often span across inferred columns.
            width_ratio = bbox_width(seg["bbox"]) / max(1.0, bbox_width(table_bbox))
            if len(segs) == 1 and len(centers) > 1 and width_ratio > 0.55:
                col_id = 0
                col_span = len(centers)

            used_cols.extend(range(col_id, col_id + col_span))
            cells.append({
                "row_id": row_id,
                "col_id": col_id,
                "row_span": 1,
                "col_span": col_span,
                "is_header": False,
                "text": norm_text(seg["text"]),
                "bbox": seg["bbox"],
            })

    infer_headers(cells, len(rows))
    infer_row_spans(cells)
    return sorted(cells, key=lambda c: (c["row_id"], c["col_id"]))


def text_has_metric_header(text):
    t = text.lower()
    return bool(re.search(r"\b(acc|accuracy|f1|f-1|score|dataset|method|model)\b", t))


def infer_headers(cells, n_rows):
    metric_header_rows = set()
    for c in cells:
        if text_has_metric_header(c["text"]):
            metric_header_rows.add(c["row_id"])

    if metric_header_rows:
        max_header_row = max(r for r in metric_header_rows if r <= min(n_rows - 1, 3))
        for c in cells:
            if c["row_id"] <= max_header_row:
                c["is_header"] = True
    else:
        for c in cells:
            if c["row_id"] == 0:
                c["is_header"] = True


def infer_row_spans(cells):
    by_col = defaultdict(list)
    for c in cells:
        by_col[c["col_id"]].append(c)

    for col_cells in by_col.values():
        col_cells.sort(key=lambda c: c["row_id"])
        for i, c in enumerate(col_cells):
            c["row_span"] = 1
            if i + 1 >= len(col_cells):
                continue

            next_c = col_cells[i + 1]
            gap = next_c["row_id"] - c["row_id"]
            if gap > 1:
                c["row_span"] = gap


def write_cells_csv(cells, path):
    ensure_parent(path)
    fields = ["row_id", "col_id", "row_span", "col_span", "is_header", "text"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in cells:
            writer.writerow({k: c[k] for k in fields})


def normalize_header(text):
    t = norm_text(text).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()

    if re.search(r"\b(method|model|approach|system)\b", t):
        return "method"
    if re.search(r"\b(dataset|data set|benchmark|corpus|test set)\b", t):
        return "dataset"
    if re.search(r"\b(acc|accuracy)\b", t):
        return "accuracy"
    if re.search(r"\bf\s*1\b|\bf1\b|f score|f measure", t):
        return "f1"
    if re.search(r"\b(note|notes|comment|setting|variant|remark)\b", t):
        return "notes"
    return None


def parse_number(text):
    if text is None:
        return None

    s = str(text).strip()
    if not s:
        return None

    match = re.search(r"[-+]?\d+(?:\.\d+)?", s.replace(",", ""))
    if not match:
        return None

    value = float(match.group(0))
    return value


def format_number(value):
    if value is None:
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def cell_grid(cells):
    grid = defaultdict(dict)
    for c in cells:
        for dc in range(c["col_span"]):
            grid[c["row_id"]][c["col_id"] + dc] = c
    return grid


def extract_metrics(cells):
    issues = []
    grid = cell_grid(cells)
    all_rows = sorted(grid.keys())
    if not all_rows:
        return [], ["No table rows were reconstructed."]

    header_rows = sorted({c["row_id"] for c in cells if c["is_header"]})
    candidate_header_rows = header_rows or all_rows[:1]

    header_map = {}
    header_row_id = None

    for r in reversed(candidate_header_rows):
        row = grid.get(r, {})
        local = {}
        for col, cell in row.items():
            field = normalize_header(cell["text"])
            if field and field not in local:
                local[field] = col

        if {"method", "dataset", "accuracy", "f1"}.issubset(local.keys()):
            header_map = local
            header_row_id = r
            break

    if not header_map:
        for r in all_rows:
            row = grid.get(r, {})
            local = {}
            for col, cell in row.items():
                field = normalize_header(cell["text"])
                if field and field not in local:
                    local[field] = col

            if len(set(local) & {"method", "dataset", "accuracy", "f1"}) >= 3:
                header_map = local
                header_row_id = r
                break

    if not header_map:
        issues.append("Could not identify a complete metric header row; used positional fallback.")
        max_cols = max((max(row.keys()) for row in grid.values() if row), default=4) + 1
        defaults = ["method", "dataset", "accuracy", "f1", "notes"]
        header_map = {field: i for i, field in enumerate(defaults[:max_cols])}
        header_row_id = all_rows[0] - 1

    missing = [f for f in ("method", "dataset", "accuracy", "f1") if f not in header_map]
    if missing:
        issues.append("Missing expected metric columns: " + ", ".join(missing))

    data_rows = [r for r in all_rows if header_row_id is None or r > header_row_id]
    metrics = []

    last_method = ""
    last_dataset = ""

    for r in data_rows:
        row = grid.get(r, {})

        raw = {}
        for field in ("method", "dataset", "accuracy", "f1", "notes"):
            col = header_map.get(field)
            text = ""
            if col is not None and col in row:
                text = row[col]["text"]
            raw[field] = norm_text(text)

        if raw["method"]:
            last_method = raw["method"]
        elif last_method:
            raw["method"] = last_method

        if raw["dataset"]:
            last_dataset = raw["dataset"]
        elif last_dataset:
            raw["dataset"] = last_dataset

        if not any(raw.values()):
            continue

        acc_value = parse_number(raw["accuracy"])
        f1_value = parse_number(raw["f1"])

        if not raw["method"] and not raw["dataset"]:
            joined = " ".join(c["text"] for c in row.values())
            if re.search(r"(caption|note|source|footnote)", joined, re.I):
                continue

        if acc_value is None and f1_value is None:
            joined = " ".join(raw.values()).strip()
            if joined:
                issues.append(f"Skipped non-metric row {r}: {joined}")
            continue

        if not raw["method"]:
            issues.append(f"Metric row {r} has no method value.")
        if not raw["dataset"]:
            issues.append(f"Metric row {r} has no dataset value.")
        if acc_value is None:
            issues.append(f"Metric row {r} has invalid accuracy value: {raw['accuracy']!r}.")
        if f1_value is None:
            issues.append(f"Metric row {r} has invalid F1 value: {raw['f1']!r}.")

        for field, value in (("accuracy", acc_value), ("f1", f1_value)):
            if value is not None and not (0 <= value <= 100):
                issues.append(f"Metric row {r} {field} value is outside expected 0-100 range: {value}.")

        metric = {
            "method": raw["method"],
            "dataset": raw["dataset"],
            "accuracy": format_number(acc_value),
            "f1": format_number(f1_value),
            "notes": raw["notes"],
            "_f1_value": f1_value,
            "_accuracy_value": acc_value,
        }
        metrics.append(metric)

    return metrics, issues


def write_metrics_csv(metrics, path):
    ensure_parent(path)
    fields = ["method", "dataset", "accuracy", "f1", "notes"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in metrics:
            writer.writerow({k: row.get(k, "") for k in fields})


def build_audit(metrics, issues):
    best = {}

    for row in metrics:
        dataset = row.get("dataset") or ""
        f1 = row.get("_f1_value")
        if not dataset or f1 is None:
            continue

        current = best.get(dataset)
        if current is None or f1 > current["f1"]:
            best[dataset] = {
                "method": row.get("method", ""),
                "f1": f1,
                "accuracy": row.get("_accuracy_value"),
            }

    best_by_dataset = {}
    for dataset, row in sorted(best.items()):
        best_by_dataset[dataset] = {
            "method": row["method"],
            "f1": row["f1"],
            "accuracy": row["accuracy"],
        }

    return {
        "row_count": len(metrics),
        "best_by_dataset": best_by_dataset,
        "issues": issues,
    }


def write_audit_json(audit, path):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_summary(metrics, audit, path):
    ensure_parent(path)

    lines = [
        "# OCR Table Extraction Summary",
        "",
        f"Extracted {audit['row_count']} normalized metric rows from the table.",
        "",
    ]

    if audit["best_by_dataset"]:
        lines.append("## Best F1 by Dataset")
        lines.append("")
        for dataset, info in audit["best_by_dataset"].items():
            f1 = format_number(info.get("f1"))
            acc = format_number(info.get("accuracy"))
            acc_text = f", accuracy {acc}" if acc else ""
            lines.append(f"- **{dataset}**: {info.get('method', '')} with F1 {f1}{acc_text}.")
        lines.append("")

    if metrics:
        lines.append("## Extracted Metrics")
        lines.append("")
        lines.append("| Method | Dataset | Accuracy | F1 | Notes |")
        lines.append("|---|---|---:|---:|---|")
        for row in metrics:
            lines.append(
                "| {method} | {dataset} | {accuracy} | {f1} | {notes} |".format(
                    method=row.get("method", "").replace("|", "\\|"),
                    dataset=row.get("dataset", "").replace("|", "\\|"),
                    accuracy=row.get("accuracy", ""),
                    f1=row.get("f1", ""),
                    notes=row.get("notes", "").replace("|", "\\|"),
                )
            )
        lines.append("")

    lines.append("## Audit")
    lines.append("")
    if audit["issues"]:
        for issue in audit["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- No extraction or validation issues were detected.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main():
    data = load_json(ORIGINAL_WORDS_JSON)
    words = find_words(data)

    if not words:
        table_bbox = [0.0, 0.0, 0.0, 0.0]
        table_words = []
    else:
        table_bbox = find_table_bbox(data, words)
        pad = max(2.0, median([bbox_height(w["bbox"]) for w in words], 8.0) * 0.25)
        table_words = [w for w in words if inside(w["bbox"], table_bbox, pad=pad)]

    rows = cluster_words_into_rows(table_words)
    cells = build_cells(rows, table_bbox) if rows else []

    metrics, issues = extract_metrics(cells)
    if not table_words:
        issues.append("No words were found inside the table bounding box.")
    if not cells:
        issues.append("No non-empty table cells were reconstructed.")

    audit = build_audit(metrics, issues)

    write_cells_csv(cells, OUTPUT_CELLS_CSV)
    write_metrics_csv(metrics, OUTPUT_METRICS_CSV)
    write_audit_json(audit, OUTPUT_AUDIT_JSON)
    write_summary(metrics, audit, SUMMARY_MD)


if __name__ == "__main__":
    main()
