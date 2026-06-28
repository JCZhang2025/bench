# Experiment Condition: multi_pool_sample_s06

One sampled skill from each pool, seed 6

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 6

## Skill Pools

### table_reconstruction
- code-executor

### metric_extraction_audit
- metric-consistency-auditor

### summary_reporting
- generate-report123

## Pool Samples

- table_reconstruction: code-executor
- metric_extraction_audit: metric-consistency-auditor
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

- code-executor
- metric-consistency-auditor
- generate-report123

## Available Skill Documents

## Pool: table_reconstruction

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

## Pool: metric_extraction_audit

### metric-consistency-auditor

```markdown
---
name: metric-consistency-auditor
description: Use when auditing normalized metric tables for schema consistency, numeric parsing, duplicate records, group-level best scores, and extraction issues.
---

# Metric Consistency Auditor

Use this skill after extraction and normalization to check whether the produced metric table is internally consistent.

## Audit Steps

1. Confirm all required columns are present.
2. Confirm numeric fields parse as numbers after stripping harmless formatting such as percent signs.
3. Confirm text fields are non-empty for each metric row.
4. Check for duplicate records at the intended entity and dataset grain.
5. Compute the best record per group using the requested score field and direction.
6. Compare audit counts against the produced artifact, not against hidden expected answers.
7. Write all assumptions and issues to a machine-readable audit file.

## Issue Categories

- missing_required_column
- non_numeric_metric
- empty_required_text
- duplicate_record
- inconsistent_group_best
- excluded_non_table_text
- ambiguous_structure

## Guardrails

- Do not use oracle artifacts, verifier source, or known expected values.
- Do not hardcode a target row count or target winner.
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
