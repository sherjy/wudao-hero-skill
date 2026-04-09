#!/usr/bin/env python3
"""微信炒股群聊天记录解析器

解析微信聊天记录导出文件，提取股票讨论相关的市场情报。

Usage:
    python3 wechat_parser.py --file <path> --output <path> [--format <auto|txt|csv|html|json>]
"""

import argparse
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import Counter


# A股股票代码正则
STOCK_CODE_PATTERN = re.compile(r'\b(6\d{5}|0\d{5}|3\d{5}|688\d{3})\b')

# 常见股票关键词（用于情绪分析）
BULLISH_KEYWORDS = ['涨停', '起飞', '冲冲冲', '上车', '加仓', '牛逼', '梭哈', '龙头', '主升', '封板', '打板']
BEARISH_KEYWORDS = ['跌停', '完了', '跑', '割肉', '崩了', '凉了', '核按钮', '退潮', '跳水', '暴跌']
FOMO_KEYWORDS = ['冲', '追', '上车', '还能买吗', '来不来得及', '赶紧']
PANIC_KEYWORDS = ['完了', '怎么办', '割了', '扛不住', '止损', '跑了', '卖了']


def detect_format(file_path: str) -> str:
    """自动检测文件格式"""
    ext = Path(file_path).suffix.lower()
    if ext == '.csv':
        return 'csv'
    elif ext in ('.html', '.htm'):
        return 'html'
    elif ext == '.json':
        return 'json'
    else:
        return 'txt'


def parse_text(file_path: str) -> list:
    """解析纯文本格式的聊天记录"""
    messages = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 尝试按常见格式分割消息
    # 格式1: "2024-01-01 12:00:00 用户名\n消息内容"
    # 格式2: "[2024-01-01 12:00] 用户名: 消息内容"
    # 格式3: 纯文本流

    lines = content.split('\n')
    current_msg = {'sender': '', 'time': '', 'content': ''}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 尝试匹配时间戳模式
        time_match = re.match(
            r'[\[（]?(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)[\]）]?\s*(.+)',
            line
        )
        if time_match:
            if current_msg['content']:
                messages.append(current_msg.copy())
            current_msg = {
                'time': time_match.group(1),
                'sender': time_match.group(2).split(':')[0].split('：')[0].strip(),
                'content': ':'.join(time_match.group(2).split(':')[1:]).strip() if ':' in time_match.group(2) else '',
            }
        else:
            current_msg['content'] += ' ' + line

    if current_msg['content']:
        messages.append(current_msg)

    return messages


def analyze_messages(messages: list) -> dict:
    """分析聊天记录，提取市场情报"""
    result = {
        'total_messages': len(messages),
        'stock_mentions': Counter(),
        'bullish_count': 0,
        'bearish_count': 0,
        'fomo_signals': [],
        'panic_signals': [],
        'notable_messages': [],
        'senders': Counter(),
    }

    for msg in messages:
        content = msg.get('content', '')
        sender = msg.get('sender', '未知')

        result['senders'][sender] += 1

        # 提取股票代码
        codes = STOCK_CODE_PATTERN.findall(content)
        for code in codes:
            result['stock_mentions'][code] += 1

        # 情绪分析
        content_lower = content.lower()
        for kw in BULLISH_KEYWORDS:
            if kw in content:
                result['bullish_count'] += 1
                break

        for kw in BEARISH_KEYWORDS:
            if kw in content:
                result['bearish_count'] += 1
                break

        # FOMO 信号
        for kw in FOMO_KEYWORDS:
            if kw in content:
                result['fomo_signals'].append({
                    'sender': sender,
                    'content': content[:100],
                    'time': msg.get('time', ''),
                })
                break

        # 恐慌信号
        for kw in PANIC_KEYWORDS:
            if kw in content:
                result['panic_signals'].append({
                    'sender': sender,
                    'content': content[:100],
                    'time': msg.get('time', ''),
                })
                break

        # 筛选有价值的消息（包含分析逻辑的长消息）
        if len(content) > 50 and any(kw in content for kw in ['因为', '逻辑', '主线', '趋势', '板块', '分析']):
            result['notable_messages'].append({
                'sender': sender,
                'content': content[:200],
                'time': msg.get('time', ''),
            })

    return result


def format_output(analysis: dict) -> str:
    """格式化输出"""
    lines = []
    lines.append("# 微信炒股群聊分析结果")
    lines.append(f"\n分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"总消息数：{analysis['total_messages']}")
    lines.append(f"发言人数：{len(analysis['senders'])}")

    # 股票提及
    lines.append("\n## 股票提及")
    if analysis['stock_mentions']:
        lines.append("\n| 代码 | 提及次数 |")
        lines.append("|------|---------|")
        for code, count in analysis['stock_mentions'].most_common(20):
            lines.append(f"| {code} | {count} |")
    else:
        lines.append("未检测到股票代码提及。")

    # 情绪分析
    lines.append("\n## 情绪分析")
    total_sentiment = analysis['bullish_count'] + analysis['bearish_count']
    if total_sentiment > 0:
        bull_pct = analysis['bullish_count'] / total_sentiment * 100
        lines.append(f"- 看多信号：{analysis['bullish_count']} 条 ({bull_pct:.0f}%)")
        lines.append(f"- 看空信号：{analysis['bearish_count']} 条 ({100-bull_pct:.0f}%)")
    else:
        lines.append("- 情绪信号不明显")

    # FOMO 信号
    if analysis['fomo_signals']:
        lines.append(f"\n## FOMO 信号（{len(analysis['fomo_signals'])} 条）")
        for sig in analysis['fomo_signals'][:5]:
            lines.append(f"- [{sig['time']}] {sig['sender']}: {sig['content']}")

    # 恐慌信号
    if analysis['panic_signals']:
        lines.append(f"\n## 恐慌信号（{len(analysis['panic_signals'])} 条）")
        for sig in analysis['panic_signals'][:5]:
            lines.append(f"- [{sig['time']}] {sig['sender']}: {sig['content']}")

    # 有价值的观点
    if analysis['notable_messages']:
        lines.append(f"\n## 值得关注的观点（{len(analysis['notable_messages'])} 条）")
        for msg in analysis['notable_messages'][:10]:
            lines.append(f"\n### [{msg['time']}] {msg['sender']}")
            lines.append(f"{msg['content']}")

    # 活跃发言者
    lines.append("\n## 活跃发言者 Top 5")
    for sender, count in analysis['senders'].most_common(5):
        lines.append(f"- {sender}: {count} 条")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='微信炒股群聊天记录解析器')
    parser.add_argument('--file', required=True, help='聊天记录文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--format', default='auto',
                        choices=['auto', 'txt', 'csv', 'html', 'json'],
                        help='文件格式（默认 auto）')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    fmt = args.format if args.format != 'auto' else detect_format(args.file)
    messages = parse_text(args.file)  # 当前主要支持文本格式
    analysis = analyze_messages(messages)
    output = format_output(analysis)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"已分析 {analysis['total_messages']} 条消息")
    print(f"检测到 {len(analysis['stock_mentions'])} 只股票提及")
    print(f"结果已写入：{args.output}")


if __name__ == '__main__':
    main()
