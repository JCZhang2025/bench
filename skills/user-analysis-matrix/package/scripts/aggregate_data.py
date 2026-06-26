"""
多维度数据聚合模块（矩阵版）
按身份维度、时间维度、能力维度分别聚合，并生成 7×7 活跃度×能力广度矩阵。
基于 generate_full_data.py 改造，支持动态维度参数和时间粒度。
"""
import json
import argparse
import os
import re
from datetime import datetime
from collections import defaultdict


def parse_time_grain(week_value):
    """
    从财周标签中提取月和季度粒度。
    支持格式：FY26-W20, 2026-W20, W20 等。
    返回: (month_label, quarter_label) 或 ('', '')
    """
    m = re.search(r'FY(\d{2})-W(\d{1,2})', str(week_value))
    if not m:
        m = re.search(r'(\d{4})-W(\d{1,2})', str(week_value))
    if not m:
        m = re.search(r'W(\d{1,2})', str(week_value))

    if m and m.group(1).isdigit() and int(m.group(1)) > 20:
        year = '20' + m.group(1)
    elif m:
        year = m.group(1) if len(m.group(1)) == 4 else '20' + m.group(1)
    else:
        return '', ''

    week_num = int(m.group(2))
    month = min(((week_num - 1) // 4) + 1, 12)
    quarter = (month - 1) // 3 + 1

    month_label = f'{year}-{month:02d}'
    quarter_label = f'{year}-Q{quarter}'
    return month_label, quarter_label


def _get_activity_rate_bin(rate):
    """将活跃率映射到7档（0~6）：0%, 0-20%, 20-40%, 40-60%, 60-80%, 80-100%, 100%"""
    if rate >= 1.0:
        return 6
    if rate >= 0.8:
        return 5
    if rate >= 0.6:
        return 4
    if rate >= 0.4:
        return 3
    if rate >= 0.2:
        return 2
    if rate > 0:
        return 1
    return 0


def _get_usage_bin(usage):
    """将使用总次数映射到10档（0~9）"""
    bins = [0, 1, 6, 11, 21, 41, 61, 81, 101, 151]
    for i in range(len(bins) - 1, -1, -1):
        if usage >= bins[i]:
            return i
    return 0


def aggregate(input_path, output_path, dimensions=None, time_grain='week',
              matrix_dim='角色'):
    """
    读取清洗后的 JSON 数据，执行多维度聚合，生成矩阵结构。

    Args:
        input_path: load_and_clean.py 输出的 JSON 路径
        output_path: 聚合结果输出路径
        dimensions: 身份维度列名列表
        time_grain: 时间粒度，'week'(默认) | 'month' | 'quarter'
        matrix_dim: 用于矩阵筛选分组的维度（默认"角色"）
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    meta = raw['meta']
    records = raw['data']
    capability_cols = meta.get('capability_cols', [])
    total_rows = len(records)

    if not dimensions:
        dimensions = ['部门', '角色', '产品线', '大区', '用户角色', '层级']

    # ========== 构建用户级别数据 ==========
    # 每个用户：活跃周数、总使用次数、使用能力集合、各周活跃标记
    user_map = defaultdict(lambda: {
        'active_weeks': 0,
        'total_weeks': 0,
        'total_usage': 0,
        'caps': set(),
        'weekly_active': set(),  # 记录哪些周活跃过
        'weekly_usage': 0,
        'dim_values': {}
    })

    week_col = None
    for c in ['财周', 'week', '周', 'fiscal_week', 'week_label']:
        if records and c in records[0]:
            week_col = c
            break

    for r in records:
        uid = str(r.get('姓名', r.get('user_id', '')))
        wk = str(r.get(week_col, '')) if week_col else ''
        user_map[uid]['total_weeks'] += 1
        user_map[uid]['weekly_usage'] += r.get('_week_usage', 0)
        user_map[uid]['total_usage'] += r.get('_week_usage', 0)
        if r.get('_is_active', 0) > 0:
            user_map[uid]['active_weeks'] += 1
            if wk:
                user_map[uid]['weekly_active'].add(wk)
        for cap in capability_cols:
            if r.get(cap, 0) > 0:
                user_map[uid]['caps'].add(cap)
        for dim in dimensions:
            if dim in r and r[dim]:
                user_map[uid]['dim_values'][dim] = r[dim]

    total_users = len(user_map)
    all_users = list(user_map.keys())

    # ========== 计算每个用户的活跃率和能力数 ==========
    for uid, info in user_map.items():
        total_weeks = max(info['total_weeks'], 1)
        info['activity_rate'] = info['active_weeks'] / total_weeks
        info['cap_count'] = len(info['caps'])
        info['rate_bin'] = _get_activity_rate_bin(info['activity_rate'])
        info['usage_bin'] = _get_usage_bin(info['total_usage'])

    # ========== 统计前用户数（用于排除离职） ==========
    # former_users: 原始数据中的离职用户数（从 meta 获取）
    former_users = meta.get('removed_resigned', 0)
    churned_users = meta.get('removed_frozen', 0)

    # ========== 身份维度聚合 ==========
    identity_results = []
    for dim in dimensions:
        groups = defaultdict(lambda: {'total_users': set(), 'active_users': set(), 'usage_sum': 0, 'cap_count_sum': 0})
        for r in records:
            group_key = r.get(dim, '未知')
            user_id = str(r.get('姓名', r.get('user_id', '')))
            groups[group_key]['total_users'].add(user_id)
            if r.get('_is_active', 0) > 0:
                groups[group_key]['active_users'].add(user_id)
            groups[group_key]['usage_sum'] += r.get('_week_usage', 0)
            groups[group_key]['cap_count_sum'] += sum(1 for c in capability_cols if c in r and r[c] > 0)

        for name, g in groups.items():
            total = len(g['total_users'])
            active = len(g['active_users'])
            identity_results.append({
                'dimension': dim,
                'group_name': name,
                'total_users': total,
                'active_users': active,
                'active_rate': round(active / total, 4) if total > 0 else 0,
                'avg_capability': round(g['cap_count_sum'] / total, 2) if total > 0 else 0,
                'total_usage': g['usage_sum']
            })

    # ========== 时间维度聚合 ==========
    week_groups = defaultdict(lambda: {'active_users': set(), 'all_users': set(), 'usage_sum': 0})

    if week_col:
        for r in records:
            wk = str(r.get(week_col, ''))
            if not wk:
                continue
            if time_grain == 'month':
                month_label, _ = parse_time_grain(wk)
                grain_key = month_label or wk
            elif time_grain == 'quarter':
                _, quarter_label = parse_time_grain(wk)
                grain_key = quarter_label or wk
            else:
                grain_key = wk
            user_id = str(r.get('姓名', r.get('user_id', '')))
            week_groups[grain_key]['all_users'].add(user_id)
            if r.get('_is_active', 0) > 0:
                week_groups[grain_key]['active_users'].add(user_id)
            week_groups[grain_key]['usage_sum'] += r.get('_week_usage', 0)

    timeline = []
    sorted_weeks = sorted(week_groups.keys())
    for i, wk in enumerate(sorted_weeks):
        g = week_groups[wk]
        total = len(g['all_users'])
        active = len(g['active_users'])
        rate = round(active / total, 4) if total > 0 else 0
        wow = None
        if i > 0:
            prev = week_groups[sorted_weeks[i - 1]]
            prev_total = len(prev['all_users'])
            prev_rate = round(len(prev['active_users']) / prev_total, 4) if prev_total > 0 else 0
            if prev_rate > 0:
                wow = round((rate - prev_rate) / prev_rate * 100, 1)

        timeline.append({
            'week': wk,
            'total_users': total,
            'active_users': active,
            'activity_rate': rate,
            'total_usage': g['usage_sum'],
            'week_over_week': wow
        })

    # ========== 能力维度聚合 ==========
    cap_results = []
    for cap in capability_cols:
        cap_users = set()
        cap_usage = 0
        for r in records:
            val = r.get(cap, 0)
            if isinstance(val, str):
                try:
                    val = float(val)
                except:
                    val = 0
            if val > 0:
                cap_users.add(str(r.get('姓名', r.get('user_id', ''))))
                cap_usage += val

        cap_results.append({
            'capability': cap,
            'user_count': len(cap_users),
            'total_usage': int(cap_usage),
            'penetration_rate': round(len(cap_users) / total_users, 4) if total_users > 0 else 0
        })

    cap_results.sort(key=lambda x: x['user_count'], reverse=True)

    # ========== 7×7 矩阵：活跃度 × 能力广度 ==========
    # 获取 matrix_dim 的所有取值
    filter_dim_values = set()
    for uid, info in user_map.items():
        val = info['dim_values'].get(matrix_dim, '未知')
        filter_dim_values.add(val)

    matrix1 = {}
    matrix1_detail = {}

    # 按筛选维度分组生成矩阵
    filter_groups = ['all'] + sorted(filter_dim_values)
    for fg in filter_groups:
        # 初始化 7×7 矩阵
        mat = [[0] * 7 for _ in range(7)]
        detail = {}

        for uid, info in user_map.items():
            # 如果按维度筛选，检查该用户是否属于该组
            if fg != 'all':
                if info['dim_values'].get(matrix_dim, '未知') != fg:
                    continue

            row = min(info['cap_count'], 6)  # 能力数（Y轴）
            col = info['rate_bin']            # 活跃率档位（X轴）
            mat[row][col] += 1

            # 详情：记录该单元格的角色分布
            key = f'{row}_{col}'
            if key not in detail:
                detail[key] = {'roles': {}, 'level1': {}}
            # 角色标识：用 matrix_dim 的值作为角色标签
            role_label = info['dim_values'].get(matrix_dim, '未知')
            detail[key]['roles'][role_label] = detail[key]['roles'].get(role_label, 0) + 1

        matrix1[fg] = mat
        matrix1_detail[fg] = detail

    # ========== 10×10 矩阵：使用次数 × 活跃度 ==========
    matrix2 = {}
    matrix2_detail = {}

    for fg in filter_groups:
        mat = [[0] * 10 for _ in range(10)]
        detail = {}

        for uid, info in user_map.items():
            if fg != 'all':
                if info['dim_values'].get(matrix_dim, '未知') != fg:
                    continue

            row = min(info['usage_bin'], 9)  # 使用次数档位
            col = info['rate_bin']            # 活跃率档位
            mat[row][col] += 1

            key = f'{row}_{col}'
            if key not in detail:
                detail[key] = {}
            role_label = info['dim_values'].get(matrix_dim, '未知')
            detail[key][role_label] = detail[key].get(role_label, 0) + 1

        matrix2[fg] = mat
        matrix2_detail[fg] = detail

    # ========== 用户分层统计 ==========
    # 高价值：能力数 >= 3 且 活跃率 > 80%（档位5或6）
    high_value_users = set()
    # 沉默：能力数 0 且 活跃率 0%
    silent_users = set()
    # 增长：非高价值、非沉默的其余用户
    growth_users = set()

    for uid, info in user_map.items():
        if info['cap_count'] >= 3 and info['rate_bin'] >= 5:
            high_value_users.add(uid)
        elif info['cap_count'] == 0 and info['rate_bin'] == 0:
            silent_users.add(uid)
        else:
            growth_users.add(uid)

    # ========== 按组织分组的用户分层 ==========
    # 使用产品线维度分组，如果没有则用 matrix_dim
    org_dim = '产品线'
    org_values = set()
    for uid, info in user_map.items():
        org_values.add(info['dim_values'].get(org_dim, '未知'))

    bu_analysis = []
    for org in sorted(org_values):
        org_users = [uid for uid, info in user_map.items()
                     if info['dim_values'].get(org_dim, '未知') == org]
        org_total = len(org_users)
        if org_total == 0:
            continue
        bu_analysis.append({
            'bu': org,
            'total': org_total,
            'high_value': len(high_value_users & set(org_users)),
            'growth': len(growth_users & set(org_users)),
            'silent_churned': len(silent_users & set(org_users))
        })

    # ========== 角色分析表 ==========
    role_analysis = []
    # 按 matrix_dim 和 产品线 两个维度组合排序
    role_groups = defaultdict(lambda: {
        'users': set(), 'total_usage': 0, 'cap_sum': 0, 'rate_sum': 0
    })
    for uid, info in user_map.items():
        role_key = info['dim_values'].get(matrix_dim, '未知')
        role_groups[role_key]['users'].add(uid)
        role_groups[role_key]['total_usage'] += info['total_usage']
        role_groups[role_key]['cap_sum'] += info['cap_count']
        role_groups[role_key]['rate_sum'] += info['activity_rate']

    for role, g in sorted(role_groups.items()):
        count = len(g['users'])
        role_analysis.append({
            'role': role,
            'user_count': count,
            'avg_activity': round(g['rate_sum'] / count, 4) if count > 0 else 0,
            'total_usage': g['total_usage'],
            'avg_capability': round(g['cap_sum'] / count, 2) if count > 0 else 0
        })

    # ========== 汇总统计 ==========
    active_user_set = set(uid for uid, info in user_map.items() if info['active_weeks'] > 0)
    avg_rate = round(len(active_user_set) / total_users, 4) if total_users > 0 else 0

    # ========== 用户列表 ==========
    user_list = []
    for uid, info in user_map.items():
        entry = {
            '姓名': uid,
            'active_weeks': info['active_weeks'],
            'total_usage': info['total_usage'],
            'capability_count': info['cap_count'],
            'activity_rate': round(info['activity_rate'], 4)
        }
        for dim in dimensions:
            if dim in info['dim_values']:
                entry[dim] = info['dim_values'][dim]
        user_list.append(entry)
    user_list.sort(key=lambda x: x['total_usage'], reverse=True)

    # ========== 组装输出 ==========
    result = {
        'meta': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'time_range': sorted_weeks[0] + ' ~ ' + sorted_weeks[-1] if sorted_weeks else '全部',
            'total_weeks': len(sorted_weeks),
            'time_grain': time_grain,
            'matrix_dim': matrix_dim,
            'filter_groups': filter_groups
        },
        'summary': {
            'total_users': total_users,
            'active_users': len(active_user_set),
            'former_users': former_users,
            'churned_users': churned_users,
            'total_weeks': len(sorted_weeks),
            'avg_activity_rate': avg_rate,
            'high_value_count': len(high_value_users),
            'silent_count': len(silent_users)
        },
        'dimensions': dimensions,
        'matrix1': matrix1,
        'matrix1_detail': matrix1_detail,
        'matrix2': matrix2,
        'matrix2_detail': matrix2_detail,
        'bu_analysis': bu_analysis,
        'role_analysis': role_analysis,
        'identity': identity_results,
        'timeline': timeline,
        'capability': cap_results,
        'user_list': user_list[:500]
    }

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, default=str)

    print(f'聚合完成！')
    print(f'用户总数: {total_users}')
    print(f'活跃用户: {len(active_user_set)}')
    print(f'活跃率: {avg_rate:.1%}')
    print(f'高价值用户: {len(high_value_users)}')
    print(f'沉默用户: {len(silent_users)}')
    print(f'矩阵筛选维度: {matrix_dim}（{len(filter_groups)} 组）')
    print(f'身份分组数: {len(identity_results)}')
    print(f'时间周期数: {len(timeline)}')
    print(f'能力类别数: {len(cap_results)}')
    print(f'用户明细: {len(user_list)} 条（输出前500条）')


def main():
    parser = argparse.ArgumentParser(description='多维度数据聚合（矩阵版）')
    parser.add_argument('--input', required=True, help='清洗后 JSON 数据路径')
    parser.add_argument('--output', required=True, help='聚合结果输出路径')
    parser.add_argument('--dimensions', default='', help='身份维度列名，逗号分隔')
    parser.add_argument('--time-grain', default='week', choices=['week', 'month', 'quarter'], help='时间粒度')
    parser.add_argument('--matrix-dim', default='角色', help='矩阵筛选分组维度（默认"角色"）')
    args = parser.parse_args()

    dims = [d.strip() for d in args.dimensions.split(',') if d.strip()] if args.dimensions else None
    aggregate(args.input, args.output, dims, time_grain=args.time_grain,
              matrix_dim=args.matrix_dim)


if __name__ == '__main__':
    main()
