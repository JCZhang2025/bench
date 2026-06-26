from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def root() -> Path:
    return Path(__file__).resolve().parent


def strip_code_fence(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text


def read_agent_content(condition: str) -> str:
    workspace = root() / "runs" / condition / "agent_workspace"
    model_content = workspace / "model_content.txt"
    if model_content.exists():
        return model_content.read_text(encoding="utf-8", errors="replace")

    response_path = workspace / "glm_response.json"
    if not response_path.exists():
        return ""
    response = json.loads(response_path.read_text(encoding="utf-8"))
    return response["choices"][0]["message"]["content"]


def parse_agent_content(content: str) -> dict[str, str]:
    if not content:
        return {"script": "", "notes": ""}
    try:
        obj = json.loads(strip_code_fence(content))
        return {
            "script": str(obj.get("script", "")),
            "notes": str(obj.get("notes", "")),
        }
    except Exception:
        return {"script": "", "notes": ""}


def read_rows(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def code_block(text: str, language: str = "") -> str:
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{language}\n{text.rstrip()}\n{fence}"


def build_report(rows: list[dict[str, Any]], csv_path: Path) -> str:
    lines: list[str] = [
        "# Agent Return Log",
        "",
        f"Source CSV: `{csv_path}`",
        "",
        "This file records what the model returned for each condition and what problem the runner/verifier reported.",
        "",
    ]

    for row in rows:
        condition = row["condition"]
        content = read_agent_content(condition)
        parsed = parse_agent_content(content)
        workspace = root() / "runs" / condition / "agent_workspace"

        lines.extend(
            [
                f"## {condition}",
                "",
                f"- timestamp: `{row.get('timestamp', '')}`",
                f"- model: `{row.get('model', '')}`",
                f"- condition type: `{row.get('condition_type', '')}`",
                f"- sample seed: `{row.get('sample_seed', '')}`",
                f"- pool samples: `{row.get('pool_samples', '')}`",
                f"- skills given: `{row.get('skills_given', '')}`",
                f"- API status: `{row.get('api_status', '')}`",
                f"- script status: `{row.get('script_status', '')}`",
                f"- verifier success: `{row.get('verifier_success', '')}`",
                f"- issue: {row.get('issues', '') or 'none'}",
                f"- generated script: `{workspace / 'generated_solution.py'}`",
                f"- raw GLM response: `{workspace / 'glm_response.json'}`",
                "",
                "### Parsed Notes",
                "",
                parsed["notes"] or row.get("notes", "") or "none",
                "",
                "### Raw Agent Return",
                "",
                code_block(content or "missing", "text"),
                "",
                "### Parsed Script",
                "",
                code_block(parsed["script"] or "Could not parse script from raw agent return.", "python"),
                "",
            ]
        )

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export readable agent return logs from GLM pilot artifacts.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=root() / "results" / "agent_runs_strict_import_gated.csv",
        help="Agent run CSV to summarize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root() / "results" / "AGENT_RETURN_LOG.md",
        help="Markdown report path.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = read_rows(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_report(rows, args.csv), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
