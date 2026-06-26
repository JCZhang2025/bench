"""
数据注入 HTML 模板模块
将聚合结果 JSON 注入 HTML 模板中的占位符，生成自包含报告文件。
基于 sync_html_data.py 改造，通用化模板占位符匹配。
"""
import json
import argparse
import os
import re
from datetime import datetime


def sync_to_html(data_path, template_path, output_path):
    """
    读取聚合 JSON 和 HTML 模板，替换占位符，输出最终 HTML。

    Args:
        data_path: aggregate_data.py 输出的 JSON 路径
        template_path: HTML 模板路径（含 __DATA_PLACEHOLDER__）
        output_path: 输出 HTML 路径
    """
    # 读取数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 添加生成时间
    data['meta']['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 读取模板
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 替换占位符
    placeholder = '__DATA_PLACEHOLDER__'
    if placeholder not in html:
        print(f'错误：模板中未找到占位符 {placeholder}')
        return False

    data_json = json.dumps(data, ensure_ascii=False, default=str, indent=2)
    html = html.replace(placeholder, data_json)

    # 写出
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'HTML 报告已生成！')
    print(f'输出路径: {os.path.abspath(output_path)}')
    print(f'文件大小: {os.path.getsize(output_path) / 1024:.0f} KB')
    print(f'用户总数: {data["summary"]["total_users"]}')
    print(f'活跃率: {data["summary"]["avg_activity_rate"]:.1%}')
    return True


def main():
    parser = argparse.ArgumentParser(description='数据注入 HTML 模板')
    parser.add_argument('--data', required=True, help='聚合结果 JSON 路径')
    parser.add_argument('--template', required=True, help='HTML 模板路径')
    parser.add_argument('--output', required=True, help='输出 HTML 路径')
    args = parser.parse_args()

    sync_to_html(args.data, args.template, args.output)


if __name__ == '__main__':
    main()
