"""
数据加载与清洗模块
从原始 Excel/CSV 读取使用明细，清洗后输出 JSON 格式。
基于 process_matrix.py 改造，路径和列名改为参数传入。
"""
import pandas as pd
import numpy as np
import json
import argparse
import os

def load_and_clean(input_path, users_path=None, resigned_path=None, capability_cols=None):
    """
    读取原始使用明细，执行清洗，返回 DataFrame。

    Args:
        input_path: 使用明细 Excel/CSV 路径
        users_path: 用户信息表路径（含身份维度），可选
        resigned_path: 离职名单 CSV 路径，可选
        capability_cols: 能力使用次数列名列表，默认自动检测含"使用次数"的列

    Returns:
        tuple: (cleaned_df, meta_dict)
    """
    # 读取原始数据
    ext = os.path.splitext(input_path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(input_path)
    else:
        df = pd.read_csv(input_path)

    meta = {
        'raw_rows': len(df),
        'raw_columns': list(df.columns),
        'removed_resigned': 0,
        'removed_duplicates': 0,
        'cleaned_rows': 0
    }

    # 排除离职人员
    if resigned_path and os.path.exists(resigned_path):
        resigned_df = pd.read_csv(resigned_path)
        # 尝试常见列名匹配用户标识
        id_col = None
        for col in ['姓名', 'itcode', 'user_id', '员工编号', '工号']:
            if col in resigned_df.columns:
                id_col = col
                break
        if id_col:
            resigned_ids = set(resigned_df[id_col].dropna().astype(str))
            # 尝试在主表中找对应列
            for col in df.columns:
                if df[col].dtype == object:
                    sample_match = df[col].dropna().astype(str).head(100).isin(resigned_ids).sum()
                    if sample_match > 0:
                        before = len(df)
                        df = df[~df[col].astype(str).isin(resigned_ids)]
                        meta['removed_resigned'] = before - len(df)
                        break

    # 合并用户信息
    if users_path and os.path.exists(users_path):
        ext2 = os.path.splitext(users_path)[1].lower()
        users_df = pd.read_excel(users_path) if ext2 in ['.xlsx', '.xls'] else pd.read_csv(users_path)
        # 找共同列进行合并，优先用已知标识列
        common_cols = list(set(df.columns) & set(users_df.columns))
        if len(common_cols) >= 1:
            merge_on = [c for c in common_cols if c.lower() in ['姓名', 'itcode', 'user_id', '员工编号', '工号']]
            if not merge_on:
                # 尝试内容匹配：找在两个表中值重合度最高的文本列
                best_col = None
                best_overlap = 0
                for c in common_cols:
                    if users_df[c].dtype == object and df[c].dtype == object:
                        overlap = len(set(df[c].dropna().astype(str).head(200)) & set(users_df[c].dropna().astype(str).head(200)))
                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_col = c
                merge_on = [best_col] if best_col else common_cols[:1]
            df = df.merge(users_df, on=merge_on[0], how='left', suffixes=('', '_extra'))
            # 去掉重复列
            extra_cols = [c for c in df.columns if c.endswith('_extra')]
            df = df.drop(columns=extra_cols, errors='ignore')
            meta['merged_user_info'] = True
            meta['user_info_columns'] = list(users_df.columns)

    # 自动检测能力列：含"使用次数"的列
    if capability_cols is None:
        capability_cols = [c for c in df.columns if '使用次数' in c]

    # 数值转换
    for col in capability_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 计算周使用次数和活跃标记
    if capability_cols:
        df['_week_usage'] = df[capability_cols].sum(axis=1)
        df['_is_active'] = (df['_week_usage'] > 0).astype(int)
    else:
        df['_week_usage'] = 0
        df['_is_active'] = 0

    # 去重
    before = len(df)
    df = df.drop_duplicates()
    meta['removed_duplicates'] = before - len(df)

    # 日期处理：自动检测日期列并计算财周
    date_cols = [c for c in df.columns if df[c].dtype == 'datetime64[ns]' or 'date' in c.lower() or '时间' in c]
    for dc in date_cols:
        try:
            df[dc] = pd.to_datetime(df[dc], errors='coerce')
        except:
            pass

    meta['capability_cols'] = capability_cols
    meta['cleaned_rows'] = len(df)
    meta['warning'] = ''
    if meta['cleaned_rows'] < meta['raw_rows'] * 0.5:
        meta['warning'] = f'清洗后数据仅剩 {meta["cleaned_rows"]}/{meta["raw_rows"]} 行（{meta["cleaned_rows"]/meta["raw_rows"]:.0%}），请确认是否正常'

    return df, meta


def main():
    parser = argparse.ArgumentParser(description='数据加载与清洗')
    parser.add_argument('--input', required=True, help='使用明细文件路径')
    parser.add_argument('--users', default=None, help='用户信息表路径')
    parser.add_argument('--resigned', default=None, help='离职名单文件路径')
    parser.add_argument('--output', required=True, help='输出 JSON 路径')
    args = parser.parse_args()

    df, meta = load_and_clean(args.input, args.users, args.resigned)

    result = {
        'meta': meta,
        'columns': list(df.columns),
        'data': df.to_dict(orient='records')
    }

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, default=str)

    print(f'清洗完成！')
    print(f'原始行数: {meta["raw_rows"]}')
    print(f'排除离职: {meta["removed_resigned"]}')
    print(f'去除重复: {meta["removed_duplicates"]}')
    print(f'最终行数: {meta["cleaned_rows"]}')
    if meta['warning']:
        print(f'警告: {meta["warning"]}')


if __name__ == '__main__':
    main()
