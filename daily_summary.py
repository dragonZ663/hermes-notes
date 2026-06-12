#!/usr/bin/env python3
"""
每日笔记邮件摘要 — 查询当天新增笔记，总结后发送邮件

使用方式：
    直接运行（发送当天摘要）：
        python daily_summary.py
    
    通过 Hermes cronjob 定时运行：
        cronjob(action="create", schedule="0 22 * * *", script="daily_summary.py", no_agent=True)
"""

import smtplib
from email.mime.text import MIMEText
from email.header import Header
import sqlite3
import json
import os
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

# ---------- 路径 ----------
HOME_NOTES = Path(os.path.expanduser("~/.hermes/notes"))
DB_PATH = HOME_NOTES / "sqlite" / "notes.db"
CONFIG_PATH = HOME_NOTES / "email_config.json"


def load_config():
    """加载邮箱配置"""
    if not CONFIG_PATH.exists():
        print(f"❌ 配置文件不存在：{CONFIG_PATH}")
        print("   请创建 email_config.json，格式：")
        print('   {"smtp_host":"smtp.163.com","smtp_port":465,')
        print('    "from_email":"xxx@163.com","password":"授权码",')
        print('    "to_email":"xxx@163.com"}')
        return None
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_today_notes():
    """查询当天创建的笔记"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM notes 
        WHERE date(created_at) = date('now', 'localtime', '-1 day')
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    notes = []
    for row in rows:
        notes.append({
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"],
            "source": row["source"] or "",
        })
    conn.close()
    return notes


def build_summary_html(notes):
    """生成 HTML 格式的邮件摘要"""
    today = date.today().isoformat()

    if not notes:
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body>
<div style="max-width:640px;margin:40px auto;font-family:system-ui,sans-serif;text-align:center;padding:40px;background:#f9fafb;border-radius:12px;">
    <h2 style="color:#666;">📭 今日无新笔记</h2>
    <p style="color:#999;">{today}</p>
</div>
</body></html>"""

    # 标签统计
    tag_count = defaultdict(int)
    for note in notes:
        for tag in note.get("tags", []):
            tag_count[tag] += 1

    tags_html = "".join(
        f'<span style="display:inline-block;background:#e8f4fd;padding:2px 10px;'
        f'margin:2px;border-radius:12px;font-size:13px;">'
        f'{tag}({count})</span>'
        for tag, count in sorted(tag_count.items(), key=lambda x: -x[1])
    )

    # 笔记列表
    notes_html = ""
    for i, note in enumerate(notes, 1):
        preview = note["content"][:200] + ("..." if len(note["content"]) > 200 else "")
        tags = " ".join(f"#{t}" for t in note.get("tags", []))
        notes_html += f"""
        <div style="margin-bottom:20px;padding:16px;background:#f9fafb;border-radius:8px;border-left:4px solid #3b82f6;">
            <h3 style="margin:0 0 8px 0;font-size:16px;">{i}. {note['title']}</h3>
            <div style="font-size:13px;color:#666;margin-bottom:8px;">
                <span>🕐 {note['created_at'][:19]}</span>
                <span style="margin-left:12px;">📎 {note['source']}</span>
            </div>
            <div style="margin-bottom:6px;font-size:13px;">{tags}</div>
            <pre style="font-size:13px;color:#333;background:#fff;padding:12px;border-radius:4px;overflow-x:auto;white-space:pre-wrap;word-break:break-all;">{preview}</pre>
        </div>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body>
<div style="max-width:640px;margin:0 auto;font-family:system-ui,sans-serif;">
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:24px;">📝 每日笔记摘要</h1>
        <p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;">{today} · 共 {len(notes)} 篇新笔记</p>
    </div>
    <div style="padding:24px;background:#fff;border:1px solid #e5e7eb;border-radius:0 0 12px 12px;">
        <div style="margin-bottom:24px;padding:16px;background:#f0fdf4;border-radius:8px;">
            <strong>📊 今日统计</strong>
            <div style="margin-top:8px;font-size:14px;color:#333;">
                新增笔记：<strong>{len(notes)}</strong> 篇<br><br>
                标签分布：<br>{tags_html}
            </div>
        </div>
        <h2 style="font-size:18px;border-bottom:2px solid #e5e7eb;padding-bottom:8px;">📄 详细内容</h2>
        {notes_html}
    </div>
    <div style="text-align:center;padding:16px;font-size:12px;color:#999;">
        <p>由 Hermes Notes 自动生成</p>
    </div>
</div>
</body></html>"""


def send_email(html_content, config):
    """通过 SMTP 发送邮件"""
    msg = MIMEText(html_content, "html", "utf-8")
    msg["From"] = f"Hermes Notes <{config['from_email']}>"
    msg["To"] = config["to_email"]
    msg["Subject"] = Header(f"📝 每日笔记摘要 - {date.today().isoformat()}", "utf-8")

    with smtplib.SMTP_SSL(config["smtp_host"], config["smtp_port"]) as server:
        server.login(config["from_email"], config["password"])
        server.send_message(msg)

    return True


def main():
    print(f"🔵 Hermes Notes - 每日邮件摘要")
    print(f"📅 日期：{date.today().isoformat()}")
    print()

    # 加载配置
    config = load_config()
    if not config:
        return 1

    # 查询笔记
    print(f"📝 正在查询当日笔记...")
    notes = get_today_notes()
    print(f"   找到 {len(notes)} 篇新笔记\n")

    # 生成摘要
    print(f"📄 正在生成 HTML 摘要...")
    html = build_summary_html(notes)
    preview_len = len(notes[0]["content"]) if notes else 0
    print(f"   摘要已生成（{len(html)} 字节）\n")

    # 发送邮件
    print(f"📧 正在发送邮件至 {config['to_email']}...")
    send_email(html, config)
    print(f"✅ 邮件发送成功！\n")

    print(f"📊 摘要包含 {len(notes)} 篇笔记")
    if notes:
        print(f"   最新：{notes[0]['title']}")
    return 0


if __name__ == "__main__":
    exit(main())
