# Experiment Condition: multi_pool_sample_s05

One sampled skill from each pool, seed 5

## Condition Metadata

- condition_type: multi_pool_sample
- sample_seed: 5

## Skill Pools

### table_extraction
- file-converter

### data_cleaning
- data-analyst-cn

### validation_audit
- code-executor

### summary_reporting
- data2visualization

## Pool Samples

- table_extraction: file-converter
- data_cleaning: data-analyst-cn
- validation_audit: code-executor
- summary_reporting: data2visualization

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

- file-converter
- data-analyst-cn
- code-executor
- data2visualization

## Available Skill Documents

## Pool: table_extraction

### file-converter

```markdown
---
version: "2.1.0"
name: file-converter
description: "File format converter. Detect formats, convert between JSON/YAML/XML/CSV/Markdown, minify and prettify code. Commands: detect, json2yaml, yaml2json, csv2md."
author: BytesAgain
homepage: https://bytesagain.com
source: https://github.com/bytesagain/ai-skills
---

# file-converter

File format utility — pretty-print or minify JSON, encode/decode URLs, hex dump files, detect file types, and show file statistics.

## Commands

### `pretty-json`

```bash
scripts/script.sh pretty-json
```

### `minify-json`

```bash
scripts/script.sh minify-json
```

### `url-encode`

```bash
scripts/script.sh url-encode
```

### `url-decode`

```bash
scripts/script.sh url-decode
```

### `hex`

```bash
scripts/script.sh hex
```

### `detect`

```bash
scripts/script.sh detect
```

### `stats`

```bash
scripts/script.sh stats
```

### `help`

```bash
scripts/script.sh help
```

### `version`

```bash
scripts/script.sh version
```

## Examples

```bash
scripts/script.sh pretty-json
scripts/script.sh minify-json
scripts/script.sh help
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `FILE_CONVERTER_DIR` | No | Data directory (default: `~/.file-converter/`) |

## Data Storage

All data saved in `~/.file-converter/`. Runs entirely on your machine.

## Requirements

- bash 4.0+
- Standard Unix tools (grep, sed, awk)

---

*Powered by BytesAgain | bytesagain.com | hello@bytesagain.com*
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

- `OUTPUT_CELLS_CSV` -> `artifacts/table_cells.csv`: CSV columns row_id,col_id,row_span,col_span,is_header,text for every reconstructed non-empty table cell.
- `OUTPUT_METRICS_CSV` -> `artifacts/metrics.csv`: CSV columns method,dataset,accuracy,f1,notes with one row per metric observation.
- `OUTPUT_AUDIT_JSON` -> `artifacts/audit.json`: JSON with row_count, best_by_dataset, and issues.
- `SUMMARY_MD` -> `artifacts/summary.md`: Short Markdown summary grounded in the extracted metrics and audit.

Do not use GUI operations, screenshots, external APIs, web/network calls, or shell commands.
