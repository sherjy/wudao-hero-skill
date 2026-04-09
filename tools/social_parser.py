#!/usr/bin/env python3
"""通用社交媒体截图扫描器

扫描截图目录，生成文件清单供 AI 读图分析使用。

Usage:
    python3 social_parser.py --dir <path> --output <path>
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime


# 支持的图片格式
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.heic', '.heif'}

# 支持的文本格式
TEXT_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.html', '.htm'}


def scan_directory(dir_path: str) -> dict:
    """扫描目录中的所有可处理文件"""
    if not os.path.isdir(dir_path):
        print(f"错误：目录不存在 {dir_path}", file=sys.stderr)
        sys.exit(1)

    images = []
    texts = []

    for root, dirs, files in os.walk(dir_path):
        for f in sorted(files):
            ext = Path(f).suffix.lower()
            full_path = os.path.join(root, f)
            stat = os.stat(full_path)
            file_info = {
                'path': full_path,
                'name': f,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'extension': ext,
            }

            if ext in IMAGE_EXTENSIONS:
                images.append(file_info)
            elif ext in TEXT_EXTENSIONS:
                texts.append(file_info)

    return {'images': images, 'texts': texts}


def format_output(scan_result: dict) -> str:
    """格式化输出"""
    images = scan_result['images']
    texts = scan_result['texts']

    lines = []
    lines.append("# 社交媒体内容扫描结果")
    lines.append(f"\n扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"图片文件：{len(images)} 个")
    lines.append(f"文本文件：{len(texts)} 个")

    if images:
        lines.append("\n## 图片文件")
        lines.append("\n| # | 文件名 | 修改时间 | 大小 | 路径 |")
        lines.append("|---|--------|---------|------|------|")
        for i, img in enumerate(images, 1):
            size_kb = img['size'] / 1024
            lines.append(f"| {i} | {img['name']} | {img['modified']} | {size_kb:.0f}KB | {img['path']} |")

        lines.append("\n### 图片分析提示")
        lines.append("请使用 `Read` 工具逐一读取图片，关注：")
        lines.append("- 内容来源平台（微信朋友圈/微博/雪球/小红书/抖音等）")
        lines.append("- 讨论的股票或板块")
        lines.append("- 观点/情绪（看多/看空/分析/吐槽）")
        lines.append("- 是否包含有价值的交易逻辑或经验分享")

    if texts:
        lines.append("\n## 文本文件")
        lines.append("\n| # | 文件名 | 修改时间 | 大小 | 路径 |")
        lines.append("|---|--------|---------|------|------|")
        for i, txt in enumerate(texts, 1):
            size_kb = txt['size'] / 1024
            lines.append(f"| {i} | {txt['name']} | {txt['modified']} | {size_kb:.0f}KB | {txt['path']} |")

        lines.append("\n### 文本分析提示")
        lines.append("请使用 `Read` 工具读取文本文件，按 insight_analyzer.md 的维度分析。")

    if not images and not texts:
        lines.append("\n未找到可处理的文件。")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='通用社交媒体截图扫描器')
    parser.add_argument('--dir', required=True, help='截图/内容目录路径')
    parser.add_argument('--output', required=True, help='输出文件路径')

    args = parser.parse_args()

    scan_result = scan_directory(args.dir)
    output = format_output(scan_result)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(output)

    total = len(scan_result['images']) + len(scan_result['texts'])
    print(f"已扫描 {total} 个文件（{len(scan_result['images'])} 图片 + {len(scan_result['texts'])} 文本）")
    print(f"结果已写入：{args.output}")


if __name__ == '__main__':
    main()
