from datetime import datetime
import re

class TyporaVisualArchitect:

    def __init__(self):
        self.date = datetime.now().strftime("%Y-%m-%d")

    def transform(self, text: str) -> str:
        content = self._build_structure(text)
        return f"```markdown\n{content}\n```"

    def _build_structure(self, text: str) -> str:
        title = self._extract_title(text)

        body = f"""
<h1 style="text-align:center;">{title}</h1>

## 内容结构

<div style="background:#e3f2fd;border-left:5px solid #2196f3;padding:12px;border-radius:6px;">
{text}
</div>

## 总结

<div style="background:linear-gradient(145deg,#bbdefb,#b2dfdb);padding:16px;border-radius:12px;">
核心内容已完成结构化重组与视觉增强。
</div>

<p style="text-align:center;color:#777;">
Typora Visual Architect · {self.date}
</p>
"""
        return body

    def _extract_title(self, text):
        match = re.search(r"^.{5,30}", text)
        return match.group(0) if match else "Visual Document"


def run(input_text: str):
    engine = TyporaVisualArchitect()
    return engine.transform(input_text)