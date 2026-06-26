# Word Multi-Pool Skill Experiment Design

## Goal

Measure whether model performance changes when the same task is solved with different combinations of skills sampled from multiple skill pools.

The task, input document, runtime protocol, and verifier stay fixed. Only the available skills change.

## Fixed Task

Input:

```text
data\original\Novels_Intro_Packet.docx
```

Instruction:

```text
Identify the first two body paragraphs, change only those two paragraphs to double line spacing, preserve all other text and formatting, and generate a Markdown summary.
```

Hidden verifier target paragraphs:

```text
paragraph 0
paragraph 2
```

These target indices are not shown in the agent prompt.

## Skill Pools

The current Word pilot uses three broad skill pools:

```text
document_processing
validation_audit
summary_reporting
```

Each pool contains several candidate skills:

```text
document_processing:
  word-docx
  office-document-specialist-suite
  file-converter
  all-to-markdown
  markdown-converter

validation_audit:
  code-executor
  data-reconciliation-exceptions
  data-anomaly-detector
  data-analysis
  user-analysis-matrix

summary_reporting:
  typora-visual-architect
  generate-report123
  markdown-converter
  sql-report-generator
  data2visualization
```

For a future OCR/data task, these pools can be replaced by pools such as OCR, data cleaning, audit, and report generation. The experiment harness stays the same.

## Conditions

```text
no_skill
multi_pool_sample_s01
multi_pool_sample_s02
multi_pool_sample_s03
multi_pool_sample_s04
multi_pool_sample_s05
multi_pool_sample_s06
multi_pool_sample_s07
multi_pool_sample_s08
multi_pool_sample_s09
multi_pool_sample_s10
multi_pool_all
```

Each `multi_pool_sample_*` condition samples one skill from every pool with a fixed seed. For example, a sampled condition contains:

```text
document_processing: one sampled skill
validation_audit: one sampled skill
summary_reporting: one sampled skill
```

The `multi_pool_all` condition provides every candidate skill from every pool and lets the model choose and combine skills.

The exact sample mapping is stored in:

```text
runs\condition_manifest.json
```

## Why Not Enumerate All Combinations?

Do not enumerate the full Cartesian product for pilot experiments. If there are four pools and each pool has five skills, choosing one skill from each pool already creates:

```text
5^4 = 625 conditions
```

If each pool can contribute any non-empty subset, the count becomes:

```text
(2^5 - 1)^4 = 923,521 conditions
```

The scalable protocol is:

1. sample a bounded number of cross-pool combinations with fixed seeds;
2. run an all-candidates condition where the model sees every pool and chooses skills itself;
3. compare no-skill, sampled combinations, and all-candidates selection.

## Main Run

Use soft import policy for artifact analysis:

```powershell
python .\glm_runner.py --all --import-policy warn --result-csv .\results\agent_runs_multi_pool_warn.csv
```

In `warn` mode, every condition should produce an edited DOCX and summary. If a generated script uses a package not supported by its skill condition, the run records a policy violation but still executes the artifact.

Use `block` only for stricter skill-gated analysis:

```powershell
python .\glm_runner.py --all --import-policy block --result-csv .\results\agent_runs_multi_pool_block.csv
```

## Primary Signals

- Per-condition verifier pass/fail.
- Failure mode from the verifier, especially wrong target paragraph, no line-spacing change, text drift, or formatting drift.
- Skill-policy violations from `skill_import_violations`.
- Comparison of:
  - no-skill baseline;
  - bounded random cross-pool sampled combinations;
  - all-candidates self-selection and composition.

This is intentionally small: one task, three skill pools, ten deterministic random cross-pool samples, and one all-candidates condition.
