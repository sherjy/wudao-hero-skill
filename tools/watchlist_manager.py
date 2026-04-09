#!/usr/bin/env python3
"""自选股管理器

管理悟道分身的自选股列表：增加、删除、查看、更新状态。

Usage:
    python3 watchlist_manager.py --action <add|remove|list|update> --base-dir <path> [options]
"""

import argparse
import os
import sys
import json
from datetime import datetime


def load_watchlist(base_dir: str) -> list:
    """加载自选股数据"""
    watchlist_path = os.path.join(base_dir, 'watchlist.md')
    meta_path = os.path.join(base_dir, 'meta.json')

    entries = []
    if not os.path.exists(watchlist_path):
        return entries

    with open(watchlist_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 解析 markdown 表格
    for line in lines:
        line = line.strip()
        if line.startswith('|') and not line.startswith('|--') and not line.startswith('| 代码'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 6:
                entries.append({
                    'ticker': cells[0],
                    'name': cells[1],
                    'date_added': cells[2],
                    'thesis': cells[3],
                    'source': cells[4],
                    'status': cells[5],
                    'notes': cells[6] if len(cells) > 6 else '',
                })

    return entries


def save_watchlist(base_dir: str, entries: list):
    """保存自选股数据"""
    watchlist_path = os.path.join(base_dir, 'watchlist.md')

    lines = []
    lines.append("# 自选股跟踪\n")
    lines.append("| 代码 | 名称 | 加入日期 | 看好理由 | 来源 | 状态 | 备注 |")
    lines.append("|------|------|---------|---------|------|------|------|")

    for e in entries:
        lines.append(f"| {e['ticker']} | {e['name']} | {e['date_added']} | {e['thesis']} | {e['source']} | {e['status']} | {e.get('notes', '')} |")

    with open(watchlist_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def update_meta_watchlist_count(base_dir: str, entries: list):
    """更新 meta.json 中的自选股计数"""
    meta_path = os.path.join(base_dir, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        active_count = sum(1 for e in entries if e['status'] in ('观察中', '已买入'))
        meta.setdefault('stats', {})['watchlist_active'] = active_count
        meta['updated_at'] = datetime.now().isoformat()
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)


def add_stock(base_dir: str, ticker: str, name: str, thesis: str, source: str, date: str):
    """添加自选股"""
    entries = load_watchlist(base_dir)

    # 检查是否已存在
    for e in entries:
        if e['ticker'] == ticker:
            print(f"{ticker} {e['name']} 已在自选中（状态：{e['status']}）")
            return

    entries.append({
        'ticker': ticker,
        'name': name or ticker,
        'date_added': date or datetime.now().strftime('%Y-%m-%d'),
        'thesis': thesis or '待补充',
        'source': source or '自判',
        'status': '观察中',
        'notes': '',
    })

    save_watchlist(base_dir, entries)
    update_meta_watchlist_count(base_dir, entries)
    print(f"已加入自选：{ticker} {name}")


def remove_stock(base_dir: str, ticker: str):
    """从自选中移除"""
    entries = load_watchlist(base_dir)
    new_entries = [e for e in entries if e['ticker'] != ticker]

    if len(new_entries) == len(entries):
        print(f"{ticker} 不在自选中")
        return

    save_watchlist(base_dir, new_entries)
    update_meta_watchlist_count(base_dir, new_entries)
    print(f"已从自选移除：{ticker}")


def list_stocks(base_dir: str):
    """列出自选股"""
    entries = load_watchlist(base_dir)

    if not entries:
        print("自选股列表为空。")
        return

    print(f"自选股（共 {len(entries)} 只）：\n")
    for e in entries:
        status_icon = {'观察中': '👀', '已买入': '💰', '已卖出': '📤', '已移除': '❌'}.get(e['status'], '❓')
        print(f"  {status_icon} {e['ticker']} {e['name']}  [{e['status']}]")
        print(f"     加入：{e['date_added']} | 来源：{e['source']}")
        print(f"     理由：{e['thesis']}")
        if e.get('notes'):
            print(f"     备注：{e['notes']}")
        print()


def update_stock(base_dir: str, ticker: str, status: str = None, notes: str = None):
    """更新自选股状态"""
    entries = load_watchlist(base_dir)
    found = False

    for e in entries:
        if e['ticker'] == ticker:
            if status:
                e['status'] = status
            if notes:
                e['notes'] = notes
            found = True
            break

    if not found:
        print(f"{ticker} 不在自选中")
        return

    save_watchlist(base_dir, entries)
    update_meta_watchlist_count(base_dir, entries)
    print(f"已更新 {ticker}：状态={status or '未变'}, 备注={notes or '未变'}")


def main():
    parser = argparse.ArgumentParser(description='自选股管理器')
    parser.add_argument('--action', required=True, choices=['add', 'remove', 'list', 'update'])
    parser.add_argument('--base-dir', default='./profile', help='profile 目录路径')
    parser.add_argument('--ticker', help='股票代码')
    parser.add_argument('--name', default='', help='股票名称')
    parser.add_argument('--thesis', default='', help='看好理由')
    parser.add_argument('--source', default='自判', help='来源')
    parser.add_argument('--date', default='', help='加入日期 YYYY-MM-DD')
    parser.add_argument('--status', help='更新状态（观察中/已买入/已卖出/已移除）')
    parser.add_argument('--notes', help='备注')

    args = parser.parse_args()

    if args.action == 'add':
        if not args.ticker:
            print("错误：add 需要 --ticker 参数", file=sys.stderr)
            sys.exit(1)
        add_stock(args.base_dir, args.ticker, args.name, args.thesis, args.source, args.date)
    elif args.action == 'remove':
        if not args.ticker:
            print("错误：remove 需要 --ticker 参数", file=sys.stderr)
            sys.exit(1)
        remove_stock(args.base_dir, args.ticker)
    elif args.action == 'list':
        list_stocks(args.base_dir)
    elif args.action == 'update':
        if not args.ticker:
            print("错误：update 需要 --ticker 参数", file=sys.stderr)
            sys.exit(1)
        update_stock(args.base_dir, args.ticker, args.status, args.notes)


if __name__ == '__main__':
    main()
