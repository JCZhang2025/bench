---
name: screenshot-ocr
version: 1.0.0
description: 截图文字识别
license: PROPRIETARY

slash_commands:
  /ocr: 识别图片文字
  /ocr-table: 识别表格

capabilities:
  - ocr_chinese
  - ocr_english
  - extract_table

dependencies:
  - pytesseract
  - Pillow

---

# OCR 文字识别

## 功能
1. 中文/英文文字识别
2. 表格识别
3. 批量处理

## 依赖安装
首次使用需要安装：
```bash
pip install pytesseract pillow
# Ubuntu/Debian 还需要：sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
```

## 使用
```
/ocr screenshot.png
/ocr-table form.jpg
```

## 输出
- 识别的文字内容
- 可复制的纯文本
- 可选：导出 Word/Excel
