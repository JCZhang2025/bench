# Experiment Condition: multi_pool_sample_s08

One sampled skill from each pool, seed 8

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 8

## Skill Pools

### document_processing
- office-document-specialist-suite

### validation_audit
- data-anomaly-detector

### summary_reporting
- sql-report-generator

## Pool Samples

- document_processing: office-document-specialist-suite
- validation_audit: data-anomaly-detector
- summary_reporting: sql-report-generator

## Task

Given Novels_Intro_Packet.docx, identify the first two body paragraphs, change only those two paragraphs to double line spacing, verify that all other text and formatting are unchanged, and generate a short Markdown formatting summary. No GUI, screenshot, external API, or cloud service should be used.

## Available Skills

- office-document-specialist-suite
- data-anomaly-detector
- sql-report-generator

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

### sql-report-generator

```markdown
# sql-report-generator - 生产级报告生成 Skill

## ⚠️ 使用前必读

本 Skill 需要 Python 依赖。**首次使用前必须安装依赖**：

```bash
skillhub_install install_skill sql-report-generator
```

工具会自动检测 Python3 环境、pip 可用性，并安装所有依赖。

### 依赖安装方式

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| **自动安装（推荐）** | `skillhub_install install_skill sql-report-generator` | 一键安装，自动处理 |
| **手动安装** | `pip install -r requirements.txt` | 熟悉 Python 环境的用户 |

### 无依赖使用（受限模式）

如果无法安装依赖，本 Skill 提供以下**降级能力**：

✅ **可用功能**：
- 报告结构设计建议
- 报告模板推荐（基于业务场景）
- 数据展示规范指导
- 报告写作建议

❌ **不可用功能**：
- 表格/矩阵/切片器生成
- HTML/PDF 报告导出
- AI 自动洞察生成
- 与 sql-master / sql-dataviz 联动

---

## ⚠️ 重要规则（必须遵守）

### 规则一：洞察与建议必须基于数据分析得出

> **🚨 严禁在真实数据场景下手动编写洞察和建议**

当接入真实数据时，**深度洞察**和**运营建议**必须通过数据分析得出结论：

```python
# ✅ 正确做法：使用自动分析
from sql_report_generator.scripts.ai_insights import quick_insights

# 分析数据并生成洞察
report = quick_insights(df, date_col="date", value_cols=["sales"])
insights = report.to_markdown()  # 统计分析得出的洞察
recommendations = report.get_recommendations()  # 统计分析得出的建议

# ❌ 错误做法：手动硬编码
# insights = "GMV 同比增长 15%，转化率提升..."  # 禁止！
```

**注意**：
- 输出时不要使用"AI洞察"、"AI分析"等词汇
- 应使用"洞察分析"、"统计分析"、"数据分析"等中性表述

**可接受的场景**：
- 演示/测试用的模拟数据
- 用户明确要求使用示例洞察

---

### 规则二：输出文件前必须仔细检查

> **🚨 每次生成看板文件后，必须先自行检查，确认无错误后再交付**

生成 HTML/PDF 文件后，**在输出前**检查清单：

| 检查项 | 说明 |
|--------|------|
| ✅ 图表是否正确渲染 | 无空白、无报错、无乱码 |
| ✅ 文字是否正常显示 | 中文、数字、符号正确，无 `{s:,.0f}` 等占位符 |
| ✅ 数据是否一致 | KPI、图表、表格数据匹配 |
| ✅ 交互是否正常 | hover、点击等功能 |
| ✅ 无工具栏/Logo | displayModeBar: false, displaylogo: false |
| ✅ 洞察与建议内容 | 无乱码、无占位符、内容完整 |

**常见错误及修复方法**：

| 错误类型 | 原因 | 修复 |
|---------|------|------|
| `{s:,.0f}` | f-string 嵌套错误 | 使用 `str()` 或预先格式化 |
| `\u00a5{...}` | Unicode 转义错误 | 使用 `\u00a5` 或 `¥` |
| `{{}}` 乱码 | 双大括号转义问题 | 确保 `{{` 在 f-string 外 |

---

## 🔗 Skill 协作关系

本 Skill 与 **sql-master**、**sql-dataviz** 组成完整的数据分析流水线：

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────────┐
│ sql-master  │ ──► │ sql-dataviz  │ ──► │ sql-report-generator   │
│  (数据层)   │     │  (可视化层)  │     │      (报告层)          │
└─────────────┘     └──────────────┘     └────────────────────────┘
      │                   │                        │
      ▼                   ▼                        ▼
   SQL 查询           图表生成                 HTML 报告
   数据获取           PNG/HTML                 AI 洞察
   格式转换           Dashboard                数据表格
```

### 协作模式

| 模式 | 组合 | 适用场景 |
|------|------|---------|
| **单独使用** | sql-report-generator | 已有图表/数据，仅需组织报告 |
| **可视化报告** | sql-dataviz + sql-report-generator | 图表 → 报告（无 SQL） |
| **数据报告** | sql-master + sql-report-generator | SQL 查询 → 报告（跳过可视化） |
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
├─ 仅报告组织 → sql-report-generator 单独使用
├─ 图表 + 报告（无 SQL）→ sql-dataviz + sql-report-generator
├─ SQL + 报告（跳过可视化）→ sql-master + sql-report-generator
└─ 完整分析报告 → sql-master + sql-dataviz + sql-report-generator ✅ 推荐
```

---

## 新增功能：AI 自动洞察生成模块

### `scripts/ai_insights.py`

纯统计分析（无需外部 AI API），自动从 DataFrame 生成结构化洞察和建议：

```python
from scripts.ai_insights import quick_insights, InsightGenerator

# 一键生成洞察
report = quick_insights(df, date_col="date", value_cols=["sales", "quantity"])
print(report.to_markdown())   # Markdown 格式
print(report.to_html())       # HTML 格式（可嵌入报告）
print(report.to_dict())       # JSON 格式

# 自定义分析
gen = InsightGenerator(df, date_col="date", value_cols=["sales"])
report = gen.generate_all()
# 包含：异常检测 / 趋势 / 相关性 / TOP N / 分布 / 季节性 / 对比
# 自动生成运营建议
```

**7 种洞察类型**：异常检测（Z-score + IQR + 环比突变）、趋势检测（线性回归）、
相关性检测（Pearson）、TOP N 分析（帕累托 80/20）、分布检测（偏度/峰度）、
季节性检测、对比分析（分组差异）

**3 种输出格式**：Markdown / HTML / JSON

## 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install pandas numpy matplotlib jinja2 scipy
```

## 概述

将 SQL 查询结果和可视化图表组织成**生产级报告**。支持表格、矩阵、切片器、交互导航、分页报表等 **8 种交互组件**，可导出为 HTML、PDF、JSON 等多种格式。

与 **sql-master** 和 **sql-dataviz** 无缝协作，形成完整的数据分析流程。

## 核心能力

### 1️⃣ 表格与矩阵（2种）

| 组件 | 场景 | 特性 |
|------|------|------|
| **表格** | 明细数据展示 | 支持排序、筛选、条件格式 |
| **矩阵** | 跨维度分析 | 支持多级钻取、热力图 |

### 2️⃣ 交互与筛选（3种）

| 组件 | 场景 | 特性 |
|------|------|------|
| **切片器** | 多维度筛选 | 按钮/列表/日期范围样式 |
| **按钮导航** | 报表页面跳转 | 支持书签、URL 跳转 |
| **图像视觉对象** | 品牌 logo、产品图片 | 静态/动态图片嵌入 |

### 3️⃣ 报告组织（3种）

| 组件 | 场景 | 特性 |
|------|------|------|
| **文本框与形状** | 报表标题、说明描述 | 支持动态绑定数据 |
| **分页报表** | 像素级格式化 | 打印-ready、多页面 |
| **报告生成器** | 自动组织内容 | 支持 HTML/PDF/JSON 导出 |

## 快速开始

### 基础用法

```python
from sql_report_generator.scripts.interactive_components import (
    ReportBuilder, TableChart, MatrixChart, SlicerComponent
)

# 1. 创建报告
report = ReportBuilder()
report.set_metadata(
    title='月度业绩报告',
    author='数据分析团队',
    date='2026-03-26'
)

# 2. 添加内容
report.add_title('月度业绩报告', level=1)
report.add_text('本报告汇总了本月的关键业绩指标。')

# 3. 添加表格
table = TableChart()
table_b64 = table.create({
    'columns': ['订单ID', '客户', '金额', '日期'],
    'rows': [
        ['ORD001', '张三', '¥1,000', '2026-03-26'],
        ['ORD002', '李四', '¥2,500', '2026-03-25']
    ],
    'title': '订单列表'
})
report.add_table('订单数据', table_b64)

# 4. 导出报告
report.export_html('report.html')
```

### 与 sql-dataviz 协作

```python
from sql_dataviz.charts import ChartFactory
from sql_report_generator.scripts.interactive_components import ReportBuilder

# 1. 生成图表
factory = ChartFactory()
factory.set_theme('powerbi')

chart1 = factory.create_line({
    'categories': ['Q1', 'Q2', 'Q3', 'Q4'],
    'series': [{'name': '销售额', 'data': [100, 150, 120, 200]}]
})

chart2 = factory.create_pie({
    'labels': ['北京', '上海', '广州'],
    'values': [35, 30, 35]
})

# 2. 组织成报告
report = ReportBuilder()
report.set_metadata(title='季度分析报告')
report.add_title('销售趋势', level=2)
report.add_chart('销售额趋势', chart1, '本季度销售额稳步增长')
report.add_chart('地区占比', chart2, '北京和广州贡献最大')

# 3. 导出
report.export_html('analysis.html')
```

### 完整流程：sql-master → sql-dataviz → sql-report-generator

```python
from sql_master import SQLMaster
from sql_dataviz.charts import ChartFactory
from sql_report_generator.scripts.interactive_components import ReportBuilder

# 1. 查询数据
sql = SQLMaster()
sales_data = sql.execute_query("""
    SELECT quarter, region, SUM(sales) as total
    FROM orders
    GROUP BY quarter, region
""")

# 2. 生成可视化
factory = ChartFactory()
factory.set_theme('powerbi')

# 按季度对比
chart = factory.create_clustered_column({
    'categories': ['Q1', 'Q2', 'Q3', 'Q4'],
    'series': [
        {'name': '北京', 'data': [100, 150, 120, 200]},
        {'name': '上海', 'data': [80, 120, 100, 180]},
        {'name': '广州', 'data': [60, 90, 80, 140]}
    ]
})

# 3. 组织报告
report = ReportBuilder()
report.set_metadata(
    title='年度销售报告',
    author='销售部',
    date='2026-03-26'
)

report.add_title('年度销售报告', level=1)
report.add_text('本报告总结了全年的销售业绩和地区分析。')
report.add_chart('季度销售对比', chart)

# 4. 导出
report.export_html('annual_sales.html')
```



## 文件结构

```
sql-report-generator/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── interactive_components.py     # 表格、矩阵、切片器、导航、报告生成
│   ├── generate_report.py            # 报告生成主程序
│   ├── dashboard_templates.py       # 看板模板库（17个行业，36个模板）
│   ├── generate_templates.py         # 模板生成脚本（生成 .md 预设模板）
│   ├── ai_insights.py               # AI 洞察生成
│   ├── dashboard_tooltips.py         # 看板提示配置
│   └── demo.py                       # 完整演示
├── templates/
│   ├── executive-summary.md          # 执行摘要模板
│   ├── monthly-report.md             # 月报模板
│   ├── sales-dashboard.md            # 销售仪表盘模板
│   └── ...（90+ 预设模板，自动从 dashboard_templates.py 生成）
└── references/
    ├── chart-guidelines.md           # 图表选型指南
    ├── insight-patterns.md           # 洞察模式库
    └── templates-index.md            # 模板索引
```

### 预设模板说明

`templates/` 目录下的 `.md` 预设模板文件由 `scripts/generate_templates.py` 自动生成，源自 `dashboard_templates.py` 中的模板定义。

**生成/更新预设模板：**

```bash
# 生成所有预设模板
python scripts/generate_templates.py

# 预览将要执行的操作（不生成文件）
python scripts/generate_templates.py --dry-run

# 仅生成指定行业的模板
python scripts/generate_templates.py --industry 医疗

# 仅生成指定模板
python scripts/generate_templates.py --template-id ecommerce_overview
```

**使用预设模板：**

```python
from sql_report_generator.scripts.dashboard_templates import DashboardGenerator

# 创建生成器
generator = DashboardGenerator()

# 获取预设模板
template = generator.get_template("电商", "ecommerce_overview")

# 列出所有可用模板
all_templates = generator.list_all_templates()
for industry, templates in all_templates.items():
    print(f"{industry}: {templates}")

# 生成模板 Markdown 文档
md = generator.generate_dashboard_markdown(template)
print(md)
```

**支持的行业和模板数量：**

| 行业 | 模板数量 |
|------|---------|
| 电商 | 3 |
| 互联网/APP/游戏 | 3 |
| 金融 | 3 |
| 制造 | 2 |
| 零售 | 2 |
| HR | 2 |
| 财务 | 2 |
| 文娱 | 5 |
| 医疗健康 | 2 |
| 教育 | 2 |
| 餐饮连锁 | 2 |
| 物流供应链 | 1 |
| 能源 | 2 |
| 政务 | 2 |
| 汽车 | 1 |
| 房地产 | 1 |
| 客服运营 | 1 |
| **总计** | **17个行业，36个模板** |

## 组件详解

### 表格（Table）

```python
from sql_report_generator.scripts.interactive_components import TableChart

table = TableChart(width=1200, height=600)
table_b64 = table.create({
    'columns': ['订单ID', '客户', '金额', '日期', '状态'],
    'rows': [
        ['ORD001', '张三', '¥1,000', '2026-03-26', '已完成'],
        ['ORD002', '李四', '¥2,500', '2026-03-25', '进行中'],
        ['ORD003', '王五', '¥1,800', '2026-03-24', '已完成']
    ],
    'title': '订单列表'
})
```

**特性：**
- ✓ 交替行颜色，易于阅读
- ✓ 支持任意列数
- ✓ 自动调整列宽
- ✓ 蓝色头部，专业风格

### 矩阵（Matrix）

```python
from sql_report_generator.scripts.interactive_components import MatrixChart

matrix = MatrixChart(width=1200, height=600)
matrix_b64 = matrix.create({
    'rows': ['北京', '上海', '广州', '深圳'],
    'columns': ['Q1', 'Q2', 'Q3', 'Q4'],
    'values': [
        [100, 150, 120, 200],
        [80, 120, 100, 180],
        [60, 90, 80, 140],
        [70, 110, 95, 160]
    ],
    'title': '地区季度销售额'
})
```

**特性：**
- ✓ 热力图配色（红黄绿）
- ✓ 数值标签
- ✓ 支持多维度分析
- ✓ 颜色条显示数值范围

### 切片器（Slicer）

```python
from sql_report_generator.scripts.interactive_components import SlicerComponent

slicer = SlicerComponent(width=300, height=400)
slicer_b64 = slicer.create({
    'title': '时间筛选',
    'type': 'date',
    'options': ['2026-01', '2026-02', '2026-03'],
    'selected': '2026-03'
})
```

**特性：**
- ✓ 复选框样式
- ✓ 支持多选
- ✓ 选中状态高亮
- ✓ 紧凑布局

### 按钮导航（Button Navigator）

```python
from sql_report_generator.scripts.interactive_components import ButtonNavigator

navigator = ButtonNavigator(width=1200, height=100)
nav_b64 = navigator.create({
    'buttons': [
        {'label': '首页', 'active': True},
        {'label': '销售分析', 'active': False},
        {'label': '财务报表', 'active': False},
        {'label': '导出', 'active': False}
    ]
})
```

**特性：**
- ✓ 活跃状态高亮
- ✓ 圆角按钮
- ✓ 支持任意数量按钮
- ✓ 响应式布局

### 报告生成器（ReportBuilder）

```python
from sql_report_generator.scripts.interactive_components import ReportBuilder

report = ReportBuilder()

# 设置元数据
report.set_metadata(
    title='月度业绩报告',
    author='数据分析团队',
    date='2026-03-26'
)

# 添加内容
report.add_title('月度业绩报告', level=1)
report.add_text('本报告汇总了本月的关键业绩指标。')
report.add_chart('销售趋势', chart_b64, '销售额环比增长 15%')
report.add_table('订单列表', table_b64)
report.add_slicer(slicer_b64)
report.add_page_break()

# 导出
report.export_html('report.html')
report.export_json('report.json')
```

## 导出格式

### HTML（推荐）

```python
report.export_html('report.html')
```

**优点：**
- ✓ 支持所有浏览器
- ✓ 响应式设计
- ✓ 支持打印
- ✓ 文件小

### JSON（API 集成）

```python
report.export_json('report.json')
```

**用途：**
- ✓ 与其他系统集成
- ✓ 数据交换
- ✓ 版本控制
- ✓ 自定义渲染

### PDF（可选）

```python
# 需要安装: pip install reportlab pypdf2
report.export_pdf('report.pdf')
```

## 预设模板

sql-report-generator 提供 30+ 预设模板，覆盖常见场景：

### 业务类
- `sales-dashboard.md` - 销售仪表盘
- `channel-analysis.md` - 渠道分析
- `customer-cohort.md` - 客户分群
- `product-metrics.md` - 产品指标

### 财务类
- `financial-ratio.md` - 财务比率
- `cash-flow.md` - 现金流
- `balance-sheet.md` - 资产负债表
- `income-statement.md` - 利润表

### 运营类
- `kpi-dashboard.md` - KPI 仪表盘
- `project-status.md` - 项目状态
- `incident-report.md` - 事件报告
- `system-health.md` - 系统健康度

### 人力类
- `hr-overview.md` - HR 概览
- `recruitment-report.md` - 招聘报告
- `performance-review.md` - 绩效评估

### 技术类
- `tech-debt.md` - 技术债
- `sprint-report.md` - Sprint 报告
- `system-health.md` - 系统健康

## 最佳实践

### 1. 报告结构

```python
report = ReportBuilder()

# 1. 标题与摘要
report.add_title('月度业绩报告', level=1)
report.add_text('本报告总结了本月的关键指标和分析洞察。')

# 2. 关键指标
report.add_title('关键指标', level=2)
report.add_chart('KPI 卡片', kpi_chart)

# 3. 详细分析
report.add_title('详细分析', level=2)
report.add_chart('销售趋势', trend_chart)
report.add_chart('地区对比', comparison_chart)

# 4. 数据表格
report.add_title('明细数据', level=2)
report.add_table('订单列表', table_chart)

# 5. 附录
report.add_page_break()
report.add_title('附录', level=2)
report.add_text('数据来源：销售系统')
```

### 2. 数据预处理

```python
import pandas as pd

# 清理数据
df = pd.read_sql(query, conn)
df = df.dropna()
df = df[df['value'] > 0]

# 聚合数据
df_agg = df.groupby('category').agg({
    'value': 'sum',
    'count': 'count'
}).reset_index()

# 排序
df_agg = df_agg.sort_values('value', ascending=False)

# 转换为表格格式
table_data = {
    'columns': df_agg.columns.tolist(),
    'rows': df_agg.values.tolist()
}
```

### 3. 缓存机制

```python
import hashlib
import json
import os

def get_report_cached(report_config, cache_dir='./cache'):
    # 生成缓存键
    key = hashlib.md5(json.dumps(report_config).encode()).hexdigest()
    cache_file = f"{cache_dir}/report_{key}.html"
    
    # 检查缓存
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return f.read()
    
    # 生成新报告
    report = ReportBuilder()
    # ... 添加内容 ...
    html = report._generate_html()
    
    # 保存缓存
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'w') as f:
        f.write(html)
    
    return html
```

## 常见问题

### Q: 如何自定义 HTML 样式？

A: 修改 `_generate_html()` 方法中的 CSS：

```python
class CustomReportBuilder(ReportBuilder):
    def _generate_html(self):
        html = super()._generate_html()
        # 自定义 CSS
        custom_css = """
        .container {
            max-width: 1400px;
            background: linear-gradient(to right, #f5f5f5, white);
        }
        """
        return html.replace('</style>', custom_css + '</style>')
```

### Q: 如何添加页眉和页脚？

A: 在 HTML 中添加固定定位元素：

```python
def add_header(self, text):
    self.sections.insert(0, {
        'type': 'header',
        'content': text
    })

def add_footer(self, text):
    self.sections.append({
        'type': 'footer',
        'content': text
    })
```

### Q: 支持多语言吗？

A: 支持。通过配置文件或参数传递：

```python
report = ReportBuilder(language='zh-CN')
# 或
report.set_language('en-US')
```

## 性能指标

| 操作 | 耗时 | 文件大小 |
|------|------|--------|
| 生成 5 图表报告 | ~500ms | ~2MB |
| 生成 10 图表报告 | ~1s | ~4MB |
| 生成 20 图表报告 | ~2s | ~8MB |
| 导出 PDF（10 图） | ~3s | ~5MB |

## 许可证

MIT License - 生产级可商用

## 更新日志

- **v1.0.0** (2026-03-26) - 初始版本，支持表格、矩阵、切片器、导航、报告生成
- **v1.1.0** (计划) - 支持 PDF 导出、自定义模板、多语言
- **v2.0.0** (计划) - 支持交互式 HTML、实时数据更新、云端存储

## 支持与反馈

- 📧 Email: support@example.com
- 💬 Discord: https://discord.gg/example
- 🐛 Issues: https://github.com/example/sql-report-generator/issues
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
