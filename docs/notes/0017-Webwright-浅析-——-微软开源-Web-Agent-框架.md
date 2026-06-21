---
id: 17
title: "Webwright 浅析 —— 微软开源 Web Agent 框架"
created: "2026-06-21 13:21:42"
source: "conversation"
tags:
  - Webwright
  - WebAgent
  - AI测试
  - Playwright
  - 自动化测试
  - 微软研究院
---

# Webwright 浅析 —— 微软开源 Web Agent 框架

**核心定位：** Webwright 是一个让 LLM 通过终端 + 写 Python 脚本的方式来操控浏览器的 Web Agent 框架，核心输出是可保存、可重放、可参数化的 Playwright 测试脚本（final_script.py）。微软研究院开源，~1.5k LoC，仅 9 个生产依赖。

**核心理念：Code-as-Action**
传统 Web Agent 是"观察 → 预测动作 → 执行 → 再观察"每步累加误差；Webwright 改为"写一段完整脚本 → 执行 → 看截图/日志 → 修复 → 重复"，一次执行一段完整代码，避免误差累积。

**两种运行模式：**
1. local_workspace（标准模式）— 输出 final_script.py + 截图 + 裁判结果，适合自动化批处理
2. local_browser（实时浏览器模式）— 有状态浏览器，Agent 直接驱动，适合快速查询/调试

**6 步工作流程（local_workspace）：**
1. 规划 — Agent 提取关键检查点写入 plan.md
2. 编写裁判配置 — 写 4 条 LLM 提示词（一次性，后续复用）
3. 探索 — 写探索脚本 → 临时浏览器 → 截图 + ARIA 树
4. 生成最终脚本 — final_script.py，每个检查点对应一张截图
5. Self Reflection 裁判 — 两阶段：并发逐图评分(1-5) → 汇总裁判 PASS/FAIL
6. 声明完成 — 仅当 predicted_label == 1 才 done，否则修复脚本重新跑

**优势：**
- NL → 可重放 Playwright 脚本，快速原型验证
- 语义级视觉验证（非像素级对比），对 UI 重构天然免疫
- 长链路 SOTA（Odysseys 基准 60.1% vs 前 SOTA 44.5%）
- 完整可观测性（trajectory.json + 截图 + 日志）
- Token 消耗约为 Codex Skill 模式的 1/8

**局限性：**
- LLM 概率性输出，同任务多次运行结果不同
- 无原生测试框架集成（需 CLI 包装）
- 运行时间长（3-10 分钟），Token 成本较高
- 需 LLM API Key，无法离线
- 单任务驱动，无测试套件概念

**定位：** 不是替代 Playwright/pytest，而是 E2E 层的"AI 加速器"。建议组合策略：Webwright 自动生成脚本 → 人工审查 → 编写 pytest 精确断言 → CI 回归。

**推荐落地路径：** 第 1 周试点 → 第 2 周选 3-5 个场景 → 第 3 周评估质量 → 第 4 周建立混合流程。

项目地址：https://github.com/microsoft/Webwright