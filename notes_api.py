#!/usr/bin/env python3
"""
Hermes Notes API - 笔记系统核心 API
"""
import sqlite3
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "/home/feilong/.hermes/notes/sqlite/notes.db"


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # 写性能优化
    return conn


def init_db():
    """初始化数据库表 + FTS5 全文索引"""
    conn = get_connection()
    cursor = conn.cursor()

    # 创建 notes 主表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source TEXT,
        metadata TEXT
    )
    """)

    # 创建 FTS5 全文索引表（虚拟表）
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
        title, content, tags,
        content='notes',
        content_rowid='id',
        tokenize='unicode61'
    )
    """)

    # 创建触发器：新增笔记时自动同步到 FTS
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
        INSERT INTO notes_fts(rowid, title, content, tags)
        VALUES (new.id, new.title, new.content, coalesce(new.tags, ''));
    END
    """)

    # 创建触发器：更新笔记时自动同步到 FTS
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
        INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
        VALUES ('delete', old.id, old.title, old.content, coalesce(old.tags, ''));
    END
    """)

    # 创建触发器：删除笔记时自动从 FTS 删除
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
        INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
        VALUES ('delete', old.id, old.title, old.content, coalesce(old.tags, ''));
        INSERT INTO notes_fts(rowid, title, content, tags)
        VALUES (new.id, new.title, new.content, coalesce(new.tags, ''));
    END
    """)

    # 创建 tags 标签表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name TEXT UNIQUE NOT NULL,
        color TEXT DEFAULT '#007AFF',
        description TEXT
    )
    """)

    # 创建 note_tags 关联表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS note_tags (
        note_id INTEGER NOT NULL,
        tag_name TEXT NOT NULL,
        PRIMARY KEY (note_id, tag_name),
        FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_name) REFERENCES tags(tag_name) ON DELETE CASCADE
    )
    """)

    conn.commit()

    # 首次初始化时，如果 FTS 表为空但有数据，批量重建
    count = cursor.execute("SELECT COUNT(*) FROM notes_fts").fetchone()[0]
    total = cursor.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    if count == 0 and total > 0:
        rebuild_fts()
    conn.close()


def rebuild_fts():
    """重建 FTS 全文索引"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes_fts(notes_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()


def create_note(title, content, tags=None, source="cli", metadata=None):
    """创建新笔记"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM notes")
    note_id = cursor.fetchone()[0]

    tags_json = json.dumps(tags or [], ensure_ascii=False) if tags else None
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False) if metadata else None

    cursor.execute("""
        INSERT INTO notes (id, title, content, tags, created_at, updated_at, source, metadata)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), ?, ?)
    """, (note_id, title, content, tags_json, source, metadata_json))

    if tags:
        for tag in tags:
            cursor.execute("""
                INSERT OR IGNORE INTO tags (tag_name, color, description)
                VALUES (?, '#007AFF', ?)
            """, (tag, f"笔记标签：{tag}"))
        cursor.executemany("""
            INSERT OR IGNORE INTO note_tags (note_id, tag_name)
            VALUES (?, ?)
        """, [(note_id, tag) for tag in tags])

    conn.commit()
    conn.close()

    # 自动同步到 Vitepress
    try:
        from sync_vitepress import sync_vitepress
        sync_vitepress()
    except Exception:
        pass

    return {
        "id": note_id,
        "title": title,
        "content": content,
        "tags": tags,
        "created_at": datetime.now().isoformat(),
    }


def update_note(note_id, title=None, content=None, tags=None):
    """更新笔记内容"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    new_title = title if title is not None else row["title"]
    new_content = content if content is not None else row["content"]
    new_tags = tags if tags is not None else (json.loads(row["tags"]) if row["tags"] else [])
    tags_json = json.dumps(new_tags, ensure_ascii=False)

    cursor.execute("""
        UPDATE notes SET title=?, content=?, tags=?, updated_at=datetime('now')
        WHERE id=?
    """, (new_title, new_content, tags_json, note_id))

    # 更新关联标签（先删后插）
    cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
    for tag in new_tags:
        cursor.execute("""
            INSERT OR IGNORE INTO tags (tag_name, color, description)
            VALUES (?, '#007AFF', ?)
        """, (tag, f"笔记标签：{tag}"))
        cursor.execute("""
            INSERT OR IGNORE INTO note_tags (note_id, tag_name)
            VALUES (?, ?)
        """, (note_id, tag))

    conn.commit()
    conn.close()

    try:
        from sync_vitepress import sync_vitepress
        sync_vitepress()
    except Exception:
        pass

    return {
        "id": note_id,
        "title": new_title,
        "content": new_content,
        "tags": new_tags,
    }


def get_note(note_id):
    """根据 ID 获取笔记"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "source": row["source"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        }
    return None


def search_notes(query, fields="all", limit=50, offset=0):
    """
    全文搜索笔记（FTS5 增强版）

    参数：
        query: 搜索关键词
        fields: "all"（搜索全部）, "title", "content", "tags"
        limit: 返回条数上限
        offset: 分页偏移量
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 构造 FTS5 查询
    fts_query = query.replace(" ", " OR ")
    if fields == "title":
        sql = """
            SELECT n.*, rank FROM notes_fts f
            JOIN notes n ON n.id = f.rowid
            WHERE notes_fts MATCH ? AND f.title MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, (query, query, limit, offset))
    elif fields == "tags":
        sql = """
            SELECT n.*, rank FROM notes_fts f
            JOIN notes n ON n.id = f.rowid
            WHERE notes_fts MATCH ? AND f.tags MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, (query, query, limit, offset))
    else:
        sql = """
            SELECT n.*, rank FROM notes_fts f
            JOIN notes n ON n.id = f.rowid
            WHERE notes_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, (query, limit, offset))

    rows = cursor.fetchall()
    notes = []
    for row in rows:
        notes.append({
            "id": row["id"],
            "title": row["title"],
            "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"],
            "rank": row["rank"],
        })

    # 如果 FTS5 匹配不到，降级为 LIKE 模糊搜索（兼容中文分词较差的情况）
    if not notes:
        like_pattern = f"%{query}%"
        if fields == "title":
            cursor.execute("""
                SELECT * FROM notes WHERE title LIKE ? ORDER BY created_at DESC
            """, (like_pattern,))
        elif fields == "tags":
            cursor.execute("""
                SELECT * FROM notes WHERE tags LIKE ? ORDER BY created_at DESC
            """, (like_pattern,))
        else:
            cursor.execute("""
                SELECT * FROM notes
                WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                ORDER BY created_at DESC
            """, (like_pattern, like_pattern, like_pattern))
        notes = [
            {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "created_at": row["created_at"],
                "rank": None,
            }
            for row in cursor.fetchall()
        ]

    conn.close()
    return notes


def list_all_notes(limit=100, offset=0):
    """列出所有笔记（按时间倒序），支持分页"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notes ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, (limit, offset))

    rows = cursor.fetchall()
    notes = []
    for row in rows:
        notes.append({
            "id": row["id"],
            "title": row["title"],
            "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "source": row["source"]
        })

    conn.close()
    return notes


def get_note_count():
    """获取笔记总数（用于分页）"""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    conn.close()
    return count


def delete_note(note_id):
    """删除笔记"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if deleted:
        try:
            from sync_vitepress import sync_vitepress
            sync_vitepress()
        except Exception:
            pass

    return deleted


def get_stats():
    """获取统计信息"""
    conn = get_connection()
    stats = {
        "total_notes": conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
        "total_tags": conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0],
    }
    conn.close()
    return stats
