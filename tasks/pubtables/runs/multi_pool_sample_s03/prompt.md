# Experiment Condition: multi_pool_sample_s03

One sampled skill from each pool, seed 3

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 3

## Skill Pools

### table_extraction
- markdown-converter

### data_cleaning
- chat2duckdb

### validation_audit
- sql-master

### summary_reporting
- generate-report123

## Pool Samples

- table_extraction: markdown-converter
- data_cleaning: chat2duckdb
- validation_audit: sql-master
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

- markdown-converter
- chat2duckdb
- sql-master
- generate-report123

## Available Skill Documents

## Pool: table_extraction

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

## Pool: data_cleaning

### chat2duckdb

```markdown
---
name: chat2duckdb
description: 基于 DuckDB 引擎的高效数据分析工具；当用户需要对 CSV/JSON/Parquet/Excel 等数据文件进行 SQL 查询、数据分析、数据抽样或需要自动纠错的查询执行时使用
dependency:
  python:
    - duckdb>=1.5.0
    - pandas>=2.0.0
    - numpy>=1.24.0
    - openpyxl>=3.1.0
---

# Chat2DuckDB 数据分析

## 任务目标
- 本技能用于对数据文件进行快速、高效的 SQL 查询和分析
- 能力包含：数据文件注册为表、自然语言转 SQL、查询执行、数据抽样、错误校正、分析结论生成
- 触发条件：用户需要分析数据文件、执行 SQL 查询、探索数据结构、生成数据分析报告

## 前置准备
- 依赖说明：安装 DuckDB 和 pandas
  ```
  duckdb>=1.5.0
  pandas>=2.0.0
  ```

## 核心功能

### 1. 数据探索（Describe 模式）
- **基本信息**：总行数、列数、表结构
- **数值列统计**：平均值、中位数、标准差、最大/最小值
- **分类列统计**：唯一值数量、最常见值、Top 值分布
- **日期列统计**：最早/最晚日期、唯一日期数
- **数据质量**：缺失值统计、完整性分析

### 2. SQL 查询执行
- **智能 SQL 生成**：根据自然语言描述自动生成 SQL
- **自动重试机制**：最多 3 次智能重试
- **SQL 校正引擎**：
  - 语法错误自动修复（移除多余分号、逗号等）
  - 列名错误智能纠正（基于编辑距离匹配）
  - 引号规范化（双引号转单引号）
  - SQL 关键字大小写规范化
- **数据抽样**：支持按比例抽样查询，快速验证逻辑

### 3. 结果分析
- 查询结果格式化输出
- 执行时间和性能统计
- 数据洞察和业务建议生成

## 操作步骤

### 步骤 1：数据准备
确认数据文件路径（CSV/JSON/Parquet/Excel 等格式）

### 步骤 2：数据探索
```bash
# 完整统计模式（推荐）
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode describe

# 简单模式（仅基本信息）
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode describe --simple

# 导出分析报告
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode describe --output report.json

# Excel 文件（默认读取第一个工作表）
python scripts/duckdb_analyzer.py --file_path ./data.xlsx --mode describe

# Excel 文件（指定工作表）
python scripts/duckdb_analyzer.py --file_path ./data.xlsx --excel_sheet "sheetTitle" --mode describe
```

### 步骤 3：SQL 查询
```bash
# 基础查询
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode query \
  --sql "SELECT * FROM data LIMIT 10"

# 聚合查询
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode query \
  --sql "SELECT category, SUM(price * quantity) as total_sales FROM data GROUP BY category"

# 抽样验证（先在小样本上测试）
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode query \
  --sql "SELECT * FROM data WHERE price > 100" --sample_fraction 0.1

# 导出查询结果（支持 CSV/Excel/JSON/Parquet）
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode query \
  --sql "SELECT * FROM data" --output result.csv

python scripts/duckdb_analyzer.py --file_path ./data.csv --mode query \
  --sql "SELECT * FROM data" --output result.xlsx

# 持久化到 DuckDB 文件（后续可直接关联查询）
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode query \
  --persist_db_path ./analysis.duckdb --persist_table \
  --sql "SELECT category, SUM(price * quantity) as total_sales FROM data GROUP BY category"
```

### 步骤 4：结果分析
- 查看查询结果和数据预览
- 分析执行时间和重试次数
- 根据结果生成业务洞察

### 步骤 5：数据持久化（可选）
- `--persist_db_path`：指定 DuckDB 数据库文件路径
- `--persist_table`：将注册表持久化为普通表（默认是临时表）
- 典型用途：跨批次积累结果、后续多表关联查询、沉淀分析基表

## 资源索引
- 核心脚本：[scripts/duckdb_analyzer.py](scripts/duckdb_analyzer.py)（DuckDB 操作核心，支持数据注册、查询执行、抽样、错误处理）
- 数据格式参考：[references/data-formats.md](references/data-formats.md)（支持的文件格式和最佳实践）

## 注意事项

### 最佳实践
1. **先探索后查询**：先用 describe 模式了解数据结构，再生成 SQL
2. **复杂查询先抽样**：对于复杂查询，先用 `--sample_fraction` 参数在小样本上验证
3. **合理使用 LIMIT**：查询结果超过 1000 行时，建议使用 LIMIT 或聚合查询
4. **利用自动校正**：SQL 错误时会自动重试和校正，无需手动干预

### 性能建议
- 大数据集使用抽样验证后再执行完整查询
- 聚合查询比全表查询更高效
- 可以设置 `--max_retries` 参数调整重试次数

### 错误处理
- 语法错误会自动修复（多余分号、逗号等）
- 列名错误会尝试匹配最相似的列名（编辑距离≤2）
- 表名错误会提示检查表名
- 所有校正操作都会在输出中显示

## 使用示例

### 示例 1：完整数据探索
**场景**：拿到新数据集，需要了解数据结构和质量

**命令**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode describe
```

**输出包含**：
- 基本信息：20 行，7 列
- 表结构：各字段名称和数据类型
- 数值列统计：price 的平均值 356.99，中位数 264.99 等
- 分类列统计：category 有 2 个唯一值，Electronics 出现 12 次
- 日期列统计：sale_date 从 2024-01-15 到 2024-02-02
- 数据质量：所有列数据完整，无缺失值

### 示例 2：销售分析查询
**场景**：分析各类别产品的销售表现

**命令**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT category, COUNT(*) as num_products, SUM(price * quantity) as total_revenue, AVG(price) as avg_price FROM data GROUP BY category ORDER BY total_revenue DESC"
```

**输出**：
```
执行 SQL: SELECT category, COUNT(*) as num_products, SUM(price * quantity) as total_revenue, AVG(price) as avg_price FROM data GROUP BY category ORDER BY total_revenue DESC

【查询结果】
执行时间：0.05 秒
重试次数：0
结果行数：2

数据预览:
   category  num_products  total_revenue  avg_price
Electronics            12       42938.24     356.99
  Furniture             8       19949.23     356.99
```

**业务洞察**：
- Electronics 类别贡献了 68% 的总收入
- 两个类别的平均价格相同，但 Electronics 销量更高

### 示例 3：区域销售对比
**场景**：分析不同区域的销售情况

**命令**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT region, COUNT(*) as num_orders, SUM(price * quantity) as total_sales, AVG(price) as avg_order_value FROM data GROUP BY region ORDER BY total_sales DESC"
```

### 示例 4：高价产品筛选（带抽样验证）
**场景**：找出高价产品（price > 200），先在 10% 样本上验证

**命令**：
```bash
# 先在样本上验证
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT product_name, category, price FROM data WHERE price > 200" --sample_fraction 0.1

# 验证无误后执行完整查询
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT product_name, category, price FROM data WHERE price > 200 ORDER BY price DESC"
```

### 示例 5：自动 SQL 校正
**场景**：SQL 有语法错误（多余分号），系统自动校正

**命令**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT * FROM data WHERE price > 100;"
```

**输出**：
```
【SQL 校正记录】
  ✓ 语法校正：;\s*$ -> 

【查询结果】
执行时间：0.03 秒
重试次数：1
结果行数：15
```

### 示例 6：导出查询结果
**场景**：将查询结果保存为 CSV、Excel、JSON 或 Parquet 文件

**CSV 导出**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT category, region, SUM(price * quantity) as sales FROM data GROUP BY category, region" \
  --output sales_summary.csv
```

**Excel 导出**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT category, region, SUM(price * quantity) as sales FROM data GROUP BY category, region" \
  --output sales_summary.xlsx
```

**JSON 导出**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT category, region, SUM(price * quantity) as sales FROM data GROUP BY category, region" \
  --output sales_summary.json
```

**Parquet 导出**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT category, region, SUM(price * quantity) as sales FROM data GROUP BY category, region" \
  --output sales_summary.parquet
```

**结果**：根据文件扩展名自动选择导出格式，保存为相应文件

### 示例 7：时间序列分析
**场景**：分析销售趋势

**命令**：
```bash
python scripts/duckdb_analyzer.py --file_path ./sales_data.csv --mode query \
  --sql "SELECT DATE_TRUNC('month', sale_date) as month, SUM(price * quantity) as monthly_sales FROM data GROUP BY month ORDER BY month"
```

## 故障排查

### 常见问题

**Q1: 文件找不到？**
```
错误：数据文件不存在：./data.csv
```
解决：检查文件路径是否正确，使用绝对路径试试

**Q2: Excel 读取失败？**
```
错误：无法注册数据表：...
```
解决：
- 确认文件为 `.xlsx` 或 `.xls`
- 如工作表不在第一个，添加参数 `--excel_sheet "工作表名"`
- 检查是否安装 `openpyxl`

**Q3: SQL 执行失败？**
系统会自动重试和校正 SQL，如果仍然失败，检查：
- 列名是否正确（区分大小写）
- SQL 语法是否正确
- 表名是否使用了默认的 'data'

**Q4: 内存不足？**
解决：
- 使用抽样查询：`--sample_fraction 0.1`
- 添加 LIMIT 限制结果数量
- 使用聚合查询而非全表查询

## 输出格式说明

### Describe 模式输出
- **基本信息**：数据规模概览
- **表结构**：字段名和数据类型
- **数值列统计**：描述性统计指标
- **分类列统计**：分布和频率信息
- **日期列统计**：时间范围信息
- **数据质量**：缺失值统计
- **数据样本**：前 5 行数据预览

### Query 模式输出
- **SQL 校正记录**：如果有自动校正，会显示校正内容
- **查询结果**：执行时间、重试次数、结果行数
- **数据预览**：完整的查询结果表格

## 高级技巧

### 1. 链式分析
先用 describe 了解数据，再执行多个查询：
```bash
# 步骤 1：探索数据
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode describe

# 步骤 2：基于了解执行针对性查询
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode query \
  --sql "SELECT category, AVG(price) as avg_price FROM data GROUP BY category"
```

### 2. 性能优化
对于大数据集：
```bash
# 先用 1% 样本快速验证
python scripts/duckdb_analyzer.py --file_path ./large_data.csv --mode query \
  --sql "SELECT ..." --sample_fraction 0.01

# 验证通过后再执行完整查询
python scripts/duckdb_analyzer.py --file_path ./large_data.csv --mode query \
  --sql "SELECT ..."
```

### 3. 数据质量检查
```bash
python scripts/duckdb_analyzer.py --file_path ./data.csv --mode describe | grep "缺失"
```

## SQL 语法约束

- 仅使用 DuckDB SQL 方言，不使用其他数据库的专有语法
- 字段名支持英文和中文查询
- 包含中文、空格、连字符、冒号等特殊字符的字段名，必须使用双引号
- 当中文字段未加双引号时，查询引擎会自动校正并重试
- 支持中文标点自动转换（如 `，；（）` 转 `,;()`）
- 默认表名为 `data`
- 生成 SQL 时优先保证可执行性，再进行性能优化

## Pandas 使用边界

- Pandas 仅用于读取文件与将 DataFrame 注册到 DuckDB
- Pandas 可用于注册前的数据安全预处理（如 `inf/-inf -> NULL`）
- 不使用 Pandas 做业务聚合分析、统计计算或口径产出
- 最终分析结果必须通过 DuckDB SQL 查询 `data` 表生成

### 字段名示例

```sql
SELECT "销售渠道", SUM("售后退款-仅退货金额") AS total_return
FROM data
GROUP BY "销售渠道"
ORDER BY total_return DESC
LIMIT 10
```

```sql
SELECT 销售渠道, SUM(售后退款-仅退货金额) AS total_return
FROM data
GROUP BY 销售渠道
```
```

## Pool: validation_audit

### sql-master

```markdown
---
name: sql-master
description: SQL 查询、数据获取智能体。覆盖 SQL 全链路能力：自然语言转生产级 SQL、慢查询诊断与执行计划分析、索引设计与优化、数仓建模、SQL 原理深度科普、查询结果可视化。支持 MySQL / PostgreSQL / Hive / Spark SQL / ClickHouse / BigQuery 多方言。触发场景：(1) 写 SQL / 生成查询，(2) SQL 慢/优化/调优，(3) 执行计划分析 EXPLAIN，(4) 索引设计，(5) 数仓建模 / 分层设计，(6) SQL 原理问题（事务/锁/MVCC/Join算法等），(7) 表结构设计 DDL，(8) SQL 报错诊断，(9) 任何"帮我写个查询"、"这个SQL为什么慢"、"怎么建索引"类请求，(10) 查询结果可视化 / 出图 / 图表 / 数据展示。
---

# SQL Master — SQL 查询、数据获取智能体

## ⚠️ 使用前必读

本 Skill 需要 Python 依赖。**首次使用前必须安装依赖**：

```bash
skillhub_install install_skill sql-master
```

工具会自动检测 Python3 环境、pip 可用性，并安装所有依赖。

### 依赖安装方式

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| **自动安装（推荐）** | `skillhub_install install_skill sql-master` | 一键安装，自动处理 |
| **手动安装** | `pip install -r requirements.txt` | 熟悉 Python 环境的用户 |

### 无依赖使用（受限模式）

如果无法安装依赖，本 Skill 提供以下**降级能力**：

✅ **可用功能**：
- SQL 语句生成（纯文本输出，无需执行）
- SQL 诊断与优化建议（基于文本分析）
- 索引设计建议（基于规则引擎）
- SQL 原理解释与科普
- 执行计划分析（用户提供 EXPLAIN 结果）

❌ **不可用功能**：
- 数据库连接与 SQL 执行
- 数据 Pipeline 处理
- 本地文件数据获取（CSV/Excel 等）
- 与 sql-dataviz / sql-report-generator 联动

---

## 🔗 Skill 协作关系

本 Skill 与 **sql-dataviz**、**sql-report-generator** 组成完整的数据分析流水线：

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────────┐
│ sql-master  │ ──► │ sql-dataviz  │ ──► │ sql-report-generator   │
│  (数据层)   │     │  (可视化层)  │     │  (报告层)              │
└─────────────┘     └──────────────┘     └────────────────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
   SQL 查询           图表生成            HTML 报告
   数据获取           PNG/HTML            AI 洞察
   格式转换           Dashboard           数据表格
```

### 协作模式

| 模式 | 组合 | 适用场景 |
|------|------|---------|
| **单独使用** | sql-master | 仅需 SQL 查询/生成/优化 |
| **可视化** | sql-master + sql-dataviz | SQL 查询 → 图表输出 |
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
├─ 仅 SQL 查询/优化 → sql-master 单独使用
├─ SQL + 图表 → sql-master + sql-dataviz
├─ 图表 + 报告（无 SQL）→ sql-dataviz + sql-report-generator
└─ 完整分析报告 → sql-master + sql-dataviz + sql-report-generator ✅ 推荐
```

---

## 新增功能：统一 Pipeline 编排（三 Skill 端到端）

### `scripts/unified_pipeline.py`

打通 sql-master → sql-dataviz → sql-report-generator 的端到端自动化：

```python
from scripts.unified_pipeline import UnifiedPipeline, analyze_file

# 完整 Pipeline
result = (
    UnifiedPipeline("销售分析")
    .from_file("sales.csv")                        # 数据源
    .query("SELECT region, SUM(sales) as total FROM data GROUP BY region")  # SQL
    .interactive_chart("bar", x_col="region", y_col="total", title="区域销售")  # 交互图
    .chart("line", x_col="region", y_col="total")              # 静态图 (PNG)
    .insights(value_cols=["total"])                            # AI 洞察
    .report(title="销售报告", output="report.html")           # 完整报告
)
print(result.log())

# 一键分析
result = analyze_file("sales.csv", output="report.html")
```

**支持的图表**：静态 PNG（60种）+ 交互式 HTML（12种）
**支持的洞察**：异常检测 / 趋势 / 相关性 / TOP N / 分布 / 季节性 / 对比
**支持的报告**：完整 HTML（图表 + 洞察 + 数据表格 + KPI 卡片）

## 新增功能：数据库连接执行层 + 数据 Pipeline

### 1. 数据库连接（scripts/database_connector.py）

支持 SQLite / MySQL / PostgreSQL / SQL Server / ClickHouse / Oracle

```python
from scripts.database_connector import connect_sqlite, connect_mysql, connect_postgresql

# SQLite（本地文件）
conn = connect_sqlite("data/sales.db")
result = conn.execute("SELECT region, SUM(amount) FROM sales GROUP BY region")
print(result.df)           # DataFrame 访问
print(result.to_dict())   # dict 访问
result.to_csv("output.csv")  # 导出 CSV
result.to_json("output.json") # 导出 JSON

# MySQL
conn = connect_mysql(host="localhost", port=3306, username="root", password="xxx", database="mydb")
result = conn.execute("SELECT * FROM orders WHERE date >= '2024-01-01'")
print(result.summary())   # 可读摘要

# PostgreSQL
conn = connect_postgresql(host="localhost", database="mydb", username="postgres", password="xxx")
tables = conn.get_tables()  # 获取所有表名
schema = conn.get_schema("orders")  # 获取表结构
conn.close()
```

### 2. 本地文件数据获取（scripts/file_connector.py）

支持 CSV / Excel / JSON / Parquet / SQLite 等所有主流格式，自动 SQL 查询 + 格式转换

```python
from scripts.file_connector import load_file, load_directory

# 加载本地文件
fc = load_file("data/sales.csv")        # 单个文件
fc = load_directory("data/reports/")     # 目录下所有文件
fc = load_file("data/*.csv")            # 通配符匹配

print(fc.shape)           # (10000, 12)
print(fc.columns)         # ['date', 'region', 'amount', ...]
print(fc.df.head())       # DataFrame

# 用途一：SQL 查询（自动建 SQLite 内存表）
result = fc.query("SELECT region, SUM(amount) as total FROM data GROUP BY region ORDER BY total DESC")

# 用途二：格式转换
fc.to_csv("output/sales_report.csv")
fc.to_excel("output/sales_report.xlsx")
fc.to_json("output/sales_report.json")
fc.to_parquet("output/sales_report.parquet")
fc.to_sqlite("output/sales.db", table_name="sales")

# 用途三：传给 sql-dataviz 画图
b64 = fc.to_dataviz("line", x_col="month", y_col="sales", title="月度销售趋势")
```

### 3. SQL Pipeline 流水线（scripts/pipeline.py）

三大用途一气呵成：数据获取 → SQL 查询 → 格式转换 → 可视化 → HTML 报告

```python
from scripts.pipeline import SQLPipeline

# 方式一：从文件开始
p = (
    SQLPipeline()
    .from_file("data/sales.csv")
    .query("SELECT region, SUM(amount) as total FROM data GROUP BY region")
    .to_csv("output/regional_sales.csv")
    .to_excel("output/regional_sales.xlsx")
)

# 方式二：从数据库开始
p = SQLPipeline().from_db(dialect="sqlite", database="data.db")
p.query("SELECT * FROM sales WHERE amount > 1000")
p.query("SELECT region, COUNT(*) FROM data GROUP BY region")

# 方式三：从 DataFrame 开始
import pandas as pd
df = pd.read_csv("data.csv")
p = SQLPipeline().from_dataframe(df)

# 管道操作
p.query("SELECT region, SUM(amount) as total FROM data GROUP BY region")
p.transform(lambda df: df[df["total"] > 1000])  # 过滤
p.to_dataviz("bar", x_col="region", y_col="total", title="区域销售排行")
p.to_report(title="销售分析报告", output="output/report.html")
p.log()   # 打印执行日志
```

**Pipeline 完整流程示例：**
```python
(
    SQLPipeline()
    .from_file("sales_2024.csv")                        # 加载数据
    .query("SELECT * FROM data WHERE region = '华东'")  # SQL 筛选
    .to_csv("output/east_sales.csv")                   # 导出 CSV
    .to_json("output/east_sales.json")                 # 导出 JSON
    .to_dataviz("line", x_col="month", y_col="sales") # 生成折线图
    .to_dataviz("pie", x_col="product", y_col="amount") # 生成饼图
    .to_report(title="华东区域销售报告", output="output/report.html")  # HTML 报告
)
```

## 核心原则

**生产级标准**：所有输出的 SQL 必须满足：
- 注释完整（业务背景 + 性能预期 + 适用数据量级）
- 明确标注数据库版本和方言
- 主动提示 NULL 处理、空集合、边界条件
- 给出多方案时说明各自 trade-off

**分层回答**：同一问题，先给结论，再给原理，最后给深入扩展。自动识别用户水平（初学者/开发者/DBA），调整解释深度。

**可复现**：生成的 SQL 必须附带最小可复现测试数据（DDL + INSERT），确保用户能直接验证。

---

## 功能模块导航

| 场景 | 参考文件 |
|------|---------|
| 自然语言 → SQL 生成 | [references/sql-generation.md](references/sql-generation.md) |
| 慢查询诊断 & 执行计划分析 | [references/query-optimization.md](references/query-optimization.md) |
| 索引设计策略 | [references/index-design.md](references/index-design.md) |
| 数仓建模 & 分层架构 | [references/data-warehouse.md](references/data-warehouse.md) |
| Hive 数据倾斜深度（引擎原理/量化模型/极端场景） | [references/hive-skew-advanced.md](references/hive-skew-advanced.md) |
| SQL 原理深度（事务/锁/MVCC/Join） | [references/sql-internals.md](references/sql-internals.md) |
| 多方言差异速查 | [references/dialect-guide.md](references/dialect-guide.md) |
| DDL 设计规范 | [references/ddl-design.md](references/ddl-design.md) |
| SQL 安全规范（注入防护/参数化查询） | [references/sql-security.md](references/sql-security.md) |
| CLI 实操速查（sqlite3/psql/mysql 连接与导入导出） | [references/cli-quickref.md](references/cli-quickref.md) |
| 查询结果可视化（图表选型/Python 代码/设计原则） | [references/visualization-guide.md](references/visualization-guide.md) |

---

## 工作流程

### 1. 意图识别
收到请求后，先判断属于哪个场景：
- **生成类**：用户描述业务需求，需要输出 SQL
- **优化类**：用户提供现有 SQL 或 EXPLAIN，需要诊断和改写
- **设计类**：表结构、索引、数仓架构设计
- **科普类**：原理解释、概念问答
- **诊断类**：报错信息分析
- **可视化类**：将查询结果转化为图表 → 加载 [references/visualization-guide.md](references/visualization-guide.md)

### 2. 上下文收集
生成或优化 SQL 前，主动确认（如未提供）：
- 数据库类型和版本
- 关键表的 schema（列名、类型、索引）
- 数据量级（行数、数据大小）
- 查询频率和性能目标（P99 < Xms？）

### 3. 输出规范

**SQL 输出模板**：
```sql
-- ============================================================
-- 业务说明：[描述这段 SQL 解决什么业务问题]
-- 数据库：MySQL 8.0 / PostgreSQL 15 / ...
-- 性能预期：[预计执行时间，适用数据量级]
-- 注意事项：[NULL 处理、边界条件、已知限制]
-- ============================================================

SELECT ...
FROM ...
WHERE ...
```

**优化报告模板**：
```
## 问题诊断
[执行计划中发现的问题，按严重程度排序]

## 优化方案
### 方案 A（推荐）
[改写后的 SQL + 原因]

### 方案 B（备选）
[另一种思路 + 适用场景]

## 预期收益
[优化前 vs 优化后的性能对比估算]

## 可复现测试
[最小 DDL + 数据 + 验证步骤]
```

### 4. 加载参考文件
根据意图识别结果，读取对应的 references/ 文件获取详细指导。

---

## 快速参考

### 常见性能陷阱（立即识别）
- `SELECT *` → 明确列名，避免回表
- `WHERE` 列上有函数 → 索引失效
- `OR` 连接不同列 → 考虑 UNION ALL
- `!=` / `NOT IN` → 无法走索引
- 隐式类型转换 → 索引失效
- `LIMIT` 大偏移量 → 延迟关联优化
- `COUNT(*)` vs `COUNT(col)` → NULL 语义差异

### Join 算法选择直觉
- 小表 JOIN 大表 → Nested Loop（小表驱动）
- 两个大表等值 JOIN → Hash Join
- 有序数据等值 JOIN → Merge Join
- 数据倾斜 → 广播小表 / 加盐打散

### 索引设计口诀
**最左前缀、区分度高、覆盖查询、避免冗余**

---

## 强制规范（MUST DO / MUST NOT）

借鉴 sql-pro 的约束清单，以下规则在任何情况下都必须遵守：

### ✅ MUST DO
- 优化前**必须先分析执行计划**（EXPLAIN / EXPLAIN ANALYZE）
- 优先使用**集合操作**，避免逐行处理（游标/循环）
- **尽早过滤**：WHERE 条件尽量前置，减少中间结果集
- 存在性检查用 `EXISTS`，不用 `COUNT(*) > 0`
- **显式处理 NULL**：IS NULL / IS NOT NULL / COALESCE / NULLIF
- 为高频查询创建**覆盖索引**
- 涉及安全场景时，必须使用**参数化查询**，详见 [references/sql-security.md](references/sql-security.md)
- 跨数据库迁移时，必须标注**方言差异**，详见 [references/dialect-guide.md](references/dialect-guide.md)

### ❌ MUST NOT
- 不在 WHERE / JOIN 条件列上使用函数（导致索引失效）
- 不用 `SELECT *`（回表开销 + 隐式依赖）
- 不用字符串拼接构造 SQL（SQL 注入风险）
- 不在大表上做无索引的全表扫描
- 不用 `OFFSET` 大偏移量分页（改用游标/keyset 分页）
- 不忽略隐式类型转换（导致索引失效 + 数据截断）
- 不在生产环境直接运行未经 EXPLAIN 验证的复杂查询
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
