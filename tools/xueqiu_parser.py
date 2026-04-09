#!/usr/bin/env python3
"""雪球帖子/讨论内容解析器

解析雪球等投资论坛的文本内容，提取交易洞察。

Usage:
    python3 xueqiu_parser.py --file <path> --output <path>
"""

import argparse
import os
import sys
import re
from datetime import datetime
from collections import Counter


# A股股票代码正则
STOCK_CODE_PATTERN = re.compile(r'\$([^$]+)\(([A-Z]{2}\d{6})\)\$|(?:SH|SZ|BJ)(\d{6})|(?:^|\s)(6\d{5}|0\d{5}|3\d{5}|688\d{3})(?:\s|$)')

# 雪球特有的标识
XUEQIU_MARKERS = ['雪球', 'xueqiu', '球友', '讨论区', '关注', '转发', '评论']

# 分析性关键词（用于识别高质量内容）
ANALYSIS_KEYWORDS = [
    '逻辑', '基本面', '技术面', '估值', '业绩', '增长', '毛利', '净利',
    '行业', '赛道', '竞争', '壁垒', '催化', '预期差', '确定性',
    '仓位', '止损', '止盈', '风控', '策略', '周期', '趋势',
]

# 情绪关键词
CONFIDENT_KEYWORDS = ['坚定看好', '重仓', '必涨', '翻倍', '确定性很高', '没问题']
CAUTIOUS_KEYWORDS = ['注意风险', '谨慎', '不确定', '可能', '观望', '控制仓位']


def parse_xueqiu_text(file_path: str) -> dict:
    """解析雪球内容文本文件"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    result = {
        'raw_content': content,
        'stock_mentions': [],
        'analysis_density': 0,
        'sentiment': 'neutral',
        'confidence_level': 'medium',
        'key_points': [],
        'word_count': len(content),
    }

    # 提取股票提及
    codes_found = set()
    for match in STOCK_CODE_PATTERN.finditer(content):
        name = match.group(1) or ''
        code = match.group(2) or match.group(3) or match.group(4) or ''
        if code and code not in codes_found:
            codes_found.add(code)
            result['stock_mentions'].append({'code': code, 'name': name.strip()})

    # 分析密度（分析性关键词占比）
    analysis_count = sum(1 for kw in ANALYSIS_KEYWORDS if kw in content)
    result['analysis_density'] = analysis_count / len(ANALYSIS_KEYWORDS) if ANALYSIS_KEYWORDS else 0

    # 情绪判断
    confident_count = sum(1 for kw in CONFIDENT_KEYWORDS if kw in content)
    cautious_count = sum(1 for kw in CAUTIOUS_KEYWORDS if kw in content)

    if confident_count > cautious_count + 1:
        result['sentiment'] = 'bullish'
        result['confidence_level'] = 'high'
    elif cautious_count > confident_count + 1:
        result['sentiment'] = 'cautious'
        result['confidence_level'] = 'low'
    elif confident_count > 0 or cautious_count > 0:
        result['sentiment'] = 'mixed'
        result['confidence_level'] = 'medium'

    # 提取关键论点（按段落分割，找包含分析关键词的段落）
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    for para in paragraphs:
        if len(para) > 30 and any(kw in para for kw in ANALYSIS_KEYWORDS):
            result['key_points'].append(para[:300])

    return result


def format_output(analysis: dict) -> str:
    """格式化输出"""
    lines = []
    lines.append("# 雪球/论坛内容分析结果")
    lines.append(f"\n分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"内容长度：{analysis['word_count']} 字")
    lines.append(f"分析密度：{analysis['analysis_density']:.0%}")
    lines.append(f"情绪倾向：{analysis['sentiment']}")
    lines.append(f"确信程度：{analysis['confidence_level']}")

    # 质量评级
    density = analysis['analysis_density']
    if density > 0.3 and len(analysis['key_points']) >= 2:
        grade = 'A级（有数据+逻辑完整+值得学习）'
    elif density > 0.15 or len(analysis['key_points']) >= 1:
        grade = 'B级（逻辑可参考但需验证）'
    else:
        grade = 'C级（情绪输出或信息不足）'
    lines.append(f"质量评级：{grade}")

    # 股票提及
    if analysis['stock_mentions']:
        lines.append("\n## 提及的股票")
        for s in analysis['stock_mentions']:
            lines.append(f"- {s['code']} {s['name']}")

    # 关键论点
    if analysis['key_points']:
        lines.append(f"\n## 关键论点（{len(analysis['key_points'])} 条）")
        for i, point in enumerate(analysis['key_points'][:5], 1):
            lines.append(f"\n### 论点 {i}")
            lines.append(point)

    # 原始内容（截取前 500 字供参考）
    lines.append("\n## 原始内容摘要")
    lines.append(analysis['raw_content'][:500])
    if len(analysis['raw_content']) > 500:
        lines.append(f"\n...（共 {analysis['word_count']} 字，已截取前 500 字）")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='雪球帖子/讨论内容解析器')
    parser.add_argument('--file', required=True, help='内容文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    analysis = parse_xueqiu_text(args.file)
    output = format_output(analysis)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"已分析 {analysis['word_count']} 字内容")
    print(f"检测到 {len(analysis['stock_mentions'])} 只股票提及")
    print(f"提取 {len(analysis['key_points'])} 个关键论点")
    print(f"结果已写入：{args.output}")


if __name__ == '__main__':
    main()
