from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.pubtables import verifier  # noqa: E402


TASK_ROOT = PROJECT_ROOT / "tasks" / "pubtables"

GENERIC_ALLOWED_TERMS = {
    "method",
    "dataset",
    "accuracy",
    "f1",
    "notes",
    "best",
    "baseline",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_custom_skills() -> list[str]:
    manifest_path = TASK_ROOT / "skill_pool_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest["custom_answer_free_skills"]


def frontmatter_keys(text: str) -> list[str]:
    if not text.startswith("---"):
        return []
    parts = text.split("---", 2)
    if len(parts) < 3:
        return []
    keys = []
    for line in parts[1].splitlines():
        if ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    return keys


def forbidden_terms() -> list[str]:
    terms: set[str] = {
        "EXPECTED_METRICS",
        "EXPECTED_CELLS",
        "EXPECTED_BEST_BY_DATASET",
        "run_oracle",
        "verify_output",
        "PMC_LOCAL",
        "table_words.json",
    }
    for row in verifier.load_expected_metrics():
        for key, value in row.items():
            text = str(value).strip()
            if key in {"method", "dataset"} or re.search(r"\d", text):
                terms.add(text)
    expected_audit = verifier.load_expected_audit()
    for dataset, value in expected_audit.get("best_by_dataset", {}).items():
        terms.add(dataset)
        terms.add(str(value["method"]))
        terms.add(str(value["f1"]))
    for cell in verifier.load_expected_cells():
        text = str(cell["text"]).strip()
        if text.lower() not in GENERIC_ALLOWED_TERMS and len(text) > 6:
            terms.add(text)
    return sorted(terms, key=lambda value: (len(value), value.lower()), reverse=True)


def audit_skill(slug: str, terms: list[str]) -> dict[str, object]:
    path = PROJECT_ROOT / "skills" / slug / "SKILL.md"
    result: dict[str, object] = {
        "skill_id": slug,
        "path": str(path.relative_to(PROJECT_ROOT)),
        "exists": path.exists(),
        "sha256": "",
        "frontmatter_keys": [],
        "frontmatter_valid": False,
        "leak_hits": [],
    }
    if not path.exists():
        return result

    text = path.read_text(encoding="utf-8", errors="replace")
    keys = frontmatter_keys(text)
    lowered = text.lower()
    hits = [term for term in terms if term.lower() in lowered]
    result.update(
        {
            "sha256": sha256_text(text),
            "frontmatter_keys": keys,
            "frontmatter_valid": keys == ["name", "description"],
            "leak_hits": hits,
        }
    )
    return result


def main() -> int:
    terms = forbidden_terms()
    custom_skills = load_custom_skills()
    results = [audit_skill(slug, terms) for slug in custom_skills]
    passed = all(
        item["exists"] and item["frontmatter_valid"] and not item["leak_hits"]
        for item in results
    )
    payload = {
        "task": "pubtables",
        "custom_skills": custom_skills,
        "forbidden_term_count": len(terms),
        "passed": passed,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
