from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import word_task


DEFAULT_BASE_URL = "https://api.z.ai/api/paas/v4"
DEFAULT_MODEL = "glm-4.5-air"
EDITED_DOCX_NAME = word_task.EDITED_DOCX_NAME

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
}


def root() -> Path:
    return Path(__file__).resolve().parent


def project_root() -> Path:
    return root().parent


def read_prompt(condition: str) -> str:
    prompt_path = root() / "runs" / condition / "prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt. Run word_task.py prepare first: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def target_paths(condition: str) -> dict[str, Path]:
    run_dir = root() / "runs" / condition
    artifacts = run_dir / "artifacts"
    agent_dir = run_dir / "agent_workspace"
    artifacts.mkdir(parents=True, exist_ok=True)
    agent_dir.mkdir(parents=True, exist_ok=True)
    return {
        "run_dir": run_dir,
        "artifacts": artifacts,
        "agent_dir": agent_dir,
        "original_docx": root() / "data" / "original" / word_task.DOCX_NAME,
        "output_docx": artifacts / EDITED_DOCX_NAME,
        "summary_md": artifacts / "summary.md",
        "generated_script": agent_dir / "generated_solution.py",
        "raw_response": agent_dir / "glm_response.json",
        "model_content": agent_dir / "model_content.txt",
        "stdout": agent_dir / "script_stdout.txt",
        "stderr": agent_dir / "script_stderr.txt",
    }


def clean_previous_outputs(paths: dict[str, Path]) -> None:
    for key in ("output_docx", "summary_md", "generated_script", "raw_response", "model_content", "stdout", "stderr"):
        path = paths[key]
        if path.exists():
            path.unlink()


def build_messages(condition: str, prompt: str, paths: dict[str, Path]) -> list[dict[str, str]]:
    system = """You are an experiment agent for a local benchmark.
Return exactly one JSON object and no Markdown fences.
The JSON schema is:
{"script": "<complete Python script>", "notes": "<short notes>"}

The script must:
- use only local file operations;
- not use GUI automation, screenshots, cloud APIs, web/network calls, or shell commands;
- use the available skill documents in the prompt as the procedural guidance for this condition;
- not assume access to skills that are not listed in the condition;
- read the original file path from environment variable ORIGINAL_DOCX;
- write the edited file path to environment variable OUTPUT_DOCX;
- write the Markdown summary path to environment variable SUMMARY_MD;
- preserve all document text and all non-target formatting except the requested change.
"""

    user = f"""{prompt}

## Runtime Paths

Use these environment variables in your generated Python script:

```text
ORIGINAL_DOCX={paths["original_docx"]}
OUTPUT_DOCX={paths["output_docx"]}
SUMMARY_MD={paths["summary_md"]}
```

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
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GLM API HTTP {exc.code}: {body[:800]}") from exc


def message_content(response: dict[str, Any]) -> str:
    return response["choices"][0]["message"]["content"]


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


def allowed_third_party_imports(condition: str) -> set[str]:
    allowed: set[str] = set()
    for skill in word_task.CONDITIONS[condition]["skills"]:
        allowed.update(SKILL_ALLOWED_THIRD_PARTY_IMPORTS.get(skill, set()))
    return allowed


def skill_import_violations(script: str, condition: str) -> list[str]:
    third_party = imported_roots(script) - stdlib_roots()
    allowed = allowed_third_party_imports(condition)
    return sorted(third_party - allowed)


def safety_check(script: str) -> None:
    lowered = script.lower()
    hits = [snippet for snippet in BANNED_SNIPPETS if snippet in lowered]
    if hits:
        raise RuntimeError(f"Generated script failed safety check. Banned snippets: {', '.join(hits)}")


def skill_import_check(script: str, condition: str) -> None:
    disallowed = skill_import_violations(script, condition)
    if disallowed:
        raise RuntimeError(
            "Generated script imported third-party modules not allowed by this skill condition: "
            + ", ".join(disallowed)
        )


def execute_script(script_path: Path, paths: dict[str, Path], timeout: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "ORIGINAL_DOCX": str(paths["original_docx"]),
            "OUTPUT_DOCX": str(paths["output_docx"]),
            "SUMMARY_MD": str(paths["summary_md"]),
        }
    )
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


def append_agent_result(row: dict[str, Any], result_csv: Path) -> None:
    out = result_csv
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp",
        "condition",
        "model",
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
    ]
    write_header = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def run_condition(args: argparse.Namespace, condition: str) -> dict[str, Any]:
    p = word_task.paths()
    word_task.ensure_dirs(p)
    if not p.original_docx.exists():
        word_task.download_sample(p.original_docx)
    if not (root() / "runs" / condition / "prompt.md").exists():
        word_task.write_condition_prompts(p)

    paths = target_paths(condition)
    clean_previous_outputs(paths)
    prompt = read_prompt(condition)
    messages = build_messages(condition, prompt, paths)
    config = word_task.CONDITIONS[condition]
    started = time.time()
    row: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "condition": condition,
        "model": args.model,
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
    }
    try:
        response = call_glm(args.api_key, args.base_url, args.model, messages, args.api_timeout)
        paths["raw_response"].write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
        row["api_status"] = "ok"
        content = message_content(response)
        paths["model_content"].write_text(content, encoding="utf-8")
        script, notes = extract_script(content)
        row["notes"] = notes
        safety_check(script)
        paths["generated_script"].write_text(script, encoding="utf-8")
        if args.import_policy != "off":
            violations = skill_import_violations(script, condition)
            row["skill_import_violations"] = ", ".join(violations)
            if violations:
                message = (
                    "Generated script imported third-party modules not allowed by this skill condition: "
                    + ", ".join(violations)
                )
                if args.import_policy == "block":
                    raise RuntimeError(message)
                row["issues"] = message

        completed = execute_script(paths["generated_script"], paths, args.exec_timeout)
        row["script_status"] = f"exit_{completed.returncode}"
        if completed.returncode != 0:
            row["issues"] = paths["stderr"].read_text(encoding="utf-8", errors="replace")[:1000]
        verify_result = word_task.verify_output(condition, paths["output_docx"], paths["summary_md"])
        word_task.append_result(verify_result)
        row["verifier_success"] = verify_result["success"]
        if verify_result["issues"]:
            row["issues"] = (row["issues"] + " | " + verify_result["issues"]).strip(" |")
    except Exception as exc:
        row["issues"] = str(exc)
        if row["api_status"] == "not_started":
            row["api_status"] = "failed"
    finally:
        row["elapsed_seconds"] = f"{time.time() - started:.2f}"
        append_agent_result(row, args.result_csv)
    return row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run GLM API on the Word formatting pilot.")
    parser.add_argument(
        "--condition",
        action="append",
        choices=sorted(word_task.CONDITIONS),
        help="Condition to run. Can be passed multiple times. Defaults to no_skill.",
    )
    parser.add_argument("--all", action="store_true", help="Run all conditions.")
    parser.add_argument("--model", default=os.environ.get("GLM_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("GLM_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key", default=os.environ.get("GLM_API_KEY") or os.environ.get("ZAI_API_KEY"))
    parser.add_argument(
        "--enforce-skill-imports",
        action="store_true",
        help="Deprecated alias for --import-policy block.",
    )
    parser.add_argument(
        "--import-policy",
        choices=["off", "warn", "block"],
        help=(
            "How to handle third-party imports not supplied by the condition's skills. "
            "off ignores them, warn records them but still executes for artifact collection, "
            "and block rejects the script before execution."
        ),
    )
    parser.add_argument(
        "--result-csv",
        type=Path,
        default=root() / "results" / "agent_runs_v2.csv",
        help="CSV path for API-backed agent run records.",
    )
    parser.add_argument("--api-timeout", type=int, default=180)
    parser.add_argument("--exec-timeout", type=int, default=60)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.import_policy is None:
        args.import_policy = "block" if args.enforce_skill_imports else "off"
    if not args.api_key:
        raise SystemExit("Missing API key. Set GLM_API_KEY or pass --api-key.")

    conditions = sorted(word_task.CONDITIONS) if args.all else (args.condition or ["no_skill"])
    rows = [run_condition(args, condition) for condition in conditions]
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0 if all(row["verifier_success"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
