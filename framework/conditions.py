from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


DEFAULT_SAMPLE_SEEDS = list(range(1, 11))


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def skills_root() -> Path:
    return project_root() / "skills"


def unique_skills_from_pools(pools: dict[str, list[str]]) -> list[str]:
    seen: set[str] = set()
    skills: list[str] = []
    for pool_skills in pools.values():
        for skill in pool_skills:
            if skill not in seen:
                seen.add(skill)
                skills.append(skill)
    return skills


def sampled_skill_pools(seed: int, pools: dict[str, list[str]]) -> dict[str, list[str]]:
    rng = random.Random(seed)
    return {pool_name: [rng.choice(pool_skills)] for pool_name, pool_skills in pools.items()}


def build_conditions(
    skill_pools: dict[str, list[str]],
    sample_seeds: list[int] | None = None,
) -> dict[str, dict[str, Any]]:
    seeds = sample_seeds or DEFAULT_SAMPLE_SEEDS
    conditions: dict[str, dict[str, Any]] = {
        "no_skill": {
            "label": "No-skill baseline",
            "skills": [],
            "skill_pools": {},
            "condition_type": "baseline",
            "sample_seed": "",
            "pool_samples": {},
            "note": "No skill document is provided. This measures direct model behavior.",
        },
        "multi_pool_all": {
            "label": "All candidates from every skill pool",
            "skills": unique_skills_from_pools(skill_pools),
            "skill_pools": skill_pools,
            "condition_type": "multi_pool_all",
            "sample_seed": "",
            "pool_samples": {},
            "note": (
                "Provide every candidate skill from every pool and let the model choose "
                "and combine skill guidance."
            ),
        },
    }

    for seed in seeds:
        pools = sampled_skill_pools(seed, skill_pools)
        pool_samples = {pool_name: pool_skills[0] for pool_name, pool_skills in pools.items()}
        conditions[f"multi_pool_sample_s{seed:02d}"] = {
            "label": f"One sampled skill from each pool, seed {seed}",
            "skills": unique_skills_from_pools(pools),
            "skill_pools": pools,
            "condition_type": "multi_pool_sample",
            "sample_seed": seed,
            "pool_samples": pool_samples,
            "note": (
                "Provide exactly one deterministic random skill from each pool. "
                "Compare repeated sampled combinations against the all-candidates condition."
            ),
        }
    return conditions


def format_skill_pools(skill_pools: dict[str, list[str]]) -> str:
    if not skill_pools:
        return "- none"
    lines: list[str] = []
    for pool_name, skills in skill_pools.items():
        lines.append(f"### {pool_name}")
        lines.extend(f"- {skill}" for skill in skills)
        lines.append("")
    return "\n".join(lines).strip()


def format_pool_samples(pool_samples: dict[str, str]) -> str:
    if not pool_samples:
        return "- none"
    return "\n".join(f"- {pool}: {skill}" for pool, skill in pool_samples.items())


def load_skill_docs(skills: list[str]) -> str:
    if not skills:
        return "No external skill document is provided in this condition."

    blocks: list[str] = []
    for slug in skills:
        skill_md = skills_root() / slug / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8", errors="replace").strip()
            blocks.append(f"### {slug}\n\n```markdown\n{content}\n```")
        else:
            blocks.append(
                f"### {slug}\n\n"
                f"Skill document not downloaded yet. Expected path: {skill_md}"
            )
    return "\n\n".join(blocks)


def load_skill_pool_docs(skill_pools: dict[str, list[str]]) -> str:
    if not skill_pools:
        return load_skill_docs([])

    blocks: list[str] = []
    for pool_name, skills in skill_pools.items():
        blocks.append(f"## Pool: {pool_name}\n\n{load_skill_docs(skills)}")
    return "\n\n".join(blocks)


def build_prompt(
    condition: str,
    config: dict[str, Any],
    task_prompt: str,
    expected_artifacts: list[dict[str, str]],
) -> str:
    skills = config["skills"]
    skills_text = "\n".join(f"- {skill}" for skill in skills) if skills else "- none"
    skill_pools = config.get("skill_pools", {})
    artifact_lines = [
        f"- `{artifact['env']}` -> `artifacts/{artifact['filename']}`: {artifact['description']}"
        for artifact in expected_artifacts
    ]
    skill_docs = load_skill_pool_docs(skill_pools) if skill_pools else load_skill_docs(skills)
    return f"""# Experiment Condition: {condition}

{config["label"]}

## Condition Metadata

- condition_type: {config.get("condition_type", "")}
- sample_seed: {config.get("sample_seed", "")}

## Skill Pools

{format_skill_pools(skill_pools)}

## Pool Samples

{format_pool_samples(config.get("pool_samples", {}))}

## Task

{task_prompt}

## Available Skills

{skills_text}

## Available Skill Documents

{skill_docs}

## Condition Note

{config["note"]}

## Required Outputs

Save these artifacts:

{chr(10).join(artifact_lines)}

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
"""


def write_condition_prompts(
    task_root: Path,
    conditions: dict[str, dict[str, Any]],
    task_prompt: str,
    expected_artifacts: list[dict[str, str]],
) -> None:
    runs_dir = task_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {}
    for condition, config in conditions.items():
        run_dir = runs_dir / condition
        (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        prompt = build_prompt(condition, config, task_prompt, expected_artifacts)
        (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
        skills = config["skills"]
        (run_dir / "skills_given.txt").write_text(
            "\n".join(skills) if skills else "none",
            encoding="utf-8",
        )
        manifest[condition] = {
            "label": config["label"],
            "condition_type": config.get("condition_type", ""),
            "sample_seed": config.get("sample_seed", ""),
            "pool_samples": config.get("pool_samples", {}),
            "skill_pools": config.get("skill_pools", {}),
            "skills": skills,
        }
    (runs_dir / "condition_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

