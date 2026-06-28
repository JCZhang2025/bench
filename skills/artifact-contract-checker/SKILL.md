---
name: artifact-contract-checker
description: Use when validating that benchmark agent outputs satisfy required file, schema, JSON, CSV, and grounded Markdown artifact contracts.
---

# Artifact Contract Checker

Use this skill to make sure the final outputs are complete and parseable before finishing the task.

## Contract Checks

1. Confirm every required output path is written.
2. Confirm CSV files have the required headers exactly once.
3. Confirm CSV rows parse without delimiter drift or accidental multiline corruption.
4. Confirm numeric fields are stored in a machine-readable form.
5. Confirm JSON artifacts parse and contain the requested top-level keys.
6. Confirm Markdown summaries are grounded in produced data and do not introduce unsupported claims.
7. Record validation issues in the audit artifact instead of silently fixing them without trace.

## Guardrails

- Validate against the task instructions and produced artifacts only.
- Do not inspect oracle outputs, verifier code, or expected-answer constants.
- Do not add hidden helper files as substitutes for required artifacts.
