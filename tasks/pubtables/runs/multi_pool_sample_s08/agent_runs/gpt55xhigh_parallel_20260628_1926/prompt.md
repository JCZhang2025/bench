# Experiment Condition: multi_pool_sample_s08

One sampled skill from each pool, seed 8

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 8

## Skill Pools

### table_reconstruction
- bbox-row-column-parser

### metric_extraction_audit
- data-analysis

### summary_reporting
- generate-report123

## Pool Samples

- table_reconstruction: bbox-row-column-parser
- metric_extraction_audit: data-analysis
- summary_reporting: generate-report123

## Task

Given a local PubTables-style OCR word JSON file, reconstruct the table structure, normalize the metric rows, audit the extracted values, and write a short grounded Markdown summary.

The input JSON follows the PubTables-style word-box setup: it contains a table bounding box and page words with text plus bounding boxes. Some caption and footnote words are present outside the table bounding box. Use word positions to reconstruct rows, columns, header cells, row spans, and column spans. Exclude caption and footnote words from the normalized metric rows.

Required normalized metric fields:
- method
- dataset
- accuracy
- f1
- notes

For the audit, report the number of normalized metric rows, the best method by F1 score for each dataset, and any extraction or validation issues you find.

## Available Skills

- bbox-row-column-parser
- data-analysis
- generate-report123

## Available Skill Documents

## Pool: table_reconstruction

### bbox-row-column-parser

```markdown
---
name: bbox-row-column-parser
description: Use when converting OCR tokens with bounding boxes into stable row groups, column groups, and cell text for noisy semi-structured tables.
---

# Bbox Row Column Parser

Use this skill when the main challenge is assigning OCR words to rows and columns from coordinates.

## Coordinate Normalization

1. For each token, compute `x_center`, `y_center`, `width`, and `height`.
2. Sort tokens by `y_center`, then by `x_center`.
3. Estimate a row tolerance from median token height. Increase tolerance only when adjacent rows would otherwise split the same baseline.
4. Estimate column bands from explicit hints, repeated x ranges, or large horizontal gaps.

## Row Grouping

- Group words into a row when their y-centers are close relative to token height.
- Recompute the row center after adding each token.
- Keep rows sorted from top to bottom.
- Do not merge vertically separated header rows just because their text is semantically related.

## Column Assignment

- Prefer provided column x-ranges when they exist.
- Otherwise infer columns from stable x clusters and repeated alignment across body rows.
- Assign a token to the column whose range contains its center.
- If a token crosses a boundary, choose the column with the largest horizontal overlap.

## Cell Text Assembly

- Within each row-column bucket, sort tokens by x position.
- Join adjacent words with spaces unless punctuation clearly attaches to a neighbor.
- Preserve original casing and symbols.
- Leave missing cells empty rather than shifting later cells left.

## Guardrails

- Do not use expected output values to tune row or column thresholds.
- Do not rely on a fixed number of rows, columns, or body records.
```

## Pool: metric_extraction_audit

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

### generate-report123

```markdown
---
name: chartjs-reporter
description: >
  This skill should be used when the user needs to turn structured data (query results,
  CSV summaries, JSON records, or Python dicts/lists) into a standalone HTML visualization
  report powered by Chart.js. It covers generating pie charts, doughnut charts, bar charts
  (vertical/horizontal), line charts, mixed charts, and KPI summary cards — all embedded
  in a dark-themed, self-contained HTML file that opens directly in any browser.
  Trigger when the user says things like "生成可视化报告", "数据出图", "生成HTML图表",
  "把查询结果可视化", "用 Chart.js 画图", or provides tabular data and asks for a visual output.
---

# chartjs-reporter — Chart.js HTML 可视化报告生成技能

## 技能目的

将结构化数据（SQL 查询结果、CSV 摘要、Python dict/list、手动提供的表格）转换为
**自包含的 HTML 可视化报告**，内嵌 Chart.js 图表和 KPI 卡片，无需服务器，
浏览器直接打开即可查看。

## 触发条件

以下任意一种情况触发本技能：
- 用户提供了数据并要求"出图"、"可视化"、"生成报告"
- 用户已有 DuckDB / SQL / pandas 查询结果，需要图表化展示
- 用户指定了图表类型（饼图、柱状图、折线图等）+ 数据
- 与 chat2duckdb 技能配合：查询完成后生成可视化报告

## 操作步骤

### 步骤 1：理解数据结构

收到数据后，确认以下信息：
- 数据形态：数值列 / 分类列 / 时间列
- 分析目的：占比 / 趋势 / 对比 / 排名
- 期望图表类型（用户未指定时，按照「图表选型规则」自动选择）

### 步骤 2：选择图表类型

| 分析目的 | 推荐图表 |
|---------|---------|
| 占比 / 构成 | doughnut（≤6类）/ pie |
| 趋势 / 时间序列 | line（fill: true 显示面积） |
| 分类对比（≤8项） | bar（垂直） |
| 分类对比（>8项或标签长） | bar（水平，indexAxis: 'y'） |
| 多指标对比 | 分组 bar |
| 排名 Top N | 水平 bar + 进度条 |
| 关键指标摘要 | KPI 卡片（非图表） |

### 步骤 3：调用生成脚本

使用 `scripts/generate_report.py` 生成 HTML 报告：

```bash
python scripts/generate_report.py \
  --title "报告标题" \
  --subtitle "副标题说明" \
  --data '{"charts": [...], "kpis": [...]}' \
  --output report.html
```

也可以直接在 Python 中调用（适合与 chat2duckdb 配合）：

```python
from scripts.generate_report import build_report
html = build_report(title, subtitle, kpis, charts)
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)
```

### 步骤 4：数据格式规范

`kpis` 列表（可选，顶部 KPI 卡片）：
```json
[
  {"label": "总营收", "value": "¥1,755,905", "sub": "全年累计", "color": "green"},
  {"label": "订单数", "value": "200",         "sub": "5 品类",  "color": "blue"}
]
```
`color` 可选值：`blue` | `green` | `yellow` | `purple` | `red`

`charts` 列表（图表配置）：
```json
[
  {
    "type": "doughnut",
    "title": "品类营收占比",
    "labels": ["Food", "Electronics", "Sports"],
    "datasets": [{"data": [456833, 351665, 349967]}]
  },
  {
    "type": "line",
    "title": "月度趋势",
    "labels": ["1月","2月","3月"],
    "datasets": [{"label": "营收", "data": [158495, 185560, 98369]}]
  }
]
```

支持的 `type` 值：`bar` | `line` | `doughnut` | `pie` | `horizontalBar`（自动转 bar + indexAxis:y）

### 步骤 5：布局规则

- KPI 卡片行：最多 4 列，超出自动换行
- 图表区：默认 2 列网格；1 个图表时全宽；3 个图表时 3 列
- 每张图表高度固定 240px，响应式宽度
- 表格（Top N 排名）：单独一行，全宽显示
- 页脚：说明数据来源和生成时间

### 步骤 6：输出与展示

- 输出路径默认为用户提供的路径，或 `./report_<timestamp>.html`
- 生成后调用 `preview_url` 工具在浏览器中预览
- 所有依赖（Chart.js）通过 CDN 加载，无需本地安装

## 与 chat2duckdb 配合的标准流程

```
1. chat2duckdb 执行 SQL 查询 → 得到 DataFrame / 字典结果
2. chartjs-reporter 将结果转换为图表配置 JSON
3. 调用 generate_report.py 生成 HTML
4. 调用 preview_url 展示报告
```

## 参考资源

- 核心脚本：[scripts/generate_report.py](scripts/generate_report.py)
- 图表配置参考：[references/chart-config-guide.md](references/chart-config-guide.md)
- 样式主题参考：[references/theme-tokens.md](references/theme-tokens.md)

## 注意事项

- 报告为**深色主题**（dark mode），背景色 `#0f172a`，适合截图展示
- 数值超过 1000 时，自动格式化为千分位（¥1,234,567）
- 颜色序列已内置，无需手动指定每个数据点颜色
- Chart.js 版本固定为 4.4.0（CDN），确保稳定性
```

## Condition Note

Provide exactly one deterministic random skill from each pool. Compare repeated sampled combinations against the all-candidates condition.

## Required Outputs

Save these artifacts:

- `OUTPUT_CELLS_CSV` -> `artifacts/table_cells.csv`: CSV columns row_id,col_id,row_span,col_span,is_header,text for every reconstructed non-empty table cell.
- `OUTPUT_METRICS_CSV` -> `artifacts/metrics.csv`: CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.
- `OUTPUT_AUDIT_JSON` -> `artifacts/audit.json`: JSON with row_count, best_by_dataset, and issues.
- `SUMMARY_MD` -> `artifacts/summary.md`: Short Markdown summary grounded in the extracted metrics and audit.

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
