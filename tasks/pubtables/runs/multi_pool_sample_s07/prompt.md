# Experiment Condition: multi_pool_sample_s07

One sampled skill from each pool, seed 7

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 7

## Skill Pools

### table_extraction
- all-to-markdown

### data_cleaning
- data-analysis

### validation_audit
- data-analysis

### summary_reporting
- typora-visual-architect

## Pool Samples

- table_extraction: all-to-markdown
- data_cleaning: data-analysis
- validation_audit: data-analysis
- summary_reporting: typora-visual-architect

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

- all-to-markdown
- data-analysis
- typora-visual-architect

## Available Skill Documents

## Pool: table_extraction

### all-to-markdown

```markdown
---
name: all-to-markdown
version: 0.1.0
description: 将任意文件（PDF、Word、Excel、PPT、图片、音频、网页等）转换为 Markdown
author: Ping Si <sipingme@gmail.com>
tags: [markdown, convert, pdf, docx, pptx, xlsx, html, ocr, youtube]
requiredEnvVars: []
---

# All to Markdown

基于 [Microsoft MarkItDown](https://github.com/microsoft/markitdown)，将任意格式的文件或 URL 转换为 Markdown，便于 LLM 分析和处理。

## 支持格式

| 类型 | 格式 |
|------|------|
| 文档 | PDF、DOCX、PPTX、XLSX、XLS、EPUB、MSG |
| 数据 | CSV、JSON、XML |
| 图片 | JPG、PNG 等（含 EXIF 元数据，可选 OCR）|
| 音频 | WAV、MP3（含语音转录，需 OpenAI Key）|
| 网页 | HTML、YouTube URL（含字幕提取）|
| 压缩 | ZIP（逐文件转换）|

## 前置要求

安装 markitdown：

```bash
pip install 'markitdown[all]'
```

## 给 AI 的使用说明

当用户需要将文件或 URL 转换为 Markdown 时，使用以下命令：

```bash
scripts/run.sh <文件路径或URL>
```

可选标志：
- `-o <输出文件>` — 保存到文件
- `--use-plugins` — 启用插件（如 markitdown-ocr）

**重要原则**：
- 转换结果直接输出到 stdout，可供 AI 直接读取分析
- 文件路径使用用户提供的实际路径，不要假设
- 转换大型文件时提前告知用户可能需要较长时间

## 使用示例

### 示例 1：转换 PDF

> 用户：帮我把这个 PDF 转成 Markdown，以便我分析内容

AI 执行：
```bash
scripts/run.sh /path/to/document.pdf
```

### 示例 2：转换并保存

> 用户：把这个 Excel 转成 Markdown 文件保存

AI 执行：
```bash
scripts/run.sh /path/to/data.xlsx -o output.md
```

### 示例 3：转换网页

> 用户：把这篇文章转成 Markdown

AI 执行：
```bash
scripts/run.sh https://example.com/article.html
```

### 示例 4：提取 YouTube 字幕

> 用户：把这个 YouTube 视频的内容提取出来

AI 执行：
```bash
scripts/run.sh https://www.youtube.com/watch?v=xxx
```

## 可选 AI 增强功能

设置 `OPENAI_API_KEY` 后，markitdown 可对图片生成 AI 描述：

```bash
OPENAI_API_KEY=sk-xxx scripts/run.sh image.jpg
```

## 安全说明

- 仅在本地执行文件转换，不发送文件内容到远程服务
- 转换 URL 时会访问对应网络地址
- 启用 LLM 功能时，图片内容会发送到 OpenAI API
```

## Pool: data_cleaning

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

### typora-visual-architect

```markdown
---
name: data-visualization-skill
description: 将结构化或半结构化数据转化为高质量 Markdown 可视化报告，适用于 Typora / Markor / PDF 导出
version: 1.0
author: 王维
---

# 📊 Data Visualization Skill

## 🧩 功能说明
该 Skill 用于：
- 数据整理
- 数据分析
- 数据可视化（Markdown + HTML + Mermaid）
- 输出高质量报告（适配 Typora / Markor / PDF）

---

## 🚀 使用方式

输入：
- 原始数据（表格 / 文本 / JSON）
- 分析目标（可选）
- 和AI的聊天内容

输出：
- 标准化 Markdown 报告
- 含图表（Mermaid / 表格 / 卡片）

---

## 📌 输出特性

- 从 CSV/JSON 文件加载数据，或使用内置示例数据集
- 使用 matplotlib 生成专业图表（柱状图、折线图、散点图）
- 生成带样式的报告，包括：
  - 蓝色主题配色（`#e3f2fd`、`#bbdefb`、`#2196f3`）
  - 弹性卡片布局展示关键指标
  - 带条纹行的样式化 HTML 表格
  - 用于数据处理流程的 Mermaid 流程图
  - 渐变总结框
- 输出内嵌 base64 图片的 Markdown（无需外部文件）
- 从 CSV/JSON 文件加载数据，或使用内置示例数据集
- 使用 matplotlib 生成专业图表（柱状图、折线图、散点图）
- 生成带样式的报告，包括：
  - 蓝色主题配色（`#e3f2fd`、`#bbdefb`、`#2196f3`）
  - 弹性卡片布局展示关键指标
  - 带条纹行的样式化 HTML 表格
  - 用于数据处理流程的 Mermaid 流程图
  - 渐变总结框
- 输出内嵌 base64 图片的 Markdown（无需外部文件）
- 通过 `config.yaml` 完全自定义
---

## 🎯 适用场景

- 市场调研
- 销售数据分析
- 食品行业分析（重点适配）
- 竞品对比
- 趋势预测
## 使用方法
1. 将数据文件（CSV/JSON）放入目录，或在 `config.yaml` 中修改数据源路径。
2. 在 `config.yaml` 中调整可视化参数（图表类型、列名、标题等）。
3. 运行技能：
   ```bash
   python run.py
   4.生成的报告将保存为 output.md（可配置）。在 Typora 或 Markor 中打开即可查看带样式的可视化结果。

## 输出格式规则（严格遵循）

本技能生成的报告完全遵循以下格式要求：

- 全文包裹在 `markdown ...`（四个反引号）内，防止外层提前闭合。
- 所有 CSS 均写在 `style` 属性中。
- 卡片布局：`display: flex`、`gap`、`border-radius`、`box-shadow`。
- 表格表头背景色 `#b3e5fc`，行间使用 `border-bottom` 分隔。
- 渐变总结框：`linear-gradient(145deg, #bbdefb, #b2dfdb)`。
- 标题和署名居中，并包含日期。
- 适当位置可包含 Mermaid 图表和任务列表。

## 依赖环境

- Python 3.8+
- pandas, matplotlib, pyyaml
- （可选）seaborn 用于高级图表

安装命令：

bash

```
pip install pandas matplotlib pyyaml
```

## 配置说明 (`config.yaml`)

| 参数              | 类型    | 描述                                    |
| :---------------- | :------ | :-------------------------------------- |
| `data_source`     | string  | CSV/JSON 文件路径（留空则使用示例数据） |
| `chart_type`      | string  | `bar`、`line` 或 `scatter`              |
| `x_column`        | string  | X 轴列名                                |
| `y_column`        | string  | Y 轴列名                                |
| `title`           | string  | 报告标题                                |
| `output_file`     | string  | 输出 Markdown 文件路径                  |
| `include_mermaid` | boolean | 是否包含处理流程图                      |

## 文件结构

- `skill.md` – 本说明文档
- `config.yaml` – 用户设置
- `run.py` – 主执行脚本
- `prompt.md` – 含内联 CSS 的 HTML/Markdown 模板
- `schema.json` – 配置文件 JSON 校验 schema

## 示例

yaml

```
# config.yaml
data_source: "sales.csv"
chart_type: "bar"
x_column: "Month"
y_column: "Revenue"
title: "月度销售报告"
output_file: "sales_report.md"
include_mermaid: true
```



运行 `python run.py` 即可生成报告。
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
