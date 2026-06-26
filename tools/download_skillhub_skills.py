from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path


API_BASE = "https://api.skillhub.cn"

WORD_PILOT_SKILLS = [
    "word-docx",
    "office-document-specialist-suite",
    "code-executor",
    "typora-visual-architect",
    "generate-report123",
]

HANDOFF_SUMMARY_SKILLS = [
    "all-to-markdown",
    "audio",
    "azure-ai-transcription-py",
    "budget-trip-planner",
    "chat2duckdb",
    "code-executor",
    "compound-eng-debugging",
    "ctf-forensics",
    "data2visualization",
    "data-analysis",
    "data-analyst-cn",
    "data-anomaly-detector",
    "data-reconciliation-exceptions",
    "excel-xlsx",
    "file-converter",
    "generate-chart",
    "generate-report123",
    "linus-dev-tools",
    "log-analyzer-new",
    "markdown-converter",
    "meeting-autopilot",
    "meeting-minutes-organizer",
    "meeting-notes-assistant",
    "mh-openai-whisper-api",
    "mimo-asr",
    "multi-source-data-cleaner-pro",
    "ocr-rlocal",
    "ocr-screen",
    "openai-whisper",
    "screen-capture-hub",
    "screenshot-ocr",
    "senior-data-scientist",
    "sql-master",
    "sql-report-generator",
    "typora-visual-architect",
    "user-analysis-matrix",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "skill-composition-pilot/0.1",
            "Accept": "application/json, text/plain, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def safe_remove_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def download_skill(slug: str, output_root: Path) -> None:
    skill_dir = output_root / slug
    download_dir = output_root / "_downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    detail = fetch_json(f"{API_BASE}/api/v1/skills/{slug}")
    files = fetch_json(f"{API_BASE}/api/v1/skills/{slug}/files")
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "detail.json").write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    (skill_dir / "files.json").write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = download_dir / f"{slug}.zip"
    zip_path.write_bytes(fetch_bytes(f"{API_BASE}/api/v1/download?slug={slug}"))

    extracted_dir = skill_dir / "package"
    safe_remove_dir(extracted_dir)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extracted_dir)

    skill_md = extracted_dir / "SKILL.md"
    if not skill_md.exists():
        raise RuntimeError(f"{slug}: downloaded package does not contain SKILL.md")
    shutil.copyfile(skill_md, skill_dir / "SKILL.md")

    display_name = detail.get("skill", {}).get("displayName", slug)
    version = files.get("version", detail.get("latestVersion", {}).get("version", "unknown"))
    print(f"downloaded {slug} ({display_name}) version={version} -> {skill_dir / 'SKILL.md'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download SkillHub skill packages for local experiments.")
    parser.add_argument("--set", choices=["word-pilot", "handoff-summary"], default="word-pilot")
    parser.add_argument("--output", type=Path, default=project_root() / "skills")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep downloading the remaining skills if one SkillHub package is unavailable.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    slugs = WORD_PILOT_SKILLS if args.set == "word-pilot" else HANDOFF_SUMMARY_SKILLS
    failures = []
    for slug in slugs:
        try:
            download_skill(slug, args.output)
        except Exception as exc:
            failures.append((slug, str(exc)))
            print(f"failed {slug}: {exc}")
            if not args.continue_on_error:
                raise

    if failures:
        print("\nDownload failures:")
        for slug, message in failures:
            print(f"- {slug}: {message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
