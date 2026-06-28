# Experiment Condition: multi_pool_sample_s08

One sampled skill from each pool, seed 8

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 8

## Skill Pools

### table_extraction
- bbox-row-column-parser

### data_cleaning
- data-analyst-cn

### validation_audit
- data-reconciliation-exceptions

### summary_reporting
- extraction-audit-summary

## Pool Samples

- table_extraction: bbox-row-column-parser
- data_cleaning: data-analyst-cn
- validation_audit: data-reconciliation-exceptions
- summary_reporting: extraction-audit-summary

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
- data-reconciliation-exceptions
- extraction-audit-summary

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

### data-reconciliation-exceptions

```markdown
---
name: data-reconciliation-exceptions
description: Reconciles data sources using stable identifiers (Pay Number, driving licence, driver card, and driver qualification card numbers), producing exception reports and “no silent failure” checks. Use when you need weekly matching with explicit reasons for non-joins and mismatches.
---

# Data quality & reconciliation with exception reporting and no silent failure

## PURPOSE
Reconciles data sources using stable identifiers (Pay Number, driving licence, driver card, and driver qualification card numbers), producing exception reports and “no silent failure” checks.

## WHEN TO USE
- TRIGGERS:
  - Reconcile these two data sources and produce an exceptions report with reasons.
  - Match names and payroll numbers across files and flag anything that does not join.
  - Build a ‘no silent failure’ check that stops the pipeline if counts do not match.
  - Create a weekly variance report for missing records, duplicates, and date gaps.
  - Design a data quality scorecard with thresholds and red flags.
- DO NOT USE WHEN…
  - You need open-ended fuzzy matching without acceptance criteria.
  - There are no stable identifiers in any source.

## INPUTS
- REQUIRED:
  - At least two datasets (CSV/XLSX) with Pay Number and/or driver document numbers.
  - Which fields must match (e.g., Name, expiry date).
- OPTIONAL:
  - Normalization rules (case, spaces, punctuation).
  - Thresholds for gates/scorecard (max % missing, etc.).
- EXAMPLES:
  - Payroll export + compliance register
  - Two weekly exports from different systems

## OUTPUTS
- Reconciliation plan (matching rules, normalization, join strategy).
- Exceptions report spec (CSV columns + reason codes) and variance checks.
- Optional artifacts: `assets/exceptions-report-template.csv` + `references/matching-rules.md`.
Success = every record is categorized (matched/missing/duplicate/mismatch/invalid) with an explicit reason; pipelines stop on anomalies.


## WORKFLOW
1. Confirm sources and key priority (Pay Number → Driver Card → Driving Licence → DQC).
2. Normalize columns:
   - trim spaces; standardize case; strip common punctuation for document numbers.
3. Validate keys:
   - flag blanks/invalid formats; identify duplicates per source.
4. Join:
   - exact join on Pay Number; then attempt secondary joins only for remaining unmatched items.
5. Produce exception categories with reasons:
   - Missing in A/B, Duplicate key, Field mismatch, Invalid key.
6. “No silent failure” gates:
   - counts within tolerance; unmatched rate below threshold; duplicate spikes flagged.
7. STOP AND ASK THE USER if:
   - columns are not mapped,
   - multiple competing IDs exist with no priority,
   - expected tolerances are unspecified.


## OUTPUT FORMAT
```csv
exception_type,reason,source_a_id,source_b_id,pay_number,name,field,source_a_value,source_b_value
```

Reason codes: `MISSING_IN_A`, `MISSING_IN_B`, `MISMATCH`, `DUPLICATE_KEY`, `INVALID_KEY`.


## SAFETY & EDGE CASES
- Read-only by default; don’t auto-edit source data. Route exceptions to review.
- Deterministic matching rules first; avoid fuzzy matching unless explicitly requested.
- Always produce an exceptions report; never drop unmatched rows.


## EXAMPLES
- Input: “Payroll vs compliance; match by Pay Number; flag name mismatch.”
  Output: join plan + mismatch reasons + exceptions report schema.

- Input: “Some rows have blank Pay Number.”
  Output: secondary key matching + invalid-key exceptions for truly unmatchable rows.
```

## Pool: summary_reporting

### extraction-audit-summary

```markdown
---
name: extraction-audit-summary
description: Use when reporting both table extraction results and audit limitations in a compact Markdown summary for benchmark artifacts.
---

# Extraction Audit Summary

Use this skill when the final summary needs to communicate what was extracted and how trustworthy the extraction is.

## Required Content

1. Briefly describe the extraction source type.
2. Summarize the number of normalized records from the generated metrics artifact.
3. Summarize the top record or best score per requested group when the task asks for it.
4. Include audit status, especially missing fields, ambiguous spans, non-numeric values, or excluded noise.
5. Keep limitations separate from results.

## Style

- Use Markdown bullets.
- Prefer precise, data-backed statements.
- Keep wording neutral.
- Avoid decorative charts unless explicitly requested.

## Guardrails

- Use only the current input, generated metrics, and generated audit.
- Do not include oracle-only values, verifier-only checks, or fixed expected answers.
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
