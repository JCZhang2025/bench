# Experiment Condition: multi_pool_sample_s10

One sampled skill from each pool, seed 10

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 10

## Skill Pools

### table_extraction
- excel-xlsx

### data_cleaning
- multi-source-data-cleaner-pro

### validation_audit
- data-analysis

### summary_reporting
- sql-report-generator

## Pool Samples

- table_extraction: excel-xlsx
- data_cleaning: multi-source-data-cleaner-pro
- validation_audit: data-analysis
- summary_reporting: sql-report-generator

## Task

Given a local PubTables-style scientific table in HTML, extract the table structure, normalize the metric rows, audit the extracted values, and write a short grounded Markdown summary.

The input table has multi-row headers and span attributes. Treat header cells, row spans, and column spans as part of the table structure. Exclude caption text and footnotes from the normalized metric rows.

Required normalized metric fields:
- method
- dataset
- accuracy
- f1
- notes

For the audit, report the number of normalized metric rows, the best method by F1 score for each dataset, and any extraction or validation issues you find.

## Available Skills

- excel-xlsx
- multi-source-data-cleaner-pro
- data-analysis
- sql-report-generator

## Available Skill Documents

## Pool: table_extraction

### excel-xlsx

```markdown
---
name: Excel / XLSX
slug: excel-xlsx
version: 1.0.2
homepage: https://clawic.com/skills/excel-xlsx
description: "Create, inspect, and edit Microsoft Excel workbooks and XLSX files with reliable formulas, dates, types, formatting, recalculation, and template preservation. Use when (1) the task is about Excel, `.xlsx`, `.xlsm`, `.xls`, `.csv`, or `.tsv`; (2) formulas, formatting, workbook structure, or compatibility matter; (3) the file must stay reliable after edits."
changelog: Tightened formula anchoring, recalculation, and model traceability after a stricter external spreadsheet audit.
metadata: {"clawdbot":{"emoji":"📗","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## When to Use

Use when the main artifact is a Microsoft Excel workbook or spreadsheet file, especially when formulas, dates, formatting, merged cells, workbook structure, or cross-platform behavior matter.

## Core Rules

### 1. Choose the workflow by job, not by habit

- Use `pandas` for analysis, reshaping, and CSV-like tasks.
- Use `openpyxl` when formulas, styles, sheets, comments, merged cells, or workbook preservation matter.
- Treat CSV as plain data exchange, not as an Excel feature-complete format.
- Reading values, preserving a live workbook, and building a model from scratch are different spreadsheet jobs.

### 2. Dates are serial numbers with legacy quirks

- Excel stores dates as serial numbers, not real date objects.
- The 1900 date system includes the false leap-day bug, and some workbooks use the 1904 system.
- Time is fractional day data, so formatting and conversion both matter.
- Date correctness is not enough if the number format still displays the wrong thing to the user.

### 3. Keep calculations in Excel when the workbook should stay live

- Write formulas into cells instead of hardcoding derived results from Python.
- Use references to assumption cells instead of magic numbers inside formulas.
- Cached formula values can be stale, so do not trust them blindly after edits.
- Check copied formulas for wrong ranges, wrong sheets, and silent off-by-one drift before delivery.
- Absolute and relative references are part of the logic, so copied formulas can be wrong even when they still "work".
- Test new formulas on a few representative cells before filling them across a whole block.
- Verify denominators, named ranges, and precedent cells before shipping formulas that depend on them.
- A workbook should ship with zero formula errors, not with known `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or circular-reference fallout left for the user to fix.
- For model-style work, document non-obvious hardcodes, assumptions, or source inputs in comments or nearby notes.

### 4. Protect data types before Excel mangles them

- Long identifiers, phone numbers, ZIP codes, and leading-zero values should usually be stored as text.
- Excel silently truncates numeric precision past 15 digits.
- Mixed text-number columns need explicit handling on read and on write.
- Scientific notation, auto-parsed dates, and stripped leading zeros are common corruption, not cosmetic issues.

### 5. Preserve workbook structure before changing content

- Existing templates override generic styling advice.
- Only the top-left cell of a merged range stores the value.
- Hidden rows, hidden columns, named ranges, and external references can still affect formulas and outputs.
- Shared strings, defined names, and sheet-level conventions can matter even when the visible cells look simple.
- Match styles for newly filled cells instead of quietly introducing a new visual system.
- If the workbook is a template, preserve sheet order, widths, freezes, filters, print settings, validations, and visual conventions unless the task explicitly changes them.
- Conditional formatting, filters, print areas, and data validation often carry business meaning even when users only mention the numbers.
- If there is no existing style guide and the file is a model, keep editable inputs visually distinguishable from formulas, but never override an established template to force a generic house style.

### 6. Recalculate and review before delivery

- Formula strings alone are not enough if the recipient needs current values.
- `openpyxl` preserves formulas but does not calculate them.
- Verify no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or circular-reference fallout remains.
- If layout matters, render or visually review the workbook before calling it finished.
- Be careful with read modes: opening a workbook for values only and then saving can flatten formulas into static values.
- If assumptions or hardcoded overrides must stay, make them obvious enough that the next editor can audit the workbook.

### 7. Scale the workflow to the file size

- Large workbooks can fail for boring reasons: memory spikes, padded empty rows, and slow full-sheet reads.
- Use streaming or chunked reads when the file is big enough that loading everything at once becomes fragile.
- Large-file workflows also need narrower reads, explicit dtypes, and sheet targeting to avoid accidental damage.

## Common Traps

- Type inference on read can leave numbers as text or convert IDs into damaged numeric values.
- Column indexing varies across tools, so off-by-one mistakes are common in generated formulas.
- Newlines in cells need wrapping to display correctly.
- External references break easily when source files move.
- Password protection in old Excel workflows is not serious security.
- `.xlsm` can contain macros, and `.xls` remains a tighter legacy format.
- Large files may need streaming reads or more careful memory handling.
- Google Sheets and LibreOffice can reinterpret dates, formulas, or styling differently from Excel.
- Dynamic array or newer Excel functions like `FILTER`, `XLOOKUP`, `SORT`, or `SEQUENCE` may fail or degrade in older viewers.
- A workbook can look fine while still carrying stale cached values from a prior recalculation.
- Saving the wrong workbook view can replace formulas with cached values and quietly destroy a live model.
- Copying formulas without checking relative references can push one bad range across an entire block.
- Hidden sheets, named ranges, validations, and merged areas often keep business logic that is invisible in a quick skim.
- A workbook can appear numerically correct while still failing because filters, conditional formats, print settings, or data validation were stripped.
- A workbook can be numerically correct and still fail visually because wrapped text, clipped labels, or narrow columns were never reviewed.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `csv` — Plain-text tabular import and export workflows.
- `data` — General data handling patterns before spreadsheet output.
- `data-analysis` — Higher-level analysis that can feed workbook deliverables.

## Feedback

- If useful: `clawhub star excel-xlsx`
- Stay updated: `clawhub sync`
```

## Pool: data_cleaning

### multi-source-data-cleaner-pro

```markdown
---
name: multi-source-data-cleaner
description: |
  EN: Production-grade data cleaning across heterogeneous sources (CSV/Excel/JSON/Parquet/SQL dumps/log files). Profiles schemas, detects encoding/delimiter, normalizes types, handles missing values, deduplicates fuzzy records, reconciles schema across sources, and outputs a clean unified dataset plus a full data-quality report. Use when user provides one or more dirty datasets and asks "清洗数据 / 合并数据 / 去重 / 缺失值处理 / data cleaning / dedup / schema reconcile".
  中文：跨异构来源（CSV/Excel/JSON/Parquet/SQL 导出/日志文件）的工业级数据清洗。剖析 schema、自动识别编码与分隔符、归一化类型、处理缺失值、模糊去重、跨源字段对齐，输出统一的干净数据集与完整数据质量报告。当用户提供脏数据并要求"清洗/合并/去重/缺失值处理"时触发。
version: 1.0.0
metadata:
  openclaw:
    emoji: "🧹"
    homepage: https://github.com/openclaw-skills/multi-source-data-cleaner
    requires:
      bins:
        - python3
    envVars:
      - name: CLEANER_DEFAULT_ENCODING
        required: false
        description: Fallback encoding when auto-detection fails. Defaults to utf-8.
      - name: CLEANER_PII_POLICY
        required: false
        description: PII handling policy, one of `keep|mask|drop`. Defaults to `mask`.
---

# Multi-Source Data Cleaner · 多源数据清洗

> Drop a folder of CSVs, Excels, and JSONs from 5 different teams; get back a single clean table, a deduplication report, and a data-quality scorecard. No manual schema mapping required.
>
> 把 5 个部门各种格式的 CSV/Excel/JSON 一起扔进来，自动给你一张干净统一表、去重报告、数据质量评分。无需手工配字段映射。

---

## 🎯 When to Use · 何时使用

**Trigger keywords (中文):** 清洗数据、数据清洗、合并数据、去重、缺失值、字段对齐、schema 合并、数据质量、数据预处理、ETL

**Trigger keywords (EN):** clean data, data cleaning, deduplicate, missing values, schema reconcile, ETL, data quality, profile dataset

**Supported sources:**

| 格式 / Format | 说明 |
|---|---|
| CSV / TSV | Auto-detect encoding (UTF-8/GBK/BIG5), delimiter, quote char, header row |
| Excel (.xlsx/.xls/.xlsm) | Multi-sheet, merged cells, formula values |
| JSON / JSONL / NDJSON | Nested structures auto-flattened |
| Parquet / Feather | Native columnar reading |
| SQL dumps (.sql) | MySQL / PostgreSQL INSERT extraction |
| Log files | Pattern-detected structured lines |

**Do NOT use when:**
- Input is unstructured free text (use NLP extraction skills first)
- Input is binary/proprietary format with no parser (Adobe Indesign, custom CAD, etc.)
- User wants real-time streaming cleaning (this is batch-oriented)

---

## 📋 Cleaning Pipeline · 清洗流程

### Step 1: Source profiling · 源剖析

```bash
python3 scripts/profile.py --input <file-or-dir> --out profile.json
```

For each source produces:
- File format, encoding, line endings
- Schema (columns, inferred types, null rates, cardinality)
- Sample rows
- Quality flags: encoding mismatches, type inconsistencies, suspicious patterns

### Step 2: Type inference & normalization · 类型推断与归一

`scripts/normalize_types.py` standardizes:
- Numbers: thousands separators, scientific notation, currency symbols → numeric
- Dates: 50+ formats (`2024-03-15`, `2024/3/15`, `15 Mar 2024`, `民国113年3月15日`, Excel serial) → ISO 8601
- Booleans: `Y/N/是/否/0/1/true/false/T/F/✓/✗` → boolean
- Phone numbers: normalize to E.164
- Chinese names: full-width / half-width normalization
- IDs: zero-padding, prefix detection

### Step 3: Missing value handling · 缺失值处理

Per-column strategy (configurable in `templates/missing_strategy.json`):
- `drop_row` — drop rows where this column is null
- `mean|median|mode` — statistical imputation (with imputation flag column)
- `constant:<value>` — fill with literal
- `forward_fill` — for time-series
- `interpolate` — linear/spline for numeric series
- `keep_null` — preserve as null (default for unknown)

**Critical rule:** every imputed value gets a sidecar `<col>_imputed` boolean column so downstream analysis can distinguish original vs. imputed data.

### Step 4: Schema reconciliation · Schema 合并

`scripts/reconcile_schema.py` aligns columns across sources using:
- Exact name match
- Fuzzy match (Levenshtein + Chinese pinyin)
- Type compatibility check
- User-supplied mapping override (`--mapping mapping.yaml`)

Outputs a `crosswalk.json` documenting every column mapping for audit.

### Step 5: Fuzzy deduplication · 模糊去重

`scripts/dedup.py` uses configurable blocking + record linkage:
- Blocking keys to narrow candidates (e.g. first 3 chars of name + phone last 4)
- Similarity scoring: Jaro-Winkler for names, token-set for addresses, exact for IDs
- Threshold-based merge with conflict resolution rules (newest wins / longest non-null / authoritative source priority)

Reports merge groups for human review before commit.

### Step 6: PII handling · 隐私字段处理

Per `CLEANER_PII_POLICY`:
- `keep` — leave as-is (use only with explicit user authorization)
- `mask` — partial mask (`王*三`, `138****5678`, `4400****1234`)
- `drop` — remove column entirely

Auto-detection of common PII: 姓名、身份证号、手机号、邮箱、地址、银行卡号、IP、车牌号。

### Step 7: Data quality report · 数据质量报告

```bash
python3 scripts/quality_report.py --input cleaned.parquet --out dq_report.md
```

Six dimensions (per DAMA-DMBOK):
- Completeness (完整性)
- Accuracy (准确性, sample validation)
- Consistency (一致性, cross-column rules)
- Timeliness (时效性)
- Uniqueness (唯一性, dedup outcome)
- Validity (有效性, regex/range checks)

Each scored 0-100 with drill-down detail.

---

## 📤 Output Format · 输出格式

```
output/
├── cleaned.parquet              # main clean dataset (or .csv if requested)
├── crosswalk.json               # source → target schema mapping
├── dedup_groups.json            # merged record groups for review
├── dq_report.md                 # human-readable data quality report
├── dq_report.json               # machine-readable DQ metrics
├── audit/
│   ├── per_source_profile.json
│   ├── imputation_log.csv
│   └── pii_actions.log
└── provenance.csv               # row-level lineage: which source each row came from
```

---

## ⚠️ Safety & Compliance · 安全合规

1. **No silent data loss** — every drop/merge/impute action logged in `audit/`.
2. **Imputation flags mandatory** — imputed values marked so they cannot masquerade as originals.
3. **PII default mask** — unless user explicitly authorizes `keep`, PII is masked.
4. **Reversibility** — original sources never modified; cleaning is non-destructive.
5. **Dedup human-in-the-loop** — fuzzy merges above threshold but below 0.95 confidence flagged for review, not auto-committed.
6. **No external network calls** — all processing local; no data leaves the workspace.

> 不静默丢数据，所有删除/合并/填充均记录到 audit/；填充值带标志列防止假冒原值；隐私字段默认脱敏；原始文件不修改；模糊去重低置信度合并强制人工复核；不向外部上传任何数据。

---

## 🚀 Usage Examples · 使用示例

### Example 1: Clean a single messy CSV

```bash
python3 scripts/run_pipeline.py \
  --input sales_q1.csv \
  --output-dir ./cleaned_q1/ \
  --pii-policy mask
```

### Example 2: Merge 3 source CSVs into unified customer table

```bash
python3 scripts/run_pipeline.py \
  --input ./customer_sources/ \
  --output-dir ./unified_customers/ \
  --dedup-keys name,phone \
  --priority-source crm_export.csv
```

### Example 3: Schema reconcile with manual mapping override

```bash
python3 scripts/run_pipeline.py \
  --input ./multi_team_data/ \
  --mapping mapping.yaml \
  --output-dir ./unified/
```

`mapping.yaml`:
```yaml
target_schema:
  customer_id: { aliases: [客户ID, cust_id, ClientID, 编号] }
  phone:        { aliases: [手机, 联系电话, Mobile, tel] }
  signup_date:  { aliases: [注册日期, 开户日期, CreatedAt], type: date }
```

### Example 4: Quality scan only (read-only audit)

```bash
python3 scripts/profile.py --input ./suspicious_dataset/ --out dq_audit.md --read-only
```

---

## 🧪 Testing · 测试

```bash
cd tests && python3 -m pytest -v
```

Fixtures include:
- Encoding test set (UTF-8 BOM, GBK, BIG5, Latin1)
- 12 date format variants
- Schema-drift simulation across 5 source files
- Synthetic dedup dataset (10k records with controlled duplication)
- PII regression suite

---

## 📚 References · 参考资料

- DAMA-DMBOK Data Quality dimensions
- Fellegi-Sunter probabilistic record linkage
- Jaro-Winkler distance for fuzzy match
- `pandas`, `pyarrow`, `recordlinkage` library docs

## 🏷️ Tags · 标签

`data` `ETL` `data-cleaning` `dedup` `schema-reconcile` `data-quality` `数据清洗` `多源整合` `去重` `数据质量`
```

## Pool: validation_audit

### data-analysis

```markdown
---
name: Data Analysis
slug: data-analysis
version: 1.0.2
homepage: https://clawic.com/skills/data-analysis
description: "Data analysis and visualization. Query databases, generate reports, automate spreadsheets, and turn raw data into clear, actionable insights. Use when (1) you need to analyze, visualize, or explain data; (2) the user wants reports, dashboards, or metrics turned into a decision; (3) the work involves SQL, Python, spreadsheets, BI tools, or notebooks; (4) you need to compare segments, cohorts, funnels, experiments, or time periods; (5) the user explicitly installs or references the skill for the current task."
changelog: Added metric contracts, chart guidance, and decision brief templates for more reliable analysis.
metadata: {"clawdbot":{"emoji":"D","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## When to Use

Use this skill when the user needs to analyze, explain, or visualize data from SQL, spreadsheets, notebooks, dashboards, exports, or ad hoc tables.

Use it for KPI debugging, experiment readouts, funnel or cohort analysis, anomaly reviews, executive reporting, and quality checks on metrics or query logic.

Prefer this skill over generic coding or spreadsheet help when the hard part is analytical judgment: metric definition, comparison design, interpretation, or recommendation.

User asks about: analyzing data, finding patterns, understanding metrics, testing hypotheses, cohort analysis, A/B testing, churn analysis, or statistical significance.

## Core Principle

Analysis without a decision is just arithmetic. Always clarify: **What would change if this analysis shows X vs Y?**

## Methodology First

Before touching data:
1. **What decision** is this analysis supporting?
2. **What would change your mind?** (the real question)
3. **What data do you actually have** vs what you wish you had?
4. **What timeframe** is relevant?

## Statistical Rigor Checklist

- [ ] Sample size sufficient? (small N = wide confidence intervals)
- [ ] Comparison groups fair? (same time period, similar conditions)
- [ ] Multiple comparisons? (20 tests = 1 "significant" by chance)
- [ ] Effect size meaningful? (statistically significant != practically important)
- [ ] Uncertainty quantified? ("12-18% lift" not just "15% lift")

## Architecture

This skill does not require local folders, persistent memory, or setup state.

Use the included reference files as lightweight guides:
- `metric-contracts.md` for KPI definitions and caveats
- `chart-selection.md` for visual choice and chart anti-patterns
- `decision-briefs.md` for stakeholder-facing outputs
- `pitfalls.md` and `techniques.md` for analytical rigor and method choice

## Quick Reference

Load only the smallest relevant file to keep context focused.

| Topic | File |
|-------|------|
| Metric definition contracts | `metric-contracts.md` |
| Visual selection and chart anti-patterns | `chart-selection.md` |
| Decision-ready output formats | `decision-briefs.md` |
| Failure modes to catch early | `pitfalls.md` |
| Method selection by question type | `techniques.md` |

## Core Rules

### 1. Start from the decision, not the dataset
- Identify the decision owner, the question that could change a decision, and the deadline before doing analysis.
- If no decision would change, reframe the request before computing anything.

### 2. Lock the metric contract before calculating
- Define entity, grain, numerator, denominator, time window, timezone, filters, exclusions, and source of truth.
- If any of those are ambiguous, state the ambiguity explicitly before presenting results.

### 3. Separate extraction, transformation, and interpretation
- Keep query logic, cleanup assumptions, and analytical conclusions distinguishable.
- Never hide business assumptions inside SQL, formulas, or notebook code without naming them in the write-up.

### 4. Choose visuals to answer a question
- Select charts based on the analytical question: trend, comparison, distribution, relationship, composition, funnel, or cohort retention.
- Do not add charts that make the deck look fuller but do not change the decision.

### 5. Brief every result in decision format
- Every output should include the answer, evidence, confidence, caveats, and recommended next action.
- If the output is going to a stakeholder, translate the method into business implications instead of leading with technical detail.

### 6. Stress-test claims before recommending action
- Segment by obvious confounders, compare the right baseline, quantify uncertainty, and check sensitivity to exclusions or time windows.
- Strong-looking numbers without robustness checks are not decision-ready.

### 7. Escalate when the data cannot support the claim
- Block or downgrade conclusions when sample size is weak, the source is unreliable, definitions drifted, or confounding is unresolved.
- It is better to say "unknown yet" than to produce false confidence.

## Common Traps

- Reusing a KPI name after changing numerator, denominator, or exclusions -> trend comparisons become invalid.
- Comparing daily, weekly, and monthly grains in one chart -> movement looks real but is mostly aggregation noise.
- Showing percentages without underlying counts -> leadership overreacts to tiny denominators.
- Using a pretty chart instead of the right chart -> the output looks polished but hides the actual decision signal.
- Hunting for interesting cuts after seeing the result -> narrative follows chance instead of evidence.
- Shipping automated reports without metric owners or caveats -> bad numbers spread faster than they can be corrected.
- Treating observational patterns as causal proof -> action plans get built on correlation alone.

## Approach Selection

| Question type | Approach | Key output |
|---------------|----------|------------|
| "Is X different from Y?" | Hypothesis test | p-value + effect size + CI |
| "What predicts Z?" | Regression/correlation | Coefficients + R² + residual check |
| "How do users behave over time?" | Cohort analysis | Retention curves by cohort |
| "Are these groups different?" | Segmentation | Profiles + statistical comparison |
| "What's unusual?" | Anomaly detection | Flagged points + context |

For technique details and when to use each, see `techniques.md`.

## Output Standards

1. **Lead with the insight**, not the methodology
2. **Quantify uncertainty** - ranges, not point estimates
3. **State limitations** - what this analysis can't tell you
4. **Recommend next steps** - what would strengthen the conclusion

## Red Flags to Escalate

- User wants to "prove" a predetermined conclusion
- Sample size too small for reliable inference
- Data quality issues that invalidate analysis
- Confounders that can't be controlled for

## External Endpoints

This skill makes no external network requests.

| Endpoint | Data Sent | Purpose |
|----------|-----------|---------|
| None | None | N/A |

No data is sent externally.

## Security & Privacy

Data that leaves your machine:
- Nothing by default.

Data that stays local:
- Nothing by default.

This skill does NOT:
- Access undeclared external endpoints.
- Store credentials or raw exports in hidden local memory files.
- Create or depend on local folder systems for persistence.
- Create automations or background jobs without explicit user confirmation.
- Rewrite its own instruction source files.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `sql` - query design and review for reliable data extraction.
- `csv` - cleanup and normalization for tabular inputs before analysis.
- `dashboard` - implementation patterns for KPI visualization layers.
- `report` - structured stakeholder-facing deliverables after analysis.
- `business-intelligence` - KPI systems and operating cadence beyond one-off analysis.

## Feedback

- If useful: `clawhub star data-analysis`
- Stay updated: `clawhub sync`
```

## Pool: summary_reporting

### sql-report-generator

```markdown
# sql-report-generator - 生产级报告生成 Skill

## ⚠️ 使用前必读

本 Skill 需要 Python 依赖。**首次使用前必须安装依赖**：

```bash
skillhub_install install_skill sql-report-generator
```

工具会自动检测 Python3 环境、pip 可用性，并安装所有依赖。

### 依赖安装方式

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| **自动安装（推荐）** | `skillhub_install install_skill sql-report-generator` | 一键安装，自动处理 |
| **手动安装** | `pip install -r requirements.txt` | 熟悉 Python 环境的用户 |

### 无依赖使用（受限模式）

如果无法安装依赖，本 Skill 提供以下**降级能力**：

✅ **可用功能**：
- 报告结构设计建议
- 报告模板推荐（基于业务场景）
- 数据展示规范指导
- 报告写作建议

❌ **不可用功能**：
- 表格/矩阵/切片器生成
- HTML/PDF 报告导出
- AI 自动洞察生成
- 与 sql-master / sql-dataviz 联动

---

## ⚠️ 重要规则（必须遵守）

### 规则一：洞察与建议必须基于数据分析得出

> **🚨 严禁在真实数据场景下手动编写洞察和建议**

当接入真实数据时，**深度洞察**和**运营建议**必须通过数据分析得出结论：

```python
# ✅ 正确做法：使用自动分析
from sql_report_generator.scripts.ai_insights import quick_insights

# 分析数据并生成洞察
report = quick_insights(df, date_col="date", value_cols=["sales"])
insights = report.to_markdown()  # 统计分析得出的洞察
recommendations = report.get_recommendations()  # 统计分析得出的建议

# ❌ 错误做法：手动硬编码
# insights = "GMV 同比增长 15%，转化率提升..."  # 禁止！
```

**注意**：
- 输出时不要使用"AI洞察"、"AI分析"等词汇
- 应使用"洞察分析"、"统计分析"、"数据分析"等中性表述

**可接受的场景**：
- 演示/测试用的模拟数据
- 用户明确要求使用示例洞察

---

### 规则二：输出文件前必须仔细检查

> **🚨 每次生成看板文件后，必须先自行检查，确认无错误后再交付**

生成 HTML/PDF 文件后，**在输出前**检查清单：

| 检查项 | 说明 |
|--------|------|
| ✅ 图表是否正确渲染 | 无空白、无报错、无乱码 |
| ✅ 文字是否正常显示 | 中文、数字、符号正确，无 `{s:,.0f}` 等占位符 |
| ✅ 数据是否一致 | KPI、图表、表格数据匹配 |
| ✅ 交互是否正常 | hover、点击等功能 |
| ✅ 无工具栏/Logo | displayModeBar: false, displaylogo: false |
| ✅ 洞察与建议内容 | 无乱码、无占位符、内容完整 |

**常见错误及修复方法**：

| 错误类型 | 原因 | 修复 |
|---------|------|------|
| `{s:,.0f}` | f-string 嵌套错误 | 使用 `str()` 或预先格式化 |
| `\u00a5{...}` | Unicode 转义错误 | 使用 `\u00a5` 或 `¥` |
| `{{}}` 乱码 | 双大括号转义问题 | 确保 `{{` 在 f-string 外 |

---

## 🔗 Skill 协作关系

本 Skill 与 **sql-master**、**sql-dataviz** 组成完整的数据分析流水线：

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────────┐
│ sql-master  │ ──► │ sql-dataviz  │ ──► │ sql-report-generator   │
│  (数据层)   │     │  (可视化层)  │     │      (报告层)          │
└─────────────┘     └──────────────┘     └────────────────────────┘
      │                   │                        │
      ▼                   ▼                        ▼
   SQL 查询           图表生成                 HTML 报告
   数据获取           PNG/HTML                 AI 洞察
   格式转换           Dashboard                数据表格
```

### 协作模式

| 模式 | 组合 | 适用场景 |
|------|------|---------|
| **单独使用** | sql-report-generator | 已有图表/数据，仅需组织报告 |
| **可视化报告** | sql-dataviz + sql-report-generator | 图表 → 报告（无 SQL） |
| **数据报告** | sql-master + sql-report-generator | SQL 查询 → 报告（跳过可视化） |
| **完整流程** | sql-master + sql-dataviz + sql-report-generator | 完整数据分析报告 |

### 🥇 最优使用方式：三 Skill 串联

```python
from scripts.unified_pipeline import UnifiedPipeline

result = (
    UnifiedPipeline("销售分析")
    .from_file("sales.csv")                                    # sql-master: 数据获取
    .query("SELECT region, SUM(sales) as total FROM data GROUP BY region")
    .interactive_chart("bar", x_col="region", y_col="total")   # sql-dataviz: 可视化
    .insights(value_cols=["total"])                            # AI 洞察
    .report(title="销售报告", output="report.html")            # sql-report-generator: 报告
)
```

### 决策指南

```
你需要什么？
├─ 仅报告组织 → sql-report-generator 单独使用
├─ 图表 + 报告（无 SQL）→ sql-dataviz + sql-report-generator
├─ SQL + 报告（跳过可视化）→ sql-master + sql-report-generator
└─ 完整分析报告 → sql-master + sql-dataviz + sql-report-generator ✅ 推荐
```

---

## 新增功能：AI 自动洞察生成模块

### `scripts/ai_insights.py`

纯统计分析（无需外部 AI API），自动从 DataFrame 生成结构化洞察和建议：

```python
from scripts.ai_insights import quick_insights, InsightGenerator

# 一键生成洞察
report = quick_insights(df, date_col="date", value_cols=["sales", "quantity"])
print(report.to_markdown())   # Markdown 格式
print(report.to_html())       # HTML 格式（可嵌入报告）
print(report.to_dict())       # JSON 格式

# 自定义分析
gen = InsightGenerator(df, date_col="date", value_cols=["sales"])
report = gen.generate_all()
# 包含：异常检测 / 趋势 / 相关性 / TOP N / 分布 / 季节性 / 对比
# 自动生成运营建议
```

**7 种洞察类型**：异常检测（Z-score + IQR + 环比突变）、趋势检测（线性回归）、
相关性检测（Pearson）、TOP N 分析（帕累托 80/20）、分布检测（偏度/峰度）、
季节性检测、对比分析（分组差异）

**3 种输出格式**：Markdown / HTML / JSON

## 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install pandas numpy matplotlib jinja2 scipy
```

## 概述

将 SQL 查询结果和可视化图表组织成**生产级报告**。支持表格、矩阵、切片器、交互导航、分页报表等 **8 种交互组件**，可导出为 HTML、PDF、JSON 等多种格式。

与 **sql-master** 和 **sql-dataviz** 无缝协作，形成完整的数据分析流程。

## 核心能力

### 1️⃣ 表格与矩阵（2种）

| 组件 | 场景 | 特性 |
|------|------|------|
| **表格** | 明细数据展示 | 支持排序、筛选、条件格式 |
| **矩阵** | 跨维度分析 | 支持多级钻取、热力图 |

### 2️⃣ 交互与筛选（3种）

| 组件 | 场景 | 特性 |
|------|------|------|
| **切片器** | 多维度筛选 | 按钮/列表/日期范围样式 |
| **按钮导航** | 报表页面跳转 | 支持书签、URL 跳转 |
| **图像视觉对象** | 品牌 logo、产品图片 | 静态/动态图片嵌入 |

### 3️⃣ 报告组织（3种）

| 组件 | 场景 | 特性 |
|------|------|------|
| **文本框与形状** | 报表标题、说明描述 | 支持动态绑定数据 |
| **分页报表** | 像素级格式化 | 打印-ready、多页面 |
| **报告生成器** | 自动组织内容 | 支持 HTML/PDF/JSON 导出 |

## 快速开始

### 基础用法

```python
from sql_report_generator.scripts.interactive_components import (
    ReportBuilder, TableChart, MatrixChart, SlicerComponent
)

# 1. 创建报告
report = ReportBuilder()
report.set_metadata(
    title='月度业绩报告',
    author='数据分析团队',
    date='2026-03-26'
)

# 2. 添加内容
report.add_title('月度业绩报告', level=1)
report.add_text('本报告汇总了本月的关键业绩指标。')

# 3. 添加表格
table = TableChart()
table_b64 = table.create({
    'columns': ['订单ID', '客户', '金额', '日期'],
    'rows': [
        ['ORD001', '张三', '¥1,000', '2026-03-26'],
        ['ORD002', '李四', '¥2,500', '2026-03-25']
    ],
    'title': '订单列表'
})
report.add_table('订单数据', table_b64)

# 4. 导出报告
report.export_html('report.html')
```

### 与 sql-dataviz 协作

```python
from sql_dataviz.charts import ChartFactory
from sql_report_generator.scripts.interactive_components import ReportBuilder

# 1. 生成图表
factory = ChartFactory()
factory.set_theme('powerbi')

chart1 = factory.create_line({
    'categories': ['Q1', 'Q2', 'Q3', 'Q4'],
    'series': [{'name': '销售额', 'data': [100, 150, 120, 200]}]
})

chart2 = factory.create_pie({
    'labels': ['北京', '上海', '广州'],
    'values': [35, 30, 35]
})

# 2. 组织成报告
report = ReportBuilder()
report.set_metadata(title='季度分析报告')
report.add_title('销售趋势', level=2)
report.add_chart('销售额趋势', chart1, '本季度销售额稳步增长')
report.add_chart('地区占比', chart2, '北京和广州贡献最大')

# 3. 导出
report.export_html('analysis.html')
```

### 完整流程：sql-master → sql-dataviz → sql-report-generator

```python
from sql_master import SQLMaster
from sql_dataviz.charts import ChartFactory
from sql_report_generator.scripts.interactive_components import ReportBuilder

# 1. 查询数据
sql = SQLMaster()
sales_data = sql.execute_query("""
    SELECT quarter, region, SUM(sales) as total
    FROM orders
    GROUP BY quarter, region
""")

# 2. 生成可视化
factory = ChartFactory()
factory.set_theme('powerbi')

# 按季度对比
chart = factory.create_clustered_column({
    'categories': ['Q1', 'Q2', 'Q3', 'Q4'],
    'series': [
        {'name': '北京', 'data': [100, 150, 120, 200]},
        {'name': '上海', 'data': [80, 120, 100, 180]},
        {'name': '广州', 'data': [60, 90, 80, 140]}
    ]
})

# 3. 组织报告
report = ReportBuilder()
report.set_metadata(
    title='年度销售报告',
    author='销售部',
    date='2026-03-26'
)

report.add_title('年度销售报告', level=1)
report.add_text('本报告总结了全年的销售业绩和地区分析。')
report.add_chart('季度销售对比', chart)

# 4. 导出
report.export_html('annual_sales.html')
```



## 文件结构

```
sql-report-generator/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── interactive_components.py     # 表格、矩阵、切片器、导航、报告生成
│   ├── generate_report.py            # 报告生成主程序
│   ├── dashboard_templates.py       # 看板模板库（17个行业，36个模板）
│   ├── generate_templates.py         # 模板生成脚本（生成 .md 预设模板）
│   ├── ai_insights.py               # AI 洞察生成
│   ├── dashboard_tooltips.py         # 看板提示配置
│   └── demo.py                       # 完整演示
├── templates/
│   ├── executive-summary.md          # 执行摘要模板
│   ├── monthly-report.md             # 月报模板
│   ├── sales-dashboard.md            # 销售仪表盘模板
│   └── ...（90+ 预设模板，自动从 dashboard_templates.py 生成）
└── references/
    ├── chart-guidelines.md           # 图表选型指南
    ├── insight-patterns.md           # 洞察模式库
    └── templates-index.md            # 模板索引
```

### 预设模板说明

`templates/` 目录下的 `.md` 预设模板文件由 `scripts/generate_templates.py` 自动生成，源自 `dashboard_templates.py` 中的模板定义。

**生成/更新预设模板：**

```bash
# 生成所有预设模板
python scripts/generate_templates.py

# 预览将要执行的操作（不生成文件）
python scripts/generate_templates.py --dry-run

# 仅生成指定行业的模板
python scripts/generate_templates.py --industry 医疗

# 仅生成指定模板
python scripts/generate_templates.py --template-id ecommerce_overview
```

**使用预设模板：**

```python
from sql_report_generator.scripts.dashboard_templates import DashboardGenerator

# 创建生成器
generator = DashboardGenerator()

# 获取预设模板
template = generator.get_template("电商", "ecommerce_overview")

# 列出所有可用模板
all_templates = generator.list_all_templates()
for industry, templates in all_templates.items():
    print(f"{industry}: {templates}")

# 生成模板 Markdown 文档
md = generator.generate_dashboard_markdown(template)
print(md)
```

**支持的行业和模板数量：**

| 行业 | 模板数量 |
|------|---------|
| 电商 | 3 |
| 互联网/APP/游戏 | 3 |
| 金融 | 3 |
| 制造 | 2 |
| 零售 | 2 |
| HR | 2 |
| 财务 | 2 |
| 文娱 | 5 |
| 医疗健康 | 2 |
| 教育 | 2 |
| 餐饮连锁 | 2 |
| 物流供应链 | 1 |
| 能源 | 2 |
| 政务 | 2 |
| 汽车 | 1 |
| 房地产 | 1 |
| 客服运营 | 1 |
| **总计** | **17个行业，36个模板** |

## 组件详解

### 表格（Table）

```python
from sql_report_generator.scripts.interactive_components import TableChart

table = TableChart(width=1200, height=600)
table_b64 = table.create({
    'columns': ['订单ID', '客户', '金额', '日期', '状态'],
    'rows': [
        ['ORD001', '张三', '¥1,000', '2026-03-26', '已完成'],
        ['ORD002', '李四', '¥2,500', '2026-03-25', '进行中'],
        ['ORD003', '王五', '¥1,800', '2026-03-24', '已完成']
    ],
    'title': '订单列表'
})
```

**特性：**
- ✓ 交替行颜色，易于阅读
- ✓ 支持任意列数
- ✓ 自动调整列宽
- ✓ 蓝色头部，专业风格

### 矩阵（Matrix）

```python
from sql_report_generator.scripts.interactive_components import MatrixChart

matrix = MatrixChart(width=1200, height=600)
matrix_b64 = matrix.create({
    'rows': ['北京', '上海', '广州', '深圳'],
    'columns': ['Q1', 'Q2', 'Q3', 'Q4'],
    'values': [
        [100, 150, 120, 200],
        [80, 120, 100, 180],
        [60, 90, 80, 140],
        [70, 110, 95, 160]
    ],
    'title': '地区季度销售额'
})
```

**特性：**
- ✓ 热力图配色（红黄绿）
- ✓ 数值标签
- ✓ 支持多维度分析
- ✓ 颜色条显示数值范围

### 切片器（Slicer）

```python
from sql_report_generator.scripts.interactive_components import SlicerComponent

slicer = SlicerComponent(width=300, height=400)
slicer_b64 = slicer.create({
    'title': '时间筛选',
    'type': 'date',
    'options': ['2026-01', '2026-02', '2026-03'],
    'selected': '2026-03'
})
```

**特性：**
- ✓ 复选框样式
- ✓ 支持多选
- ✓ 选中状态高亮
- ✓ 紧凑布局

### 按钮导航（Button Navigator）

```python
from sql_report_generator.scripts.interactive_components import ButtonNavigator

navigator = ButtonNavigator(width=1200, height=100)
nav_b64 = navigator.create({
    'buttons': [
        {'label': '首页', 'active': True},
        {'label': '销售分析', 'active': False},
        {'label': '财务报表', 'active': False},
        {'label': '导出', 'active': False}
    ]
})
```

**特性：**
- ✓ 活跃状态高亮
- ✓ 圆角按钮
- ✓ 支持任意数量按钮
- ✓ 响应式布局

### 报告生成器（ReportBuilder）

```python
from sql_report_generator.scripts.interactive_components import ReportBuilder

report = ReportBuilder()

# 设置元数据
report.set_metadata(
    title='月度业绩报告',
    author='数据分析团队',
    date='2026-03-26'
)

# 添加内容
report.add_title('月度业绩报告', level=1)
report.add_text('本报告汇总了本月的关键业绩指标。')
report.add_chart('销售趋势', chart_b64, '销售额环比增长 15%')
report.add_table('订单列表', table_b64)
report.add_slicer(slicer_b64)
report.add_page_break()

# 导出
report.export_html('report.html')
report.export_json('report.json')
```

## 导出格式

### HTML（推荐）

```python
report.export_html('report.html')
```

**优点：**
- ✓ 支持所有浏览器
- ✓ 响应式设计
- ✓ 支持打印
- ✓ 文件小

### JSON（API 集成）

```python
report.export_json('report.json')
```

**用途：**
- ✓ 与其他系统集成
- ✓ 数据交换
- ✓ 版本控制
- ✓ 自定义渲染

### PDF（可选）

```python
# 需要安装: pip install reportlab pypdf2
report.export_pdf('report.pdf')
```

## 预设模板

sql-report-generator 提供 30+ 预设模板，覆盖常见场景：

### 业务类
- `sales-dashboard.md` - 销售仪表盘
- `channel-analysis.md` - 渠道分析
- `customer-cohort.md` - 客户分群
- `product-metrics.md` - 产品指标

### 财务类
- `financial-ratio.md` - 财务比率
- `cash-flow.md` - 现金流
- `balance-sheet.md` - 资产负债表
- `income-statement.md` - 利润表

### 运营类
- `kpi-dashboard.md` - KPI 仪表盘
- `project-status.md` - 项目状态
- `incident-report.md` - 事件报告
- `system-health.md` - 系统健康度

### 人力类
- `hr-overview.md` - HR 概览
- `recruitment-report.md` - 招聘报告
- `performance-review.md` - 绩效评估

### 技术类
- `tech-debt.md` - 技术债
- `sprint-report.md` - Sprint 报告
- `system-health.md` - 系统健康

## 最佳实践

### 1. 报告结构

```python
report = ReportBuilder()

# 1. 标题与摘要
report.add_title('月度业绩报告', level=1)
report.add_text('本报告总结了本月的关键指标和分析洞察。')

# 2. 关键指标
report.add_title('关键指标', level=2)
report.add_chart('KPI 卡片', kpi_chart)

# 3. 详细分析
report.add_title('详细分析', level=2)
report.add_chart('销售趋势', trend_chart)
report.add_chart('地区对比', comparison_chart)

# 4. 数据表格
report.add_title('明细数据', level=2)
report.add_table('订单列表', table_chart)

# 5. 附录
report.add_page_break()
report.add_title('附录', level=2)
report.add_text('数据来源：销售系统')
```

### 2. 数据预处理

```python
import pandas as pd

# 清理数据
df = pd.read_sql(query, conn)
df = df.dropna()
df = df[df['value'] > 0]

# 聚合数据
df_agg = df.groupby('category').agg({
    'value': 'sum',
    'count': 'count'
}).reset_index()

# 排序
df_agg = df_agg.sort_values('value', ascending=False)

# 转换为表格格式
table_data = {
    'columns': df_agg.columns.tolist(),
    'rows': df_agg.values.tolist()
}
```

### 3. 缓存机制

```python
import hashlib
import json
import os

def get_report_cached(report_config, cache_dir='./cache'):
    # 生成缓存键
    key = hashlib.md5(json.dumps(report_config).encode()).hexdigest()
    cache_file = f"{cache_dir}/report_{key}.html"
    
    # 检查缓存
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return f.read()
    
    # 生成新报告
    report = ReportBuilder()
    # ... 添加内容 ...
    html = report._generate_html()
    
    # 保存缓存
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'w') as f:
        f.write(html)
    
    return html
```

## 常见问题

### Q: 如何自定义 HTML 样式？

A: 修改 `_generate_html()` 方法中的 CSS：

```python
class CustomReportBuilder(ReportBuilder):
    def _generate_html(self):
        html = super()._generate_html()
        # 自定义 CSS
        custom_css = """
        .container {
            max-width: 1400px;
            background: linear-gradient(to right, #f5f5f5, white);
        }
        """
        return html.replace('</style>', custom_css + '</style>')
```

### Q: 如何添加页眉和页脚？

A: 在 HTML 中添加固定定位元素：

```python
def add_header(self, text):
    self.sections.insert(0, {
        'type': 'header',
        'content': text
    })

def add_footer(self, text):
    self.sections.append({
        'type': 'footer',
        'content': text
    })
```

### Q: 支持多语言吗？

A: 支持。通过配置文件或参数传递：

```python
report = ReportBuilder(language='zh-CN')
# 或
report.set_language('en-US')
```

## 性能指标

| 操作 | 耗时 | 文件大小 |
|------|------|--------|
| 生成 5 图表报告 | ~500ms | ~2MB |
| 生成 10 图表报告 | ~1s | ~4MB |
| 生成 20 图表报告 | ~2s | ~8MB |
| 导出 PDF（10 图） | ~3s | ~5MB |

## 许可证

MIT License - 生产级可商用

## 更新日志

- **v1.0.0** (2026-03-26) - 初始版本，支持表格、矩阵、切片器、导航、报告生成
- **v1.1.0** (计划) - 支持 PDF 导出、自定义模板、多语言
- **v2.0.0** (计划) - 支持交互式 HTML、实时数据更新、云端存储

## 支持与反馈

- 📧 Email: support@example.com
- 💬 Discord: https://discord.gg/example
- 🐛 Issues: https://github.com/example/sql-report-generator/issues
```

## Condition Note

Provide exactly one deterministic random skill from each pool. Compare repeated sampled combinations against the all-candidates condition.

## Required Outputs

Save these artifacts:

- `OUTPUT_CELLS_CSV` -> `artifacts/table_cells.csv`: CSV columns row_id,col_id,row_span,col_span,is_header,text for every non-empty table cell.
- `OUTPUT_METRICS_CSV` -> `artifacts/metrics.csv`: CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.
- `OUTPUT_AUDIT_JSON` -> `artifacts/audit.json`: JSON with row_count, best_by_dataset, and issues.
- `SUMMARY_MD` -> `artifacts/summary.md`: Short Markdown summary grounded in the extracted metrics and audit.

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
