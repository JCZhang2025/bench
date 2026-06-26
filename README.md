# Skill-Composition Pilot Experiments

This project uses a thin reusable framework plus task packages for skill-composition experiments.

The active task is `pubtables`, a local PubTables-style table extraction benchmark. The old `word_formatting` pilot is kept as a legacy smoke test, but it is no longer the main experiment because it only exercises one document-editing skill.

## Layout

```text
framework/
  conditions.py      shared skill-pool sampling and prompt generation
  runner.py          generic API agent runner

tasks/
  pubtables/
    task.py          task entrypoint and runner-facing interface
    verifier.py      PubTables artifact verifier
    skill_pools.json active skill-pool config
    task_spec.json   task prompt and output contract
    data/original/   local OCR word JSON fixture
    data/gold/       oracle artifacts and verifier rules
    runs/            prompts, agent workspaces, artifacts
    results/         verifier and agent CSV logs

skills/              downloaded SkillHub/custom skills
```

## PubTables Task

The task gives the agent a local PubTables-style OCR word JSON file with word text, bounding boxes, a table bounding box, and a small column hint. This is closer to PubTables-1M `*_Words_JSON` data than the earlier HTML proxy. The agent must reconstruct table structure and produce:

- `table_cells.csv`: structural cell inventory
- `metrics.csv`: normalized metric rows
- `audit.json`: row count, best method by dataset, and issues
- `summary.md`: grounded Markdown summary

The current experiment conditions are:

- `no_skill`: no skill document baseline
- `multi_pool_sample_s01` through `multi_pool_sample_s10`: one deterministic random skill from each pool
- `multi_pool_all`: all candidate skills from every pool, letting the model choose and combine

Current pools:

```text
table_reconstruction
metric_extraction_audit
summary_reporting
```

## Local Smoke Test

From PowerShell:

```powershell
cd E:\research\pilot_experiments
python tools\audit_pubtables_skills.py
python -m tasks.pubtables.task prepare --force
python -m tasks.pubtables.task oracle --condition multi_pool_sample_s02
python -m tasks.pubtables.task verify --condition multi_pool_sample_s02
```

## Run Agent

Set `GLM_API_KEY`, `ZAI_API_KEY`, or an explicit provider API key, then run one condition:

```powershell
cd E:\research\pilot_experiments
python framework\runner.py --task pubtables --condition multi_pool_sample_s02 --import-policy warn
```

Run all conditions:

```powershell
python framework\runner.py --task pubtables --all --import-policy warn --result-csv tasks\pubtables\results\agent_runs_multi_pool_warn.csv
```

Use `--import-policy warn` for the main pilot so every condition still produces artifacts for error analysis. Import violations are recorded but do not stop execution.

Use `--import-policy block` only for stricter skill-gated analysis:

```powershell
python framework\runner.py --task pubtables --all --import-policy block --result-csv tasks\pubtables\results\agent_runs_multi_pool_block.csv
```

## Docker

From PowerShell:

```powershell
cd E:\research\pilot_experiments
docker compose run --rm benchmark python -m tasks.pubtables.task prepare --force
docker compose run --rm benchmark python framework/runner.py --task pubtables --condition multi_pool_sample_s02 --import-policy warn
```

Create `.env` from `.env.example` and pass it explicitly if you want Docker to see the API key:

```powershell
docker compose --env-file .env run --rm benchmark python framework/runner.py --task pubtables --all --import-policy warn
```
