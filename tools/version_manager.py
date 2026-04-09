#!/usr/bin/env python3
"""悟道分身版本存档与回滚管理器

Usage:
    python3 version_manager.py --action <backup|rollback|list> --base-dir <path> [--version <v>]
"""

import argparse
import os
import sys
import shutil
import json
from datetime import datetime


def backup(base_dir: str):
    """备份当前版本"""
    versions_dir = os.path.join(base_dir, 'versions')
    meta_path = os.path.join(base_dir, 'meta.json')

    if not os.path.exists(meta_path):
        print("错误：meta.json 不存在，无法备份", file=sys.stderr)
        sys.exit(1)

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    current_version = meta.get('version', 'v0')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{current_version}_{timestamp}"
    backup_dir = os.path.join(versions_dir, backup_name)

    os.makedirs(backup_dir, exist_ok=True)

    # 备份核心文件
    core_files = [
        'trading-dna.md',
        'experience-log.md',
        'watchlist.md',
        'regret-log.md',
        'cross-skill-log.md',
        'WUDAO-SELF.md',
        'meta.json',
    ]

    backed_up = []
    for fname in core_files:
        src = os.path.join(base_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(backup_dir, fname))
            backed_up.append(fname)

    print(f"已备份版本 {backup_name}")
    print(f"  备份文件：{', '.join(backed_up)}")
    print(f"  路径：{backup_dir}")
    return backup_name


def rollback(base_dir: str, version: str):
    """回滚到指定版本"""
    versions_dir = os.path.join(base_dir, 'versions')

    if not os.path.isdir(versions_dir):
        print("错误：没有历史版本", file=sys.stderr)
        sys.exit(1)

    # 查找匹配的版本
    target_dir = None
    for vname in sorted(os.listdir(versions_dir), reverse=True):
        if vname.startswith(version) or vname == version:
            target_dir = os.path.join(versions_dir, vname)
            break

    if not target_dir or not os.path.isdir(target_dir):
        print(f"错误：找不到版本 {version}", file=sys.stderr)
        list_versions(base_dir)
        sys.exit(1)

    # 先备份当前版本
    print("先备份当前版本...")
    backup(base_dir)

    # 恢复文件
    restored = []
    for fname in os.listdir(target_dir):
        src = os.path.join(target_dir, fname)
        dst = os.path.join(base_dir, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            restored.append(fname)

    print(f"\n已回滚到版本 {version}")
    print(f"  恢复文件：{', '.join(restored)}")


def list_versions(base_dir: str):
    """列出所有版本"""
    versions_dir = os.path.join(base_dir, 'versions')

    if not os.path.isdir(versions_dir):
        print("没有历史版本。")
        return

    versions = sorted(os.listdir(versions_dir), reverse=True)
    if not versions:
        print("没有历史版本。")
        return

    print(f"历史版本（共 {len(versions)} 个）：\n")
    for v in versions:
        # 尝试读取该版本的 meta.json 获取更多信息
        vmeta_path = os.path.join(versions_dir, v, 'meta.json')
        extra = ''
        if os.path.exists(vmeta_path):
            try:
                with open(vmeta_path, 'r', encoding='utf-8') as f:
                    vmeta = json.load(f)
                stats = vmeta.get('stats', {})
                exp_count = stats.get('experience_entries', '?')
                extra = f"  （经验:{exp_count}条）"
            except (json.JSONDecodeError, KeyError):
                pass
        print(f"  {v}{extra}")


def main():
    parser = argparse.ArgumentParser(description='悟道分身版本管理器')
    parser.add_argument('--action', required=True, choices=['backup', 'rollback', 'list'])
    parser.add_argument('--base-dir', default='./profile', help='profile 目录路径')
    parser.add_argument('--version', help='回滚目标版本（如 v3）')

    args = parser.parse_args()

    if args.action == 'backup':
        backup(args.base_dir)
    elif args.action == 'rollback':
        if not args.version:
            print("错误：rollback 需要 --version 参数", file=sys.stderr)
            sys.exit(1)
        rollback(args.base_dir, args.version)
    elif args.action == 'list':
        list_versions(args.base_dir)


if __name__ == '__main__':
    main()
