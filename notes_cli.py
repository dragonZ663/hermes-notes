#!/usr/bin/env python3
"""
Hermes Notes CLI - 命令行工具
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from notes_api import (
    create_note, get_note, search_notes_in_content,
    list_all_notes, get_stats, delete_note, update_note,
    search_notes, get_note_count
)
from datetime import datetime
import json

API_DIR = os.path.dirname(__file__)


def cmd_create(title, content, tags=None, source="cli"):
    """创建笔记"""
    if not title:
        print("❌ 错误：标题不能为空")
        return
    if not content:
        print("❌ 错误：内容不能为空")
        return

    result = create_note(title, content, tags, source)
    print(f"\n✅ 笔记已创建：")
    print(f"   📝 标题：{result['title']}")
    print(f"   🆔 ID: {result['id']}")
    print(f"   ⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   🌐 访问：http://localhost:5173/notes/")


def cmd_read(note_id):
    """读取笔记"""
    note = get_note(note_id)
    if note:
        print(f"\n# {note['title']}\n")
        print("-" * 60)
        print(note['content'])
        print("-" * 60)
        print(f"标签：{', '.join(note['tags']) if note['tags'] else '无'}")
        print(f"来源：{note['source']}")
    else:
        print(f"❌ 笔记不存在：ID {note_id}")


def cmd_search(query, fields="all"):
    """搜索笔记（FTS5 全文搜索）"""
    if len(query) < 2:
        print("🔍 搜索查询至少需要 2 个字符")
        return

    notes = search_notes(query, fields=fields)
    if not notes:
        print(f"❌ 未找到包含 '{query}' 的笔记")
        return

    print(f"\n🔍 找到 {len(notes)} 个结果（FTS5 全文搜索）:\n" + "=" * 60)
    for note in notes:
        tags = ', '.join(note['tags']) if note['tags'] else '无'
        print(f"\n📝 [{note['id']}] {note['title']}")
        print(f"   🏷️  标签：{tags}")
        print(f"   📄 内容：{note['content']}")
        if note.get('rank') is not None:
            print(f"   📊 相关度：{note['rank']:.2f}")


def cmd_list(limit=10, offset=0):
    """列出笔记（支持分页）"""
    notes = list_all_notes(limit, offset)
    total = get_note_count()
    if not notes:
        print("📭 暂无笔记")
        return

    page_end = min(offset + limit, total)
    page_info = f"(第 {offset+1}-{page_end} 条，共 {total} 条)"
    print(f"\n📚 {page_info}\n" + "=" * 60)
    for note in notes:
        print(f"\n📝 [{note['id']}] {note['title']}")
        print(f"   🏷️  标签：{', '.join(note['tags']) if note['tags'] else '无'}")
        print(f"   ⏰ 创建：{note['created_at'][:10]}")
        print(f"   📄 预览：{note['content'][:80]}...")


def cmd_stats():
    """查看统计信息"""
    stats = get_stats()
    print(f"\n📊 笔记系统统计:")
    print(f"   📝 总笔记数：{stats['total_notes']}")
    print(f"   🏷️  标签总数：{stats['total_tags']}")


def cmd_delete(note_id):
    """删除笔记"""
    success = delete_note(note_id)
    if success:
        print(f"✅ 笔记已删除：ID {note_id}")
    else:
        print(f"❌ 笔记不存在：ID {note_id}")


def cmd_update(note_id, title=None, content=None, tags=None):
    """更新笔记"""
    if not title and not content and not tags:
        print("❌ 错误：至少指定一个更新字段（--title / --content / --tags）")
        return

    result = update_note(note_id, title=title, content=content, tags=tags)
    if result:
        print(f"\n✅ 笔记已更新：")
        print(f"   🆔 ID: {result['id']}")
        print(f"   📝 标题：{result['title']}")
        print(f"   🏷️  标签：{', '.join(result['tags']) if result['tags'] else '无'}")
    else:
        print(f"❌ 笔记不存在：ID {note_id}")


def cli_main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Notes CLI v1.1 — FTS5 全文搜索 + 分页")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create", help="创建笔记")
    p_create.add_argument("title", help="笔记标题")
    p_create.add_argument("content", help="笔记内容")
    p_create.add_argument("tags", nargs="*", default=[], help="标签列表")

    p_read = sub.add_parser("read", help="读取笔记")
    p_read.add_argument("id", type=int, help="笔记 ID")

    p_search = sub.add_parser("search", help="搜索笔记（FTS5 全文搜索）")
    p_search.add_argument("query", help="搜索关键词")
    p_search.add_argument("--fields", default="all", choices=["all", "title", "content", "tags"],
                        help="搜索范围：all(全部)/title/content/tags")

    p_list = sub.add_parser("list", help="列出笔记")
    p_list.add_argument("--limit", type=int, default=10, help="数量限制")
    p_list.add_argument("--offset", type=int, default=0, help="分页偏移量")

    p_stats = sub.add_parser("stats", help="统计信息")

    p_delete = sub.add_parser("delete", help="删除笔记")
    p_delete.add_argument("id", type=int, help="笔记 ID")

    p_update = sub.add_parser("update", help="更新笔记")
    p_update.add_argument("id", type=int, help="笔记 ID")
    p_update.add_argument("--title", help="新标题")
    p_update.add_argument("--content", help="新内容")
    p_update.add_argument("--tags", nargs="*", default=None, help="新标签列表")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args.title, args.content, args.tags)
    elif args.command == "read":
        cmd_read(args.id)
    elif args.command == "search":
        cmd_search(args.query, args.fields)
    elif args.command == "list":
        cmd_list(args.limit, args.offset)
    elif args.command == "stats":
        cmd_stats()
    elif args.command == "delete":
        cmd_delete(args.id)
    elif args.command == "update":
        cmd_update(args.id, title=args.title, content=args.content, tags=args.tags)
    else:
        print("🔵 Hermes Notes CLI v1.1 — FTS5 全文搜索 + 分页")
        parser.print_help()


if __name__ == "__main__":
    cli_main()
