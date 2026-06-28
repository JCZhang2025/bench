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


def get_env_path(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def ensure_parent(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def first_present(mapping, keys, default=None):
    for key in keys:
        if isinstance(mapping, dict) and key in mapping:
            return mapping[key]
    return default


def normalize_bbox(raw):
    if raw is None:
        return None

    if isinstance(raw, dict):
        if all(k in raw for k in ("x0", "y0", "x1", "y1")):
            return [float(raw["x0"]), float(raw["y0"]), float(raw["x1"]), float(raw["y1"])]
        if all(k in raw for k in ("left", "top", "right", "bottom")):
            return [float(raw["left"]), float(raw["top"]), float(raw["right"]), float(raw["bottom"])]
        if all(k in raw for k in ("x", "y", "w", "h")):
            x, y, w, h = float(raw["x"]), float(raw["y"]), float(raw["w"]), float(raw["h"])
            return [x, y, x + w, y + h]
        if all(k in raw for k in ("x", "y", "width", "height")):
            x, y = float(raw["x"]), float(raw["y"])
            w, h = float(raw["width"]), float(raw["height"])
            return [x, y, x + w, y + h]

    if isinstance(raw, (list, tuple)) and len(raw) >= 4:
        vals = [float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3])]
        x0, y0, x1, y1 = vals
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        return [x0, y0, x1, y1]

    return None


def bbox_center(box):
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def bbox_union(boxes):
    xs0, ys0, xs1, ys1 = zip(*boxes)
    return [min(xs0), min(ys0), max(xs1), max(ys1)]


def bbox_intersects_or_inside(inner, outer, pad=0.5):
    cx, cy = bbox_center(inner)
    return (
        outer[0] - pad <= cx <= outer[2] + pad
        and outer[1] - pad <= cy <= outer[3] + pad
    )


def text_of_word(word):
    value = first_present(word, ["text", "token", "word", "value", "content", "str"], "")
    return str(value).strip()


def bbox_of_word(word):
    raw = first_present(word, ["bbox", "box", "bounding_box", "bounds"])
    box = normalize_bbox(raw)
    if box:
        return box

    keys = ("x0", "y0", "x1", "y1")
    if all(k in word for k in keys):
        return [float(word["x0"]), float(word["y0"]), float(word["x1"]), float(word["y1"])]

    keys = ("left", "top", "right", "bottom")
    if all(k in word for k in keys):
        return [float(word["left"]), float(word["top"]), float(word["right"]), float(word["bottom"])]

    return None


def find_table_bbox(data, words):
    candidates = []

    def visit(obj, key_hint=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                lower = str(key).lower()
                if "bbox" in lower or "box" in lower or "bounds" in lower:
                    box = normalize_bbox(value)
                    if box and ("table" in lower or key_hint == "table"):
                        candidates.append(box)
                if lower in ("table", "tables"):
                    visit(value, "table")
                elif lower not in ("words", "tokens"):
                    visit(value, key_hint)
        elif isinstance(obj, list):
            for item in obj:
                visit(item, key_hint)

    visit(data)

    if candidates:
        return max(candidates, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))

    table_like = first_present(data, ["table_bbox", "table_box", "table_bounds"])
    box = normalize_bbox(table_like)
    if box:
        return box

    word_boxes = [w["bbox"] for w in words]
    if not word_boxes:
        raise RuntimeError("No word boxes found and no table bounding box found.")
    return bbox_union(word_boxes)


def collect_words(data):
    candidates = []

    def maybe_word(obj):
        if not isinstance(obj, dict):
            return None
        txt = text_of_word(obj)
        box = bbox_of_word(obj)
        if txt and box:
            return {"text": txt, "bbox": box}
        return None

    def visit(obj):
        if isinstance(obj, dict):
            w = maybe_word(obj)
            if w:
                candidates.append(w)
                return
            for value in obj.values():
                visit(value)
        elif isinstance(obj, list):
            for item in obj:
                visit(item)

    for key in ("words", "page_words", "tokens", "ocr_words"):
        value = first_present(data, [key])
        if isinstance(value, list):
            for item in value:
                w = maybe_word(item)
                if w:
                    candidates.append(w)

    if not candidates:
        visit(data)

    seen = set()
    unique = []
    for w in candidates:
        key = (w["text"], tuple(round(v, 3) for v in w["bbox"]))
        if key not in seen:
            seen.add(key)
            unique.append(w)

    return unique


def median(values, default=1.0):
    vals = sorted(float(v) for v in values if v is not None)
    if not vals:
        return default
    n = len(vals)
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2.0


def group_words_into_lines(words):
    if not words:
        return []

    heights = [w["bbox"][3] - w["bbox"][1] for w in words]
    y_tol = max(2.0, median(heights) * 0.65)

    ordered = sorted(words, key=lambda w: (bbox_center(w["bbox"])[1], w["bbox"][0]))
    rows = []

    for word in ordered:
        cy = bbox_center(word["bbox"])[1]
        best_idx = None
        best_dist = None

        for idx, row in enumerate(rows):
            dist = abs(cy - row["cy"])
            if dist <= y_tol and (best_dist is None or dist < best_dist):
                best_idx = idx
                best_dist = dist

        if best_idx is None:
            rows.append({"words": [word], "cy": cy})
        else:
            row = rows[best_idx]
            row["words"].append(word)
            row["cy"] = sum(bbox_center(w["bbox"])[1] for w in row["words"]) / len(row["words"])

    rows.sort(key=lambda r: r["cy"])
    for row in rows:
        row["words"].sort(key=lambda w: w["bbox"][0])
        row["bbox"] = bbox_union([w["bbox"] for w in row["words"]])
        row["text"] = " ".join(w["text"] for w in row["words"])

    return rows


def cluster_x_columns(words, table_bbox):
    centers = sorted(bbox_center(w["bbox"])[0] for w in words)
    widths = [w["bbox"][2] - w["bbox"][0] for w in words]
    if not centers:
        return []

    x_tol = max(8.0, median(widths) * 1.2)
    clusters = []

    for x in centers:
        if not clusters or abs(x - clusters[-1]["center"]) > x_tol:
            clusters.append({"values": [x], "center": x})
        else:
            clusters[-1]["values"].append(x)
            clusters[-1]["center"] = sum(clusters[-1]["values"]) / len(clusters[-1]["values"])

    centers = [c["center"] for c in clusters]

    if len(centers) == 1:
        x0, x1 = table_bbox[0], table_bbox[2]
        return [{"id": 0, "left": x0, "right": x1, "center": centers[0]}]

    boundaries = [table_bbox[0]]
    for left, right in zip(centers, centers[1:]):
        boundaries.append((left + right) / 2.0)
    boundaries.append(table_bbox[2])

    columns = []
    for idx, center in enumerate(centers):
        columns.append(
            {
                "id": idx,
                "left": boundaries[idx],
                "right": boundaries[idx + 1],
                "center": center,
            }
        )
    return columns


def assign_col_id(word, columns):
    cx = bbox_center(word["bbox"])[0]
    for col in columns:
        if col["left"] <= cx <= col["right"]:
            return col["id"]
    return min(columns, key=lambda c: abs(cx - c["center"]))["id"]


def split_row_into_cells(row, columns):
    grouped = defaultdict(list)
    for word in row["words"]:
        grouped[assign_col_id(word, columns)].append(word)

    cells = []
    for col_id in sorted(grouped):
        ws = sorted(grouped[col_id], key=lambda w: w["bbox"][0])
        text = " ".join(w["text"] for w in ws).strip()
        if text:
            cells.append(
                {
                    "row_id": row["row_id"],
                    "col_id": col_id,
                    "bbox": bbox_union([w["bbox"] for w in ws]),
                    "text": text,
                    "row_span": 1,
                    "col_span": 1,
                    "is_header": False,
                }
            )
    return cells


def infer_header_rows(row_cells, n_cols):
    header_rows = set()
    saw_body = False

    for row_id in sorted(row_cells):
        cells = row_cells[row_id]
        texts = [c["text"] for c in cells]
        numeric_like = sum(1 for t in texts if parse_number(t) is not None or looks_metric_value(t))
        has_methodish_text = any(re.search(r"[A-Za-z]", t) for t in texts)
        has_many_values = numeric_like >= 2
        has_dataset_or_method = any(
            re.search(r"\b(method|model|dataset|data|accuracy|acc|f1|score|notes?)\b", t, re.I)
            for t in texts
        )

        if not saw_body and (has_dataset_or_method or not has_many_values):
            header_rows.add(row_id)
            continue

        if has_many_values and has_methodish_text:
            saw_body = True

    if not header_rows and row_cells:
        header_rows.add(min(row_cells))

    return header_rows


def infer_header_spans(all_cells, header_rows, columns):
    issues = []
    n_cols = len(columns)
    header_cells = [c for c in all_cells if c["row_id"] in header_rows]

    child_rows = sorted(header_rows)
    if not child_rows:
        return issues

    for cell in header_cells:
        cell["is_header"] = True

    by_row = defaultdict(list)
    for cell in header_cells:
        by_row[cell["row_id"]].append(cell)

    for row_id in child_rows:
        by_row[row_id].sort(key=lambda c: c["col_id"])

    for row_id in child_rows[:-1]:
        lower_cells = []
        for lower_row in child_rows:
            if lower_row > row_id:
                lower_cells.extend(by_row[lower_row])

        for cell in by_row[row_id]:
            x0, _, x1, _ = cell["bbox"]
            covered = []
            for col in columns:
                overlap = max(0.0, min(x1, col["right"]) - max(x0, col["left"]))
                width = max(1e-6, col["right"] - col["left"])
                if overlap / width >= 0.25 or (x0 <= col["center"] <= x1):
                    covered.append(col["id"])

            if len(covered) > 1:
                cell["col_id"] = min(covered)
                cell["col_span"] = len(covered)
            else:
                cell["col_span"] = 1

            has_child_under = any(
                lc["col_id"] >= cell["col_id"]
                and lc["col_id"] < cell["col_id"] + cell["col_span"]
                for lc in lower_cells
            )
            if not has_child_under and len(child_rows) > 1:
                cell["row_span"] = max(1, max(child_rows) - row_id + 1)

    occupied = defaultdict(set)
    for cell in header_cells:
        for r in range(cell["row_id"], cell["row_id"] + cell["row_span"]):
            for c in range(cell["col_id"], min(n_cols, cell["col_id"] + cell["col_span"])):
                key = (r, c)
                if key in occupied[r]:
                    issues.append(
                        f"Ambiguous header overlap near row {r}, column {c}; conservative spans retained."
                    )
                occupied[r].add(c)

    return issues


def parse_number(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    text = text.replace("\u2212", "-")
    text = re.sub(r"[, ]", "", text)
    text = re.sub(r"^[^\d.+-]+", "", text)
    text = re.sub(r"[^\d.%+-]+$", "", text)

    percent = text.endswith("%")
    if percent:
        text = text[:-1]

    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", text)
    if not match:
        return None

    try:
        num = float(match.group(0))
    except ValueError:
        return None

    if percent:
        num = num / 100.0 if num > 1 else num
    return num


def looks_metric_value(text):
    return parse_number(text) is not None


def normalize_header(text):
    t = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    if re.search(r"\b(method|model|approach|system)\b", t):
        return "method"
    if re.search(r"\b(dataset|data set|corpus|benchmark|split)\b", t):
        return "dataset"
    if re.search(r"\b(acc|accuracy)\b", t):
        return "accuracy"
    if re.search(r"\bf\s*1\b|\bf1\b|f score|f measure", t):
        return "f1"
    if re.search(r"\b(note|notes|remark|comment|setting|variant)\b", t):
        return "notes"
    return None


def build_column_roles(row_cells, header_rows, n_cols):
    roles = {}
    header_text_by_col = defaultdict(list)

    for row_id in header_rows:
        for cell in row_cells.get(row_id, []):
            for col_id in range(cell["col_id"], min(n_cols, cell["col_id"] + cell.get("col_span", 1))):
                header_text_by_col[col_id].append(cell["text"])

    for col_id in range(n_cols):
        text = " ".join(header_text_by_col[col_id])
        role = normalize_header(text)
        if role:
            roles[col_id] = role

    missing = [field for field in ("method", "dataset", "accuracy", "f1", "notes") if field not in roles.values()]
    if missing:
        unresolved = [c for c in range(n_cols) if c not in roles]
        for field, col_id in zip(missing, unresolved):
            roles[col_id] = field

    return roles


def clean_text(text):
    return re.sub(r"\s+", " ", str(text or "").strip())


def extract_metrics(row_cells, header_rows, n_cols):
    roles = build_column_roles(row_cells, header_rows, n_cols)
    metrics = []
    issues = []

    for row_id in sorted(row_cells):
        if row_id in header_rows:
            continue

        record = {"method": "", "dataset": "", "accuracy": "", "f1": "", "notes": ""}
        for cell in row_cells[row_id]:
            role = roles.get(cell["col_id"])
            if not role:
                continue
            value = clean_text(cell["text"])
            if role in ("accuracy", "f1"):
                num = parse_number(value)
                if num is None:
                    issues.append(f"Row {row_id}: could not parse {role} value from '{value}'.")
                    record[role] = value
                else:
                    record[role] = format_number(num)
            elif role in record:
                record[role] = value

        if any(record.values()):
            if not record["method"]:
                issues.append(f"Row {row_id}: missing method.")
            if not record["dataset"]:
                issues.append(f"Row {row_id}: missing dataset.")
            for metric_name in ("accuracy", "f1"):
                if record[metric_name] == "":
                    issues.append(f"Row {row_id}: missing {metric_name}.")
                elif parse_number(record[metric_name]) is None:
                    issues.append(f"Row {row_id}: invalid {metric_name} value '{record[metric_name]}'.")
            metrics.append(record)

    return metrics, issues


def format_number(num):
    if num is None:
        return ""
    if math.isfinite(num):
        return f"{num:.6g}"
    return str(num)


def compute_best_by_dataset(metrics):
    best = {}
    for row in metrics:
        dataset = row.get("dataset", "").strip()
        f1 = parse_number(row.get("f1"))
        if not dataset or f1 is None:
            continue
        current = best.get(dataset)
        if current is None or f1 > current["f1"]:
            best[dataset] = {
                "method": row.get("method", ""),
                "f1": f1,
                "accuracy": parse_number(row.get("accuracy")),
            }

    return {
        dataset: {
            "method": item["method"],
            "f1": format_number(item["f1"]),
            "accuracy": format_number(item["accuracy"]) if item["accuracy"] is not None else "",
        }
        for dataset, item in sorted(best.items())
    }


def write_cells_csv(path, cells):
    ensure_parent(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["row_id", "col_id", "row_span", "col_span", "is_header", "text"],
        )
        writer.writeheader()
        for c in sorted(cells, key=lambda x: (x["row_id"], x["col_id"], x["text"])):
            writer.writerow(
                {
                    "row_id": c["row_id"],
                    "col_id": c["col_id"],
                    "row_span": c.get("row_span", 1),
                    "col_span": c.get("col_span", 1),
                    "is_header": str(bool(c.get("is_header"))).lower(),
                    "text": c["text"],
                }
            )


def write_metrics_csv(path, metrics):
    ensure_parent(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "dataset", "accuracy", "f1", "notes"])
        writer.writeheader()
        for row in metrics:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})


def write_audit_json(path, audit):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)


def write_summary_md(path, metrics, audit):
    ensure_parent(path)

    best_lines = []
    for dataset, item in audit["best_by_dataset"].items():
        best_lines.append(
            f"- **{dataset}**: {item['method']} with F1 `{item['f1']}`"
            + (f" and accuracy `{item['accuracy']}`." if item.get("accuracy") else ".")
        )

    issue_lines = audit.get("issues") or ["No extraction or validation issues were detected."]

    lines = [
        "# Extracted Table Metrics",
        "",
        f"Normalized metric rows: **{audit['row_count']}**.",
        "",
        "## Best Method By Dataset",
        "",
        *(best_lines or ["No valid F1 scores were available to rank methods by dataset."]),
        "",
        "## Audit Notes",
        "",
        *[f"- {issue}" for issue in issue_lines],
        "",
    ]

    if metrics:
        lines.extend(
            [
                "## Normalized Metrics",
                "",
                "| Method | Dataset | Accuracy | F1 | Notes |",
                "|---|---|---:|---:|---|",
            ]
        )
        for row in metrics:
            lines.append(
                "| {method} | {dataset} | {accuracy} | {f1} | {notes} |".format(
                    method=escape_md(row.get("method", "")),
                    dataset=escape_md(row.get("dataset", "")),
                    accuracy=escape_md(row.get("accuracy", "")),
                    f1=escape_md(row.get("f1", "")),
                    notes=escape_md(row.get("notes", "")),
                )
            )
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def escape_md(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def reconstruct_table(data):
    all_words = collect_words(data)
    table_bbox = find_table_bbox(data, all_words)

    table_words = [
        w for w in all_words
        if bbox_intersects_or_inside(w["bbox"], table_bbox)
    ]

    issues = []
    outside_count = len(all_words) - len(table_words)
    if outside_count:
        issues.append(f"Excluded {outside_count} caption/footnote or out-of-table word(s) outside the table bounding box.")

    if not table_words:
        raise RuntimeError("No OCR words were found inside the table bounding box.")

    rows = group_words_into_lines(table_words)
    for idx, row in enumerate(rows):
        row["row_id"] = idx

    columns = cluster_x_columns(table_words, table_bbox)
    if not columns:
        raise RuntimeError("Could not infer table columns from word positions.")

    all_cells = []
    row_cells = defaultdict(list)

    for row in rows:
        cells = split_row_into_cells(row, columns)
        all_cells.extend(cells)
        row_cells[row["row_id"]].extend(cells)

    header_rows = infer_header_rows(row_cells, len(columns))
    span_issues = infer_header_spans(all_cells, header_rows, columns)
    issues.extend(span_issues)

    return all_cells, row_cells, header_rows, len(columns), issues


def main():
    paths = {name: get_env_path(name) for name in REQUIRED_ENV}

    with open(paths["ORIGINAL_WORDS_JSON"], "r", encoding="utf-8") as f:
        data = json.load(f)

    cells, row_cells, header_rows, n_cols, reconstruction_issues = reconstruct_table(data)
    metrics, metric_issues = extract_metrics(row_cells, header_rows, n_cols)
    best_by_dataset = compute_best_by_dataset(metrics)

    audit = {
        "row_count": len(metrics),
        "best_by_dataset": best_by_dataset,
        "issues": reconstruction_issues + metric_issues,
    }

    write_cells_csv(paths["OUTPUT_CELLS_CSV"], cells)
    write_metrics_csv(paths["OUTPUT_METRICS_CSV"], metrics)
    write_audit_json(paths["OUTPUT_AUDIT_JSON"], audit)
    write_summary_md(paths["SUMMARY_MD"], metrics, audit)


if __name__ == "__main__":
    main()
