# Experiment Condition: multi_pool_sample_s09

One sampled skill from each pool, seed 9

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 9

## Skill Pools

### table_extraction
- chat2duckdb

### data_cleaning
- chat2duckdb

### validation_audit
- data-anomaly-detector

### summary_reporting
- data2visualization

## Pool Samples

- table_extraction: chat2duckdb
- data_cleaning: chat2duckdb
- validation_audit: data-anomaly-detector
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

- chat2duckdb
- data-anomaly-detector
- data2visualization

## Available Skill Documents

## Pool: table_extraction

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

### data-anomaly-detector

```markdown
---
name: "data-anomaly-detector"
description: "Detect anomalies and outliers in construction data: unusual costs, schedule variances, productivity spikes. Statistical and ML-based detection methods."
homepage: "https://datadrivenconstruction.io"
metadata: {"openclaw": {"emoji": "✔️", "os": ["darwin", "linux", "win32"], "homepage": "https://datadrivenconstruction.io", "requires": {"bins": ["python3"]}}}
---
# Data Anomaly Detector for Construction

## Overview

Detect unusual patterns, outliers, and anomalies in construction data. Identify cost overruns, schedule delays, productivity issues, and data quality problems before they impact projects.

## Business Case

Construction data often contains anomalies that indicate:
- Cost estimate errors or fraud
- Schedule logic issues
- Productivity problems
- Data entry mistakes
- Equipment or material issues

Early detection prevents costly corrections and project delays.

## Technical Implementation

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats

class AnomalyType(Enum):
    OUTLIER = "outlier"
    PATTERN_BREAK = "pattern_break"
    MISSING_SEQUENCE = "missing_sequence"
    DUPLICATE = "duplicate"
    IMPOSSIBLE_VALUE = "impossible_value"
    TREND_DEVIATION = "trend_deviation"

class AnomalySeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Anomaly:
    id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    field: str
    value: Any
    expected_range: Optional[Tuple[float, float]] = None
    description: str = ""
    row_index: Optional[int] = None
    detection_method: str = ""
    confidence: float = 0.0
    suggested_action: str = ""

@dataclass
class AnomalyReport:
    source: str
    detected_at: datetime
    total_records: int
    anomalies: List[Anomaly]
    summary: Dict[str, int]

class ConstructionAnomalyDetector:
    """Detect anomalies in construction data."""

    # Construction-specific thresholds
    COST_THRESHOLDS = {
        'concrete_per_cy': (200, 800),
        'steel_per_ton': (1500, 4000),
        'labor_per_hour': (25, 150),
        'overhead_percentage': (5, 25),
        'contingency_percentage': (3, 20),
    }

    SCHEDULE_THRESHOLDS = {
        'max_activity_duration': 365,  # days
        'max_lag': 30,  # days
        'min_productivity': 0.1,
        'max_productivity': 10.0,
    }

    def __init__(self):
        self.anomalies: List[Anomaly] = []
        self.detection_history: List[AnomalyReport] = []

    def detect_cost_anomalies(self, df: pd.DataFrame, cost_column: str,
                              group_by: str = None) -> List[Anomaly]:
        """Detect anomalies in cost data."""
        anomalies = []

        # Statistical outlier detection (IQR method)
        Q1 = df[cost_column].quantile(0.25)
        Q3 = df[cost_column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = df[(df[cost_column] < lower_bound) | (df[cost_column] > upper_bound)]

        for idx, row in outliers.iterrows():
            value = row[cost_column]
            severity = AnomalySeverity.HIGH if abs(value - df[cost_column].median()) > 3 * IQR else AnomalySeverity.MEDIUM

            anomalies.append(Anomaly(
                id=f"COST-{idx}",
                anomaly_type=AnomalyType.OUTLIER,
                severity=severity,
                field=cost_column,
                value=value,
                expected_range=(lower_bound, upper_bound),
                description=f"Cost value {value:,.2f} outside expected range",
                row_index=idx,
                detection_method="IQR",
                confidence=0.95,
                suggested_action="Review cost estimate for errors"
            ))

        # Negative cost check
        negatives = df[df[cost_column] < 0]
        for idx, row in negatives.iterrows():
            anomalies.append(Anomaly(
                id=f"COST-NEG-{idx}",
                anomaly_type=AnomalyType.IMPOSSIBLE_VALUE,
                severity=AnomalySeverity.CRITICAL,
                field=cost_column,
                value=row[cost_column],
                expected_range=(0, None),
                description="Negative cost value detected",
                row_index=idx,
                detection_method="Business Rule",
                confidence=1.0,
                suggested_action="Correct data entry error or investigate credit"
            ))

        # Group-based anomalies (if grouped)
        if group_by and group_by in df.columns:
            group_stats = df.groupby(group_by)[cost_column].agg(['mean', 'std'])

            for group_name, stats in group_stats.iterrows():
                group_data = df[df[group_by] == group_name]
                z_scores = np.abs((group_data[cost_column] - stats['mean']) / stats['std'])

                for idx, z in z_scores.items():
                    if z > 3:
                        anomalies.append(Anomaly(
                            id=f"COST-GROUP-{idx}",
                            anomaly_type=AnomalyType.OUTLIER,
                            severity=AnomalySeverity.MEDIUM,
                            field=cost_column,
                            value=df.loc[idx, cost_column],
                            description=f"Unusual cost for group {group_name} (z-score: {z:.2f})",
                            row_index=idx,
                            detection_method="Z-Score by Group",
                            confidence=min(z / 5, 1.0)
                        ))

        return anomalies

    def detect_schedule_anomalies(self, df: pd.DataFrame) -> List[Anomaly]:
        """Detect anomalies in schedule data."""
        anomalies = []

        # Check for required columns
        required = ['start_date', 'end_date']
        if not all(col in df.columns for col in required):
            return anomalies

        # Convert dates
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])

        # Calculate duration
        df['duration'] = (df['end_date'] - df['start_date']).dt.days

        # Negative duration (end before start)
        negative_duration = df[df['duration'] < 0]
        for idx, row in negative_duration.iterrows():
            anomalies.append(Anomaly(
                id=f"SCHED-NEG-{idx}",
                anomaly_type=AnomalyType.IMPOSSIBLE_VALUE,
                severity=AnomalySeverity.CRITICAL,
                field="duration",
                value=row['duration'],
                description="End date before start date",
                row_index=idx,
                detection_method="Business Rule",
                confidence=1.0,
                suggested_action="Correct dates"
            ))

        # Extremely long durations
        long_tasks = df[df['duration'] > self.SCHEDULE_THRESHOLDS['max_activity_duration']]
        for idx, row in long_tasks.iterrows():
            anomalies.append(Anomaly(
                id=f"SCHED-LONG-{idx}",
                anomaly_type=AnomalyType.OUTLIER,
                severity=AnomalySeverity.MEDIUM,
                field="duration",
                value=row['duration'],
                expected_range=(0, self.SCHEDULE_THRESHOLDS['max_activity_duration']),
                description=f"Task duration {row['duration']} days exceeds threshold",
                row_index=idx,
                detection_method="Threshold",
                confidence=0.9,
                suggested_action="Review if task should be broken down"
            ))

        # Zero duration non-milestones
        if 'is_milestone' in df.columns:
            zero_duration = df[(df['duration'] == 0) & (~df['is_milestone'])]
            for idx, row in zero_duration.iterrows():
                anomalies.append(Anomaly(
                    id=f"SCHED-ZERO-{idx}",
                    anomaly_type=AnomalyType.IMPOSSIBLE_VALUE,
                    severity=AnomalySeverity.HIGH,
                    field="duration",
                    value=0,
                    description="Zero duration task that is not a milestone",
                    row_index=idx,
                    detection_method="Business Rule",
                    confidence=1.0,
                    suggested_action="Add duration or mark as milestone"
                ))

        return anomalies

    def detect_productivity_anomalies(self, df: pd.DataFrame,
                                      quantity_col: str,
                                      hours_col: str) -> List[Anomaly]:
        """Detect productivity anomalies."""
        anomalies = []

        # Calculate productivity
        df['productivity'] = df[quantity_col] / df[hours_col].replace(0, np.nan)

        # Use Modified Z-Score (more robust for skewed data)
        median = df['productivity'].median()
        mad = np.abs(df['productivity'] - median).median()
        modified_z = 0.6745 * (df['productivity'] - median) / mad

        outliers = df[np.abs(modified_z) > 3.5]

        for idx, row in outliers.iterrows():
            prod = row['productivity']
            z = modified_z.loc[idx]

            severity = AnomalySeverity.HIGH if abs(z) > 5 else AnomalySeverity.MEDIUM
            direction = "high" if z > 0 else "low"

            anomalies.append(Anomaly(
                id=f"PROD-{idx}",
                anomaly_type=AnomalyType.OUTLIER,
                severity=severity,
                field="productivity",
                value=prod,
                description=f"Unusually {direction} productivity: {prod:.2f} units/hour",
                row_index=idx,
                detection_method="Modified Z-Score",
                confidence=min(abs(z) / 7, 1.0),
                suggested_action=f"Investigate {direction} productivity cause"
            ))

        return anomalies

    def detect_time_series_anomalies(self, df: pd.DataFrame,
                                      date_col: str,
                                      value_col: str,
                                      window: int = 7) -> List[Anomaly]:
        """Detect anomalies in time series data (e.g., daily costs, progress)."""
        anomalies = []

        df = df.sort_values(date_col).copy()
        df['rolling_mean'] = df[value_col].rolling(window=window, center=True).mean()
        df['rolling_std'] = df[value_col].rolling(window=window, center=True).std()

        # Points outside 2 standard deviations from rolling mean
        df['z_score'] = (df[value_col] - df['rolling_mean']) / df['rolling_std']

        outliers = df[np.abs(df['z_score']) > 2].dropna()

        for idx, row in outliers.iterrows():
            anomalies.append(Anomaly(
                id=f"TS-{idx}",
                anomaly_type=AnomalyType.TREND_DEVIATION,
                severity=AnomalySeverity.MEDIUM if abs(row['z_score']) < 3 else AnomalySeverity.HIGH,
                field=value_col,
                value=row[value_col],
                expected_range=(
                    row['rolling_mean'] - 2 * row['rolling_std'],
                    row['rolling_mean'] + 2 * row['rolling_std']
                ),
                description=f"Value deviates from {window}-day trend",
                row_index=idx,
                detection_method="Rolling Z-Score",
                confidence=min(abs(row['z_score']) / 4, 1.0)
            ))

        return anomalies

    def detect_duplicate_anomalies(self, df: pd.DataFrame,
                                   key_columns: List[str]) -> List[Anomaly]:
        """Detect duplicate records."""
        anomalies = []

        duplicates = df[df.duplicated(subset=key_columns, keep=False)]

        if len(duplicates) > 0:
            dup_groups = duplicates.groupby(key_columns).size()
            for keys, count in dup_groups.items():
                anomalies.append(Anomaly(
                    id=f"DUP-{hash(str(keys)) % 10000}",
                    anomaly_type=AnomalyType.DUPLICATE,
                    severity=AnomalySeverity.HIGH,
                    field=str(key_columns),
                    value=keys,
                    description=f"Found {count} duplicate records for {keys}",
                    detection_method="Exact Match",
                    confidence=1.0,
                    suggested_action="Review and remove duplicates"
                ))

        return anomalies

    def detect_sequence_gaps(self, df: pd.DataFrame, sequence_col: str) -> List[Anomaly]:
        """Detect gaps in sequential data (invoice numbers, PO numbers, etc.)."""
        anomalies = []

        # Extract numeric part if mixed format
        df['seq_num'] = pd.to_numeric(
            df[sequence_col].astype(str).str.extract(r'(\d+)')[0],
            errors='coerce'
        )

        sorted_seq = df['seq_num'].dropna().sort_values()
        expected = range(int(sorted_seq.min()), int(sorted_seq.max()) + 1)
        actual = set(sorted_seq.astype(int))
        missing = set(expected) - actual

        if missing:
            # Group consecutive missing numbers
            missing_ranges = []
            sorted_missing = sorted(missing)
            start = sorted_missing[0]
            end = start

            for num in sorted_missing[1:]:
                if num == end + 1:
                    end = num
                else:
                    missing_ranges.append((start, end))
                    start = num
                    end = num
            missing_ranges.append((start, end))

            for start, end in missing_ranges:
                range_str = str(start) if start == end else f"{start}-{end}"
                anomalies.append(Anomaly(
                    id=f"SEQ-{start}",
                    anomaly_type=AnomalyType.MISSING_SEQUENCE,
                    severity=AnomalySeverity.MEDIUM,
                    field=sequence_col,
                    value=range_str,
                    description=f"Missing sequence number(s): {range_str}",
                    detection_method="Sequence Analysis",
                    confidence=1.0,
                    suggested_action="Investigate missing numbers"
                ))

        return anomalies

    def run_full_detection(self, df: pd.DataFrame, config: Dict) -> AnomalyReport:
        """Run all applicable anomaly detection methods."""
        all_anomalies = []

        # Cost anomalies
        if 'cost_columns' in config:
            for col in config['cost_columns']:
                if col in df.columns:
                    all_anomalies.extend(
                        self.detect_cost_anomalies(df, col, config.get('group_by'))
                    )

        # Schedule anomalies
        if 'start_date' in df.columns and 'end_date' in df.columns:
            all_anomalies.extend(self.detect_schedule_anomalies(df))

        # Productivity
        if 'quantity_col' in config and 'hours_col' in config:
            all_anomalies.extend(
                self.detect_productivity_anomalies(
                    df, config['quantity_col'], config['hours_col']
                )
            )

        # Duplicates
        if 'key_columns' in config:
            all_anomalies.extend(
                self.detect_duplicate_anomalies(df, config['key_columns'])
            )

        # Sequence gaps
        if 'sequence_column' in config:
            all_anomalies.extend(
                self.detect_sequence_gaps(df, config['sequence_column'])
            )

        # Create summary
        summary = {}
        for a in all_anomalies:
            key = f"{a.anomaly_type.value}_{a.severity.value}"
            summary[key] = summary.get(key, 0) + 1

        report = AnomalyReport(
            source=config.get('source_name', 'Unknown'),
            detected_at=datetime.now(),
            total_records=len(df),
            anomalies=all_anomalies,
            summary=summary
        )

        self.detection_history.append(report)
        return report

    def generate_report(self, report: AnomalyReport) -> str:
        """Generate markdown anomaly report."""
        lines = [f"# Anomaly Detection Report", ""]
        lines.append(f"**Source:** {report.source}")
        lines.append(f"**Detected At:** {report.detected_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Total Records:** {report.total_records:,}")
        lines.append(f"**Anomalies Found:** {len(report.anomalies)}")
        lines.append("")

        # Summary by severity
        lines.append("## Summary by Severity")
        for severity in AnomalySeverity:
            count = sum(1 for a in report.anomalies if a.severity == severity)
            if count > 0:
                lines.append(f"- **{severity.value.upper()}:** {count}")
        lines.append("")

        # Critical anomalies first
        critical = [a for a in report.anomalies if a.severity == AnomalySeverity.CRITICAL]
        if critical:
            lines.append("## Critical Anomalies")
            for a in critical:
                lines.append(f"\n### {a.id}")
                lines.append(f"- **Type:** {a.anomaly_type.value}")
                lines.append(f"- **Field:** {a.field}")
                lines.append(f"- **Value:** {a.value}")
                lines.append(f"- **Description:** {a.description}")
                lines.append(f"- **Action:** {a.suggested_action}")

        # All anomalies table
        lines.append("\n## All Anomalies")
        lines.append("| ID | Type | Severity | Field | Description |")
        lines.append("|-----|------|----------|-------|-------------|")
        for a in report.anomalies[:50]:
            lines.append(f"| {a.id} | {a.anomaly_type.value} | {a.severity.value} | {a.field} | {a.description[:50]} |")

        if len(report.anomalies) > 50:
            lines.append(f"\n*... and {len(report.anomalies) - 50} more anomalies*")

        return "\n".join(lines)
```

## Quick Start

```python
import pandas as pd

# Load data
df = pd.read_excel("project_costs.xlsx")

# Initialize detector
detector = ConstructionAnomalyDetector()

# Run detection
config = {
    'source_name': 'Project Costs Q1 2026',
    'cost_columns': ['total_cost', 'labor_cost', 'material_cost'],
    'group_by': 'cost_code',
    'key_columns': ['project_id', 'cost_code', 'date'],
    'sequence_column': 'invoice_number'
}

report = detector.run_full_detection(df, config)

# Generate report
print(detector.generate_report(report))

# Get critical anomalies for immediate action
critical = [a for a in report.anomalies if a.severity == AnomalySeverity.CRITICAL]
print(f"\n{len(critical)} critical anomalies require immediate attention")
```

## Dependencies

```bash
pip install pandas numpy scipy
```

## Resources

- **Statistical Methods**: IQR, Z-Score, Modified Z-Score
- **Construction Benchmarks**: RSMeans, ENR indices
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
