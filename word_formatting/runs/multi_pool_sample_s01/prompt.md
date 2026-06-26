# Experiment Condition: multi_pool_sample_s01

One sampled skill from each pool, seed 1

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 1

## Skill Pools

### document_processing
- office-document-specialist-suite

### validation_audit
- user-analysis-matrix

### summary_reporting
- typora-visual-architect

## Pool Samples

- document_processing: office-document-specialist-suite
- validation_audit: user-analysis-matrix
- summary_reporting: typora-visual-architect

## Task

Given Novels_Intro_Packet.docx, identify the first two body paragraphs, change only those two paragraphs to double line spacing, verify that all other text and formatting are unchanged, and generate a short Markdown formatting summary. No GUI, screenshot, external API, or cloud service should be used.

## Available Skills

- office-document-specialist-suite
- user-analysis-matrix
- typora-visual-architect

## Available Skill Documents

## Pool: document_processing

### office-document-specialist-suite

```markdown
---
name: office-document-specialist-suite
description: Advanced suite for creating, editing, and analyzing Microsoft Office documents (Word, Excel, PowerPoint). Provides specialized tools for automated reporting and document management.
metadata:
  {
    "openclaw": {
      "emoji": "📄",
      "requires": { 
        "bins": ["python3"], 
        "pip": ["python-docx", "openpyxl", "python-pptx"] 
      }
    }
  }
---

# Office Document Specialist Suite

A specialized toolset for professional document manipulation.

## Features

- **Word (.docx)**: Create and edit professional reports, manage styles, and insert tables/images.
- **Excel (.xlsx)**: Data analysis, automated spreadsheet generation, and complex formatting.
- **PowerPoint (.pptx)**: Automated slide deck creation from structured data.

## Usage

Each tool in the suite is designed to be called programmatically by the agent or via the provided CLI scripts.

## Installation

Run the included `setup.sh` to initialize the Python virtual environment and install dependencies.
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

Provide exactly one deterministic random skill from each pool. Compare repeated sampled combinations against the all-candidates selection condition.

## Required Outputs

Save the edited file and summary as:

```text
artifacts/Novels_Intro_Packet.edited.docx
artifacts/summary.md
```

Do not use GUI operations, screenshots, external APIs, or cloud services.
