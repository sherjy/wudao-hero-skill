#!/usr/bin/env python3
"""卖飞追踪器

记录和追踪用户卖早了的股票，生成反思条目。

Usage:
    python3 regret_tracker.py --action <add|list|reflect> --base-dir <path> [options]
"""

import argparse
import os
import sys
import json
from datetime import datetime


def load_regrets(base_dir: str) -> list:
    """加载卖飞记录"""
    regret_path = os.path.join(base_dir, 'regret-log.md')
    entries = []

    if not os.path.exists(regret_path):
        return entries

    with open(regret_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析 ### 开头的条目
    sections = content.split('\n### ')
    for section in sections[1:]:  # 跳过第一段（文件头部）
        entry = {'raw': section}
        lines = section.strip().split('\n')

        if lines:
            # 第一行是标题：代码 名称
            header = lines[0].strip()
            entry['header'] = header

            for line in lines[1:]:
                line = line.strip()
                if line.startswith('- 卖出日期：'):
                    entry['sold_date'] = line.replace('- 卖出日期：', '').strip()
                elif line.startswith('- 卖出价：'):
                    entry['sold_price'] = line.replace('- 卖出价：', '').strip()
                elif line.startswith('- 卖出理由：'):
                    entry['sold_reason'] = line.replace('- 卖出理由：', '').strip()
                elif line.startswith('- 代码：'):
                    entry['ticker'] = line.replace('- 代码：', '').strip()

        entries.append(entry)

    return entries


def add_regret(base_dir: str, ticker: str, name: str, sold_date: str,
               sold_price: str, reason: str):
    """添加卖飞记录"""
    regret_path = os.path.join(base_dir, 'regret-log.md')

    # 确保文件存在
    if not os.path.exists(regret_path):
        with open(regret_path, 'w', encoding='utf-8') as f:
            f.write("# 卖飞追踪\n\n> 记录那些卖早了的票，提醒自己下次拿住。\n\n---\n")

    entry = f"""
### {ticker} {name}
- 代码：{ticker}
- 卖出日期：{sold_date or datetime.now().strftime('%Y-%m-%d')}
- 卖出价：{sold_price or '未知'}
- 卖出理由：{reason or '未说明'}
- 卖出后走势：待追踪
- 反思：待补充
- 记录时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    with open(regret_path, 'a', encoding='utf-8') as f:
        f.write(entry)

    # 更新 meta.json
    meta_path = os.path.join(base_dir, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        meta.setdefault('stats', {})['regret_entries'] = meta.get('stats', {}).get('regret_entries', 0) + 1
        meta['updated_at'] = datetime.now().isoformat()
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"已记录卖飞：{ticker} {name}")
    print(f"  卖出日期：{sold_date}")
    print(f"  卖出价：{sold_price}")
    print(f"  理由：{reason}")


def list_regrets(base_dir: str):
    """列出卖飞记录"""
    entries = load_regrets(base_dir)

    if not entries:
        print("没有卖飞记录。（这是好事！）")
        return

    print(f"卖飞追踪（共 {len(entries)} 条）：\n")
    for e in entries:
        print(f"  {e.get('header', '未知')}")
        print(f"    卖出日期：{e.get('sold_date', '?')}")
        print(f"    卖出价：{e.get('sold_price', '?')}")
        print(f"    理由：{e.get('sold_reason', '?')}")
        print()


def generate_reflect_prompt(base_dir: str) -> str:
    """生成反思提示，供 AI 补充后续走势和反思"""
    entries = load_regrets(base_dir)

    if not entries:
        return "没有卖飞记录需要反思。"

    lines = []
    lines.append("# 卖飞反思任务\n")
    lines.append("以下卖飞记录需要更新后续走势和反思。")
    lines.append("请使用 WebSearch 查询这些股票的当前价格，计算卖出后的涨幅，")
    lines.append("并结合用户的 Trading DNA 生成反思。\n")

    for e in entries:
        ticker = e.get('ticker', '')
        if ticker:
            lines.append(f"## {e.get('header', ticker)}")
            lines.append(f"- 卖出日期：{e.get('sold_date', '?')}")
            lines.append(f"- 卖出价：{e.get('sold_price', '?')}")
            lines.append(f"- 需要查询：{ticker} 当前价格")
            lines.append(f"- 需要计算：卖出后涨幅")
            lines.append(f"- 需要反思：为什么卖早了？涉及 DNA 哪个弱点？")
            lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='卖飞追踪器')
    parser.add_argument('--action', required=True, choices=['add', 'list', 'reflect'])
    parser.add_argument('--base-dir', default='./profile', help='profile 目录路径')
    parser.add_argument('--ticker', help='股票代码')
    parser.add_argument('--name', default='', help='股票名称')
    parser.add_argument('--sold-date', default='', help='卖出日期 YYYY-MM-DD')
    parser.add_argument('--sold-price', default='', help='卖出价格')
    parser.add_argument('--reason', default='', help='卖出理由')

    args = parser.parse_args()

    if args.action == 'add':
        if not args.ticker:
            print("错误：add 需要 --ticker 参数", file=sys.stderr)
            sys.exit(1)
        add_regret(args.base_dir, args.ticker, args.name,
                   args.sold_date, args.sold_price, args.reason)
    elif args.action == 'list':
        list_regrets(args.base_dir)
    elif args.action == 'reflect':
        prompt = generate_reflect_prompt(args.base_dir)
        print(prompt)


if __name__ == '__main__':
    main()
