---
id: 14
title: "python -c 与 Heredoc：Python 命令行执行方式详解"
created: "2026-06-11 15:22:20"
source: "conversation"
tags:
  - python
  - shell
  - cli
---

# python -c 与 Heredoc：Python 命令行执行方式详解

# python -c 与 Heredoc：Python 命令行执行方式详解

## 一、`python -c` — 命令行直接执行

### 语法

```bash
python -c "代码"
python3 -c "代码"
```

`-c` = **command**，意思是从命令行参数直接执行 Python 代码。

### 基础示例

```bash
python3 -c "print('hello world')"
# 输出: hello world
```

### 多条语句用 `;` 分隔

```bash
python3 -c "x = 42; y = x * 2; print(y)"
```

### 单引号内嵌双引号更省事

```bash
python3 -c 'print("hello")'
```

### 配合管道

```bash
python3 -c "import json; print(json.dumps({'a': 1}))" | jq .
```

### 各语言对比

| 语言 | 命令 |
|------|------|
| Python | `python -c "代码"` |
| Node.js | `node -e "代码"` |
| Ruby | `ruby -e "代码"` |
| Bash | `bash -c "命令"` |

### 适用场景

- **单行代码**或**短代码块**，快速验证想法
- 一次性计算或输出
- 配合管道做数据处理

---

## 二、`sys.path.insert()` vs `PYTHONPATH`

很多人会把代码里的 `sys.path.insert(0, xxx)` 当成设 `PYTHONPATH`，其实是两回事。

### `sys.path.insert(0, xxx)`

```python
import sys
sys.path.insert(0, "/home/feilong/.hermes/notes/")
```

直接在当前 Python 进程的模块搜索列表**最前面**插入一个路径，之后 `import` 会优先从那里找。

### `PYTHONPATH` 环境变量

```bash
export PYTHONPATH="/home/feilong/.hermes/notes/"
python3 my_script.py
```

Python 启动时自动把 `PYTHONPATH` 的值追加到 `sys.path` 里。

### 核心区别

| 对比维度 | `sys.path.insert(0, ...)` | `PYTHONPATH` 环境变量 |
|----------|--------------------------|----------------------|
| **作用范围** | 仅当前 Python 进程 | 该 shell 下启动的所有 Python 进程 |
| **生效时机** | 运行时动态添加 | 解释器启动时自动加载 |
| **插入位置** | 可控制（`insert(0)` → 最前面） | 默认在 `sys.path` 第二个位置 |
| **是否需要改代码** | 需要写 `.py` 文件里 | 不需要，设环境变量即可 |
| **持久化** | 每次运行都要写 | 可写入 `~/.bashrc` |

### 为什么代码里要写 `sys.path.insert(0, ...)`

`launch.json` 里的 `PYTHONPATH` **只在 VSCode 调试时生效**。终端直接跑 `python3` 时没有那个环境变量。所以代码里写 `sys.path.insert()` 相当于**兜底操作**——不管有没有设 `PYTHONPATH`，都能找到需要的模块。

**一句话总结：** `PYTHONPATH` 是"起跑前告诉 Python 去哪找"；`sys.path.insert()` 是"跑起来之后临时加一条路"。效果类似，但前者是外部环境变量，后者是代码里的兜底操作。

---

## 三、Heredoc（Here Document）

### 基本用法

```bash
python3 <<EOF
print("hello")
x = 42
print(x * 2)
EOF
```

`<<EOF` 和 `EOF` 之间的内容被**当作标准输入**喂给 `python3`。

### 引号的作用

| 写法 | 效果 |
|------|------|
| `<<EOF` | **解析变量** — `$HOME`、`$PATH` 会被替换成实际值 |
| `<<'EOF'` | **原样输出** — `$HOME` 就是字符串，不做变量替换 |
| `<<"EOF"` | 同 `<<'EOF'` |
| `<<\EOF` | 同 `<<'EOF'` |

### 示例对比

```bash
# 不加引号 — 变量被替换
python3 <<EOF
import os
print(os.environ.get("HOME"))
EOF
# 输出: /home/feilong

# 加引号 — 原样
python3 <<'EOF'
print("$HOME")
EOF
# 输出: $HOME
```

### Heredoc vs `-c`

| 方式 | 适用场景 |
|------|----------|
| `python -c "..."` | **单行或短代码**，用引号搞定 |
| `python3 <<EOF` | **多行代码**，不用操心引号嵌套和转义 |

Heredoc 里双引号、单引号、反引号随便用，**不用操心引号打架**。

### 其他语言也用

```bash
# Node.js
node << 'EOF'
console.log("hello");
EOF

# Ruby
ruby << 'EOF'
puts "hello"
EOF
```

**一句话总结：** Heredoc 就是 shell 里的多行字符串输入，用 `<<` 定界符把一大段代码原样送给命令执行，加引号是纯文本，不加会展开变量。

---

## 四、三种方式对比总结

| 方式 | 适合场景 | 优点 | 缺点 |
|------|----------|------|------|
| `python -c` | 单行/短代码 | 简洁快速，适合管道 | 多行要 `;` 分隔，引号容易打架 |
| `python < script.py` | 已有脚本文件 | 完整 IDE 支持 | 需要额外文件 |
| `python <<EOF` | 多行代码 | 引号随便用，适合临时多行脚本 | 不利于复用 |

## 实际使用建议

- **一行搞定的** → `python -c`
- **三五行以上的临时脚本** → `python << 'EOF'`
- **需要反复用/调试的** → 写 `.py` 文件
