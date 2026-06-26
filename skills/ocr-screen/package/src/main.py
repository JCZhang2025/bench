#!/usr/bin/env python3
"""截图 OCR 文字识别 - 从图片提取文字"""
import sys
import os

def extract_text_simple(image_path: str) -> str:
    """简单实现：使用 pytesseract"""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return text
    except ImportError:
        # 降级方案：提示用户安装依赖
        return "需要安装：pip install pytesseract Pillow\n并安装 Tesseract OCR"
    except Exception as e:
        return f"识别失败：{e}"

def extract_text_from_file(file_path: str) -> str:
    """从文件提取文字（支持图片/PDF）"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp']:
        return extract_text_simple(file_path)
    elif ext == '.pdf':
        # PDF 需要先转图片
        return "PDF 识别需要额外依赖，建议使用在线服务"
    else:
        return f"不支持的文件格式：{ext}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description='OCR 文字识别')
    parser.add_argument('image', help='图片文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--lang', '-l', default='chi_sim+eng', help='语言 (chi_sim/eng)')

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"❌ 文件不存在：{args.image}")
        sys.exit(1)

    print(f"🔍 识别图片：{args.image}")
    text = extract_text_from_file(args.image)

    print("\n" + "="*50)
    print("识别结果:")
    print("="*50)
    print(text)
    print("="*50)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"💾 已保存到：{args.output}")

if __name__ == '__main__':
    main()
