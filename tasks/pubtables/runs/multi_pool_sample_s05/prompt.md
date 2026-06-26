# Experiment Condition: multi_pool_sample_s05

One sampled skill from each pool, seed 5

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 5

## Skill Pools

### table_extraction
- excel-xlsx

### data_cleaning
- data-analyst-cn

### validation_audit
- data-anomaly-detector

### summary_reporting
- generate-chart

## Pool Samples

- table_extraction: excel-xlsx
- data_cleaning: data-analyst-cn
- validation_audit: data-anomaly-detector
- summary_reporting: generate-chart

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

- excel-xlsx
- data-analyst-cn
- data-anomaly-detector
- generate-chart

## Available Skill Documents

## Pool: table_extraction

### excel-xlsx

```markdown
---
name: Excel / XLSX
slug: excel-xlsx
version: 1.0.2
homepage: https://clawic.com/skills/excel-xlsx
description: "Create, inspect, and edit Microsoft Excel workbooks and XLSX files with reliable formulas, dates, types, formatting, recalculation, and template preservation. Use when (1) the task is about Excel, `.xlsx`, `.xlsm`, `.xls`, `.csv`, or `.tsv`; (2) formulas, formatting, workbook structure, or compatibility matter; (3) the file must stay reliable after edits."
changelog: Tightened formula anchoring, recalculation, and model traceability after a stricter external spreadsheet audit.
metadata: {"clawdbot":{"emoji":"📗","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## When to Use

Use when the main artifact is a Microsoft Excel workbook or spreadsheet file, especially when formulas, dates, formatting, merged cells, workbook structure, or cross-platform behavior matter.

## Core Rules

### 1. Choose the workflow by job, not by habit

- Use `pandas` for analysis, reshaping, and CSV-like tasks.
- Use `openpyxl` when formulas, styles, sheets, comments, merged cells, or workbook preservation matter.
- Treat CSV as plain data exchange, not as an Excel feature-complete format.
- Reading values, preserving a live workbook, and building a model from scratch are different spreadsheet jobs.

### 2. Dates are serial numbers with legacy quirks

- Excel stores dates as serial numbers, not real date objects.
- The 1900 date system includes the false leap-day bug, and some workbooks use the 1904 system.
- Time is fractional day data, so formatting and conversion both matter.
- Date correctness is not enough if the number format still displays the wrong thing to the user.

### 3. Keep calculations in Excel when the workbook should stay live

- Write formulas into cells instead of hardcoding derived results from Python.
- Use references to assumption cells instead of magic numbers inside formulas.
- Cached formula values can be stale, so do not trust them blindly after edits.
- Check copied formulas for wrong ranges, wrong sheets, and silent off-by-one drift before delivery.
- Absolute and relative references are part of the logic, so copied formulas can be wrong even when they still "work".
- Test new formulas on a few representative cells before filling them across a whole block.
- Verify denominators, named ranges, and precedent cells before shipping formulas that depend on them.
- A workbook should ship with zero formula errors, not with known `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or circular-reference fallout left for the user to fix.
- For model-style work, document non-obvious hardcodes, assumptions, or source inputs in comments or nearby notes.

### 4. Protect data types before Excel mangles them

- Long identifiers, phone numbers, ZIP codes, and leading-zero values should usually be stored as text.
- Excel silently truncates numeric precision past 15 digits.
- Mixed text-number columns need explicit handling on read and on write.
- Scientific notation, auto-parsed dates, and stripped leading zeros are common corruption, not cosmetic issues.

### 5. Preserve workbook structure before changing content

- Existing templates override generic styling advice.
- Only the top-left cell of a merged range stores the value.
- Hidden rows, hidden columns, named ranges, and external references can still affect formulas and outputs.
- Shared strings, defined names, and sheet-level conventions can matter even when the visible cells look simple.
- Match styles for newly filled cells instead of quietly introducing a new visual system.
- If the workbook is a template, preserve sheet order, widths, freezes, filters, print settings, validations, and visual conventions unless the task explicitly changes them.
- Conditional formatting, filters, print areas, and data validation often carry business meaning even when users only mention the numbers.
- If there is no existing style guide and the file is a model, keep editable inputs visually distinguishable from formulas, but never override an established template to force a generic house style.

### 6. Recalculate and review before delivery

- Formula strings alone are not enough if the recipient needs current values.
- `openpyxl` preserves formulas but does not calculate them.
- Verify no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or circular-reference fallout remains.
- If layout matters, render or visually review the workbook before calling it finished.
- Be careful with read modes: opening a workbook for values only and then saving can flatten formulas into static values.
- If assumptions or hardcoded overrides must stay, make them obvious enough that the next editor can audit the workbook.

### 7. Scale the workflow to the file size

- Large workbooks can fail for boring reasons: memory spikes, padded empty rows, and slow full-sheet reads.
- Use streaming or chunked reads when the file is big enough that loading everything at once becomes fragile.
- Large-file workflows also need narrower reads, explicit dtypes, and sheet targeting to avoid accidental damage.

## Common Traps

- Type inference on read can leave numbers as text or convert IDs into damaged numeric values.
- Column indexing varies across tools, so off-by-one mistakes are common in generated formulas.
- Newlines in cells need wrapping to display correctly.
- External references break easily when source files move.
- Password protection in old Excel workflows is not serious security.
- `.xlsm` can contain macros, and `.xls` remains a tighter legacy format.
- Large files may need streaming reads or more careful memory handling.
- Google Sheets and LibreOffice can reinterpret dates, formulas, or styling differently from Excel.
- Dynamic array or newer Excel functions like `FILTER`, `XLOOKUP`, `SORT`, or `SEQUENCE` may fail or degrade in older viewers.
- A workbook can look fine while still carrying stale cached values from a prior recalculation.
- Saving the wrong workbook view can replace formulas with cached values and quietly destroy a live model.
- Copying formulas without checking relative references can push one bad range across an entire block.
- Hidden sheets, named ranges, validations, and merged areas often keep business logic that is invisible in a quick skim.
- A workbook can appear numerically correct while still failing because filters, conditional formats, print settings, or data validation were stripped.
- A workbook can be numerically correct and still fail visually because wrapped text, clipped labels, or narrow columns were never reviewed.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `csv` — Plain-text tabular import and export workflows.
- `data` — General data handling patterns before spreadsheet output.
- `data-analysis` — Higher-level analysis that can feed workbook deliverables.

## Feedback

- If useful: `clawhub star excel-xlsx`
- Stay updated: `clawhub sync`
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

### generate-chart

```markdown
---
name: data-visualization
description: AI智能数据可视化；支持多种图表类型（柱状图、折线图、饼图、散点图、直方图、箱线图、小提琴图、面积图、热力图、平行坐标图、旭日图等），根据数据特征自动分析并推荐最佳图表组合，生成精美交互式HTML仪表板
dependency:
  python:
    - plotly
    - pandas
    - numpy
---

# 数据可视化Skill

## 任务目标
- 本Skill用于：AI智能分析数据特征，自动推荐最佳图表组合，生成精美的交互式HTML可视化仪表板
- 能力包含：智能数据分析、多种图表类型支持（柱状图、折线图、饼图、散点图、直方图、箱线图、小提琴图、面积图、热力图、平行坐标图、旭日图等）、自动图表推荐、综合仪表板生成
- 触发条件：用户需要将数据可视化展示、不确定用什么图表类型、需要快速生成专业可视化效果

## 前置准备
- 依赖说明：
  ```
  plotly
  pandas
  numpy
  ```

## 操作步骤
1. **数据准备与分析**
   - 用户提供数据（可以是表格数据、CSV格式或结构化数据）
   - AI智能分析数据特征（数据类型、维度、关系、相关性等）
   - AI根据数据特征自动推荐最合适的图表类型组合

2. **图表生成**
   - 调用 `scripts/generate_chart.py` 生成交互式HTML可视化仪表板
   - AI自动选择最佳图表类型（支持10+种图表类型）
   - 所有图表统一展示在一个美观的页面中

3. **输出与优化**
   - 生成单个HTML文件，包含多种交互式图表
   - 支持鼠标悬停、缩放、平移等交互功能
   - 响应式设计，适配不同屏幕尺寸

## 资源索引
- 必要脚本：见 [scripts/generate_chart.py](scripts/generate_chart.py)(用途：根据数据生成指定类型的图表)
- 领域参考：见 [references/chart-types.md](references/chart-types.md)(何时读取：需要了解不同图表类型的适用场景和数据格式要求时)
- 领域参考：见 [references/data-format.md](references/data-format.md)(何时读取：需要了解输入数据的格式规范时)

## 注意事项
- AI会自动分析数据特征并推荐最佳图表组合
- 支持的图表类型：柱状图、折线图、饼图、散点图、直方图、箱线图、小提琴图、面积图、热力图、平行坐标图、旭日图等
- 图表类型选择基于数据特征（数值列数量、分类列数量、数据分布、相关性等）
- 图表支持缩放、平移等交互操作
- 生成最多15个图表，按优先级排序

## 使用示例

### 示例1：AI自动分析并生成仪表板
- 功能说明：AI分析数据特征，自动推荐并生成最佳图表组合
- 执行方式：AI智能分析+脚本自动生成
- 示例命令：python scripts/generate_chart.py --input sales.csv --output dashboard.html
- 输出内容：单个HTML文件，包含AI推荐的多种图表（柱状图、折线图、饼图、散点图、热力图等）

### 示例2：支持的图表类型
- 柱状图：类别对比、值计数分布
- 折线图：时间序列趋势分析
- 饼图：占比分析
- 散点图：变量相关性分析
- 直方图：数值分布分析
- 箱线图：数据分布差异对比
- 小提琴图：分布密度展示
- 面积图：趋势变化可视化
- 热力图：相关性矩阵展示
- 平行坐标图：多维度数据展示
- 旭日图：层级数据分析
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
