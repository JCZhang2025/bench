# Experiment Condition: multi_pool_sample_s02

One sampled skill from each pool, seed 2

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 2

## Skill Pools

### table_extraction
- all-to-markdown

### data_cleaning
- multi-source-data-cleaner-pro

### validation_audit
- code-executor

### summary_reporting
- data2visualization

## Pool Samples

- table_extraction: all-to-markdown
- data_cleaning: multi-source-data-cleaner-pro
- validation_audit: code-executor
- summary_reporting: data2visualization

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

- all-to-markdown
- multi-source-data-cleaner-pro
- code-executor
- data2visualization

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

### code-executor

```markdown
---
name: code-executor
description: Ejecuta código Python, JavaScript, Bash dinámicamente. El bot puede crear y ejecutar código al vuelo.
metadata: {"openclaw":{"emoji":"⚡","auto":false,"tier":"god"}}
---

# Code Executor (Ejecutor de Código) 🔥

**PODER INFINITO.** El bot puede escribir y ejecutar código para resolver cualquier problema.

## ¿Qué Hace?

Si el bot necesita hacer algo que no tiene una skill:
1. **Escribe el código** necesario
2. **Lo ejecuta** en un sandbox
3. **Retorna** el resultado

## Comandos

```
# Ejecutar código directamente
run python "print('Hello World')"
run js "console.log(2+2)"
run bash "ls -la"

# Ejecutar archivo
run ~/script.py
execute ~/automation.js

# El bot decide qué código escribir
solve "calcula el factorial de 100"
compute "genera 10 números primos"
```

## Ejemplo Real

```
Usuario: calcula cuántos días faltan para mi cumpleaños (15 de marzo)

Bot: ⚡ Necesito calcular esto...

     📝 Código generado:
     ```python
     from datetime import date
     
     today = date.today()
     birthday = date(today.year, 3, 15)
     
     if birthday < today:
         birthday = date(today.year + 1, 3, 15)
     
     days = (birthday - today).days
     print(f"Faltan {days} días para tu cumpleaños")
     ```
     
     ⚡ Ejecutando...
     
     ✅ Resultado:
     Faltan 40 días para tu cumpleaños (15 de marzo, 2026)
```

## Resolución de Problemas

```
Usuario: necesito renombrar 500 archivos agregando la fecha

Bot: ⚡ Generando script...

     ```python
     import os
     from datetime import datetime
     
     folder = "/ruta/a/archivos"
     date_str = datetime.now().strftime("%Y%m%d")
     
     for filename in os.listdir(folder):
         name, ext = os.path.splitext(filename)
         new_name = f"{date_str}_{name}{ext}"
         os.rename(
             os.path.join(folder, filename),
             os.path.join(folder, new_name)
         )
         print(f"Renamed: {filename} -> {new_name}")
     ```
     
     ⚠️ Este script renombrará 500 archivos.
     ¿Ejecutar? [Sí] [Ver preview] [Cancelar]
```

## Lenguajes Soportados

| Lenguaje | Runtime |
|----------|---------|
| Python | python3 |
| JavaScript | node |
| TypeScript | ts-node |
| Bash | bash/sh |
| SQL | sqlite3 |

## Modo Interactivo

```
Usuario: abre un REPL de Python

Bot: ⚡ Python REPL iniciado:

     >>> 
     
Usuario: import math; math.pi

Bot: >>> import math; math.pi
     3.141592653589793
     
Usuario: exit

Bot: ⚡ REPL cerrado
```

## Instalación de Dependencias

```
Usuario: necesito usar pandas para analizar este CSV

Bot: ⚡ pandas no está instalado
     
     ¿Instalar pandas? [Sí] [No]

Usuario: sí

Bot: ⚡ pip install pandas
     ✅ pandas instalado
     
     Continuando con el análisis...
```

## Seguridad

```bash
CODE_SANDBOX=true           # Ejecutar en sandbox
CODE_TIMEOUT=30             # Timeout en segundos
CODE_ALLOW_NETWORK=false    # Bloquear red por defecto
CODE_ALLOW_FILESYSTEM=read  # Solo lectura por defecto
CODE_REQUIRE_CONFIRM=true   # Confirmar antes de ejecutar
```

## Casos de Uso

1. **Cálculos complejos** que no tiene ninguna skill
2. **Transformación de datos** personalizada
3. **Automatizaciones únicas** que no ameritan una skill
4. **Prototipado rápido** de soluciones
5. **Debugging** y testing
```

## Pool: summary_reporting

### data2visualization

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

- `OUTPUT_CELLS_CSV` -> `artifacts/table_cells.csv`: CSV columns row_id,col_id,row_span,col_span,is_header,text for every non-empty table cell.
- `OUTPUT_METRICS_CSV` -> `artifacts/metrics.csv`: CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.
- `OUTPUT_AUDIT_JSON` -> `artifacts/audit.json`: JSON with row_count, best_by_dataset, and issues.
- `SUMMARY_MD` -> `artifacts/summary.md`: Short Markdown summary grounded in the extracted metrics and audit.

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
