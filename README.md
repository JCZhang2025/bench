# Skill-Composition Pilot Experiments

This project now uses a thin reusable framework plus task packages.

The active task is `pubtables`, a local PubTables-style table extraction benchmark. The old `word_formatting` pilot is kept as a legacy smoke test, but it is no longer the main experiment because it only exercises one document-editing skill.

## Layout

```text
framework/
  conditions.py      shared skill-pool sampling and prompt generation
  runner.py          generic GLM agent runner

tasks/
  pubtables/
    task.py          task prompt, skill pools, fixture, oracle, verifier
    data/            local HTML fixture and hidden verifier target
    runs/            prompts, agent workspaces, artifacts
    results/         verifier and agent CSV logs

skills/              downloaded SkillHub skills
```

## PubTables Task

The task gives the agent a local PubTables-style HTML table with multi-row headers and span attributes. The agent must produce:

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
table_extraction
data_cleaning
validation_audit
summary_reporting
```

## Local Smoke Test

From PowerShell:

```powershell
cd C:\Users\Administrator\Documents\research\pilot_experiments
python -m tasks.pubtables.task prepare --force
python -m tasks.pubtables.task oracle --condition multi_pool_sample_s02
python -m tasks.pubtables.task verify --condition multi_pool_sample_s02
```

## Run GLM Agent

Set `GLM_API_KEY` or `ZAI_API_KEY`, then run one condition:

```powershell
cd C:\Users\Administrator\Documents\research\pilot_experiments
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
cd C:\Users\Administrator\Documents\research\pilot_experiments
docker compose run --rm benchmark python -m tasks.pubtables.task prepare --force
docker compose run --rm benchmark python framework/runner.py --task pubtables --condition multi_pool_sample_s02 --import-policy warn
```

Create `.env` from `.env.example` and pass it explicitly if you want Docker to see the API key:

```powershell
docker compose --env-file .env run --rm benchmark python framework/runner.py --task pubtables --all --import-policy warn
```

