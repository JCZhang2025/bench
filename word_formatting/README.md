# Word Formatting Multi-Pool Pilot

Task:

```text
Given Novels_Intro_Packet.docx, identify the first two body paragraphs, change only those two paragraphs to double line spacing, verify that all other text and formatting are unchanged, and generate a short Markdown formatting summary. No GUI, screenshot, external API, or cloud service should be used.
```

The agent-facing prompt does not reveal the hidden target paragraph indices or the verifier implementation.

## Current Conditions

The active experiment uses:

```text
no_skill
multi_pool_sample_s01..s10
multi_pool_all
```

Each sample condition chooses one deterministic random skill from every pool:

```text
document_processing
validation_audit
summary_reporting
```

The `multi_pool_all` condition provides every candidate skill from every pool and lets the model choose and combine skills.

The exact mapping is stored in:

```text
runs\condition_manifest.json
```

## Prepare

```powershell
cd C:\Users\Administrator\Documents\research\pilot_experiments\word_formatting
& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\word_task.py prepare
```

## Run GLM

Use `warn` mode for the main artifact-preserving pilot:

```powershell
& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\glm_runner.py --all --import-policy warn --result-csv .\results\agent_runs_multi_pool_warn.csv
```

Use `block` mode only for strict skill-gated analysis:

```powershell
& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\glm_runner.py --all --import-policy block --result-csv .\results\agent_runs_multi_pool_block.csv
```

## Summaries

```powershell
& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\export_agent_return_log.py --csv .\results\agent_runs_multi_pool_warn.csv --output .\results\AGENT_RETURN_LOG_multi_pool.md

& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\summarize_family_results.py --csv .\results\agent_runs_multi_pool_warn.csv --output .\results\MULTI_POOL_RESULT_SUMMARY.md
```

## Verifier

```powershell
& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\word_task.py verify-all
```

The verifier checks that the edited DOCX opens, text is unchanged, the hidden target paragraphs are double spaced, non-target formatting is unchanged, and `summary.md` exists.
