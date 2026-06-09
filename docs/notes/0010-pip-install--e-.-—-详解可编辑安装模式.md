---
id: 10
title: "pip install -e . — 详解可编辑安装模式"
created: "2026-06-09 09:10:56"
source: "conversation"
tags:
  - python
  - pip
---

# pip install -e . — 详解可编辑安装模式

## 一、基本含义

```bash
pip install -e .
```

- `pip install` — 用 pip 安装 Python 包
- `-e` = `--editable` — 以**可编辑模式**安装
- `.` — 当前目录

完整含义：**把当前目录下的 Python 项目，以可编辑模式安装到当前 Python 环境中。**

---

## 二、普通安装 vs 可编辑安装

### 普通安装 `pip install .`

把当前项目打包后复制到 Python 环境的 `site-packages` 里。

**结果：**
- 安装后代码已拷贝进环境
- 修改项目源码**不会自动生效**
- 改代码后需重新安装

### 可编辑安装 `pip install -e .`

建立一种"链接关系"——让 Python 环境直接指向你当前项目目录。

**结果：**
- 修改项目源码后**不用重新安装**
- Python 运行时直接使用当前目录的最新代码
- 特别适合**开发阶段**

---

## 三、示例

```
my_project/
├── pyproject.toml
├── src/
│   └── mypkg/
│       └── hello.py
```

执行 `pip install -e .` 后，在任何地方都可以 `import mypkg`，且改源码后立即生效。

---

## 四、适用场景

### 适合用
- 看开源项目源码，本地调试
- 准备修改代码
- 开发 CLI 工具
- 希望代码改完立刻生效

### 不适合
- 生产环境部署
- 只想安装稳定版本使用
- 不希望环境依赖本地源码目录

生产环境更推荐：`pip install .` 或 `pip install some-package`

---

## 五、依赖的项目文件

`pip install -e .` 会读取当前目录的项目元数据：
- `pyproject.toml`（最常用）
- `setup.py`
- `setup.cfg`

当前目录必须是一个**可被 pip 识别的 Python 项目**，否则报错。

---

## 六、与 requirements.txt 的区别

| 命令 | 作用 |
|------|------|
| `pip install -r requirements.txt` | 安装依赖列表中的第三方包 |
| `pip install -e .` | 安装**当前项目本身** |

常见组合：

```bash
pip install -e .
pip install -r requirements-dev.txt
```

含义：先安装项目本身（可编辑），再安装开发依赖。

---

## 七、`python -m pip install -e .` 与 `pip install -e .` 的区别

功能基本一样，但 `python -m` 更稳：

```bash
python -m pip install -e .
```

它明确使用"当前这个 python 对应的 pip"执行安装，在多 Python 版本、虚拟环境、Windows 环境中更安全。

---

## 八、一句话记忆

> **`pip install -e .` = 把当前项目以"开发模式"安装到当前 Python 环境，改源码后通常不用重新安装。**

---

## 九、常见配套命令

```bash
pip install -e .           # 安装项目本身（可编辑模式）
pip install -e ".[dev]"    # 安装项目 + dev 开发依赖
python -m webwright.run.cli # 安装后运行模块
