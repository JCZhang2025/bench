# Experiment Condition: multi_pool_sample_s04

One sampled skill from each pool, seed 4

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 4

## Skill Pools

### table_extraction
- bbox-row-column-parser

### data_cleaning
- data-analyst-cn

### validation_audit
- metric-consistency-auditor

### summary_reporting
- generate-report123

## Pool Samples

- table_extraction: bbox-row-column-parser
- data_cleaning: data-analyst-cn
- validation_audit: metric-consistency-auditor
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
- data-analyst-cn
- metric-consistency-auditor
- generate-report123

## Available Skill Documents

## Pool: table_extraction

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

## Pool: data_cleaning

### data-analyst-cn

```markdown
---
name: data-analyst-cn
version: 1.0.23
description: 数据分析助手 - 数据清洗、统计分析、可视化建议。适合：数据分析师、产品经理、运营。
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["python3"]
---

# 数据分析助手 Skill

快速进行数据清洗、统计分析和可视化。

## 核心功能

| 功能 | 描述 |
|------|------|
| 数据清洗 | 去重、填充、格式化 |
| 统计分析 | 描述统计、相关分析 |
| 可视化 | 图表建议、代码生成 |
| 报告生成 | 自动生成分析报告 |

## 使用方法

### 分析数据

```
分析这个 CSV 文件：sales.csv
```

### 数据清洗

```
清洗这个数据集，处理缺失值和异常值
```

### 生成图表

```
为这些数据生成折线图代码
```

## Python 数据分析模板

### 读取数据

```python
import pandas as pd

# CSV
df = pd.read_csv('data.csv')

# Excel
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# JSON
df = pd.read_json('data.json')

# 数据库
import sqlite3
conn = sqlite3.connect('database.db')
df = pd.read_sql('SELECT * FROM table', conn)

# API
import requests
response = requests.get('https://api.example.com/data')
df = pd.DataFrame(response.json())
```

### 数据预览

```python
# 基本信息
print(df.shape)        # 行列数
print(df.columns)      # 列名
print(df.dtypes)       # 数据类型
print(df.info())       # 详细信息

# 查看数据
print(df.head())       # 前 5 行
print(df.tail())       # 后 5 行
print(df.sample(5))    # 随机 5 行

# 描述统计
print(df.describe())   # 数值列统计
print(df.describe(include='all'))  # 所有列
```

### 数据清洗

```python
# 处理缺失值
df.isnull().sum()                    # 统计缺失
df.dropna()                          # 删除缺失行
df.fillna(0)                         # 填充 0
df.fillna(df.mean())                 # 填充均值
df['col'].fillna(df['col'].mode()[0])  # 填充众数

# 处理重复
df.duplicated().sum()                # 统计重复
df.drop_duplicates()                 # 删除重复
df.drop_duplicates(subset=['col'])   # 按列去重

# 数据类型转换
df['date'] = pd.to_datetime(df['date'])
df['price'] = df['price'].astype(float)
df['category'] = df['category'].astype('category')

# 异常值处理
Q1 = df['col'].quantile(0.25)
Q3 = df['col'].quantile(0.75)
IQR = Q3 - Q1
df = df[(df['col'] >= Q1 - 1.5*IQR) & (df['col'] <= Q3 + 1.5*IQR)]

# 字符串处理
df['name'] = df['name'].str.strip()
df['name'] = df['name'].str.lower()
df['name'] = df['name'].str.replace('old', 'new')
```

### 统计分析

```python
# 集中趋势
df['col'].mean()      # 均值
df['col'].median()    # 中位数
df['col'].mode()      # 众数

# 离散程度
df['col'].std()       # 标准差
df['col'].var()       # 方差
df['col'].max() - df['col'].min()  # 极差

# 分布
df['col'].skew()      # 偏度
df['col'].kurt()      # 峰度
df['col'].quantile([0.25, 0.5, 0.75])  # 分位数

# 相关分析
df.corr()             # 相关矩阵
df.corr()['target']   # 与目标的相关性

# 分组统计
df.groupby('category').agg({
    'sales': ['sum', 'mean', 'count'],
    'profit': 'mean'
})

# 交叉表
pd.crosstab(df['col1'], df['col2'])
```

### 时间序列分析

```python
# 日期处理
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')

# 时间重采样
df.resample('D').sum()      # 按天
df.resample('W').mean()     # 按周
df.resample('M').sum()      # 按月

# 滚动统计
df['rolling_mean'] = df['col'].rolling(window=7).mean()
df['rolling_std'] = df['col'].rolling(window=7).std()

# 时间差
df['diff'] = df['col'].diff()
df['pct_change'] = df['col'].pct_change()

# 季节分解
from statsmodels.tsa.seasonal import seasonal_decompose
result = seasonal_decompose(df['col'], model='additive', period=12)
result.plot()
```

## 可视化代码

### 基础图表

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 折线图
plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['value'])
plt.title('趋势图')
plt.xlabel('日期')
plt.ylabel('数值')
plt.show()

# 柱状图
plt.bar(df['category'], df['value'])
plt.xticks(rotation=45)
plt.show()

# 散点图
plt.scatter(df['x'], df['y'], alpha=0.5)
plt.xlabel('X')
plt.ylabel('Y')
plt.show()

# 直方图
plt.hist(df['value'], bins=20, edgecolor='black')
plt.xlabel('数值')
plt.ylabel('频数')
plt.show()

# 箱线图
sns.boxplot(data=df, x='category', y='value')
plt.show()

# 热力图
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0)
plt.show()
```

### 高级图表

```python
# 分组柱状图
df_grouped = df.groupby(['category', 'type'])['value'].sum().unstack()
df_grouped.plot(kind='bar', figsize=(12, 6))
plt.legend(title='类型')
plt.show()

# 小提琴图
sns.violinplot(data=df, x='category', y='value')
plt.show()

# 配对图
sns.pairplot(df[['col1', 'col2', 'col3', 'category']], hue='category')
plt.show()

# 时间序列
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df.index, df['value'], label='实际值')
ax.plot(df.index, df['rolling_mean'], label='7日均值', linestyle='--')
ax.fill_between(df.index, df['lower'], df['upper'], alpha=0.2)
ax.legend()
plt.show()
```

## 分析报告模板

```python
def generate_report(df):
    """生成数据分析报告"""
    report = f"""
# 数据分析报告

## 1. 数据概览
- 数据量：{len(df)} 行 × {len(df.columns)} 列
- 时间范围：{df['date'].min()} 至 {df['date'].max()}
- 缺失值：{df.isnull().sum().sum()} 个

## 2. 关键指标
- 总销售额：¥{df['sales'].sum():,.2f}
- 平均订单：¥{df['sales'].mean():,.2f}
- 最高订单：¥{df['sales'].max():,.2f}
- 最低订单：¥{df['sales'].min():,.2f}

## 3. 分布特征
- 偏度：{df['sales'].skew():.2f}
- 峰度：{df['sales'].kurt():.2f}
- 标准差：{df['sales'].std():,.2f}

## 4. Top 5 类别
{df.groupby('category')['sales'].sum().sort_values(ascending=False).head().to_markdown()}

## 5. 趋势分析
- 环比增长：{df['sales'].pct_change().mean()*100:.2f}%
- 月均销售额：¥{df.resample('M', on='date')['sales'].sum().mean():,.2f}

## 6. 建议
1. 重点推广 Top 3 类别
2. 优化低转化品类
3. 关注季节性波动
"""
    return report
```

## 注意事项

- 大数据集注意内存使用
- 处理前备份数据
- 结果需要业务验证
- 可视化要简洁清晰

---

创建：2026-03-12
版本：1.0
```

## Pool: validation_audit

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
