from __future__ import annotations

import argparse
import ast
import csv
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_BASE_URL = "https://api.z.ai/api/paas/v4"
DEFAULT_MODEL = "glm-4.5-air"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"

BANNED_SNIPPETS = [
    "subprocess",
    "os.system",
    "popen",
    "socket",
    "requests",
    "urllib",
    "shutil.rmtree",
    "eval(",
    "exec(",
    "__import__",
]

SKILL_ALLOWED_THIRD_PARTY_IMPORTS = {
    "word-docx": {"docx", "lxml"},
    "office-document-specialist-suite": {"docx", "openpyxl", "pptx", "lxml"},
    "excel-xlsx": {"openpyxl", "pandas"},
    "data-analysis": {"pandas", "numpy", "matplotlib", "seaborn"},
    "data-analyst-cn": {"pandas", "numpy", "matplotlib", "seaborn"},
    "multi-source-data-cleaner-pro": {"pandas", "numpy"},
    "chat2duckdb": {"duckdb", "pandas"},
    "sql-master": {"duckdb", "pandas"},
    "file-converter": {"yaml"},
    "markdown-converter": {"markitdown"},
    "all-to-markdown": {"markitdown"},
    "typora-visual-architect": {"pandas", "matplotlib"},
    "generate-chart": {"matplotlib", "pandas", "numpy"},
    "generate-report123": {"pandas", "numpy"},
    "data2visualization": {"pandas", "matplotlib", "numpy"},
}

AGENT_RESULT_FIELDNAMES = [
    "timestamp",
    "run_id",
    "task",
    "condition",
    "provider",
    "model",
    "reasoning_effort",
    "condition_type",
    "sample_seed",
    "pool_samples",
    "skill_pools",
    "skills_given",
    "skill_imports_enforced",
    "import_policy",
    "skill_import_violations",
    "api_status",
    "script_status",
    "verifier_success",
    "issues",
    "notes",
    "elapsed_seconds",
    "run_dir",
    "artifacts_dir",
    "agent_workspace",
]


def load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_task(task_name: str) -> ModuleType:
    return importlib.import_module(f"tasks.{task_name}.task")


def read_prompt(task: ModuleType, condition: str) -> str:
    prompt_path = task.ROOT / "runs" / condition / "prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt. Run `python -m tasks.{task.TASK_NAME}.task prepare` first: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def make_run_id() -> str:
    return "run_" + datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_run_id(run_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", run_id.strip())
    cleaned = cleaned.strip("._-")
    if not cleaned:
        raise ValueError("run_id must contain at least one letter, digit, underscore, dash, or dot.")
    return cleaned


def prepare_agent_run_paths(
    task: ModuleType,
    condition: str,
    run_id: str,
    overwrite: bool,
) -> dict[str, Path]:
    base_paths = task.runtime_paths(condition)
    condition_dir = base_paths["run_dir"]
    run_dir = condition_dir / "agent_runs" / run_id
    if run_dir.exists() and not overwrite:
        raise FileExistsError(
            f"Agent run directory already exists: {run_dir}. "
            "Use --run-id with a new value or pass --overwrite-run-id."
        )
    if overwrite and run_dir.exists():
        shutil.rmtree(run_dir)

    artifacts = run_dir / "artifacts"
    agent_dir = run_dir / "agent_workspace"
    artifacts.mkdir(parents=True, exist_ok=True)
    agent_dir.mkdir(parents=True, exist_ok=True)

    paths = dict(base_paths)
    paths.update(
        {
            "condition_dir": condition_dir,
            "run_dir": run_dir,
            "artifacts": artifacts,
            "agent_dir": agent_dir,
            "cells_csv": artifacts / "table_cells.csv",
            "metrics_csv": artifacts / "metrics.csv",
            "audit_json": artifacts / "audit.json",
            "summary_md": artifacts / "summary.md",
            "generated_script": agent_dir / "generated_solution.py",
            "raw_response": agent_dir / "glm_response.json",
            "model_content": agent_dir / "model_content.txt",
            "stdout": agent_dir / "script_stdout.txt",
            "stderr": agent_dir / "script_stderr.txt",
            "run_metadata": run_dir / "run_metadata.json",
        }
    )

    for filename in ("prompt.md", "skills_given.txt"):
        src = condition_dir / filename
        if src.exists():
            shutil.copyfile(src, run_dir / filename)
    return paths


def clean_previous_outputs(task: ModuleType, paths: dict[str, Path]) -> None:
    keys = list(task.OUTPUT_PATH_KEYS) + [
        "generated_script",
        "raw_response",
        "model_content",
        "stdout",
        "stderr",
    ]
    for key in keys:
        path = paths[key]
        if path.exists():
            path.unlink()


def format_runtime_env(env: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in env.items())


def build_messages(task: ModuleType, condition: str, prompt: str, paths: dict[str, Path]) -> list[dict[str, str]]:
    task_contract = getattr(task, "AGENT_CONTRACT", "Follow the task instructions exactly and produce all required artifacts.")
    system = f"""You are an experiment agent for a local benchmark.
Return exactly one JSON object and no Markdown fences.
The JSON schema is:
{{"script": "<complete Python script>", "notes": "<short notes>"}}

The script must:
- use only local file operations;
- not use GUI automation, screenshots, cloud APIs, web/network calls, or shell commands;
- use the available skill documents in the prompt as procedural guidance for this condition;
- not assume access to skills that are not listed in the condition;
- read input file paths only from the provided environment variables;
- write every required output artifact to the provided environment variable paths;
- avoid hardcoded absolute paths.

Task-specific contract:
{task_contract}
"""

    user = f"""{prompt}

## Runtime Paths

Use these environment variables in your generated Python script:

```text
{format_runtime_env(task.runtime_env(condition, paths))}
```

You are running task: {task.TASK_NAME}
You are running condition: {condition}.

Generate the Python script now."""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_glm(api_key: str, base_url: str, model: str, messages: list[dict[str, str]], timeout: int) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "top_p": 0.8,
        "max_tokens": 4096,
        "stream": False,
        "thinking": {"type": "disabled"},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CodexBench/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GLM API HTTP {exc.code}: {body[:800]}") from exc


def call_openai_responses(
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: int,
    reasoning_effort: str | None,
    max_output_tokens: int,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/responses"
    instructions = "\n\n".join(message["content"] for message in messages if message["role"] == "system")
    user_input = "\n\n".join(message["content"] for message in messages if message["role"] != "system")
    payload: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": user_input,
        "max_output_tokens": max_output_tokens,
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CodexBench/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API HTTP {exc.code}: {body[:800]}") from exc


def call_model(args: argparse.Namespace, messages: list[dict[str, str]]) -> dict[str, Any]:
    if args.provider == "glm-chat":
        return call_glm(args.api_key, args.base_url, args.model, messages, args.api_timeout)
    if args.provider == "openai-responses":
        return call_openai_responses(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
            messages=messages,
            timeout=args.api_timeout,
            reasoning_effort=args.reasoning_effort,
            max_output_tokens=args.max_output_tokens,
        )
    raise ValueError(f"Unsupported provider: {args.provider}")


def message_content(response: dict[str, Any]) -> str:
    if "choices" in response:
        return response["choices"][0]["message"]["content"]
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    parts: list[str] = []
    for item in response.get("output", []) or []:
        if isinstance(item, dict) and item.get("type") == "message":
            for content in item.get("content", []) or []:
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    parts.append(content["text"])
        elif isinstance(item, dict) and isinstance(item.get("content"), list):
            for content in item["content"]:
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    parts.append(content["text"])
    return "\n".join(parts)


def response_incomplete_reason(response: dict[str, Any]) -> str:
    details = response.get("incomplete_details")
    if isinstance(details, dict):
        reason = details.get("reason")
        return str(reason) if reason else ""
    return ""


def strip_code_fence(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text


def extract_script(content: str) -> tuple[str, str]:
    cleaned = strip_code_fence(content)
    try:
        obj = json.loads(cleaned)
        script = obj["script"]
        notes = obj.get("notes", "")
        return script, notes
    except Exception:
        match = re.search(r"```(?:python)?\s*(.*?)```", content, re.DOTALL)
        if not match:
            raise ValueError("Model response did not contain parseable JSON or a Python code block.")
        return match.group(1), "extracted from Python code block"


def imported_roots(script: str) -> set[str]:
    tree = ast.parse(script)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def stdlib_roots() -> set[str]:
    roots = set(getattr(sys, "stdlib_module_names", set()))
    roots.update(sys.builtin_module_names)
    roots.update({"os", "pathlib", "typing"})
    return roots


def allowed_third_party_imports(task: ModuleType, condition: str) -> set[str]:
    allowed: set[str] = set()
    for skill in task.CONDITIONS[condition]["skills"]:
        allowed.update(SKILL_ALLOWED_THIRD_PARTY_IMPORTS.get(skill, set()))
    return allowed


def skill_import_violations(task: ModuleType, script: str, condition: str) -> list[str]:
    third_party = imported_roots(script) - stdlib_roots()
    allowed = allowed_third_party_imports(task, condition)
    return sorted(third_party - allowed)


def safety_check(script: str) -> None:
    lowered = script.lower()
    hits = [snippet for snippet in BANNED_SNIPPETS if snippet in lowered]
    if hits:
        raise RuntimeError(f"Generated script failed safety check. Banned snippets: {', '.join(hits)}")


def execute_script(task: ModuleType, condition: str, script_path: Path, paths: dict[str, Path], timeout: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(task.runtime_env(condition, paths))
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(paths["agent_dir"]),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    paths["stdout"].write_text(completed.stdout, encoding="utf-8", errors="replace")
    paths["stderr"].write_text(completed.stderr, encoding="utf-8", errors="replace")
    return completed


def ensure_result_csv_schema(result_csv: Path, fieldnames: list[str]) -> list[str]:
    if not result_csv.exists():
        return fieldnames
    with result_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        existing_fieldnames = reader.fieldnames or []
        rows = list(reader)
    if existing_fieldnames == fieldnames:
        return fieldnames

    merged_fieldnames = list(fieldnames)
    for fieldname in existing_fieldnames:
        if fieldname not in merged_fieldnames:
            merged_fieldnames.append(fieldname)
    with result_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=merged_fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in merged_fieldnames})
    return merged_fieldnames


def append_agent_result(row: dict[str, Any], result_csv: Path) -> None:
    result_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ensure_result_csv_schema(result_csv, AGENT_RESULT_FIELDNAMES)
    write_header = not result_csv.exists()
    with result_csv.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def run_condition(args: argparse.Namespace, task: ModuleType, condition: str) -> dict[str, Any]:
    task.prepare(force=False)
    paths = prepare_agent_run_paths(
        task=task,
        condition=condition,
        run_id=args.run_id,
        overwrite=args.overwrite_run_id,
    )
    clean_previous_outputs(task, paths)
    prompt = read_prompt(task, condition)
    messages = build_messages(task, condition, prompt, paths)
    config = task.CONDITIONS[condition]
    started = time.time()
    row: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "run_id": args.run_id,
        "task": task.TASK_NAME,
        "condition": condition,
        "provider": args.provider,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "condition_type": config.get("condition_type", ""),
        "sample_seed": config.get("sample_seed", ""),
        "pool_samples": json.dumps(config.get("pool_samples", {}), ensure_ascii=False),
        "skill_pools": json.dumps(config.get("skill_pools", {}), ensure_ascii=False),
        "skills_given": "|".join(config["skills"]) if config["skills"] else "none",
        "skill_imports_enforced": args.import_policy == "block",
        "import_policy": args.import_policy,
        "skill_import_violations": "",
        "api_status": "not_started",
        "script_status": "not_started",
        "verifier_success": False,
        "issues": "",
        "notes": "",
        "elapsed_seconds": "",
        "run_dir": str(paths["run_dir"]),
        "artifacts_dir": str(paths["artifacts"]),
        "agent_workspace": str(paths["agent_dir"]),
    }
    try:
        response = call_model(args, messages)
        paths["raw_response"].write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
        row["api_status"] = "ok"
        content = message_content(response)
        paths["model_content"].write_text(content, encoding="utf-8")
        incomplete_reason = response_incomplete_reason(response)
        if incomplete_reason:
            raise RuntimeError(f"Model response incomplete: {incomplete_reason}")
        if not content.strip():
            raise RuntimeError("Model response did not contain visible text content.")
        script, notes = extract_script(content)
        row["notes"] = notes
        safety_check(script)
        paths["generated_script"].write_text(script, encoding="utf-8")
        if args.import_policy != "off":
            violations = skill_import_violations(task, script, condition)
            row["skill_import_violations"] = ", ".join(violations)
            if violations:
                message = (
                    "Generated script imported third-party modules not allowed by this skill condition: "
                    + ", ".join(violations)
                )
                if args.import_policy == "block":
                    raise RuntimeError(message)
                row["issues"] = message

        completed = execute_script(task, condition, paths["generated_script"], paths, args.exec_timeout)
        row["script_status"] = f"exit_{completed.returncode}"
        if completed.returncode != 0:
            row["issues"] = paths["stderr"].read_text(encoding="utf-8", errors="replace")[:1000]
        verify_result = task.verify_output(condition, paths)
        row["verifier_success"] = verify_result["success"]
        if verify_result["issues"]:
            row["issues"] = (row["issues"] + " | " + verify_result["issues"]).strip(" |")
    except Exception as exc:
        row["issues"] = str(exc)
        if row["api_status"] == "not_started":
            row["api_status"] = "failed"
    finally:
        row["elapsed_seconds"] = f"{time.time() - started:.2f}"
        paths["run_metadata"].write_text(
            json.dumps(row, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        append_agent_result(row, args.result_csv)
    return row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an API model on a skill-composition task.")
    parser.add_argument("--task", default="pubtables", help="Task package under tasks/, e.g. pubtables.")
    parser.add_argument("--condition", action="append", help="Condition to run. Can be passed multiple times.")
    parser.add_argument("--all", action="store_true", help="Run all conditions.")
    parser.add_argument(
        "--provider",
        choices=["glm-chat", "openai-responses"],
        default=os.environ.get("MODEL_PROVIDER", "glm-chat"),
        help="API provider/surface to use.",
    )
    parser.add_argument("--model", default=os.environ.get("GLM_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument(
        "--reasoning-effort",
        default=os.environ.get("REASONING_EFFORT"),
        help="Reasoning effort for providers that support it, e.g. xhigh for OpenAI Responses.",
    )
    parser.add_argument("--max-output-tokens", type=int, default=int(os.environ.get("MAX_OUTPUT_TOKENS", "8192")))
    parser.add_argument(
        "--import-policy",
        choices=["off", "warn", "block"],
        default=os.environ.get("IMPORT_POLICY", "warn"),
        help="off ignores third-party imports, warn records them, block rejects them before execution.",
    )
    parser.add_argument("--result-csv", type=Path, default=None)
    parser.add_argument(
        "--run-id",
        default=None,
        help="Stable ID for this runner invocation. Defaults to run_YYYYMMDD_HHMMSS.",
    )
    parser.add_argument(
        "--overwrite-run-id",
        action="store_true",
        help="Overwrite existing per-condition agent run directories for the given run ID.",
    )
    parser.add_argument("--api-timeout", type=int, default=120)
    parser.add_argument("--exec-timeout", type=int, default=60)
    return parser


def main() -> None:
    load_dotenv_file(PROJECT_ROOT / ".env")
    args = build_parser().parse_args()
    args.run_id = sanitize_run_id(args.run_id or make_run_id())
    task = load_task(args.task)
    if args.base_url is None:
        if args.provider == "openai-responses":
            args.base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("KRILL_BASE_URL") or DEFAULT_OPENAI_BASE_URL
        else:
            args.base_url = os.environ.get("GLM_BASE_URL", DEFAULT_BASE_URL)
    if args.api_key is None:
        if args.provider == "openai-responses":
            args.api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("KRILL_API_KEY")
        else:
            args.api_key = os.environ.get("GLM_API_KEY") or os.environ.get("ZAI_API_KEY")
    if args.result_csv is None:
        args.result_csv = task.ROOT / "results" / "agent_runs_multi_pool_warn.csv"
    if not args.api_key:
        raise SystemExit("Missing API key. Set GLM_API_KEY, ZAI_API_KEY, OPENAI_API_KEY, or KRILL_API_KEY.")

    conditions = sorted(task.CONDITIONS) if args.all else (args.condition or ["no_skill"])
    unknown = [condition for condition in conditions if condition not in task.CONDITIONS]
    if unknown:
        raise SystemExit(f"Unknown condition(s) for task {task.TASK_NAME}: {', '.join(unknown)}")

    try:
        rows = [run_condition(args, task, condition) for condition in conditions]
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
