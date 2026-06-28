#!/usr/bin/env python3
import os, json, csv, re
from collections import defaultdict

INPUT = os.environ["ORIGINAL_WORDS_JSON"]
CELLS_CSV = os.environ["OUTPUT_CELLS_CSV"]
METRICS_CSV = os.environ["OUTPUT_METRICS_CSV"]
AUDIT_JSON = os.environ["OUTPUT_AUDIT_JSON"]
SUMMARY_MD = os.environ["SUMMARY_MD"]

def load_words(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        words = data.get("words") or data.get("page_words") or data.get("word_boxes") or []
        table_bbox = data.get("table_bbox") or data.get("table_bbox") or data.get("bbox")
    elif isinstance(data, list):
        words = data
        table_bbox = None
    else:
        words = []
        table_bbox = None
    return words, table_bbox

def get_bbox(w):
    for key in ("bbox", "bounding_box", "box"):
        if isinstance(w, dict) and key in w:
            return w[key]
    return None

def get_text(w):
    if isinstance(w, dict):
        return str(w.get("text", w.get("word", w.get("content", ""))))
    return str(w)

def bbox_vals(bbox):
    if isinstance(bbox, dict):
        x0 = bbox.get("x0", bbox.get("left", bbox.get("x", 0)))
        y0 = bbox.get("y0", bbox.get("top", bbox.get("y", 0)))
        x1 = bbox.get("x1", bbox.get("right", bbox.get("x0", 0) + bbox.get("width", 0)))
        y1 = bbox.get("y1", bbox.get("bottom", bbox.get("y0", 0) + bbox.get("height", 0)))
        return float(x0), float(y0), float(x1), float(y1)
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
    return 0.0, 0.0, 0.0, 0.0

def inside_table(bbox, table_bbox):
    if table_bbox is None:
        return True
    tx0, ty0, tx1, ty1 = bbox_vals(table_bbox)
    x0, y0, x1, y1 = bbox_vals(bbox)
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    return (tx0 <= cx <= tx1) and (ty0 <= cy <= ty1)

def cluster(values, tol):
    if not values:
        return []
    vals = sorted(values)
    clusters = [[vals[0]]]
    for v in vals[1:]:
        if v - clusters[-1][-1] <= tol:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [sum(c)/len(c) for c in clusters]

def reconstruct(words, table_bbox):
    inside = []
    for w in words:
        bbox = get_bbox(w)
        if bbox is None:
            continue
        if not inside_table(bbox, table_bbox):
            continue
        x0, y0, x1, y1 = bbox_vals(bbox)
        text = get_text(w).strip()
        if not text:
            continue
        inside.append({"text": text, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                       "cx": (x0+x1)/2, "cy": (y0+y1)/2})
    if not inside:
        return [], []
    ys = [w["y0"] for w in inside]
    y_range = max(ys) - min(ys) if len(ys) > 1 else 1.0
    row_tol = max(8.0, y_range * 0.06)
    row_centers = cluster([w["cy"] for w in inside], row_tol)
    row_centers.sort()
    row_map = {}
    for i, rc in enumerate(row_centers):
        for w in inside:
            if abs(w["cy"] - rc) <= row_tol:
                row_map[id(w)] = i
    xs = [w["x0"] for w in inside]
    x_range = max(xs) - min(xs) if len(xs) > 1 else 1.0
    col_tol = max(8.0, x_range * 0.06)
    col_centers = cluster([w["cx"] for w in inside], col_tol)
    col_centers.sort()
    col_map = {}
    for j, cc in enumerate(col_centers):
        for w in inside:
            if abs(w["cx"] - cc) <= col_tol:
                col_map[id(w)] = j
    grid = defaultdict(list)
    for w in inside:
        r = row_map.get(id(w), 0)
        c = col_map.get(id(w), 0)
        grid[(r, c)].append(w)
    cells = []
    for (r, c), ws in sorted(grid.items()):
        ws_sorted = sorted(ws, key=lambda w: w["x0"])
        text = " ".join(w["text"] for w in ws_sorted)
        cells.append({"row_id": r, "col_id": c, "row_span": 1, "col_span": 1,
                      "is_header": 1 if r == 0 else 0, "text": text})
    return cells, row_centers

def parse_number(s):
    s2 = s.strip().replace("%", "")
    s2 = re.sub(r"[^0-9.\-]", "", s2)
    if s2 in ("", "-", ".", "-."):
        return None
    try:
        return float(s2)
    except ValueError:
        return None

def normalize_metrics(cells):
    if not cells:
        return []
    max_row = max(c["row_id"] for c in cells)
    max_col = max(c["col_id"] for c in cells)
    grid = {}
    for c in cells:
        grid[(c["row_id"], c["col_id"])] = c["text"]
    header_texts = [grid.get((0, j), "").strip().lower() for j in range(max_col+1)]
    col_idx = {}
    for j, h in enumerate(header_texts):
        if "method" in h or "model" in h or "approach" in h:
            col_idx["method"] = j
        elif "dataset" in h or "data" in h or "corpus" in h:
            col_idx["dataset"] = j
        elif "acc" in h:
            col_idx["accuracy"] = j
        elif h in ("f1", "f1-score", "f1 score") or "f1" in h:
            col_idx["f1"] = j
        elif "note" in h or "remark" in h or "comment" in h:
            col_idx["notes"] = j
    if "method" not in col_idx:
        col_idx["method"] = 0
    if "dataset" not in col_idx:
        col_idx["dataset"] = 1
    if "accuracy" not in col_idx:
        for j, h in enumerate(header_texts):
            if j not in col_idx.values() and h:
                col_idx["accuracy"] = j
                break
    if "f1" not in col_idx:
        for j in range(max_col+1):
            if j not in col_idx.values():
                col_idx["f1"] = j
                break
    metrics = []
    for r in range(1, max_row+1):
        method = grid.get((r, col_idx.get("method", 0)), "").strip()
        dataset = grid.get((r, col_idx.get("dataset", 1)), "").strip()
        acc_raw = grid.get((r, col_idx.get("accuracy", 2)), "").strip()
        f1_raw = grid.get((r, col_idx.get("f1", 3)), "").strip()
        notes = grid.get((r, col_idx.get("notes", -1)), "").strip() if "notes" in col_idx else ""
        if not method and not dataset and not acc_raw and not f1_raw:
            continue
        acc = parse_number(acc_raw)
        f1 = parse_number(f1_raw)
        metrics.append({
            "method": method or "unknown",
            "dataset": dataset or "unknown",
            "accuracy": "" if acc is None else f"{acc:.4f}",
            "f1": "" if f1 is None else f"{f1:.4f}",
            "notes": notes
        })
    return metrics

def audit_metrics(metrics):
    issues = []
    by_ds = defaultdict(list)
    for m in metrics:
        by_ds[m["dataset"]].append(m)
        if not m["method"] or m["method"] == "unknown":
            issues.append({"type": "MISSING_METHOD", "detail": "Row has no method name"})
        if not m["dataset"] or m["dataset"] == "unknown":
            issues.append({"type": "MISSING_DATASET", "detail": "Row has no dataset name"})
        if m["accuracy"] == "":
            issues.append({"type": "MISSING_ACCURACY", "detail": f"Accuracy missing for {m['method']}/{m['dataset']}"})
        if m["f1"] == "":
            issues.append({"type": "MISSING_F1", "detail": f"F1 missing for {m['method']}/{m['dataset']}"})
    best = {}
    for ds, rows in by_ds.items():
        valid = [r for r in rows if r["f1"] != ""]
        if valid:
            top = max(valid, key=lambda r: float(r["f1"]))
            best[ds] = {"method": top["method"], "f1": top["f1"]}
    return best, issues

def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_summary(path, metrics, best, issues, cells):
    lines = []
    lines.append("# PubTables Reconstruction Summary")
    lines.append("")
    lines.append(f"- Reconstructed cells: {len(cells)}")
    lines.append(f"- Normalized metric rows: {len(metrics)}")
    lines.append(f"- Audit issues: {len(issues)}")
    lines.append("")
    lines.append("## Best Method by Dataset (F1)")
    lines.append("")
    if best:
        lines.append("| Dataset | Best Method | F1 |")
        lines.append("|---------|-------------|----|")
        for ds, info in sorted(best.items()):
            lines.append(f"| {ds} | {info['method']} | {info['f1']} |")
    else:
        lines.append("No valid F1 scores found.")
    lines.append("")
    lines.append("## Extracted Metrics")
    lines.append("")
    lines.append("| Method | Dataset | Accuracy | F1 | Notes |")
    lines.append("|--------|---------|----------|----|-------|")
    for m in metrics:
        lines.append(f"| {m['method']} | {m['dataset']} | {m['accuracy']} | {m['f1']} | {m['notes']} |")
    lines.append("")
    if issues:
        lines.append("## Audit Issues")
        lines.append("")
        for iss in issues:
            lines.append(f"- **{iss['type']}**: {iss['detail']}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    words, table_bbox = load_words(INPUT)
    cells, row_centers = reconstruct(words, table_bbox)
    write_csv(CELLS_CSV, cells, ["row_id", "col_id", "row_span", "col_span", "is_header", "text"])
    metrics = normalize_metrics(cells)
    write_csv(METRICS_CSV, metrics, ["method", "dataset", "accuracy", "f1", "notes"])
    best, issues = audit_metrics(metrics)
    audit = {"row_count": len(metrics), "best_by_dataset": best, "issues": issues}
    write_json(AUDIT_JSON, audit)
    write_summary(SUMMARY_MD, metrics, best, issues, cells)

if __name__ == "__main__":
    main()
