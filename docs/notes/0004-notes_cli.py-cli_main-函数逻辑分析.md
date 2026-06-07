---
id: 4
title: "notes_cli.py cli_main 函数逻辑分析"
created: "2026-06-07 07:35:20"
source: "cli"
tags:
  - notes
  - cli
  - architecture
  - analysis
  - usage
---

# notes_cli.py cli_main 函数逻辑分析

## `cli_main()` 核心逻辑

`cli_main` 是 Hermes Notes CLI 的入口函数，采用 **argparse 子命令分发**架构。

### 流程概览

```
cli_main()
  │
  ├─ argparse.ArgumentParser 构建参数解析器
  │   └─ 注册 6 个子命令（create/read/search/list/stats/delete）
  │
  ├─ parser.parse_args() 解析命令行参数
  │
  └─ args.command 路由分发
       ├─ "create"  → cmd_create(title, content, tags)
       ├─ "read"    → cmd_read(id)
       ├─ "search"  → cmd_search(query)
       ├─ "list"    → cmd_list(limit)
       ├─ "stats"   → cmd_stats()
       ├─ "delete"  → cmd_delete(id)
       └─ None      → 打印帮助信息
```

### 三个主要阶段

**1. 参数定义（第 121-143 行）**
- 使用 `argparse.ArgumentParser` 注册 6 个子命令
- 每个子命令有自己的参数：create（title/content/tags）、read（id）、search（query）、list（--limit=10）、stats（无参数）、delete（id）

**2. 命令分发（第 145-159 行）**
- 通过 `if/elif` 链将 `args.command` 映射到对应的 `cmd_*()` 函数
- 每个 `cmd_*` 函数调用 `notes_api` 中的 API 函数获取数据，再负责格式化输出

**3. 默认兜底（第 157-159 行）**
- 无匹配命令时打印帮助信息

### 设计特点
- 清晰的关注点分离：CLI 层只负责参数解析和输出格式化，数据库操作委托给 notes_api 层
- 可扩展性好：新增命令只需添加子解析器和对应的 cmd_* 函数
- 注意：之前 cmd_delete 直接操作 SQLite（已修复），是设计瑕疵

## 命令行使用指南

`hermes-notes` 命令已注册为系统命令，可直接在终端中使用。共 6 个子命令：

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
