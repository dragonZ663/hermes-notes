---
id: 9
title: "Deep Agents vs Hermes Agent — 能力对比"
created: "2026-06-09 05:39:05"
source: "conversation"
tags:
  - agent
  - langchain
---

# Deep Agents vs Hermes Agent — 能力对比

## 背景

Deep Agents 是 LangChain 官方推出的 Agent Harness（代理套件），底层基于 LangGraph 运行时，通过 `pip install deepagents` 使用。

Hermes Agent（我当前运行的 Agent 系统）是由 Nous Research 开发的端到端 Agent 系统。

两者都是 "Agent Harness" 架构，但定位和使用方式有本质差异。

---

## 核心定位差异

| | Deep Agents | Hermes Agent |
|---|-----------|--------------|
| **本质** | **Python 库** — 你 `pip install` 后在代码里调它 | **端到端系统** — 在服务端持续运行，你说它做 |
| **使用方式** | `create_deep_agent(model, tools)` → 你写代码编排 | 对话式交互（WeChat / Telegram / 终端） |
| **部署** | 你的代码决定部署方式 | 自带 Gateway + Provider 架构 |
| **平台** | 纯后端库 | 前端（微信/Telegram）+ 后端一体 |
| **状态** | 每次调用独立 | 持续运行，跨会话共享记忆 |

---

## 能力逐项对比

| 能力 | Deep Agents | Hermes Agent |
|------|:-----------:|:------------:|
| **Task Planning** | ✅ 内置 `write_todos` | ✅ `todo` 工具 |
| **Memory** | ✅ 内置 | ✅ 跨会话持久化（重启不丢） |
| **Skills** | ✅ 内置 | ✅ 可复用工作流（版本管理 + patch） |
| **Subagents** | ✅ 内置 | ✅ `delegate_task` 多 Agent 并行 |
| **Human-in-the-loop** | ✅ 内置 | ✅ 每个消息都是交互式 |
| **Context 管理** | ✅ 虚拟文件系统 + 压缩 | ✅ 上下文压缩 + 中间结果屏蔽 |
| **Streaming** | ✅ 内置 | ✅ 平台原生流式输出 |
| **Sandboxes** | ✅ 安全执行环境 | ✅ `execute_code` + 终端 |
| **多平台接入** | ❌ | ✅ **Telegram / WeChat / 终端** |
| **Cron 调度** | ❌ | ✅ **定时任务 + 无代理模式 + 看门狗脚本** |
| **会话搜索** | ❌ | ✅ **SQLite FTS5 全文检索历史对话** |
| **浏览器自动化** | ❌ | ✅ **导航 / 点击 / 截图 / 控制台** |
| **跨会话记忆** | 单实例 | ✅ **全局共享，重启不丢** |
| **文件系统集成** | 只读虚拟 FS | ✅ **读/写/搜索/编辑/补丁全套** |
| **Skill 自动加载** | ❌ | ✅ **任务匹配 → 自动加载** |

---

## 一句话总结

- **Deep Agents** = 你构建 Agent 应用的**框架/库**
- **Hermes Agent** = 已经在日常使用的**端到端 Agent 系统**

两者定位不同，不冲突——Deep Agents 适合你用来构建自己的 AI 应用，而 Hermes 是供你直接使用的 AI 助手。