#!/usr/bin/env python3
"""
Hermes Notes Demo - 演示脚本
展示笔记系统的完整功能
"""

import sys
sys.path.insert(0, "/home/feilong/.hermes/notes")

from notes_api import (
    create_note, get_note,
    search_notes_in_content,
    list_all_notes, get_stats
)
from datetime import datetime

print("\n" + "=" * 60)
print("🔵 Hermes Notes Demo - 演示脚本")
print("=" * 60)

# 1. 统计信息
print("\n📊 1. 统计信息")
print("-" * 40)
stats = get_stats()
print(f"总笔记数：{stats['total_notes']}")
print(f"标签总数：{stats['total_tags']}")

# 2. 创建笔记
print("\n📝 2. 创建笔记")
print("-" * 40)

note1 = create_note(
    title="Hermes Agent 学习笔记",
    content="今天开始学习 Hermes Agent！\n\n1. 基础使用\n2. 配置管理\n3. 工具管理",
    tags=["学习", "hermes"],
    source="demo"
)
print(f"✅ 笔记 1 已创建")
print(f"   标题：{note1['title']}")
print(f"   ID: {note1['id']}")

# 3. 创建第二个笔记
print("\n📝 3. 创建第二个笔记")
print("-" * 40)

note2 = create_note(
    title="Python 代码示例",
    content="# 一个简单的 Python 函数\ndef greet(name):\n    return f'Hello, {name}!'\nprint(greet('Hermes'))",
    tags=["代码", "python"],
    source="demo"
)
print(f"✅ 笔记 2 已创建")
print(f"   标题：{note2['title']}")
print(f"   ID: {note2['id']}")

# 4. 读取笔记
print("\n📖 4. 读取笔记")
print("-" * 40)
note = get_note(note1["id"])
print(f"标题：{note['title']}")
print(f"内容：{note['content']}")
print(f"标签：{', '.join(note['tags']) if note['tags'] else '无'}")

# 5. 搜索笔记
print("\n🔍 5. 搜索笔记")
print("-" * 40)
search_result = search_notes_in_content("学习")
print(f"搜索关键词：'学习'")
print(f"找到 {len(search_result)} 条结果")

# 6. 列出所有笔记
print("\n📚 6. 列出所有笔记")
print("-" * 40)
notes = list_all_notes()
for note in notes:
    print(f"  • {note['title']} - {note['created_at'][:10]}")

# 7. 更新统计信息
print("\n📊 7. 更新统计")
print("-" * 40)
stats = get_stats()
print(f"总笔记数：{stats['total_notes']}")

print("\n" + "=" * 60)
print("✅ Demo 演示完成！")
print("=" * 60)
print("\n📁 系统文件:")
print("   API:  /home/feilong/.hermes/notes/notes_api.py")
print("   CLI:  /home/feilong/.hermes/notes/notes_cli.py")
print("   Cron: /home/feilong/.hermes/notes/cronjob_auto_record.py")
print("   DB:   /home/feilong/.hermes/notes/sqlite/notes.db")
print("   Notes:/home/feilong/.hermes/notes/*.md")
print("\n🎓 现在你可以开始记录学习笔记了！")
print("=" * 60 + "\n")
