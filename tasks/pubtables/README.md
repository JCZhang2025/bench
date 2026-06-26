# PubTables-Style Task

This task is the scalable replacement for the Word formatting smoke test.

The agent receives a local PubTables-style HTML table with multi-row headers and span attributes. It must produce:

- `table_cells.csv`: structural cell inventory
- `metrics.csv`: normalized metric rows
- `audit.json`: row count, best method by dataset, and issues
- `summary.md`: grounded Markdown summary

Run locally:

```powershell
python -m tasks.pubtables.task prepare --force
python -m tasks.pubtables.task oracle --condition multi_pool_sample_s02
python -m tasks.pubtables.task verify --condition multi_pool_sample_s02
```

Run the GLM agent:

```powershell
python framework\runner.py --task pubtables --condition multi_pool_sample_s02 --import-policy warn
```

