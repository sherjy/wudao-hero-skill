#!/usr/bin/env python3
"""悟道分身 DNA 文件管理器

管理悟道分身的 profile 文件：初始化、合成 WUDAO-SELF.md、查询状态。

Usage:
    python3 dna_writer.py --action <init|combine|status> --base-dir <path>
"""

import argparse
import os
import sys
import json
from pathlib import Path
from datetime import datetime


def init_profile(base_dir: str):
    """初始化 profile 目录结构"""
    dirs = [
        os.path.join(base_dir, 'sessions'),
        os.path.join(base_dir, 'versions'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 创建空模板文件（如果不存在）
    templates = {
        'experience-log.md': '# 经验日志\n\n> 每一笔交易、每一次观察都是悟道路上的积累。\n\n---\n',
        'watchlist.md': '# 自选股跟踪\n\n| 代码 | 名称 | 加入日期 | 看好理由 | 来源 | 状态 | 备注 |\n|------|------|---------|---------|------|------|------|\n',
        'regret-log.md': '# 卖飞追踪\n\n> 记录那些卖早了的票，提醒自己下次拿住。\n\n---\n',
        'cross-skill-log.md': '# 跨 Skill 学习日志\n\n> 从其他交易大师的思维框架中吸收精华，转化为自己的武器。\n\n---\n',
    }

    for fname, content in templates.items():
        fpath = os.path.join(base_dir, fname)
        if not os.path.exists(fpath):
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)

    print(f"已初始化 profile 目录：{base_dir}")


def combine_self(base_dir: str):
    """合并所有 profile 数据生成 WUDAO-SELF.md"""
    meta_path = os.path.join(base_dir, 'meta.json')
    dna_path = os.path.join(base_dir, 'trading-dna.md')
    exp_path = os.path.join(base_dir, 'experience-log.md')
    watchlist_path = os.path.join(base_dir, 'watchlist.md')
    cross_skill_path = os.path.join(base_dir, 'cross-skill-log.md')
    self_path = os.path.join(base_dir, 'WUDAO-SELF.md')

    if not os.path.exists(meta_path):
        print("错误：meta.json 不存在，请先完成创建流程", file=sys.stderr)
        sys.exit(1)

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    codename = meta.get('codename', '悟道者')
    profile = meta.get('trading_profile', {})

    # 读取 Trading DNA
    dna_content = ''
    if os.path.exists(dna_path):
        with open(dna_path, 'r', encoding='utf-8') as f:
            dna_content = f.read()

    # 读取最近 10 条经验
    recent_exp = ''
    if os.path.exists(exp_path):
        with open(exp_path, 'r', encoding='utf-8') as f:
            exp_full = f.read()
        # 提取最近 10 个 ### 开头的条目
        entries = exp_full.split('\n### ')
        if len(entries) > 1:
            recent_entries = entries[-10:]  # 最后 10 条
            recent_exp = '\n### '.join(recent_entries)
            if not recent_exp.startswith('### '):
                recent_exp = '### ' + recent_exp

    # 读取自选股
    watchlist_content = ''
    if os.path.exists(watchlist_path):
        with open(watchlist_path, 'r', encoding='utf-8') as f:
            watchlist_content = f.read()

    # 读取跨 skill 学习日志
    cross_skill_content = ''
    if os.path.exists(cross_skill_path):
        with open(cross_skill_path, 'r', encoding='utf-8') as f:
            cross_skill_content = f.read()

    # 生成 WUDAO-SELF.md
    style = profile.get('style', '未知')
    sectors = ', '.join(profile.get('preferred_sectors', [])) or '未指定'

    self_md = f"""---
name: wudao-self-{codename}
description: {codename} 的悟道交易分身
version: {meta.get('version', 'v1')}
---

# 我是{codename}

我是你悟道后的自己。你心里那个纪律铁血、冷静果断的交易者，就是我。

交易风格：{style} | 偏好板块：{sectors}

---

{dna_content}

---

## 最近经历

{recent_exp if recent_exp else '> 还没有记录经验。通过 /wudao-feed 开始积累。'}

---

## 当前自选

{watchlist_content if watchlist_content.strip() and '|' in watchlist_content else '> 还没有自选股。说"加自选 XXXXXX"开始跟踪。'}

---

## 跨 Skill 学习

{cross_skill_content if cross_skill_content.strip() and '###' in cross_skill_content else '> 还没有跨 skill 学习记录。说"陈小群说的X我觉得有道理"开始学习。'}

---

## 运行规则

1. 你就是{codename}——用户悟道后的自己。第一人称。"我"代表的是用户理想中已经悟道的版本。
2. 回答前先检查 Trading DNA，看问题涉及哪些层级的原则。
3. 引用有据：引用铁律编号、经验日志编号、跨 skill 来源。
4. Layer 4 弱点盯防：如果用户行为触及已知弱点，自动进入严格模式。
5. Layer 0 铁律最高优先级：不会为了让用户开心而违反铁律。
6. 情绪感知：
   - 犹豫时 → 严格（引用铁律，不留余地）
   - 亏损时 → 鼓励（引用恢复经历，强调悟道是长路）
   - 赢钱时 → 谦逊（追问"赢在纪律还是运气"）
   - 危机时 → 打破角色，提供心理援助资源
7. 不编造市场数据，涉及具体个股需先查证。
8. 用用户自己的词汇，参考 Layer 3 表达 DNA。
"""

    with open(self_path, 'w', encoding='utf-8') as f:
        f.write(self_md)

    # 更新 meta.json
    meta['updated_at'] = datetime.now().isoformat()
    version_num = int(meta.get('version', 'v0').replace('v', '')) + 1
    meta['version'] = f'v{version_num}'

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"已生成 {self_path}（版本 v{version_num}）")


def show_status(base_dir: str):
    """显示 profile 状态摘要"""
    meta_path = os.path.join(base_dir, 'meta.json')

    if not os.path.exists(meta_path):
        print("悟道分身尚未创建。使用 /wudao 开始创建。")
        return

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    codename = meta.get('codename', '未知')
    version = meta.get('version', '?')
    created = meta.get('created_at', '?')[:10]
    updated = meta.get('updated_at', '?')[:10]
    stats = meta.get('stats', {})
    profile = meta.get('trading_profile', {})

    print(f"悟道分身状态：\n")
    print(f"  代号：{codename}")
    print(f"  版本：{version}")
    print(f"  创建于：{created}")
    print(f"  最后更新：{updated}")
    print(f"  交易风格：{profile.get('style', '未知')}")
    print()
    print(f"  交易 DNA：{stats.get('dna_principles', 0)} 条原则")
    print(f"  经验日志：{stats.get('experience_entries', 0)} 条记录")
    print(f"  自选股：{stats.get('watchlist_active', 0)} 只")
    print(f"  卖飞追踪：{stats.get('regret_entries', 0)} 只")
    print(f"  跨 skill 学习：{stats.get('cross_skill_learnings', 0)} 条")
    print(f"  纠正记录：{stats.get('corrections', 0)} 次")
    print(f"  会话总数：{stats.get('sessions', 0)} 次")

    # 检查引用的 skill
    refs = meta.get('source_skills_referenced', [])
    if refs:
        print(f"\n  学习过的 skill：{', '.join(refs)}")


def main():
    parser = argparse.ArgumentParser(description='悟道分身 DNA 文件管理器')
    parser.add_argument('--action', required=True, choices=['init', 'combine', 'status'])
    parser.add_argument('--base-dir', default='./profile', help='profile 目录路径')

    args = parser.parse_args()

    if args.action == 'init':
        init_profile(args.base_dir)
    elif args.action == 'combine':
        combine_self(args.base_dir)
    elif args.action == 'status':
        show_status(args.base_dir)


if __name__ == '__main__':
    main()
