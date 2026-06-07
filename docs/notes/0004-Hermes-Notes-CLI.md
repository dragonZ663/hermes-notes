---
id: 4
title: "Hermes Notes CLI"
created: "2026-06-07 07:35:20"
source: "cli"
tags:
  - notes
  - cli
  - architecture
  - analysis
  - usage
---

# Hermes Notes CLI

## Hermes Notes CLI — 整体架构

`hermes-notes` 是一个从终端直接调用的笔记管理命令行工具，采用三层架构：**声明 → 生成包装脚本 → 参数解析与分发**。

### 命令调用链路

```
终端输入
  │
  ▼
hermes-notes 命令 (位于 .venv/bin/hermes-notes)
  │  🡐 pip 根据 pyproject.toml 自动生成的包装脚本
  ▼
from notes_cli import cli_main
sys.exit(cli_main())
  │  🡐 调用开发者写的真正入口函数
  ▼
argparse 解析 sys.argv
  │  🡐 识别子命令和参数
  ▼
路由分发到 cmd_*() 函数
  │  🡐 每个子命令对应一个处理函数
  ▼
notes_api.*() 操作 SQLite → sync_vitepress() → docs/notes/*.md
```

---

### 第一层：pyproject.toml 声明

```toml
[project.scripts]
hermes-notes = "notes_cli:cli_main"
```

- `[project.scripts]` 是 Python 包标准的 **console_scripts 入口点**
- 等号左边 `hermes-notes` 是最终用户在终端输入的命令名
- 等号右边 `"notes_cli:cli_main"` 表示：导入 `notes_cli` 模块，调用其中的 `cli_main` 函数

---

### 第二层：pip 生成的包装脚本

当执行 `uv pip install -e .`（或 `pip install -e .`）时，pip 在虚拟环境的 `bin/` 目录下自动生成一个可执行文件，位于 `.venv/bin/hermes-notes`。

```python
#!/home/feilong/.hermes/notes/.venv/bin/python3
# -*- coding: utf-8 -*-
import sys
from notes_cli import cli_main
if __name__ == "__main__":
    if sys.argv[0].endswith("-script.pyw"):
        sys.argv[0] = sys.argv[0][:-11]
    elif sys.argv[0].endswith(".exe"):
        sys.argv[0] = sys.argv[0][:-4]
    sys.exit(cli_main())
```

#### sys.argv 的含义

`sys.argv` 是 Python 从 Shell 收到的命令行参数列表。例如执行：

```bash
hermes-notes update 4 --title "新标题"
```

`sys.argv` 的值为：

```python
["hermes-notes", "update", "4", "--title", "新标题"]
```

- `sys.argv[0]` = 程序名（`"hermes-notes"`）
- `sys.argv[1]` = 第一个参数（`"update"`）
- 以此类推... 这些参数最终传给 `argparse` 解析。

#### if...elif 平台兼容逻辑

这段代码处理不同平台上可执行文件名后缀的差异，让命令名在帮助信息中显示干净：

| 条件 | 处理 | 场景 |
|---|---|---|
| `sys.argv[0]` 以 `-script.pyw` 结尾 | 去掉这 11 个字符 | Windows 上的 `.pyw` 包装（无控制台窗口） |
| `sys.argv[0]` 以 `.exe` 结尾 | 去掉这 4 个字符 | Windows 上的 `.exe` 包装 |

在 Linux/WSL 下，`sys.argv[0]` 就是 `"hermes-notes"`，两个条件都不命中，直接跳到 `sys.exit(cli_main())`。这段代码对当前环境没有实际影响，只是 pip 自动生成模板为跨平台兼容做的保护。

#### `-e`（editable）模式的意义

安装时加了 `-e` 标志，意味着包装脚本通过 `import` 直接链接到你的源代码目录（`~/.hermes/notes/`），而不是把代码拷贝到 site-packages 里。因此修改 `notes_cli.py` 后**不需要重新安装，改动立即生效**。

---

### 第三层：cli_main() 参数解析与分发

`cli_main` 是 CLI 的真正入口函数，采用 **argparse 子命令分发**架构。

#### 流程概览

```
cli_main()
  │
  ├─ argparse.ArgumentParser 构建参数解析器
  │   └─ 注册 7 个子命令（create/read/search/list/stats/update/delete）
  │
  ├─ parser.parse_args() 解析 sys.argv[1:]（自动剔除程序名）
  │
  └─ args.command 路由分发
       ├─ "create"  → cmd_create(title, content, tags)
       ├─ "read"    → cmd_read(id)
       ├─ "search"  → cmd_search(query)
       ├─ "list"    → cmd_list(limit)
       ├─ "stats"   → cmd_stats()
       ├─ "update"  → cmd_update(id, title, content, tags)
       ├─ "delete"  → cmd_delete(id)
       └─ None      → 打印帮助信息
```

#### 三个主要阶段

**1. 参数定义**
- 使用 `argparse.ArgumentParser` 注册 7 个子命令
- 每个子命令有自己的参数：
  - `create`：title（位置参数）、content（位置参数）、tags（可选，多个）
  - `read`：id（位置参数，整数）
  - `search`：query（位置参数）
  - `list`：--limit（可选，默认 10）
  - `stats`：无参数
  - `update`：id（位置参数）、--title、--content、--tags（均为可选）
  - `delete`：id（位置参数，整数）

**2. 命令分发**
- 通过 `if/elif` 链将 `args.command` 映射到对应的 `cmd_*()` 函数
- 每个 `cmd_*` 函数调用 `notes_api` 中的 API 函数获取数据，再负责格式化输出

**3. 默认兜底**
- 无匹配命令时打印帮助信息和版本信息

---

### 设计特点

- **关注点分离**：CLI 层（`notes_cli.py`）只负责参数解析和输出格式化，数据库/文件操作全部委托给 API 层（`notes_api.py`）
- **跨平台兼容**：pip 自动生成的包装脚本处理了 Windows `.pyw`/`.exe` 和 Linux 的差异
- **可扩展性好**：新增命令只需三步：① 添加 cmd_* 函数 ② 添加子解析器 ③ 添加 elif 分支
- **零外部依赖**：CLI 和 API 层全部使用 Python 标准库（argparse、sqlite3、json、os、re）
- **SQLite 为唯一数据源**：根目录不再生成冗余 .md 文件，全部通过 sync_vitepress() 统一同步到 docs/

---

## 命令行使用指南

`hermes-notes` 命令已注册为系统命令，可直接在终端中使用。共 7 个子命令：

### 创建笔记

```bash
hermes-notes create "标题" "内容" [标签1 标签2 ...]
```

示例：
```bash
hermes-notes create "Python 学习笔记" "Python 是一种解释型语言..." python 学习
hermes-notes create "会议记录" "讨论了 Q3 计划" 会议 工作
```

### 读取笔记

```bash
hermes-notes read <笔记ID>
```

示例：
```bash
hermes-notes read 4
```

### 搜索笔记

```bash
hermes-notes search <关键词>
```

示例：
```bash
hermes-notes search cli_main
```

### 列出笔记

```bash
hermes-notes list [--limit N]
```

示例：
```bash
hermes-notes list            # 列出最近 10 条
hermes-notes list --limit 20 # 列出最近 20 条
```

### 统计信息

```bash
hermes-notes stats
```

### 更新笔记

```bash
hermes-notes update <笔记ID> [--title "新标题"] [--content "新内容"] [--tags 标签1 标签2 ...]
```

支持单独更新标题、内容或标签。示例：
```bash
hermes-notes update 4 --title "新标题"
hermes-notes update 4 --content "更新后的笔记内容"
hermes-notes update 4 --tags python 教程
hermes-notes update 4 --title "新标题" --content "新内容" --tags python 教程
```

### 删除笔记

```bash
hermes-notes delete <笔记ID>
```

示例：
```bash
hermes-notes delete 3
```

### 查看帮助

```bash
hermes-notes --help            # 总帮助
hermes-notes create --help     # 子命令帮助
```

### 备选调用方式

如果在 `~/.hermes/notes` 目录下，也可以用 Python 直接运行：

```bash
cd ~/.hermes/notes
python notes_cli.py create "标题" "内容"
python notes_cli.py list
```
