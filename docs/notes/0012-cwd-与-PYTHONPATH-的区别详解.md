---
id: 12
title: "cwd 与 PYTHONPATH 的区别详解"
created: "2026-06-11 08:18:23"
source: "conversation"
tags:
  - python
  - vscode
  - debugging
---

# cwd 与 PYTHONPATH 的区别详解

# cwd 与 PYTHONPATH 的区别详解

可以把它们理解成两个**完全不同层面的东西**：

- **`cwd`**：决定**程序从哪一个目录"开始看世界"**
- **`PYTHONPATH`**：决定 **Python 去哪些目录里找模块/包**

它们经常一起出现，所以容易混淆，但职责不一样。

---

## `cwd`（Current Working Directory）

当前工作目录。

**影响范围：**
- 相对路径文件读写
- 某些工具默认查找配置文件的位置
- `Path.cwd()` / `os.getcwd()` 的结果

### 示例

在 `launch.json` 中：
```json
"cwd": "${workspaceFolder}"
```
意味着运行调试程序时，把当前工作目录设置成项目根目录。

当代码里写：
```python
open("config.yaml")
```
Python 会从 `cwd` 开始找：`/path/to/Webwright/config.yaml`

```python
Path("outputs/result.json")
```
会被解释成：`/path/to/Webwright/outputs/result.json`

### 依赖 cwd 的常见场景
- 读取 `.env`
- 读取相对路径配置文件
- 查找日志目录
- pytest 查找配置
- 一些 CLI 的默认行为

**如果不设置 `cwd`**，VSCode 可能从别的目录启动，导致配置文件找不到、输出目录跑偏、"同样代码在终端能跑，在 VSCode 里不行"等问题。

---

## PYTHONPATH

告诉 Python：**除了默认路径外，还要去哪些目录里找 `import` 的模块**。

**影响范围：**
- `import webwright`
- `from xxx import yyy`
- 模块能不能被 Python 找到

### 示例

在 `launch.json` 中：
```json
"env": {
  "PYTHONPATH": "${workspaceFolder}/src"
}
```

对于 `src/` 布局的项目：
```bash
Webwright/
├── src/
│   └── webwright/
│       ├── __init__.py
│       └── main.py
```

如果没有 `PYTHONPATH=${workspaceFolder}/src`，Python 找不到 `import webwright`，会报 `ModuleNotFoundError`。

`PYTHONPATH` 的作用本质上是把某些目录提前/额外放进 `sys.path`。可以通过以下代码查看：
```python
import sys
from pprint import pprint
pprint(sys.path)
```

---

## 两者的核心区别

| 维度 | cwd | PYTHONPATH |
|------|-----|------------|
| 管什么 | 相对路径从哪里算起 | import 的模块去哪里找 |
| 典型问题 | 文件找不到（config.yaml 找不到、输出到奇怪位置） | 模块导入失败（ModuleNotFoundError） |
| 影响的代码 | `open("config.yaml")`, `Path("outputs")` | `import webwright`, `from xxx import yyy` |
| 查看方式 | `os.getcwd()` / `Path.cwd()` | `sys.path` |

---

## 直观比喻

把 Python 程序想象成一个人：

**`cwd`** — "你现在站在哪个房间里"。你说"帮我拿桌上的文件"，得先知道你站在哪个房间。

**`PYTHONPATH`** — "你查地图时允许搜索哪些仓库/图书馆"。你说"帮我找到 webwright 这个包"，Python 就要去一堆目录里找。

---

## 常见误区

### 误区 1：cwd 能解决 import 问题
**不一定。** `src/` 布局的项目，即使 `cwd` 设对了，`import webwright` 仍然可能失败，因为 `webwright` 的父目录（`src/`）需要出现在 `sys.path` 里。

### 误区 2：设置了 PYTHONPATH 就能控制相对路径
**不能。** `open("config.yaml")` 仍然看的是 `cwd`，不是 `PYTHONPATH`。

### 误区 3：两者二选一就够了
很多项目里**两个都要配**：`cwd` 保证文件路径逻辑稳定，`PYTHONPATH` 保证 import 稳定。特别是 `src/` 布局的 Python 项目，这非常常见。

---

## 在 VSCode launch.json 中的实际配置

```json
"cwd": "${workspaceFolder}",
"justMyCode": false,
"env": {
  "PYTHONPATH": "${workspaceFolder}/src",
  "WORKSPACE_DIR": "${workspaceFolder}",
  "WEBWRIGHT_OUTPUT_DIR": "/var/tmp/webwright-outputs"
}
```

逐项解读：
- **`cwd`**：程序从项目根目录启动，相对路径稳定
- **`PYTHONPATH`**：让 Python 能正确找到 `src/webwright`，避免 `ModuleNotFoundError`
- **`WORKSPACE_DIR`** / **`WEBWRIGHT_OUTPUT_DIR`**：项目自定义环境变量，代码通过 `os.environ` 读取

---

## 快速判断法

以后遇到问题就问自己：

> **问题是"文件找不到"吗？**（config.yaml 找不到、截图输出位置不对） → 优先看 **`cwd`**
>
> **问题是"模块导入失败"吗？**（`ModuleNotFoundError`、`import xxx` 失败） → 优先看 **`PYTHONPATH`**

---

## 一句话总结

> **`cwd` 决定相对文件路径从哪里算；`PYTHONPATH` 决定 Python 去哪里找 import 的模块。**
> 一个管"文件路径语义"，一个管"模块搜索路径"。