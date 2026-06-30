---
id: 18
title: "Hermes Agent Skills 系统架构与规范"
created: "2026-06-30 14:57:11"
source: "cli"
tags:
  - SKILL
  - 渐进式披露
---

# Hermes Agent Skills 系统架构与规范

## 三层渐进式披露机制

| 层级 | 方法 | 返回内容 |
|------|------|----------|
| Layer 1 | skills_list() | 所有 skill 的 name + description |
| Layer 2 | skill_view(name) | 完整 SKILL.md + linked_files 清单（文件名+路径）|
| Layer 3 | skill_view(name, file_path) | 按需读取具体文件内容 |

skills_list() 和 skill_view() 是 Agent 可直接调用的工具（Tool），persona 中的"必须先扫描 skills"是系统指令（System Prompt），驱动 Agent 主动去调用。

linked_files 不是从 SKILL.md 解析的，而是扫描 skill 目录结构自动生成的。

## 目录结构规范

skill_manage.write_file 强制：支持文件必须放在以下目录之一，名称不可改：
- references/ — 参考文档
- templates/ — 模板文件
- scripts/ — 可执行脚本
- assets/ — 静态资源

SKILL.md 中的章节名（如 ## Reference Files）是惯例而非约束，没有工具层面的强制校验。

commands/ 目录不在上述白名单中，用于 slash command 路由。Slash command（如 /webwright:run `[task]`）本质是预写 agent prompt 模板 + $ARGUMENTS 插值，不是真正的 CLI 命令。

## 三层信息分工

| 来源 | 方式 | 内容 |
|------|------|------|
| linked_files | 目录遍历 | "有什么、在哪找" |
| SKILL.md 正文 | 作者编写 | "每个文件干什么用、何时用" |
| Agent 运行时 | 按需决策 | "现在需要哪个 -> 按需加载" |

## 官方文档

完整技能编写文档：https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
