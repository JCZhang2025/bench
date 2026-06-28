from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from framework.conditions import build_conditions, write_condition_prompts
from tasks.pubtables import verifier


TASK_NAME = "pubtables"
ROOT = Path(__file__).resolve().parent

SAMPLE_SEEDS = list(range(1, 11))
OUTPUT_PATH_KEYS = ("cells_csv", "metrics_csv", "audit_json", "summary_md")
RESULT_FIELDNAMES = verifier.RESULT_FIELDNAMES


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def task_spec_path() -> Path:
    return ROOT / "task_spec.json"


def skill_pools_path() -> Path:
    return ROOT / "skill_pools.json"


def data_dir() -> Path:
    return ROOT / "data" / "original"


def gold_dir() -> Path:
    return ROOT / "data" / "gold"


def runs_dir() -> Path:
    return ROOT / "runs"


def results_dir() -> Path:
    return ROOT / "results"


def results_csv() -> Path:
    return results_dir() / "results.csv"


TASK_SPEC = load_json(task_spec_path())
TASK_PROMPT = TASK_SPEC["task_prompt"]
AGENT_CONTRACT = TASK_SPEC["agent_contract"]
EXPECTED_ARTIFACTS = TASK_SPEC["expected_artifacts"]
WORDS_JSON_NAME = TASK_SPEC.get("words_json_name", "table_words.json")

SKILL_POOLS: dict[str, list[str]] = load_json(skill_pools_path())
CONDITIONS = build_conditions(SKILL_POOLS, SAMPLE_SEEDS)


def original_words_json() -> Path:
    return data_dir() / WORDS_JSON_NAME


def ensure_dirs() -> None:
    data_dir().mkdir(parents=True, exist_ok=True)
    runs_dir().mkdir(parents=True, exist_ok=True)
    results_dir().mkdir(parents=True, exist_ok=True)
    for condition in CONDITIONS:
        (runs_dir() / condition / "artifacts").mkdir(parents=True, exist_ok=True)


def ensure_input_files() -> None:
    ensure_dirs()
    if not original_words_json().exists():
        raise FileNotFoundError(
            f"Missing PubTables input fixture: {original_words_json()}. "
            "Restore tasks/pubtables/data/original/table_words.json before preparing the task."
        )


def init_results_csv(force: bool = False) -> None:
    results_dir().mkdir(parents=True, exist_ok=True)
    if results_csv().exists() and not force:
        return
    with results_csv().open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=RESULT_FIELDNAMES).writeheader()


def prepare(force: bool = False) -> None:
    ensure_input_files()
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
        "original_words_json": original_words_json(),
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
        "ORIGINAL_WORDS_JSON": str(paths["original_words_json"]),
        "OUTPUT_CELLS_CSV": str(paths["cells_csv"]),
        "OUTPUT_METRICS_CSV": str(paths["metrics_csv"]),
        "OUTPUT_AUDIT_JSON": str(paths["audit_json"]),
        "SUMMARY_MD": str(paths["summary_md"]),
    }


def copy_gold_artifact(filename: str, destination: Path) -> None:
    source = gold_dir() / filename
    if not source.exists():
        raise FileNotFoundError(f"Missing gold artifact: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def run_oracle(condition: str) -> None:
    prepare(force=False)
    paths = runtime_paths(condition)
    copy_gold_artifact("table_cells.csv", paths["cells_csv"])
    copy_gold_artifact("metrics.csv", paths["metrics_csv"])
    copy_gold_artifact("audit.json", paths["audit_json"])
    copy_gold_artifact("summary.md", paths["summary_md"])
    print(f"Oracle artifacts written to {paths['artifacts']}")


def append_result(result: dict[str, Any]) -> None:
    init_results_csv(force=False)
    with results_csv().open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDNAMES)
        writer.writerow({key: result.get(key, "") for key in RESULT_FIELDNAMES})


def print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def verify_output(condition: str, paths: dict[str, Path]) -> dict[str, Any]:
    return verifier.verify_output(condition, paths)


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

    prepare_parser = subparsers.add_parser("prepare", help="Create prompts and result CSV.")
    prepare_parser.add_argument("--force", action="store_true", help="Reset results.csv.")

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
        print(f"Input OCR word JSON: {original_words_json()}")
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
