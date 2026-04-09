#!/usr/bin/env python3
"""交易 App 截图解析器

扫描截图目录，生成文件清单和提取提示供 AI 读图使用。

Usage:
    python3 trading_screenshot_parser.py --dir <path> --output <path> [--type <auto|holdings|transactions|chart|account>]
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime


# 支持的图片格式
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.heic', '.heif'}


def scan_screenshots(dir_path: str, img_type: str = 'auto'):
    """扫描目录中的截图文件"""
    if not os.path.isdir(dir_path):
        print(f"错误：目录不存在 {dir_path}", file=sys.stderr)
        sys.exit(1)

    images = []
    for root, dirs, files in os.walk(dir_path):
        for f in sorted(files):
            ext = Path(f).suffix.lower()
            if ext in IMAGE_EXTENSIONS:
                full_path = os.path.join(root, f)
                stat = os.stat(full_path)
                images.append({
                    'path': full_path,
                    'name': f,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                })

    return images


def generate_manifest(images: list, img_type: str):
    """生成截图清单和分析提示"""
    lines = []
    lines.append(f"# 交易截图扫描结果")
    lines.append(f"")
    lines.append(f"扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"文件数量：{len(images)}")
    lines.append(f"截图类型：{img_type}")
    lines.append(f"")

    if not images:
        lines.append("未找到图片文件。")
        return '\n'.join(lines)

    lines.append("## 文件清单")
    lines.append("")
    lines.append("| # | 文件名 | 修改时间 | 大小 | 路径 |")
    lines.append("|---|--------|---------|------|------|")

    for i, img in enumerate(images, 1):
        size_kb = img['size'] / 1024
        lines.append(f"| {i} | {img['name']} | {img['modified']} | {size_kb:.0f}KB | {img['path']} |")

    lines.append("")
    lines.append("## 分析提示")
    lines.append("")
    lines.append("请使用 `Read` 工具逐一读取上述图片文件，按以下要点分析：")
    lines.append("")

    if img_type in ('auto', 'holdings'):
        lines.append("### 持仓截图分析要点")
        lines.append("- 提取每只持仓标的：代码、名称、成本价、现价、盈亏百分比")
        lines.append("- 计算仓位集中度（单只最大占比）")
        lines.append("- 识别板块分布")
        lines.append("- A 股颜色规则：红色=涨/盈利，绿色=跌/亏损")
        lines.append("")

    if img_type in ('auto', 'transactions'):
        lines.append("### 交割单/成交记录分析要点")
        lines.append("- 提取每笔交易：时间、代码、买/卖、价格、数量")
        lines.append("- 计算单笔盈亏")
        lines.append("- 识别操作频率和模式")
        lines.append("")

    if img_type in ('auto', 'chart'):
        lines.append("### K线/走势图分析要点")
        lines.append("- 识别当前趋势（上升/下降/横盘）")
        lines.append("- 标注关键支撑/阻力位")
        lines.append("- 识别量价关系")
        lines.append("- 注意涨跌停板（+10%/+20%）")
        lines.append("")

    if img_type in ('auto', 'account'):
        lines.append("### 账户总览分析要点")
        lines.append("- 提取总资产、今日盈亏、总盈亏、收益率")
        lines.append("- 计算仓位比例（持仓/总资产）")
        lines.append("- 评估可用资金充裕度")
        lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='交易 App 截图解析器')
    parser.add_argument('--dir', required=True, help='截图目录路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--type', default='auto',
                        choices=['auto', 'holdings', 'transactions', 'chart', 'account'],
                        help='截图类型（默认 auto 自动检测）')

    args = parser.parse_args()

    images = scan_screenshots(args.dir, args.type)
    manifest = generate_manifest(images, args.type)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(manifest)

    print(f"已扫描 {len(images)} 个截图文件")
    print(f"清单已写入：{args.output}")


if __name__ == '__main__':
    main()
