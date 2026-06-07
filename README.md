# 📝 Hermes Notes — 学习笔记系统

> 一个轻量级的个人笔记系统，Python API + SQLite 存储 + Vitepress 静态站点 + GitHub Pages 自动部署。

---

## 系统架构

```
                   ┌──────────────┐
                   │   Terminal   │
                   │  notes_cli   │
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │  notes_api   │
                   │  (Python)    │
                   └──┬───┬───┬───┘
                      │   │   │
          ┌───────────┘   │   └────────────┐
          ▼               ▼                ▼
   ┌──────────┐   ┌────────────┐   ┌──────────────┐
   │ SQLite   │   │sync_vite-  │   │ Email 摘要   │
   │ notes.db │   │press.py    │   │ daily-       │
   └──────────┘   └─────┬──────┘   │ summary      │
                        │          └──────────────┘
                        ▼
                 ┌──────────────┐
                 │ Vitepress    │
                 │ docs/ 站点   │
                 └──────┬───────┘
                        │ git push
                        ▼
                 ┌──────────────┐
                 │ GitHub Pages │
                 │ 自动部署     │
                 └──────────────┘
```

- **SQLite** 是**唯一数据源**
- 创建/更新/删除笔记自动通过 `sync_vitepress()` 同步到 Vitepress
- 推送到 GitHub 后 GitHub Actions 自动构建部署到 GitHub Pages

---

## 文件结构

```
~/.hermes/notes/
├── notes_api.py          # Python API（create/get/search/update/delete）
├── notes_cli.py          # 命令行工具
├── sync_vitepress.py     # Vitepress 站点同步脚本
├── pyproject.toml        # 项目配置
├── .gitignore
├── README.md
├── email_config.json     # 163 SMTP 邮箱配置（权限 600）
├── sqlite/
│   └── notes.db          # SQLite 数据库
├── docs/                 # Vitepress 文档站点
│   ├── .vitepress/
│   │   └── config.ts     # Vitepress 配置（base: /hermes-notes/）
│   ├── index.md          # 首页
│   ├── notes/            # 自动生成的笔记页面（由 sync_vitepress 维护）
│   ├── tags/             # 自动生成的标签页面
│   └── package.json
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions 自动部署
```

配套定时脚本（Hermes 统一管理）：

```
~/.hermes/scripts/
├── daily-summary         # 每日笔记邮件摘要（每天 8:00）
└── token-report          # 每日 Token 用量报告（每天 8:05）
```

---

## 快速开始

### 创建笔记

```python
import sys
sys.path.insert(0, "/home/feilong/.hermes/notes")
from notes_api import create_note

note = create_note(
    title="笔记标题",
    content="笔记内容...",
    tags=["tag1", "tag2"],
    source="cli"          # 来源标记：cli / conversation / assistant
)
print(f"✅ 笔记已创建：ID={note['id']}")
```

```bash
python ~/.hermes/notes/notes_cli.py create "标题" "内容" 标签1 标签2
```

### 读取笔记

```python
from notes_api import get_note
note = get_note(1)
print(note['title'], note['content'])
```

```bash
python ~/.hermes/notes/notes_cli.py read 1
```

### 更新笔记

```python
from notes_api import update_note
result = update_note(1, title="新标题", content="新内容", tags=["new-tag"])
```

### 删除笔记

```python
from notes_api import delete_note
deleted = delete_note(1)  # 返回 True/False
```

### 搜索笔记

```python
from notes_api import search_notes_in_content
notes = search_notes_in_content("关键词")
```

### 列出笔记

```python
from notes_api import list_all_notes
notes = list_all_notes(limit=20)
for n in notes:
    print(f"[{n['id']}] {n['title']} — {n['created_at'][:10]}")
```

### 统计

```python
from notes_api import get_stats
stats = get_stats()
# { total_notes: N, total_tags: N }
```

---

## 完整 API 参考

```python
from notes_api import *

create_note(title, content, tags=None, source="cli", metadata=None)
get_note(note_id)                         # → dict or None
update_note(note_id, title=None, content=None, tags=None)  # → dict
delete_note(note_id)                      # → bool
search_notes_in_content(query)            # → list[dict]
list_all_notes(limit=100)                 # → list[dict]
get_stats()                               # → dict
```

所有写操作（create/update/delete）会自动触发 `sync_vitepress()` 同步到 Vitepress 站点。

---

## 每日定时任务

| 时间 | 脚本 | 说明 | 渠道 |
|------|------|------|------|
| 每天 8:00 | `daily-summary` | 前一天新增笔记摘要 | 微信 + 邮箱 |
| 每天 8:05 | `token-report` | 前一天 Token 用量报告 | 微信 + 邮箱 |

邮箱配置：`email_config.json`（163 SMTP，SSL 465 端口，权限 600）。

---

## Vitepress 文档站点

### 本地预览

```bash
cd ~/.hermes/notes/docs
npm run dev
# 访问 http://localhost:5173/hermes-notes/
```

### 手动同步

```bash
python ~/.hermes/notes/sync_vitepress.py
```

> 通过 API 创建/更新/删除时会**自动同步**，通常不需要手动运行。

---

## GitHub Pages 自动部署

每次推送到 `main` 分支，GitHub Actions 自动执行：

```
git push
  → actions/checkout@v4
  → actions/setup-node@v4（Node 22）
  → npm ci
  → vitepress build
  → upload-pages-artifact
  → deploy-pages@v4
  → https://dragonZ663.github.io/hermes-notes/
```

### 发布流程

```bash
cd ~/.hermes/notes
git add .
git commit -m "📝 新笔记标题"
git push
# 等 1-2 分钟，站点自动更新
```

---

## 特点

- **零外部依赖**：纯 Python 标准库（argparse、sqlite3、json）
- **SQLite 唯一数据源**：无冗余文件，数据一致性保障
- **Vitepress 自动同步**：笔记创建/更新/删除自动同步到 Web 站点
- **GitHub Pages 部署**：推送即上线，零运维成本
- **每日邮件摘要**：自动发送前一日新增笔记
- **每日 Token 报告**：自动统计 Hermes 使用量
- **标签分类**：支持多标签管理 + 自动生成标签页面
- **全文搜索**：Vitepress 内置本地搜索
