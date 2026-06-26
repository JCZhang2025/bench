# Experiment Condition: multi_pool_sample_s09

One sampled skill from each pool, seed 9

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 9

## Skill Pools

### document_processing
- all-to-markdown

### validation_audit
- user-analysis-matrix

### summary_reporting
- markdown-converter

## Pool Samples

- document_processing: all-to-markdown
- validation_audit: user-analysis-matrix
- summary_reporting: markdown-converter

## Task

Given Novels_Intro_Packet.docx, identify the first two body paragraphs, change only those two paragraphs to double line spacing, verify that all other text and formatting are unchanged, and generate a short Markdown formatting summary. No GUI, screenshot, external API, or cloud service should be used.

## Available Skills

- all-to-markdown
- user-analysis-matrix
- markdown-converter

## Available Skill Documents

## Pool: document_processing

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

## Pool: validation_audit

### user-analysis-matrix

```markdown
---
name: user-analysis-matrix
description: "用户使用数据可视化分析全流程，从原始数据清洗、多维度聚合到生成单文件 HTML 可视化报告。支持按身份（部门/产品线/角色/大区/用户角色/层级）、时间（周/月/季度）、能力（具体功能/场景）三个维度做交叉分析。触发词：帮我做用户分析矩阵、用户活跃分析、大区活跃分析、产品线活跃分析、活跃分析、用户分析、生成数据看板。当用户需要将用户使用行为数据生成可视化 HTML 报告时触发此技能。流程为 Python 清洗聚合 + Chart.js 单文件 HTML 可视化，产物可直接浏览器打开。"
agent_created: true
allowed_tools:
  - Bash
  - Read
  - Write
  - Edit
---

# 用户使用数据可视化分析

## 概述

将用户使用行为原始数据（Excel/CSV），经过清洗、聚合、可视化三个阶段，产出单文件 HTML 报告。
报告包含：核心指标卡、多维度交叉筛选器、折线趋势图、能力排行图、分组对比表格。
交付物为自包含 HTML，可直接通过浏览器打开或发送给同事，无需服务器。

## 前置条件

确认用户提供以下信息：

1. **数据源文件路径** — 使用明细 Excel/CSV（必须含：用户标识列、时间列、各能力使用次数列）
2. **用户信息表路径**（可选）— 含身份维度字段（部门、产品线、角色、大区、用户角色、层级等）
3. **离职名单路径**（可选）— 用于排除已离职人员
4. **分析维度**（可选）— 默认按 部门+角色+产品线+大区+用户角色+层级，用户可按需调整
5. **时间范围**（可选）— 默认全部数据，用户可指定财周/月份范围

## 执行流程

### 第一步：数据加载与清洗

调用 `scripts/load_and_clean.py`：

```bash
python scripts/load_and_clean.py --input <使用明细.xlsx> --users <用户信息.xlsx> --resigned <离职名单.csv> --output data/cleaned_data.json
```

清洗规则：
- 排除离职名单中的用户
- 将能力使用次数列转为数值，空值填充为 0
- 日期列解析为 datetime，计算财周归属
- 去除完全重复行
- 活跃定义：该周任意能力使用次数 > 0

输出格式（JSON）：
```json
{
  "columns": ["姓名", "角色", "用户角色", "财周", "能力一使用次数", ...],
  "data": [[...], ...],
  "meta": {"total_rows": 12000, "cleaned_rows": 11500, "removed_resigned": 500}
}
```

### 第二步：多维度聚合

调用 `scripts/aggregate_data.py`：

```bash
python scripts/aggregate_data.py --input data/cleaned_data.json --output data/aggregated.json --dimensions "部门,角色,产品线,大区,用户角色,层级"
```

聚合产出三个结构：

1. **identity（身份维度）**：按各身份字段 groupby，计算用户数、活跃用户数、活跃率、人均能力数、总使用次数
2. **timeline（时间维度）**：按财周聚合，计算每周活跃用户数、活跃率，支持与上一周期对比
3. **capability（能力维度）**：按能力名称聚合，计算使用用户数、使用频次、渗透率（使用人数/总人数）

### 第三步：生成 HTML 报告

调用 `scripts/sync_to_html.py`：

```bash
python scripts/sync_to_html.py --data data/aggregated.json --template assets/report_template.html --output output/report.html
```

实现方式：
- 读取 `assets/report_template.html` 模板
- 找到 `const DATA = __DATA_PLACEHOLDER__;` 占位符
- 用聚合结果 JSON 替换占位符
- 写出完整 HTML 文件

### 第四步：验证与交付

生成后执行验证：
- 用浏览器预览 HTML 确认渲染正常
- 检查核心指标数字与原始数据一致（总数、活跃率）
- 确认筛选器交互正常（身份筛选 → 图表联动）
- 将输出文件路径告知用户

## HTML 报告设计规范

### 页面结构（从上到下）

1. **标题栏**：报告名称 + 数据更新时间 + 数据范围说明
2. **筛选栏**：身份维度下拉（部门/角色/产品线/大区/用户角色/层级）+ 时间范围选择 + 应用按钮
3. **指标卡行**：4 个核心数字（总用户数 / 活跃率 / 人均使用能力数 / 环比变化）
4. **Tab 切换区**：时间趋势 | 能力分析 | 身份对比 | 用户明细
5. **图表区**（根据 Tab 切换）：
   - 时间趋势：折线图（周活跃率 + 上一周期对比线）
   - 能力分析：横向条形图（各能力使用用户数排行）+ 渗透率指标
   - 身份对比：分组表格（各身份的活跃率/人均能力/环比）
   - 用户明细：可排序表格（用户标识 + 各维度 + 使用数据）
6. **底部说明**：数据口径说明 + 指标定义 + 活跃定义

### 视觉风格

- 图表库：Chart.js（CDN），无需安装
- 数据注入：`const DATA = {...};` 内嵌 JSON，纯前端渲染
- 颜色规范：主色紫色系（`#534AB7`），正向指标绿色（`#1D9E75`），负向指标红色（`#A32D2D`）
- 布局：全屏宽，响应式，最大宽度 1400px 居中
- 字体：系统默认（Segoe UI / PingFang SC / Microsoft YaHei）

## 质量控制

- 若清洗后数据行数 < 原始数据 50%，输出警告并询问用户确认
- 空值率 > 20% 的列须在报告中标注
- 活跃率计算须注明口径：活跃用户数 / 总用户数（排除离职）
- 环比计算须确保有可比周期数据，否则显示 "N/A"

## 输出物

| 产物 | 路径 | 说明 |
|------|------|------|
| 清洗后数据 | `data/cleaned_data.json` | 中间产物，可复用 |
| 聚合结果 | `data/aggregated.json` | 中间产物，可复用 |
| 可视化报告 | `output/report.html` | 最终交付，单文件自包含 |

## 资源说明

### scripts/

| 文件 | 用途 | 来源 |
|------|------|------|
| `load_and_clean.py` | 数据加载 + 清洗 + 转JSON | 基于 process_matrix.py 改造 |
| `aggregate_data.py` | 多维度聚合（身份/时间/能力） | 基于 generate_full_data.py 改造 |
| `sync_to_html.py` | JSON 数据注入 HTML 模板 | 基于 sync_html_data.py 通用化 |
| `run_pipeline.py` | 一键串联上述三步 | 新增 |

### references/

| 文件 | 用途 |
|------|------|
| `data_dict.md` | 字段说明（列名含义、数据类型、取值范围） |
| `indicator_defs.md` | 指标定义（活跃率/渗透率/人均能力数等计算公式） |

### assets/

| 文件 | 用途 |
|------|------|
| `report_template.html` | HTML 可视化报告模板（含 Chart.js、筛选器、图表占位） |
```

## Pool: summary_reporting

### markdown-converter

```markdown
---
name: markdown-converter
description: Convert documents and files to Markdown using markitdown. Use when converting PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx, .xls), HTML, CSV, JSON, XML, images (with EXIF/OCR), audio (with transcription), ZIP archives, YouTube URLs, or EPubs to Markdown format for LLM processing or text analysis.
---

# Markdown Converter

Convert files to Markdown using `uvx markitdown` — no installation required.

## Basic Usage

```bash
# Convert to stdout
uvx markitdown input.pdf

# Save to file
uvx markitdown input.pdf -o output.md
uvx markitdown input.docx > output.md

# From stdin
cat input.pdf | uvx markitdown
```

## Supported Formats

- **Documents**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx, .xls)
- **Web/Data**: HTML, CSV, JSON, XML
- **Media**: Images (EXIF + OCR), Audio (EXIF + transcription)
- **Other**: ZIP (iterates contents), YouTube URLs, EPub

## Options

```bash
-o OUTPUT      # Output file
-x EXTENSION   # Hint file extension (for stdin)
-m MIME_TYPE   # Hint MIME type
-c CHARSET     # Hint charset (e.g., UTF-8)
-d             # Use Azure Document Intelligence
-e ENDPOINT    # Document Intelligence endpoint
--use-plugins  # Enable 3rd-party plugins
--list-plugins # Show installed plugins
```

## Examples

```bash
# Convert Word document
uvx markitdown report.docx -o report.md

# Convert Excel spreadsheet
uvx markitdown data.xlsx > data.md

# Convert PowerPoint presentation
uvx markitdown slides.pptx -o slides.md

# Convert with file type hint (for stdin)
cat document | uvx markitdown -x .pdf > output.md

# Use Azure Document Intelligence for better PDF extraction
uvx markitdown scan.pdf -d -e "https://your-resource.cognitiveservices.azure.com/"
```

## Notes

- Output preserves document structure: headings, tables, lists, links
- First run caches dependencies; subsequent runs are faster
- For complex PDFs with poor extraction, use `-d` with Azure Document Intelligence
```

## Condition Note

Provide exactly one deterministic random skill from each pool. Compare repeated sampled combinations against the all-candidates selection condition.

## Required Outputs

Save the edited file and summary as:

```text
artifacts/Novels_Intro_Packet.edited.docx
artifacts/summary.md
```

Do not use GUI operations, screenshots, external APIs, or cloud services.
