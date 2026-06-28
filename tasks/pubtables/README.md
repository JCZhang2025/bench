# PubTables-Style OCR Word Task

This task is the scalable replacement for the Word formatting smoke test.

The agent receives a local PubTables-style OCR word JSON file: page words with text, bounding boxes, a table bounding box, and a small column hint. This is closer to PubTables-1M `*_Words_JSON` data than the earlier HTML proxy. It must reconstruct the table and produce:

- `table_cells.csv`: structural cell inventory
- `metrics.csv`: normalized metric rows
- `audit.json`: row count, best method by dataset, and issues
- `summary.md`: grounded Markdown summary

The active three-pool design is `table_reconstruction`, `metric_extraction_audit`, and `summary_reporting`. It includes answer-free custom skills for OCR word-box structure reconstruction, bbox row/column parsing, table-boundary noise filtering, header span detection, metric auditing, artifact contract checking, and grounded summaries. These skills are procedural and do not include fixture-specific answers. See `skill_pool_manifest.json`.

Run locally:

```powershell
python tools\audit_pubtables_skills.py
python -m tasks.pubtables.task prepare --force
python -m tasks.pubtables.task oracle --condition multi_pool_sample_s02
python -m tasks.pubtables.task verify --condition multi_pool_sample_s02
```

Run the GLM agent:

```powershell
python framework\runner.py --task pubtables --condition multi_pool_sample_s02 --import-policy warn
```

Agent outputs are written under a non-overwriting run ID:

```text
runs\<condition>\agent_runs\<run_id>\
```

Use `--run-id my_run_name` to make the ID explicit.
