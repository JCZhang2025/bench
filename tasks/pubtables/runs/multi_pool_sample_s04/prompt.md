# Experiment Condition: multi_pool_sample_s04

One sampled skill from each pool, seed 4

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 4

## Skill Pools

### table_extraction
- markdown-converter

### data_cleaning
- data-analyst-cn

### validation_audit
- code-executor

### summary_reporting
- sql-report-generator

## Pool Samples

- table_extraction: markdown-converter
- data_cleaning: data-analyst-cn
- validation_audit: code-executor
- summary_reporting: sql-report-generator

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
- data-analyst-cn
- code-executor
- sql-report-generator

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

Provide exactly one deterministic random skill from each pool. Compare repeated sampled combinations against the all-candidates condition.

## Required Outputs

Save these artifacts:

- `OUTPUT_CELLS_CSV` -> `artifacts/table_cells.csv`: CSV columns row_id,col_id,row_span,col_span,is_header,text for every reconstructed non-empty table cell.
- `OUTPUT_METRICS_CSV` -> `artifacts/metrics.csv`: CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.
- `OUTPUT_AUDIT_JSON` -> `artifacts/audit.json`: JSON with row_count, best_by_dataset, and issues.
- `SUMMARY_MD` -> `artifacts/summary.md`: Short Markdown summary grounded in the extracted metrics and audit.

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
