# 📝 Hermes Notes - 学习笔记系统

## 🎯 功能概述

这是一个专为 Hermes Agent 用户设计的轻量级笔记系统，支持：
- ✅ 创建/读取/更新/删除笔记
- ✅ 标签管理和分类
- ✅ SQLite 持久化存储
- ✅ Markdown 文件导出
- ✅ 定时自动记录笔记

## 📂 系统文件

| 文件 | 说明 |
|------|------|
| `notes_api.py` | Python API，创建/读取/搜索笔记（创建时自动同步 Vitepress） |
| `notes_cli.py` | 命令行工具，创建/管理笔记 |
| `sync_vitepress.py` | Vitepress 站点同步脚本 |
| `sqlite/notes.db` | SQLite 数据库 |
| `notes/*.md` | Markdown 笔记文件 |
| `docs/` | Vitepress 文档站点（`npm run dev` 启动） |

## 🚀 快速开始

### 1. 创建笔记

**方法 1：Python API**
```python
import sys
sys.path.insert(0, "/home/feilong/.hermes/notes")
from notes_api import create_note

note = create_note(
    title="Hermes Agent 学习笔记",
    content="今天学习了 Hermes Agent 的基础使用...",
    tags=["hermes", "学习"],
    source="api"
)
print(f"✅ 笔记已创建：{note['filename']}")
```

**方法 2：命令行**
```bash
python /home/feilong/.hermes/notes/notes_cli.py create "笔记标题" "笔记内容" [标签]
```

### 2. 读取笔记

**方法 1：Python API**
```python
from notes_api import get_note
note = get_note(note["id"])
print(note['content'])
```

**方法 2：命令行**
```bash
python /home/feilong/.hermes/notes/notes_cli.py read <ID>
```

### 3. 搜索笔记

```python
from notes_api import search_notes_in_content
notes = search_notes_in_content("Hermes")
for note in notes:
    print(note['title'])
```

### 4. 列出笔记

```python
from notes_api import list_all_notes
notes = list_all_notes(10)
for note in notes:
    print(f" - {note['title']}")
```

## 🤖 与 Hermes 集成

### 在 Hermes 会话中创建笔记

**方式 1：直接导入 API**
```python
from notes_api import create_note
create_note(
    title="会话记录",
    content="今天的对话内容...",
    tags=["会话", "记录"],
    source="session"
)
```

**方式 2：使用 hermes_tools**
```python
hermes_tools.python(
    code="""
import sys
sys.path.insert(0, '/home/feilong/.hermes/notes')
from notes_api import create_note
create_note(
    title='学习笔记：' + '学习 Hermes Agent',
    content='今天学习了...',
    tags=['hermes', '学习']
)
"""
)
```

### 定时自动记录（Cronjob）

创建一个定时任务，每小时自动记录一次：

```python
from cronjob import ...
cronjob(
    action="create",
    schedule="1h",  # 每小时一次
    prompt="""
🔵 Hermes Notes Auto-Recorder

📊 自动记录笔记...

调用 cronjob_auto_record.py
"""
)
```

或者使用脚本模式：

```python
cronjob(
    action="create",
    schedule="30m",  # 每 30 分钟
    prompt="/home/feilong/.hermes/notes/cronjob_auto_record.py",
    no_agent=True  # 直接执行脚本
)
```

## 📊 数据持久化

- **SQLite 数据库**: `~/.hermes/notes/sqlite/notes.db`
- **Markdown 文件**: `~/.hermes/notes/*.md`
- **自动备份**: 笔记文件可随时导出或迁移

## 🔧 高级用法

### 标签管理

```python
from notes_api import create_note

# 带标签的笔记
note = create_note(
    title="重要笔记",
    content="...",
    tags=["重要", "待办", "hermes"],
    source="api"
)
```

### 元数据存储

```python
note = create_note(
    title="技术笔记",
    content="...",
    tags=["技术", "hermes"],
    source="api",
    metadata={
        "author": "user",
        "project": "hermes-agent",
        "version": "1.0"
    }
)
```

## 📚 完整 API 参考

```python
from notes_api import *

# 创建笔记
create_note(title, content, tags, source, metadata)

# 获取笔记
get_note(note_id)

# 搜索笔记
search_notes_in_content(query)

# 列出笔记
list_all_notes(limit=100)

# 获取统计
get_stats()
```

## 🎓 学习路线

1. **第 1 天**：学习 Hermes 基础使用
2. **第 2 天**：学习配置管理
3. **第 3 天**：学习工具集管理
4. **第 4 天**：学习定时任务（cronjob）
5. **第 5 天**：学习笔记系统

每个学习笔记都可以记录到笔记系统中！📝

## 🌟 特点

- **轻量级**：纯 Python 实现，无外部依赖
- **持久化**：SQLite + Markdown 文件双重存储
- **可搜索**：支持内容搜索
- **可扩展**：支持元数据和标签
- **集成化**：与 Hermes 平台无缝集成
- **可视化**：Vitepress 文档站点，浏览器内浏览/搜索

---

## 🎨 Vitepress 文档站点

笔记系统内置 Vitepress 文档站点，将所有笔记渲染为精美的静态网站。

### 启动开发服务器

```bash
cd ~/.hermes/notes/docs
npm run dev
```

访问 `http://localhost:5173/` 即可浏览笔记。

### 构建静态站点

```bash
cd ~/.hermes/notes/docs
npm run build
```

构建产物在 `docs/.vitepress/dist/`，可部署到 GitHub Pages、Vercel 等平台。

### 手动同步

```bash
python ~/.hermes/notes/sync_vitepress.py
```

> **注意**：通过 `notes_api.create_note()` 创建笔记时会**自动同步** Vitepress，无需手动操作。

## 📝 示例笔记

```
# 学习笔记 - 第 1 天

今天学习了 Hermes 的基础使用！

1. 安装和配置
2. 基本对话
3. 工具管理

标签：hermes, 学习，day1
```
