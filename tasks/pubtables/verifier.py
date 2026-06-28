from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent

RESULT_FIELDNAMES = [
    "timestamp",
    "condition",
    "success",
    "cells_exists",
    "metrics_exists",
    "audit_exists",
    "summary_exists",
    "metrics_correct",
    "structure_correct",
    "audit_correct",
    "summary_grounded",
    "issues",
]


def gold_dir() -> Path:
    return ROOT / "data" / "gold"


def gold_metrics_csv() -> Path:
    return gold_dir() / "metrics.csv"


def gold_cells_csv() -> Path:
    return gold_dir() / "table_cells.csv"


def gold_audit_json() -> Path:
    return gold_dir() / "audit.json"


def verification_rules_json() -> Path:
    return gold_dir() / "verification_rules.json"


def normalize_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [{normalize_header(k): (v or "").strip() for k, v in row.items()} for row in reader]


def load_expected_metrics() -> list[dict[str, Any]]:
    return [normalize_metric_row(row) for row in read_csv_rows(gold_metrics_csv())]


def load_expected_cells() -> list[dict[str, str]]:
    return read_csv_rows(gold_cells_csv())


def load_expected_audit() -> dict[str, Any]:
    return json.loads(gold_audit_json().read_text(encoding="utf-8"))


def load_verification_rules() -> dict[str, Any]:
    return json.loads(verification_rules_json().read_text(encoding="utf-8"))


def to_float(value: Any) -> float | None:
    try:
        return float(str(value).strip().rstrip("%"))
    except Exception:
        return None


def normalize_metric_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "method": str(row.get("method", "")).strip(),
        "dataset": str(row.get("dataset", "")).strip(),
        "accuracy": to_float(row.get("accuracy")),
        "f1": to_float(row.get("f1")),
        "notes": str(row.get("notes", "")).strip(),
    }


def metrics_match(path: Path, issues: list[str]) -> bool:
    try:
        rows = [normalize_metric_row(row) for row in read_csv_rows(path)]
    except Exception as exc:
        issues.append(f"Could not read metrics.csv: {exc}")
        return False
    expected = load_expected_metrics()
    sort_key = lambda row: (row["dataset"], row["method"], row["notes"])
    rows_sorted = sorted(rows, key=sort_key)
    expected_sorted = sorted(expected, key=sort_key)
    if len(rows_sorted) != len(expected_sorted):
        issues.append(f"metrics.csv row count mismatch: expected {len(expected_sorted)}, got {len(rows_sorted)}.")
        return False
    ok = True
    for observed, target in zip(rows_sorted, expected_sorted):
        for key in ("method", "dataset", "notes"):
            if observed[key] != target[key]:
                issues.append(f"metrics.csv mismatch for {key}: expected {target[key]!r}, got {observed[key]!r}.")
                ok = False
        for key in ("accuracy", "f1"):
            if observed[key] is None or abs(observed[key] - target[key]) > 0.001:
                issues.append(f"metrics.csv mismatch for {key}: expected {target[key]!r}, got {observed[key]!r}.")
                ok = False
    return ok


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "header"}


def structure_match(path: Path, issues: list[str]) -> bool:
    try:
        rows = read_csv_rows(path)
    except Exception as exc:
        issues.append(f"Could not read table_cells.csv: {exc}")
        return False
    rules = load_verification_rules()
    texts = {row.get("text", "") for row in rows}
    required_texts = set(rules["required_cell_texts"])
    missing = sorted(text for text in required_texts if text not in texts)
    if missing:
        issues.append("table_cells.csv missing required cell text: " + ", ".join(missing))
        return False

    grouped_header = rules["grouped_header"]
    has_span = False
    header_count = 0
    for row in rows:
        if boolish(row.get("is_header")):
            header_count += 1
        if (
            row.get("text") == grouped_header["text"]
            and str(row.get("col_span", "")).strip() == str(grouped_header["col_span"])
        ):
            has_span = True

    ok = True
    if not has_span:
        issues.append("table_cells.csv did not preserve col_span=2 for the grouped score header.")
        ok = False
    minimum_headers = int(rules["minimum_header_cells"])
    if header_count < minimum_headers:
        issues.append(f"table_cells.csv has too few header cells: expected at least {minimum_headers}, got {header_count}.")
        ok = False
    for forbidden in rules["forbidden_cell_text_substrings"]:
        if any(forbidden in row.get("text", "") for row in rows):
            issues.append("table_cells.csv should exclude the table footnote from the structural extraction.")
            ok = False
            break
    return ok


def audit_match(path: Path, issues: list[str]) -> bool:
    try:
        audit = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"Could not read audit.json: {exc}")
        return False

    expected_audit = load_expected_audit()
    expected_metrics = load_expected_metrics()
    ok = True
    if int(audit.get("row_count", -1)) != len(expected_metrics):
        issues.append(f"audit.json row_count mismatch: expected {len(expected_metrics)}, got {audit.get('row_count')!r}.")
        ok = False
    observed_best = audit.get("best_by_dataset", {})
    expected_best = expected_audit.get("best_by_dataset", {})
    for dataset, target in expected_best.items():
        observed = observed_best.get(dataset, {})
        if observed.get("method") != target["method"] or to_float(observed.get("f1")) != target["f1"]:
            issues.append(f"audit.json best_by_dataset mismatch for {dataset}.")
            ok = False
    return ok


def summary_match(path: Path, issues: list[str]) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        issues.append(f"Could not read summary.md: {exc}")
        return False
    required = load_verification_rules()["summary_required_terms"]
    missing = [item for item in required if item not in text]
    if missing:
        issues.append("summary.md missing grounded result(s): " + ", ".join(missing))
        return False
    return True


def finish_result(condition: str, checks: dict[str, bool], issues: list[str]) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "condition": condition,
        "success": all(checks.values()),
        **checks,
        "issues": " | ".join(issues),
    }


def verify_output(condition: str, paths: dict[str, Path]) -> dict[str, Any]:
    issues: list[str] = []
    checks = {
        "cells_exists": paths["cells_csv"].exists() and paths["cells_csv"].stat().st_size > 0,
        "metrics_exists": paths["metrics_csv"].exists() and paths["metrics_csv"].stat().st_size > 0,
        "audit_exists": paths["audit_json"].exists() and paths["audit_json"].stat().st_size > 0,
        "summary_exists": paths["summary_md"].exists() and paths["summary_md"].stat().st_size > 0,
        "metrics_correct": False,
        "structure_correct": False,
        "audit_correct": False,
        "summary_grounded": False,
    }
    for key, exists in (
        ("cells_csv", checks["cells_exists"]),
        ("metrics_csv", checks["metrics_exists"]),
        ("audit_json", checks["audit_exists"]),
        ("summary_md", checks["summary_exists"]),
    ):
        if not exists:
            issues.append(f"Missing or empty artifact: {paths[key]}")

    if checks["metrics_exists"]:
        checks["metrics_correct"] = metrics_match(paths["metrics_csv"], issues)
    if checks["cells_exists"]:
        checks["structure_correct"] = structure_match(paths["cells_csv"], issues)
    if checks["audit_exists"]:
        checks["audit_correct"] = audit_match(paths["audit_json"], issues)
    if checks["summary_exists"]:
        checks["summary_grounded"] = summary_match(paths["summary_md"], issues)
    return finish_result(condition, checks, issues)
