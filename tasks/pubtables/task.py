from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from framework.conditions import build_conditions, write_condition_prompts


TASK_NAME = "pubtables"
ROOT = Path(__file__).resolve().parent

HTML_NAME = "pubtables_sample.html"

TASK_PROMPT = """Given a local PubTables-style scientific table in HTML, extract the table structure, normalize the metric rows, audit the extracted values, and write a short grounded Markdown summary.

The input table has multi-row headers and span attributes. Treat header cells, row spans, and column spans as part of the table structure. Exclude caption text and footnotes from the normalized metric rows.

Required normalized metric fields:
- method
- dataset
- accuracy
- f1
- notes

For the audit, report the number of normalized metric rows, the best method by F1 score for each dataset, and any extraction or validation issues you find."""

AGENT_CONTRACT = """For this PubTables task:
- parse ORIGINAL_HTML as the only input table source;
- write a structural cell inventory to OUTPUT_CELLS_CSV;
- write normalized numeric metric rows to OUTPUT_METRICS_CSV;
- write audit metadata JSON to OUTPUT_AUDIT_JSON;
- write a Markdown summary to SUMMARY_MD;
- do not include caption or footnote text as metric rows."""

EXPECTED_ARTIFACTS = [
    {
        "env": "OUTPUT_CELLS_CSV",
        "filename": "table_cells.csv",
        "description": "CSV columns row_id,col_id,row_span,col_span,is_header,text for every non-empty table cell.",
    },
    {
        "env": "OUTPUT_METRICS_CSV",
        "filename": "metrics.csv",
        "description": "CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.",
    },
    {
        "env": "OUTPUT_AUDIT_JSON",
        "filename": "audit.json",
        "description": "JSON with row_count, best_by_dataset, and issues.",
    },
    {
        "env": "SUMMARY_MD",
        "filename": "summary.md",
        "description": "Short Markdown summary grounded in the extracted metrics and audit.",
    },
]

OUTPUT_PATH_KEYS = ("cells_csv", "metrics_csv", "audit_json", "summary_md")

SKILL_POOLS: dict[str, list[str]] = {
    "table_extraction": [
        "all-to-markdown",
        "markdown-converter",
        "file-converter",
        "chat2duckdb",
        "excel-xlsx",
    ],
    "data_cleaning": [
        "multi-source-data-cleaner-pro",
        "data-analysis",
        "data-analyst-cn",
        "excel-xlsx",
        "chat2duckdb",
    ],
    "validation_audit": [
        "code-executor",
        "data-reconciliation-exceptions",
        "data-anomaly-detector",
        "data-analysis",
        "sql-master",
    ],
    "summary_reporting": [
        "typora-visual-architect",
        "generate-report123",
        "data2visualization",
        "sql-report-generator",
        "generate-chart",
    ],
}

SAMPLE_SEEDS = list(range(1, 11))
CONDITIONS = build_conditions(SKILL_POOLS, SAMPLE_SEEDS)

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

HTML_FIXTURE = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>PubTables local fixture</title></head>
<body>
<table id="pubtables-fixture">
  <caption>Table 2. Model performance on two biomedical table benchmarks.</caption>
  <thead>
    <tr>
      <th rowspan="2">Method</th>
      <th rowspan="2">Dataset</th>
      <th colspan="2">Evaluation score (%)</th>
      <th rowspan="2">Notes</th>
    </tr>
    <tr>
      <th>Accuracy</th>
      <th>F1</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>GraphNet</td><td>PubMed QA</td><td>91.2</td><td>88.6</td><td>best</td></tr>
    <tr><td>TreeCRF</td><td>PubMed QA</td><td>89.5</td><td>86.9</td><td>baseline</td></tr>
    <tr><td>GraphNet</td><td>ChemTable</td><td>84.7</td><td>81.3</td><td>cross-domain</td></tr>
    <tr><td>TableFormer</td><td>ChemTable</td><td>87.8</td><td>84.2</td><td>best</td></tr>
    <tr><td>Rule Parser</td><td>ChemTable</td><td>71.0</td><td>68.4</td><td>weak baseline</td></tr>
  </tbody>
  <tfoot>
    <tr><td colspan="5">Footnote: scores are micro-averaged over table cells.</td></tr>
  </tfoot>
</table>
</body>
</html>
"""

EXPECTED_METRICS = [
    {"method": "GraphNet", "dataset": "PubMed QA", "accuracy": 91.2, "f1": 88.6, "notes": "best"},
    {"method": "TreeCRF", "dataset": "PubMed QA", "accuracy": 89.5, "f1": 86.9, "notes": "baseline"},
    {"method": "GraphNet", "dataset": "ChemTable", "accuracy": 84.7, "f1": 81.3, "notes": "cross-domain"},
    {"method": "TableFormer", "dataset": "ChemTable", "accuracy": 87.8, "f1": 84.2, "notes": "best"},
    {"method": "Rule Parser", "dataset": "ChemTable", "accuracy": 71.0, "f1": 68.4, "notes": "weak baseline"},
]

EXPECTED_BEST_BY_DATASET = {
    "PubMed QA": {"method": "GraphNet", "f1": 88.6},
    "ChemTable": {"method": "TableFormer", "f1": 84.2},
}


def data_dir() -> Path:
    return ROOT / "data" / "original"


def runs_dir() -> Path:
    return ROOT / "runs"


def results_dir() -> Path:
    return ROOT / "results"


def results_csv() -> Path:
    return results_dir() / "results.csv"


def original_html() -> Path:
    return data_dir() / HTML_NAME


def ensure_dirs() -> None:
    data_dir().mkdir(parents=True, exist_ok=True)
    runs_dir().mkdir(parents=True, exist_ok=True)
    results_dir().mkdir(parents=True, exist_ok=True)
    for condition in CONDITIONS:
        (runs_dir() / condition / "artifacts").mkdir(parents=True, exist_ok=True)


def ensure_input_files(force: bool = False) -> None:
    ensure_dirs()
    if force or not original_html().exists():
        original_html().write_text(HTML_FIXTURE, encoding="utf-8")


def init_results_csv(force: bool = False) -> None:
    results_dir().mkdir(parents=True, exist_ok=True)
    if results_csv().exists() and not force:
        return
    with results_csv().open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=RESULT_FIELDNAMES).writeheader()


def prepare(force: bool = False) -> None:
    ensure_input_files(force=force)
    write_condition_prompts(ROOT, CONDITIONS, TASK_PROMPT, EXPECTED_ARTIFACTS)
    init_results_csv(force=force)


def runtime_paths(condition: str) -> dict[str, Path]:
    run_dir = runs_dir() / condition
    artifacts = run_dir / "artifacts"
    agent_dir = run_dir / "agent_workspace"
    artifacts.mkdir(parents=True, exist_ok=True)
    agent_dir.mkdir(parents=True, exist_ok=True)
    return {
        "run_dir": run_dir,
        "artifacts": artifacts,
        "agent_dir": agent_dir,
        "original_html": original_html(),
        "cells_csv": artifacts / "table_cells.csv",
        "metrics_csv": artifacts / "metrics.csv",
        "audit_json": artifacts / "audit.json",
        "summary_md": artifacts / "summary.md",
        "generated_script": agent_dir / "generated_solution.py",
        "raw_response": agent_dir / "glm_response.json",
        "model_content": agent_dir / "model_content.txt",
        "stdout": agent_dir / "script_stdout.txt",
        "stderr": agent_dir / "script_stderr.txt",
    }


def runtime_env(condition: str, paths: dict[str, Path]) -> dict[str, str]:
    return {
        "ORIGINAL_HTML": str(paths["original_html"]),
        "OUTPUT_CELLS_CSV": str(paths["cells_csv"]),
        "OUTPUT_METRICS_CSV": str(paths["metrics_csv"]),
        "OUTPUT_AUDIT_JSON": str(paths["audit_json"]),
        "SUMMARY_MD": str(paths["summary_md"]),
    }


class CellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.in_tfoot = False
        self.current_row = -1
        self.current_col = 0
        self.current_cell: dict[str, Any] | None = None
        self.current_text: list[str] = []
        self.cells: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name: value or "" for name, value in attrs}
        if tag == "table":
            self.in_table = True
        elif tag == "tfoot" and self.in_table:
            self.in_tfoot = True
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row += 1
            self.current_col = 0
        elif tag in {"td", "th"} and self.in_table and self.in_row:
            self.in_cell = True
            self.current_text = []
            self.current_cell = {
                "row_id": self.current_row,
                "col_id": self.current_col,
                "row_span": int(attrs_dict.get("rowspan", "1") or "1"),
                "col_span": int(attrs_dict.get("colspan", "1") or "1"),
                "is_header": tag == "th",
                "in_tfoot": self.in_tfoot,
            }

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.current_cell is not None:
            text = " ".join(" ".join(self.current_text).split())
            if text:
                cell = dict(self.current_cell)
                cell["text"] = text
                self.cells.append(cell)
            self.current_col += self.current_cell["col_span"]
            self.current_cell = None
            self.in_cell = False
        elif tag == "tr":
            self.in_row = False
        elif tag == "tfoot":
            self.in_tfoot = False
        elif tag == "table":
            self.in_table = False


def expected_cells() -> list[dict[str, Any]]:
    parser = CellParser()
    parser.feed(HTML_FIXTURE)
    return [
        {key: cell[key] for key in ("row_id", "col_id", "row_span", "col_span", "is_header", "text")}
        for cell in parser.cells
        if not cell["in_tfoot"]
    ]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_oracle(condition: str) -> None:
    prepare(force=False)
    paths = runtime_paths(condition)
    cell_rows = expected_cells()
    write_csv(paths["cells_csv"], ["row_id", "col_id", "row_span", "col_span", "is_header", "text"], cell_rows)
    write_csv(paths["metrics_csv"], ["method", "dataset", "accuracy", "f1", "notes"], EXPECTED_METRICS)
    paths["audit_json"].write_text(
        json.dumps(
            {
                "row_count": len(EXPECTED_METRICS),
                "best_by_dataset": EXPECTED_BEST_BY_DATASET,
                "issues": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    paths["summary_md"].write_text(
        "# PubTables Extraction Summary\n\n"
        "- Extracted 5 normalized metric rows from the PubTables-style HTML table.\n"
        "- Best PubMed QA method by F1: GraphNet (88.6).\n"
        "- Best ChemTable method by F1: TableFormer (84.2).\n"
        "- No extraction or validation issues were found.\n",
        encoding="utf-8",
    )
    print(f"Oracle artifacts written to {paths['artifacts']}")


def normalize_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [{normalize_header(k): (v or "").strip() for k, v in row.items()} for row in reader]


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
    expected = [normalize_metric_row(row) for row in EXPECTED_METRICS]
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
    texts = {row.get("text", "") for row in rows}
    required_texts = {
        "Method",
        "Dataset",
        "Evaluation score (%)",
        "Accuracy",
        "F1",
        "Notes",
        "GraphNet",
        "PubMed QA",
        "TableFormer",
        "ChemTable",
        "Rule Parser",
        "weak baseline",
    }
    missing = sorted(text for text in required_texts if text not in texts)
    if missing:
        issues.append("table_cells.csv missing required cell text: " + ", ".join(missing))
        return False

    has_span = False
    header_count = 0
    for row in rows:
        if boolish(row.get("is_header")):
            header_count += 1
        if row.get("text") == "Evaluation score (%)" and str(row.get("col_span", "")).strip() == "2":
            has_span = True
    ok = True
    if not has_span:
        issues.append("table_cells.csv did not preserve col_span=2 for the grouped score header.")
        ok = False
    if header_count < 6:
        issues.append(f"table_cells.csv has too few header cells: expected at least 6, got {header_count}.")
        ok = False
    if any("Footnote:" in row.get("text", "") for row in rows):
        issues.append("table_cells.csv should exclude the table footnote from the structural extraction.")
        ok = False
    return ok


def audit_match(path: Path, issues: list[str]) -> bool:
    try:
        audit = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"Could not read audit.json: {exc}")
        return False
    ok = True
    if int(audit.get("row_count", -1)) != len(EXPECTED_METRICS):
        issues.append(f"audit.json row_count mismatch: expected {len(EXPECTED_METRICS)}, got {audit.get('row_count')!r}.")
        ok = False
    best = audit.get("best_by_dataset", {})
    for dataset, target in EXPECTED_BEST_BY_DATASET.items():
        observed = best.get(dataset, {})
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
    required = ["GraphNet", "TableFormer", "PubMed QA", "ChemTable", "88.6", "84.2"]
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


def append_result(result: dict[str, Any]) -> None:
    init_results_csv(force=False)
    with results_csv().open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDNAMES)
        writer.writerow({key: result.get(key, "") for key in RESULT_FIELDNAMES})


def print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def verify(condition: str) -> dict[str, Any]:
    paths = runtime_paths(condition)
    result = verify_output(condition, paths)
    append_result(result)
    print_result(result)
    return result


def verify_all() -> None:
    failed = False
    for condition in CONDITIONS:
        result = verify(condition)
        failed = failed or not result["success"]
    if failed:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PubTables-style skill-composition task.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Create fixture, prompts, and result CSV.")
    prepare_parser.add_argument("--force", action="store_true", help="Regenerate fixture and reset results.csv.")

    oracle_parser = subparsers.add_parser("oracle", help="Generate known-correct artifacts for one condition.")
    oracle_parser.add_argument("--condition", choices=sorted(CONDITIONS), default="multi_pool_sample_s02")

    verify_parser = subparsers.add_parser("verify", help="Verify one condition output.")
    verify_parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)

    subparsers.add_parser("verify-all", help="Verify all condition folders.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "prepare":
        prepare(force=args.force)
        print(f"Prepared PubTables task at {ROOT}")
        print(f"Input HTML: {original_html()}")
        print(f"Conditions: {', '.join(CONDITIONS)}")
    elif args.command == "oracle":
        run_oracle(args.condition)
    elif args.command == "verify":
        result = verify(args.condition)
        if not result["success"]:
            raise SystemExit(1)
    elif args.command == "verify-all":
        verify_all()
    else:
        raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    if str(ROOT.parents[1]) not in sys.path:
        sys.path.insert(0, str(ROOT.parents[1]))
    main()
