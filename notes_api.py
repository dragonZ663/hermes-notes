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
    return conn


def init_db():
    """初始化数据库表"""
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


def create_note(title, content, tags=None, source="cli", metadata=None):
    """创建新笔记"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 生成唯一 ID
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM notes")
    note_id = cursor.fetchone()[0]
    
    tags_json = json.dumps(tags or [], ensure_ascii=False) if tags else None
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False) if metadata else None
    
    cursor.execute("""
        INSERT INTO notes (id, title, content, tags, created_at, updated_at, source, metadata)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), ?, ?)
    """, (note_id, title, content, tags_json, source, metadata_json))
    
    # 插入标签
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

    # 自动同步到 Vitepress 文档站点
    try:
        from sync_vitepress import sync_vitepress
        sync_vitepress()
    except Exception:
        pass  # Vitepress 同步失败不影响笔记创建

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
    
    # 获取现有笔记
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    # 只更新提供的字段
    new_title = title if title is not None else row["title"]
    new_content = content if content is not None else row["content"]
    new_tags = tags if tags is not None else (json.loads(row["tags"]) if row["tags"] else [])
    tags_json = json.dumps(new_tags, ensure_ascii=False)
    
    cursor.execute("""
        UPDATE notes SET title=?, content=?, tags=?, updated_at=datetime('now')
        WHERE id=?
    """, (new_title, new_content, tags_json, note_id))
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
    conn.close()
    return None


def search_notes_in_content(query):
    """在笔记内容中搜索"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notes WHERE content LIKE ? ORDER BY created_at DESC
    """, (f"%{query}%",))
    
    rows = cursor.fetchall()
    notes = []
    for row in rows:
        notes.append({
            "id": row["id"],
            "title": row["title"],
            "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"]
        })
    
    conn.close()
    return notes


def list_all_notes(limit=100):
    """列出所有笔记（按时间倒序）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notes ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    
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


def delete_note(note_id):
    """删除笔记（数据库记录 + 自动同步 Vitepress）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if deleted:
        # 自动同步 Vitepress，docs/ 中的文件会被重建（被删的笔记自然消失）
        try:
            from sync_vitepress import sync_vitepress
            sync_vitepress()
        except Exception:
            pass

    return deleted


def get_stats():
    """获取统计信息"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {
        "total_notes": cursor.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
        "total_tags": cursor.execute("SELECT COUNT(*) FROM tags").fetchone()[0],
    }
    
    conn.close()
    return stats
