#!/usr/bin/env python3
"""
sync_vitepress.py — 将 SQLite 笔记同步到 Vitepress 文档站点

用法:
    python sync_vitepress.py          # 同步所有笔记
    python sync_vitepress.py --build  # 同步后自动 vitepress build
"""

import sqlite3
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 路径配置
HERMES_NOTES = Path("/home/feilong/.hermes/notes")
DB_PATH = HERMES_NOTES / "sqlite" / "notes.db"
DOCS_DIR = HERMES_NOTES / "docs"
NOTES_OUT = DOCS_DIR / "notes"
TAGS_OUT = DOCS_DIR / "tags"
SIDEBAR_PATH = DOCS_DIR / ".vitepress" / "sidebar.json"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_all_notes():
    """从 SQLite 读取所有笔记"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
    rows = cursor.fetchall()
    notes = []
    for row in rows:
        notes.append({
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "source": row["source"] or "",
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        })
    conn.close()
    return notes


def get_tag_stats(notes):
    """统计每个标签下的笔记数"""
    tag_notes = defaultdict(list)
    for note in notes:
        for tag in note.get("tags", []):
            tag_notes[tag].append(note)
    return dict(sorted(tag_notes.items()))


def strip_leading_h1(content, title):
    """如果内容开头有和标题重复的 H1，去掉它（防御性去重）"""
    lines = content.split("\n")
    cleaned = []
    seen_h1 = False
    for line in lines:
        stripped = line.strip()
        if not seen_h1 and stripped.startswith("# ") and stripped[2:].strip() == title:
            seen_h1 = True
            continue
        if not seen_h1 and stripped == "":
            continue
        cleaned.append(line)
    return "\n".join(cleaned) if seen_h1 else content


def generate_note_files(notes):
    """为每篇笔记生成 Vitepress markdown 文件"""
    # 清空旧文件，防止残留
    if NOTES_OUT.exists():
        for f in NOTES_OUT.iterdir():
            if f.name != "index.md":  # index.md 由 generate_notes_index 生成
                f.unlink()
    NOTES_OUT.mkdir(parents=True, exist_ok=True)

    for note in notes:
        note_id = note["id"]
        title = note["title"]
        content = note["content"]
        tags = note.get("tags", [])
        created = note.get("created_at", "")
        source = note.get("source", "")

        # 防御性去重：如果内容以 # title 开头，去掉它
        content = strip_leading_h1(content, title)

        # 安全文件名
        slug = re.sub(r'[<>:"/\\|?*\s]+', '-', title)[:60].strip('-')
        filename = f"{note_id:04d}-{slug}.md"
        filepath = NOTES_OUT / filename

        # Vitepress frontmatter
        tags_yaml = "\n".join(f"  - {t}" for t in tags) if tags else ""
        frontmatter = f"""---
id: {note_id}
title: "{title}"
created: "{created}"
source: "{source}"
tags:
{tags_yaml}
---

"""

        md = frontmatter + f"# {title}\n\n" + content
        filepath.write_text(md, encoding="utf-8")

    return len(notes)


def generate_notes_index(notes):
    """生成笔记总览页"""
    lines = [
        "# 📝 所有笔记",
        "",
        f"共 **{len(notes)}** 篇笔记。",
        "",
        "| # | 标题 | 标签 | 日期 |",
        "|---|------|------|------|"
    ]

    for i, note in enumerate(notes, 1):
        note_id = note["id"]
        title = note["title"]
        tags = note.get("tags", [])
        created = note.get("created_at", "")[:10]

        slug = re.sub(r'[<>:"/\\|?*\s]+', '-', title)[:60].strip('-')
        note_link = f"/notes/{note_id:04d}-{slug}"
        tag_badges = " ".join(f"`{t}`" for t in tags) if tags else "-"

        lines.append(f"| {i} | [{title}]({note_link}) | {tag_badges} | {created} |")

    (NOTES_OUT / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_tag_pages(notes, tag_stats):
    """生成标签页面"""
    # 清空旧标签文件
    if TAGS_OUT.exists():
        for f in TAGS_OUT.iterdir():
            if f.name != "index.md":
                f.unlink()
    TAGS_OUT.mkdir(parents=True, exist_ok=True)

    # 标签总览页（按小写 slug 去重，避免大小写冲突）
    seen_slugs = set()
    tag_index_items = []
    for tag, tag_notes in tag_stats.items():
        tag_slug = re.sub(r'[\s]+', '-', tag).lower()
        if tag_slug not in seen_slugs:
            seen_slugs.add(tag_slug)
            tag_index_items.append((tag, tag_slug, len(tag_notes)))

    lines = [
        "# 🏷️ 标签分类",
        "",
        f"共 **{len(tag_index_items)}** 个标签，**{len(notes)}** 篇笔记。",
        "",
        "| 标签 | 笔记数 |",
        "|------|--------|"
    ]
    for tag, tag_slug, count in tag_index_items:
        lines.append(f"| [{tag}](/tags/{tag_slug}) | {count} |")

    (TAGS_OUT / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 每个标签的独立页面（按小写合并）
    merged = {}
    for tag, tag_notes in tag_stats.items():
        tag_slug = re.sub(r'[\s]+', '-', tag).lower()
        if tag_slug not in merged:
            merged[tag_slug] = {"display": tag, "notes": []}
        merged[tag_slug]["notes"].extend(tag_notes)

    for tag_slug, info in merged.items():
        tag_lines = [
            f"# 🏷️ {info['display']}",
            "",
            f"共 **{len(info['notes'])}** 篇笔记。",
            "",
            "| # | 标题 | 日期 |",
            "|---|------|------|"
        ]
        for i, note in enumerate(info["notes"], 1):
            note_id = note["id"]
            title = note["title"]
            slug = re.sub(r'[<>:"/\\|?*\s]+', '-', title)[:60].strip('-')
            created = note.get("created_at", "")[:10]
            note_link = f"/notes/{note_id:04d}-{slug}"
            tag_lines.append(f"| {i} | [{title}]({note_link}) | {created} |")

        (TAGS_OUT / f"{tag_slug}.md").write_text("\n".join(tag_lines) + "\n", encoding="utf-8")


def generate_sidebar(notes, tag_stats):
    """生成 Vitepress 侧边栏配置"""
    sidebar = []

    # 最新笔记（前 10 篇）
    recent_items = []
    for note in notes[:10]:
        title = note["title"]
        slug = re.sub(r'[<>:"/\\|?*\s]+', '-', title)[:60].strip('-')
        note_id = note["id"]
        recent_items.append({
            "text": title[:30] + ("..." if len(title) > 30 else ""),
            "link": f"/notes/{note_id:04d}-{slug}"
        })
    sidebar.append({"text": "📝 最新笔记", "collapsed": False, "items": recent_items})

    # 标签分类（小写 slug，避免大小写冲突）
    tag_items = [{"text": "🏷️ 标签总览", "link": "/tags/"}]
    seen_slugs = set()
    for tag in list(tag_stats.keys())[:30]:
        tag_slug = re.sub(r'[\s]+', '-', tag).lower()
        if tag_slug in seen_slugs:
            continue
        seen_slugs.add(tag_slug)
        count = len(tag_stats[tag])
        tag_items.append({
            "text": f"{tag} ({count})",
            "link": f"/tags/{tag_slug}"
        })
    sidebar.append({"text": "🏷️ 标签分类", "collapsed": True, "items": tag_items})

    # 笔记总览
    sidebar.append({"text": "📋 笔记总览", "link": "/notes/"})

    SIDEBAR_PATH.write_text(
        json.dumps(sidebar, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_homepage_stats(notes):
    """更新首页的统计信息"""
    stats_html = f"""---
layout: home

hero:
  name: "Hermes Notes"
  text: "个人学习笔记"
  tagline: 由 Hermes Agent 驱动的知识库 · 共 {len(notes)} 篇笔记
  actions:
    - theme: brand
      text: 浏览笔记
      link: /notes/
    - theme: alt
      text: 按标签查看
      link: /tags/

features:
  - icon: 📝
    title: 自动记录
    details: Hermes 对话内容自动转化为结构化笔记，无需手动整理
  - icon: 🔍
    title: 全文搜索
    details: 内置本地搜索，快速定位任何知识点
  - icon: 🏷️
    title: 标签分类
    details: 按标签组织笔记，构建个人知识图谱
  - icon: ⚡
    title: 即时同步
    details: 笔记创建后自动同步到文档站点，所见即所得
---
"""
    (DOCS_DIR / "index.md").write_text(stats_html, encoding="utf-8")


def sync_vitepress():
    """主同步流程（先清理旧文件，再全量生成）"""
    print("🔄 正在同步笔记到 Vitepress...")

    notes = get_all_notes()
    tag_stats = get_tag_stats(notes)

    print(f"   📝 找到 {len(notes)} 篇笔记，{len(tag_stats)} 个标签")

    n_files = generate_note_files(notes)
    print(f"   📄 生成 {n_files} 个笔记文件")

    generate_notes_index(notes)
    print("   📋 生成笔记总览页")

    generate_tag_pages(notes, tag_stats)
    print("   🏷️ 生成标签页面")

    generate_sidebar(notes, tag_stats)
    print("   📑 生成侧边栏配置")

    update_homepage_stats(notes)
    print("   🏠 更新首页")

    print("✅ 同步完成！")
    print(f"\n   运行文档站点: cd {DOCS_DIR} && npm run dev")
    print(f"   构建静态站点: cd {DOCS_DIR} && npm run build")


if __name__ == "__main__":
    import sys
    sync_vitepress()

    if "--build" in sys.argv:
        import subprocess
        print("\n🔨 正在构建静态站点...")
        subprocess.run(["npm", "run", "build"], cwd=str(DOCS_DIR))
