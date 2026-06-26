from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


def root() -> Path:
    return Path(__file__).resolve().parent


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def build_summary(rows: list[dict[str, Any]], source: Path) -> str:
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_type[row.get("condition_type", "unknown") or "unknown"].append(row)

    lines = [
        "# Skill-Family Result Summary",
        "",
        f"Source CSV: `{source}`",
        "",
        "## Aggregate",
        "",
        "| condition_type | runs | pass | pass_rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for condition_type, group in sorted(by_type.items()):
        total = len(group)
        passed = sum(1 for row in group if truthy(row.get("verifier_success")))
        rate = passed / total if total else 0
        lines.append(f"| `{condition_type}` | {total} | {passed} | {rate:.2%} |")

    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| condition | type | seed | pool_samples | skills | verifier | import_violations | issues |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        condition = row.get("condition", "")
        condition_type = row.get("condition_type", "")
        seed = row.get("sample_seed", "")
        pool_samples = row.get("pool_samples", "")
        skills = row.get("skills_given", "")
        verifier = row.get("verifier_success", "")
        violations = row.get("skill_import_violations", "")
        issues = (row.get("issues", "") or "").replace("|", "/")
        lines.append(
            f"| `{condition}` | `{condition_type}` | {seed} | `{pool_samples}` | `{skills}` | `{verifier}` | `{violations}` | {issues} |"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize sample-vs-all skill-family experiment results.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=root() / "results" / "agent_runs_multi_pool_warn.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root() / "results" / "MULTI_POOL_RESULT_SUMMARY.md",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = read_rows(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_summary(rows, args.csv), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
