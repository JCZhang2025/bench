"""
一键流水线：数据清洗 → 多维聚合 → 生成 HTML 报告
串联 load_and_clean.py → aggregate_data.py → sync_to_html.py
"""
import subprocess
import sys
import os
import argparse


def run_pipeline(input_path, output_html, users_path=None, resigned_path=None, dimensions=None, time_grain='week', template_path=None, matrix_dim='角色'):
    """
    一键执行完整流水线。

    Args:
        input_path: 使用明细文件路径
        output_html: 输出 HTML 报告路径
        users_path: 用户信息表路径（可选）
        resigned_path: 离职名单路径（可选）
        dimensions: 身份维度列名，逗号分隔（可选）
        time_grain: 时间粒度，'week' | 'month' | 'quarter'（默认 week）
        matrix_dim: 矩阵筛选分组维度（默认"角色"）
        template_path: 自定义 HTML 模板路径（可选，默认使用 assets/report_template.html）
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)

    # 默认模板路径
    if not template_path:
        template_path = os.path.join(skill_dir, 'assets', 'report_template.html')

    # 中间产物路径
    cleaned_path = os.path.join(os.path.dirname(output_html) or '.', 'cleaned_data.json')
    aggregated_path = os.path.join(os.path.dirname(output_html) or '.', 'aggregated_data.json')

    python = sys.executable

    # 第一步：数据加载与清洗
    print('=' * 50)
    print('第一步：数据加载与清洗')
    print('=' * 50)
    cmd1 = [python, os.path.join(script_dir, 'load_and_clean.py'),
            '--input', input_path, '--output', cleaned_path]
    if users_path:
        cmd1 += ['--users', users_path]
    if resigned_path:
        cmd1 += ['--resigned', resigned_path]
    result = subprocess.run(cmd1, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print('清洗失败:', result.stderr)
        return False

    # 第二步：多维聚合
    print('=' * 50)
    print('第二步：多维度聚合')
    print('=' * 50)
    cmd2 = [python, os.path.join(script_dir, 'aggregate_data.py'),
            '--input', cleaned_path, '--output', aggregated_path, '--time-grain', time_grain, '--matrix-dim', matrix_dim]
    if dimensions:
        cmd2 += ['--dimensions', dimensions]
    result = subprocess.run(cmd2, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print('聚合失败:', result.stderr)
        return False

    # 第三步：生成 HTML
    print('=' * 50)
    print('第三步：生成 HTML 报告')
    print('=' * 50)
    cmd3 = [python, os.path.join(script_dir, 'sync_to_html.py'),
            '--data', aggregated_path, '--template', template_path, '--output', output_html]
    result = subprocess.run(cmd3, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print('生成 HTML 失败:', result.stderr)
        return False

    print('=' * 50)
    print('流水线执行完成！')
    print(f'报告路径: {os.path.abspath(output_html)}')
    print(f'中间产物: {cleaned_path}, {aggregated_path}')
    print('=' * 50)
    return True


def main():
    parser = argparse.ArgumentParser(description='一键生成用户分析 HTML 报告')
    parser.add_argument('--input', required=True, help='使用明细文件路径 (Excel/CSV)')
    parser.add_argument('--output', required=True, help='输出 HTML 报告路径')
    parser.add_argument('--users', default=None, help='用户信息表路径')
    parser.add_argument('--resigned', default=None, help='离职名单文件路径')
    parser.add_argument('--dimensions', default='', help='身份维度列名，逗号分隔')
    parser.add_argument('--time-grain', default='week', choices=['week', 'month', 'quarter'], help='时间粒度：week(周)/month(月)/quarter(季度)，默认 week')
    parser.add_argument('--template', default=None, help='自定义 HTML 模板路径')
    parser.add_argument('--matrix-dim', default='角色', help='矩阵筛选分组维度（默认"角色"）')
    args = parser.parse_args()

    run_pipeline(
        input_path=args.input,
        output_html=args.output,
        users_path=args.users,
        resigned_path=args.resigned,
        dimensions=args.dimensions if args.dimensions else None,
        time_grain=args.time_grain,
        template_path=args.template,
        matrix_dim=args.matrix_dim
    )


if __name__ == '__main__':
    main()
