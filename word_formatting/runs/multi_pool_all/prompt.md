# Experiment Condition: multi_pool_all

All candidates from every skill pool

## Condition Metadata

- condition_type: multi_pool_all
- sample_seed: 

## Skill Pools

### document_processing
- word-docx
- office-document-specialist-suite
- file-converter
- all-to-markdown
- markdown-converter

### validation_audit
- code-executor
- data-reconciliation-exceptions
- data-anomaly-detector
- data-analysis
- user-analysis-matrix

### summary_reporting
- typora-visual-architect
- generate-report123
- markdown-converter
- sql-report-generator
- data2visualization

## Pool Samples

- none

## Task

Given Novels_Intro_Packet.docx, identify the first two body paragraphs, change only those two paragraphs to double line spacing, verify that all other text and formatting are unchanged, and generate a short Markdown formatting summary. No GUI, screenshot, external API, or cloud service should be used.

## Available Skills

- word-docx
- office-document-specialist-suite
- file-converter
- all-to-markdown
- markdown-converter
- code-executor
- data-reconciliation-exceptions
- data-anomaly-detector
- data-analysis
- user-analysis-matrix
- typora-visual-architect
- generate-report123
- sql-report-generator
- data2visualization

## Available Skill Documents

## Pool: document_processing

### word-docx

```markdown
---
name: Word / DOCX
slug: word-docx
version: 1.0.2
homepage: https://clawic.com/skills/word-docx
description: "Create, inspect, and edit Microsoft Word documents and DOCX files with reliable styles, numbering, tracked changes, tables, sections, and compatibility checks. Use when (1) the task is about Word or `.docx`; (2) the file includes tracked changes, comments, fields, tables, templates, or page layout constraints; (3) the document must survive round-trip editing without formatting drift."
changelog: Tightened the skill around fragile review workflows, reference stability, and layout drift after a stricter external audit.
metadata: {"clawdbot":{"emoji":"📘","os":["linux","darwin","win32"]}}
---

## When to Use

Use when the main artifact is a Microsoft Word document or `.docx` file, especially when tracked changes, comments, headers, numbering, fields, tables, templates, or compatibility matter.

## Core Rules

### 1. Treat DOCX as OOXML, not plain text

- A `.docx` file is a ZIP of XML parts, so structure matters as much as visible text.
- The critical parts are usually `word/document.xml`, `styles.xml`, `numbering.xml`, headers, footers, and relationship files.
- Text may be split across multiple runs; never assume one word or sentence lives in one XML node.
- Use different workflows on purpose: structured extraction for quick reading, style-driven generation for new files, and OOXML-aware editing for fragile existing documents.
- If the job is mainly reading, extracting, or reviewing, prefer a structure-preserving read path before touching OOXML.
- For deep edits, inspect the package layout instead of relying only on rendered output.
- Reading, generating, and preserving an existing reviewed document are different jobs even when the format is the same.
- Legacy `.doc` inputs usually need conversion before you can trust modern `.docx` assumptions.

### 2. Preserve styles and direct formatting deliberately

- Prefer named styles over direct formatting so the document stays editable.
- Styles layer: paragraph styles, character styles, and direct formatting do not behave the same.
- Removing direct formatting is often safer than stacking more inline formatting on top.
- When editing an existing file, extend the current style system instead of inventing a parallel one.
- Copying content between documents can silently import foreign styles, theme settings, and numbering definitions.

### 3. Lists and numbering are their own system

- Bullets and numbering belong to Word's numbering definitions, not pasted Unicode characters.
- `abstractNum`, `num`, and paragraph numbering properties all matter, so restart behavior is rarely "visual only".
- Indentation and numbering are related but not identical; a list can have broken numbering even if the indent looks right.
- A list that looks correct in one editor can restart, flatten, or renumber itself later if the underlying numbering state is wrong.

### 4. Page layout lives in sections

- Margins, orientation, headers, footers, and page numbering are section-level behavior.
- First-page and odd/even headers can differ inside the same document, so one header fix may not fix the document.
- Set page size explicitly because A4 and US Letter defaults change pagination and table widths.
- Use section breaks for layout changes; manual spacing and stray page breaks usually create drift.
- Header and footer media use part-specific relationships, so copied IDs often break images or links.
- Tables, page breaks, and headers often drift together, so treat layout fixes as document-wide, not local cosmetic edits.
- Table geometry depends on page width, margins, and fixed widths, so "close enough" table edits often break later in Google Docs or LibreOffice.

### 5. Track changes, comments, and fields need precise edits

- Visible text is not the full document when tracked changes are enabled.
- Insertions, deletions, and comments carry metadata that can survive careless edits.
- Deleted text may still exist in the XML even when it no longer appears on screen.
- Comment anchors and review ranges can break if edits move text without preserving the surrounding structure.
- Comment markers and review wrappers do not behave like inline formatting, so moving text carelessly can orphan or misplace them.
- Comments, footnotes, bookmarks, and linked media may live in separate parts, not only in the main document body.
- Tables of contents, page numbers, dates, cross-references, and mail merge placeholders are fields.
- Edit the field source carefully and expect cached display values to lag until refresh.
- Hyperlinks, bookmarks, and references can break if IDs or relationships stop matching.
- Bookmarks, footnotes, comment ranges, and cross-references depend on stable anchors even when the visible text seems untouched.
- A document can look correct while still containing stale field output that refreshes later into something different.
- For review workflows, make minimal replacements instead of rewriting whole paragraphs.
- In tracked-change workflows, only the changed span should look changed; broad rewrites create noisy reviews and can destroy the original formatting context.
- For legal, academic, or business review documents, default to review-style edits over wholesale paragraph rewrites unless the user explicitly wants a rewrite.

### 6. Verify round-trip compatibility before delivery

- Complex documents can shift between Word, LibreOffice, Google Docs, and conversion tools.
- Tables, headers, embedded fonts, and copied styles are common sources of layout drift.
- Treat `.docm` as macro-bearing and higher risk; treat `.doc` as legacy input that may need conversion first.
- When layout matters, explicit table widths are safer than auto-fit or percentage-style behavior that different editors reinterpret.
- A document that passes a text check can still fail on pagination, table widths, or reference refresh after the recipient opens it.

## Common Traps

- Copy-paste can import unwanted styles and numbering definitions.
- Header or footer images use part-specific relationships, so reusing IDs blindly breaks them.
- Empty paragraphs used as spacing make templates fragile; spacing belongs in paragraph settings.
- A clean-looking export can still hide unresolved revisions, comments, or stale field values.
- Restarting lists "by eye" usually fails because numbering state lives outside the paragraph text.
- One visible phrase can be split across several runs, bookmarks, revision tags, or field boundaries.
- Replacing a whole paragraph to change one clause often breaks review quality, bookmarks, comments, or nearby inline formatting.
- Deleting all visible text from a paragraph or list item can still leave behind an empty paragraph mark, empty bullet, or unstable numbering.
- Table auto-fit and percentage-like width behavior can look acceptable in Word and still drift in Google Docs or LibreOffice.
- LibreOffice and Google Docs can shift complex tables, section behavior, and embedded fonts even when Word looks perfect.
- Compatibility mode can silently cap newer features or change pagination behavior.
- A single change in page size or margin defaults can ripple through tables, headers, TOC, and cross-references.
- A revision workflow can look accepted on screen while leftover metadata, comments, or field caches still make the file unstable later.
- TOC entries, footnotes, and cross-references can look correct until the recipient updates fields and exposes broken anchors.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `documents` — General document handling and format conversion.
- `brief` — Concise business writing and structured summaries.
- `article` — Long-form drafting and editorial structure.

## Feedback

- If useful: `clawhub star word-docx`
- Stay updated: `clawhub sync`
```

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

### data-analysis

```markdown
---
name: Data Analysis
slug: data-analysis
version: 1.0.2
homepage: https://clawic.com/skills/data-analysis
description: "Data analysis and visualization. Query databases, generate reports, automate spreadsheets, and turn raw data into clear, actionable insights. Use when (1) you need to analyze, visualize, or explain data; (2) the user wants reports, dashboards, or metrics turned into a decision; (3) the work involves SQL, Python, spreadsheets, BI tools, or notebooks; (4) you need to compare segments, cohorts, funnels, experiments, or time periods; (5) the user explicitly installs or references the skill for the current task."
changelog: Added metric contracts, chart guidance, and decision brief templates for more reliable analysis.
metadata: {"clawdbot":{"emoji":"D","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## When to Use

Use this skill when the user needs to analyze, explain, or visualize data from SQL, spreadsheets, notebooks, dashboards, exports, or ad hoc tables.

Use it for KPI debugging, experiment readouts, funnel or cohort analysis, anomaly reviews, executive reporting, and quality checks on metrics or query logic.

Prefer this skill over generic coding or spreadsheet help when the hard part is analytical judgment: metric definition, comparison design, interpretation, or recommendation.

User asks about: analyzing data, finding patterns, understanding metrics, testing hypotheses, cohort analysis, A/B testing, churn analysis, or statistical significance.

## Core Principle

Analysis without a decision is just arithmetic. Always clarify: **What would change if this analysis shows X vs Y?**

## Methodology First

Before touching data:
1. **What decision** is this analysis supporting?
2. **What would change your mind?** (the real question)
3. **What data do you actually have** vs what you wish you had?
4. **What timeframe** is relevant?

## Statistical Rigor Checklist

- [ ] Sample size sufficient? (small N = wide confidence intervals)
- [ ] Comparison groups fair? (same time period, similar conditions)
- [ ] Multiple comparisons? (20 tests = 1 "significant" by chance)
- [ ] Effect size meaningful? (statistically significant != practically important)
- [ ] Uncertainty quantified? ("12-18% lift" not just "15% lift")

## Architecture

This skill does not require local folders, persistent memory, or setup state.

Use the included reference files as lightweight guides:
- `metric-contracts.md` for KPI definitions and caveats
- `chart-selection.md` for visual choice and chart anti-patterns
- `decision-briefs.md` for stakeholder-facing outputs
- `pitfalls.md` and `techniques.md` for analytical rigor and method choice

## Quick Reference

Load only the smallest relevant file to keep context focused.

| Topic | File |
|-------|------|
| Metric definition contracts | `metric-contracts.md` |
| Visual selection and chart anti-patterns | `chart-selection.md` |
| Decision-ready output formats | `decision-briefs.md` |
| Failure modes to catch early | `pitfalls.md` |
| Method selection by question type | `techniques.md` |

## Core Rules

### 1. Start from the decision, not the dataset
- Identify the decision owner, the question that could change a decision, and the deadline before doing analysis.
- If no decision would change, reframe the request before computing anything.

### 2. Lock the metric contract before calculating
- Define entity, grain, numerator, denominator, time window, timezone, filters, exclusions, and source of truth.
- If any of those are ambiguous, state the ambiguity explicitly before presenting results.

### 3. Separate extraction, transformation, and interpretation
- Keep query logic, cleanup assumptions, and analytical conclusions distinguishable.
- Never hide business assumptions inside SQL, formulas, or notebook code without naming them in the write-up.

### 4. Choose visuals to answer a question
- Select charts based on the analytical question: trend, comparison, distribution, relationship, composition, funnel, or cohort retention.
- Do not add charts that make the deck look fuller but do not change the decision.

### 5. Brief every result in decision format
- Every output should include the answer, evidence, confidence, caveats, and recommended next action.
- If the output is going to a stakeholder, translate the method into business implications instead of leading with technical detail.

### 6. Stress-test claims before recommending action
- Segment by obvious confounders, compare the right baseline, quantify uncertainty, and check sensitivity to exclusions or time windows.
- Strong-looking numbers without robustness checks are not decision-ready.

### 7. Escalate when the data cannot support the claim
- Block or downgrade conclusions when sample size is weak, the source is unreliable, definitions drifted, or confounding is unresolved.
- It is better to say "unknown yet" than to produce false confidence.

## Common Traps

- Reusing a KPI name after changing numerator, denominator, or exclusions -> trend comparisons become invalid.
- Comparing daily, weekly, and monthly grains in one chart -> movement looks real but is mostly aggregation noise.
- Showing percentages without underlying counts -> leadership overreacts to tiny denominators.
- Using a pretty chart instead of the right chart -> the output looks polished but hides the actual decision signal.
- Hunting for interesting cuts after seeing the result -> narrative follows chance instead of evidence.
- Shipping automated reports without metric owners or caveats -> bad numbers spread faster than they can be corrected.
- Treating observational patterns as causal proof -> action plans get built on correlation alone.

## Approach Selection

| Question type | Approach | Key output |
|---------------|----------|------------|
| "Is X different from Y?" | Hypothesis test | p-value + effect size + CI |
| "What predicts Z?" | Regression/correlation | Coefficients + R² + residual check |
| "How do users behave over time?" | Cohort analysis | Retention curves by cohort |
| "Are these groups different?" | Segmentation | Profiles + statistical comparison |
| "What's unusual?" | Anomaly detection | Flagged points + context |

For technique details and when to use each, see `techniques.md`.

## Output Standards

1. **Lead with the insight**, not the methodology
2. **Quantify uncertainty** - ranges, not point estimates
3. **State limitations** - what this analysis can't tell you
4. **Recommend next steps** - what would strengthen the conclusion

## Red Flags to Escalate

- User wants to "prove" a predetermined conclusion
- Sample size too small for reliable inference
- Data quality issues that invalidate analysis
- Confounders that can't be controlled for

## External Endpoints

This skill makes no external network requests.

| Endpoint | Data Sent | Purpose |
|----------|-----------|---------|
| None | None | N/A |

No data is sent externally.

## Security & Privacy

Data that leaves your machine:
- Nothing by default.

Data that stays local:
- Nothing by default.

This skill does NOT:
- Access undeclared external endpoints.
- Store credentials or raw exports in hidden local memory files.
- Create or depend on local folder systems for persistence.
- Create automations or background jobs without explicit user confirmation.
- Rewrite its own instruction source files.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `sql` - query design and review for reliable data extraction.
- `csv` - cleanup and normalization for tabular inputs before analysis.
- `dashboard` - implementation patterns for KPI visualization layers.
- `report` - structured stakeholder-facing deliverables after analysis.
- `business-intelligence` - KPI systems and operating cadence beyond one-off analysis.

## Feedback

- If useful: `clawhub star data-analysis`
- Stay updated: `clawhub sync`
```

### user-analysis-matrix

```markdown
---
name: user-analysis-matrix
description: "用户使用数据可视化分析全流程，从原始数据清洗、多维度聚合到生成单文件 HTML 可视化报告。支持按身份（部门/产品线/角色/大区/用户角色/层级）、时间（周/月/季度）、能力（具体功能/场景）三个维度做交叉分析。触发词：帮我做用户分析矩阵、用户活跃分析、大区活跃分析、产品线活跃分析、活跃分析、用户分析、生成数据看板。当用户需要将用户使用行为数据生成可视化 HTML 报告时触发此技能。流程为 Python 清洗聚合 + Chart.js 单文件 HTML 可视化，产物可直接浏览器打开。"
agent_created: true
allowed_tools:
  - Bash
  - Read
  - Write
  - Edit
---

# 用户使用数据可视化分析

## 概述

将用户使用行为原始数据（Excel/CSV），经过清洗、聚合、可视化三个阶段，产出单文件 HTML 报告。
报告包含：核心指标卡、多维度交叉筛选器、折线趋势图、能力排行图、分组对比表格。
交付物为自包含 HTML，可直接通过浏览器打开或发送给同事，无需服务器。

## 前置条件

确认用户提供以下信息：

1. **数据源文件路径** — 使用明细 Excel/CSV（必须含：用户标识列、时间列、各能力使用次数列）
2. **用户信息表路径**（可选）— 含身份维度字段（部门、产品线、角色、大区、用户角色、层级等）
3. **离职名单路径**（可选）— 用于排除已离职人员
4. **分析维度**（可选）— 默认按 部门+角色+产品线+大区+用户角色+层级，用户可按需调整
5. **时间范围**（可选）— 默认全部数据，用户可指定财周/月份范围

## 执行流程

### 第一步：数据加载与清洗

调用 `scripts/load_and_clean.py`：

```bash
python scripts/load_and_clean.py --input <使用明细.xlsx> --users <用户信息.xlsx> --resigned <离职名单.csv> --output data/cleaned_data.json
```

清洗规则：
- 排除离职名单中的用户
- 将能力使用次数列转为数值，空值填充为 0
- 日期列解析为 datetime，计算财周归属
- 去除完全重复行
- 活跃定义：该周任意能力使用次数 > 0

输出格式（JSON）：
```json
{
  "columns": ["姓名", "角色", "用户角色", "财周", "能力一使用次数", ...],
  "data": [[...], ...],
  "meta": {"total_rows": 12000, "cleaned_rows": 11500, "removed_resigned": 500}
}
```

### 第二步：多维度聚合

调用 `scripts/aggregate_data.py`：

```bash
python scripts/aggregate_data.py --input data/cleaned_data.json --output data/aggregated.json --dimensions "部门,角色,产品线,大区,用户角色,层级"
```

聚合产出三个结构：

1. **identity（身份维度）**：按各身份字段 groupby，计算用户数、活跃用户数、活跃率、人均能力数、总使用次数
2. **timeline（时间维度）**：按财周聚合，计算每周活跃用户数、活跃率，支持与上一周期对比
3. **capability（能力维度）**：按能力名称聚合，计算使用用户数、使用频次、渗透率（使用人数/总人数）

### 第三步：生成 HTML 报告

调用 `scripts/sync_to_html.py`：

```bash
python scripts/sync_to_html.py --data data/aggregated.json --template assets/report_template.html --output output/report.html
```

实现方式：
- 读取 `assets/report_template.html` 模板
- 找到 `const DATA = __DATA_PLACEHOLDER__;` 占位符
- 用聚合结果 JSON 替换占位符
- 写出完整 HTML 文件

### 第四步：验证与交付

生成后执行验证：
- 用浏览器预览 HTML 确认渲染正常
- 检查核心指标数字与原始数据一致（总数、活跃率）
- 确认筛选器交互正常（身份筛选 → 图表联动）
- 将输出文件路径告知用户

## HTML 报告设计规范

### 页面结构（从上到下）

1. **标题栏**：报告名称 + 数据更新时间 + 数据范围说明
2. **筛选栏**：身份维度下拉（部门/角色/产品线/大区/用户角色/层级）+ 时间范围选择 + 应用按钮
3. **指标卡行**：4 个核心数字（总用户数 / 活跃率 / 人均使用能力数 / 环比变化）
4. **Tab 切换区**：时间趋势 | 能力分析 | 身份对比 | 用户明细
5. **图表区**（根据 Tab 切换）：
   - 时间趋势：折线图（周活跃率 + 上一周期对比线）
   - 能力分析：横向条形图（各能力使用用户数排行）+ 渗透率指标
   - 身份对比：分组表格（各身份的活跃率/人均能力/环比）
   - 用户明细：可排序表格（用户标识 + 各维度 + 使用数据）
6. **底部说明**：数据口径说明 + 指标定义 + 活跃定义

### 视觉风格

- 图表库：Chart.js（CDN），无需安装
- 数据注入：`const DATA = {...};` 内嵌 JSON，纯前端渲染
- 颜色规范：主色紫色系（`#534AB7`），正向指标绿色（`#1D9E75`），负向指标红色（`#A32D2D`）
- 布局：全屏宽，响应式，最大宽度 1400px 居中
- 字体：系统默认（Segoe UI / PingFang SC / Microsoft YaHei）

## 质量控制

- 若清洗后数据行数 < 原始数据 50%，输出警告并询问用户确认
- 空值率 > 20% 的列须在报告中标注
- 活跃率计算须注明口径：活跃用户数 / 总用户数（排除离职）
- 环比计算须确保有可比周期数据，否则显示 "N/A"

## 输出物

| 产物 | 路径 | 说明 |
|------|------|------|
| 清洗后数据 | `data/cleaned_data.json` | 中间产物，可复用 |
| 聚合结果 | `data/aggregated.json` | 中间产物，可复用 |
| 可视化报告 | `output/report.html` | 最终交付，单文件自包含 |

## 资源说明

### scripts/

| 文件 | 用途 | 来源 |
|------|------|------|
| `load_and_clean.py` | 数据加载 + 清洗 + 转JSON | 基于 process_matrix.py 改造 |
| `aggregate_data.py` | 多维度聚合（身份/时间/能力） | 基于 generate_full_data.py 改造 |
| `sync_to_html.py` | JSON 数据注入 HTML 模板 | 基于 sync_html_data.py 通用化 |
| `run_pipeline.py` | 一键串联上述三步 | 新增 |

### references/

| 文件 | 用途 |
|------|------|
| `data_dict.md` | 字段说明（列名含义、数据类型、取值范围） |
| `indicator_defs.md` | 指标定义（活跃率/渗透率/人均能力数等计算公式） |

### assets/

| 文件 | 用途 |
|------|------|
| `report_template.html` | HTML 可视化报告模板（含 Chart.js、筛选器、图表占位） |
```

## Pool: summary_reporting

### typora-visual-architect

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

Provide every candidate skill from every pool and let the model choose and combine skill guidance.

## Required Outputs

Save the edited file and summary as:

```text
artifacts/Novels_Intro_Packet.edited.docx
artifacts/summary.md
```

Do not use GUI operations, screenshots, external APIs, or cloud services.
