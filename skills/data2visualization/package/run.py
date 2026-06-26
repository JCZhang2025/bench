import json
from typing import Any, Dict, List

def parse_data(raw_data: str) -> Any:
    """
    尝试解析 JSON / 简单表格 / 纯文本
    """
    if not raw_data:
        return {}

    # 1️⃣ 尝试 JSON
    try:
        return json.loads(raw_data)
    except:
        pass

    # 2️⃣ 尝试 CSV/表格（逗号或制表符）
    lines = raw_data.strip().split("\n")
    if len(lines) > 1:
        delimiter = "," if "," in lines[0] else "\t"
        headers = lines[0].split(delimiter)
        data = []
        for line in lines[1:]:
            values = line.split(delimiter)
            if len(values) == len(headers):
                row = dict(zip(headers, values))
                data.append(row)
        if data:
            return data

    # 3️⃣ fallback 文本
    return {"text": raw_data}


def analyze_data(data: Any) -> Dict:
    """
    基础数据分析逻辑（可扩展）
    """
    result = {
        "type": "",
        "summary": "",
        "fields": [],
        "sample_size": 0,
        "insights": []
    }

    # JSON对象
    if isinstance(data, dict):
        result["type"] = "dict"
        result["fields"] = list(data.keys())
        result["sample_size"] = len(data)
        result["summary"] = f"检测到字典数据，包含 {len(data)} 个字段"
        result["insights"].append("数据结构较简单，适合做结构拆解分析")

    # 列表数据（表格）
    elif isinstance(data, list) and len(data) > 0:
        result["type"] = "table"
        result["sample_size"] = len(data)

        if isinstance(data[0], dict):
            result["fields"] = list(data[0].keys())
            result["summary"] = f"检测到表格数据，共 {len(data)} 行，字段 {len(result['fields'])} 个"

            # 简单字段分析
            numeric_fields = []
            for key in result["fields"]:
                try:
                    float(data[0][key])
                    numeric_fields.append(key)
                except:
                    continue

            if numeric_fields:
                result["insights"].append(f"存在数值字段：{', '.join(numeric_fields)}，可用于趋势分析")

            result["insights"].append("适合进行分组统计、趋势分析或占比分析")

    else:
        result["type"] = "text"
        result["summary"] = "检测到非结构化文本数据"
        result["insights"].append("建议进行关键词提取或语义分析")

    return result


def generate_mermaid(data: Any, analysis: Dict) -> str:
    """
    根据数据类型生成基础 Mermaid 图
    """
    if analysis["type"] == "table":
        return """
```mermaid
pie
    title 数据结构占比示意
    "数据行数" : 60
    "字段数量" : 40
```
"""
    elif analysis["type"] == "dict":
        return """
```mermaid
graph TD
A[输入数据] --> B[字段解析]
B --> C[结构分析]
C --> D[结果输出]
```
"""
    else:
        return """
```mermaid
graph LR
A[文本输入] --> B[语义解析]
B --> C[关键词提取]
C --> D[分析结果]
```
"""


def generate_table_preview(data: Any, max_rows: int = 5) -> List[Dict]:
    """
    返回用于展示的前几行数据
    """
    if isinstance(data, list):
        return data[:max_rows]
    elif isinstance(data, dict):
        return [{k: v} for k, v in list(data.items())[:max_rows]]
    return []


def run(params: Dict) -> Dict:
    """
    主执行入口
    """
    raw_data = params.get("data", "")
    goal = params.get("goal", "数据分析")
    chart_type = params.get("chart_type", "auto")

    # 1️⃣ 数据解析
    parsed_data = parse_data(raw_data)

    # 2️⃣ 数据分析
    analysis = analyze_data(parsed_data)

    # 3️⃣ 图表生成
    chart = generate_mermaid(parsed_data, analysis)

    # 4️⃣ 数据预览
    preview = generate_table_preview(parsed_data)

    # 5️⃣ 输出结构
    result = {
        "title": f"{goal}报告",
        "summary": analysis["summary"],
        "analysis": {
            "type": analysis["type"],
            "fields": analysis["fields"],
            "sample_size": analysis["sample_size"],
            "insights": analysis["insights"]
        },
        "preview": preview,
        "visualization": chart,
        "conclusion": "建议基于当前数据进一步细化分析维度，并结合业务场景做决策。"
    }

    return result