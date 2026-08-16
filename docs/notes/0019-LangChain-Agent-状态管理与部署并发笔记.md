---
id: 19
title: "LangChain Agent 状态管理与部署并发笔记"
created: "2026-08-16 12:37:14"
source: "cli"
tags:
  - LangChain
  - Agent
  - 并发
---

# LangChain Agent 状态管理与部署并发笔记

> 整理自 2026-08-16 与 Claude 的对话，围绕 [demo/create_agent.py](../demo/create_agent.py) 中 `InMemorySaver` 的使用展开。
> 涵盖：checkpointer 生命周期、agent 实例生命周期、多轮对话场景、uvicorn worker、GIL 与并发/并行。

---

## 目录

1. [Checkpointer 与 State 的两种"共享"](#1-checkpointer-与-state-的两种共享)
2. [Agent 实例的生命周期](#2-agent-实例的生命周期)
3. [Checkpointer 的生命周期](#3-checkpointer-的生命周期)
4. [什么场景会多次 invoke 同一个 agent](#4-什么场景会多次-invoke-同一个-agent)
5. [Uvicorn worker 是什么](#5-uvicorn-worker-是什么)
6. [GIL、进程、线程、核、并发与并行](#6-gil进程线程核并发与并行)
7. [对 LLM/Agent 应用的含义](#7-对-llmagent-应用的含义)

---

## 1. Checkpointer 与 State 的两种"共享"

这是最容易被混淆的点。**"共享"其实有两层不同的含义**：

### 1.1 单次 run 内节点间的 State 共享

LangGraph 的 State 是图的共享通道：每个节点读入 State、返回增量更新、框架自动合并。**它不依赖 checkpointer**。`create_agent` 和手写 StateGraph 都一样。

### 1.2 跨多次 invoke 之间的状态保留

**这才是 checkpointer 的职责。** 没有 checkpointer 时，每次 `invoke` 都从零开始建 State；有了 checkpointer + 同一个 `thread_id`，多次调用才能累积同一份 State。

> 关键澄清：**内存 Saver 会丢的是"跨进程"那层，而"节点间共享 State"那层永远在、跟 checkpointer 无关。**

### 1.3 `create_agent` 与手写 StateGraph 的关系

**两者不是两种 State 机制，而是同一套机制的两层 API。** `langchain.agents.create_agent` 内部本身就是 LangGraph 图，传的 `checkpointer` 会被 `compile()` 进内部图。区别只在封装粒度：

| | `create_agent`（高层封装） | 手写 StateGraph（底层） |
|---|---|---|
| State 结构 | 内置（`messages` 序列 + runtime 字段） | 完全自定义 |
| 节点/边 | 框架预设 model→tools 循环 | 自己写节点逻辑、条件路由 |
| checkpointer | 传参即可 | 自己 `compile(checkpointer=...)` |
| 节点间 State 共享 | ✅ 有 | ✅ 有 |

---

## 2. Agent 实例的生命周期

**agent 实例就是一个普通 Python 对象**（编译好的 LangGraph 图）。存活由两件事决定：**还有没有引用指向它** + **进程是否还活着**。

### 2.1 FastAPI 场景：模块级创建则长存

```python
# app.py —— 模块级创建，进程存活期间一直存在
checkpointer = InMemorySaver()
agent = create_agent(model=model, tools=[...], checkpointer=checkpointer)

@app.post("/chat")
def chat(message: str, thread_id: str):
    # 所有用户、所有对话，都复用这一个全局 agent
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result
```

只要进程不退出，agent 就一直存活，可服务成千上万次请求，靠 `thread_id` 隔离不同对话。

### 2.2 一次性脚本：进程退出即全没

demo 里是脚本，main 结束后 **Python 进程退出**，所有对象（agent、checkpointer、内存数据）被操作系统一并回收。不是"agent 被自动回收"，而是**整个进程死了**。

### 2.3 agent 是无状态的"蓝图"

agent 本身不"记住"任何对话——图结构、节点、工具、模型的引用是它的全部。**对话记忆在 checkpointer 里，跟 agent 没关系**。所以一个 agent 实例可以同时服务无数个对话，靠 thread_id 互不干扰。

---

## 3. Checkpointer 的生命周期

**checkpointer 是独立的对象，生命周期不严格绑定 agent。**

```python
checkpointer = InMemorySaver()       # 对象A：checkpointer
agent = create_agent(..., checkpointer=checkpointer)  # 对象B：agent，内部引用了A
```

checkpoint 数据存在 checkpointer **内部**的存储字典里（thread_id → checkpoint 映射）。数据存亡取决于两个条件：

1. **checkpointer 对象还活着**（还有引用、没被 GC）
2. **进程还活着**（内存还没释放）

而 **agent 的死活与这两条都没有必然关系**：

- 若 checkpointer 只被 agent 引用（如 `create_agent(..., checkpointer=InMemorySaver())` 没存变量）：agent 被 GC 时 checkpointer 也跟着被回收，**看起来"同生共死"**。
- 若外部仍单独持有 checkpointer（如 FastAPI 的全局变量）：即使 agent 销毁，**checkpointer 和数据仍在**，可用它创建新 agent，历史对话照样接续。

### 存亡条件一览

| 对象 | 存活条件 | 数据 |
|---|---|---|
| agent | 有引用 + 进程活着 | 无状态蓝图，不存记忆 |
| checkpointer（内存型） | 有引用 + 进程活着 | 存着所有 thread 的对话记忆 |
| 进程 | 程序不退出 | 退出了，上面两个全没 |

> **硬边界是进程退出**——内存一释放数据全没。这就是 InMemorySaver 只适合单进程 demo、生产要用共享持久化存储（Postgres/Redis/Sqlite）的原因。

---

## 4. 什么场景会多次 invoke 同一个 agent

> 澄清：agent 内部多轮 LLM/tool 调用 ≠ 跨 invoke 状态。内部 agentic loop 发生在**一次 invoke 的调用栈里**，靠 State 流动，不碰 checkpointer。checkpointer 解决的是"**这次 run 结束后，下次全新 run 还记得上次的事**"。

### 场景 A：多轮对话服务（最常见）

```
第一次 invoke（thread_id="user-123"）
  用户：帮我把 gutenberg.org/files/64317 的盖茨比全文抓下来
  → agent 调 fetch_text_from_url，State.messages 里存下了抓来的全文

第二次 invoke（thread_id 还是 "user-123"）
  用户：刚才那本书的主角是谁？
  → agent 必须知道"刚才那本书"是哪本
```

没有 checkpointer，第二次 run 的 State 从零开始；有了 checkpointer + 同一 thread_id，LangGraph 每次 run 开始时**从 checkpoint 恢复 State**，多轮对话成立。

### 场景 B：Human-in-the-loop / interrupt 挂起恢复

- 第一次 `invoke()`：agent 遇到 `interrupt`（如"要花 $50 调用付费 API，批准吗？"），State 被存下，run 结束（挂起态）。
- 用户批准后**再次 `invoke()`（同一 thread_id）**：从挂起的检查点**接着跑**，而非从头再来。

### 场景 C：进程重启后的恢复

崩溃/重启后，换 `SqliteSaver`/`PostgresSaver`，同一 thread_id 还能接回上次对话。对长时间运行的异步任务很重要。

### 生产注意

真实部署常跑在**多 worker 进程**后面（如 FastAPI + 多个 uvicorn worker）。此时 `InMemorySaver` 连"进程内多次 invoke"都靠不住——两次请求可能落在**不同 worker 进程**，内存不共享，状态照样丢。生产须用共享存储 checkpointer。

---

## 5. Uvicorn worker 是什么

### 5.1 三层结构

```
┌─────────────────────────────────────────────┐
│  uvicorn master 进程（管理者，不干活）        │
│  · 接收 OS 传来的网络连接（端口 8000）        │
│  · 把每个请求分发给某个空闲 worker            │
└──────────────┬──────────────────────────────┘
               │ 分发给…
    ┌──────────┴──────────┐
    │   worker 1          │   worker 2
    │  ┌──────────────┐   │   ┌──────────────┐
    │  │ 独立 Python   │   │   │ 独立 Python   │
    │  │ 解释器 + 独立  │   │   │ 解释器 + 独立  │
    │  │ 内存空间       │   │   │ 内存空间       │
    │  │ agent +       │   │   │ agent +       │
    │  │ InMemorySaver │   │   │ InMemorySaver │
    │  └──────────────┘   │   └──────────────┘
    └──────────┬──────────┘   └──────────┬──────────┘
               └──── 各自的内存互不可见 ──┘
```

**worker 就是一个独立的 Python 进程。** uvicorn 是"进程调度壳"，`--workers 4` 启动 4 个完全独立、各跑一份应用的进程，master 负责收请求并轮流分发。

### 5.2 为什么要多 worker

1. **吃满多核 CPU**：Python 有 GIL，一个进程只能用一核。
2. **故障隔离**：worker 崩了 master 自动重启，其他 worker 不受影响。
3. **更高吞吐**：多个请求真正并行。

### 5.3 关键点：每个 worker 是"平行宇宙"

每个 worker **独立执行一遍模块级代码**，于是系统里有 **N 份 agent 实例 + N 份 InMemorySaver**，各在各的内存里，互不可见。

### 5.4 回到对话记忆场景

```
用户发消息 → master 分发给 worker 1 → worker 1 记下 thread_id="u1"
用户再发消息 → master 这次分发给 worker 2！→ worker 2 里没有 "u1"，记忆丢失
```

**不是代码 bug，而是内存不共享。** 生产必须让所有 worker 读写**同一后端存储**（Postgres / Redis / Sqlite 文件）：

```
所有 worker ──读写──► 同一个 Postgres 里的 checkpoint 表
```

### 5.5 类比：服务员 vs 点单本

- **InMemorySaver = 每个服务员自己口袋里的便签本**。另一个服务员接单时看不到。
- **持久化 checkpointer = 桌上的共同点单本**。不管谁接单都在同一本子上记。

---

## 6. GIL、进程、线程、核、并发与并行

### 6.1 GIL 那句话的正确理解

**GIL（全局解释器锁）**：同一时刻，**一个进程里只有一个线程能执行 Python 字节码**。

```
一个 Python 进程
┌─────────────────────────┐
│  线程A ─┐                │
│  线程B ─┤ 争夺同一把 GIL  │  ← 任何时候只有拿到锁的线程在跑
│  线程C ─┘                │     多线程 ≠ 多核利用
└─────────────────────────┘
```

两个例外：
- **I/O 时会释放 GIL** → 多线程在 I/O 密集场景仍有价值。
- NumPy/Pandas 底层 C 库等可绕开 GIL。

### 6.2 worker 与核的关系

每个 worker 是独立进程，有**自己的 GIL**：

```
4 核服务器
┌────────────┬────────────┬────────────┬────────────┐
│  核1        │  核2        │  核3        │  核4        │
│ worker1    │ worker2    │ worker3    │ worker4    │
│ 自己的GIL  │ 自己的GIL   │ 自己的GIL   │ 自己的GIL   │
└────────────┴────────────┴────────────┴────────────┘
```

**4 个 worker = 4 份 Python 代码在 4 个核上真正并行。** 超过核数的 worker 反而增加调度开销。

### 6.3 4 核、4 worker、同时 10 个请求——会阻塞吗？

**结论：不会排队等死。** 取决于代码是同步还是异步。

#### 情况 A：异步端点（`async def` + `await`）——推荐

每个 worker 内部跑**事件循环**（单线程，但能同时挂起成千上万个请求）：

```
worker 事件循环（单线程，跑在核上）
┌─────────────────────────────────────────────┐
│ 请求1 正在等 LLM 返回（I/O 等待）──┐          │
│ 请求2 正在等数据库（I/O 等待）─────┤ 谁有结果   │
│ 请求3 正在等抓网页（I/O 等待）─────┤ 就唤醒谁   │
│ 请求4-10 排队中，但随时能切进来    │          │
└─────────────────────────────────────────────┘
```

- 绝大多数时间在等外部响应，等待不占 CPU，事件循环趁机切换。
- 10 个请求无感，1000 个也没问题（前提负载都是 I/O 等待）。

#### 情况 B：同步端点（普通 `def`）——FastAPI 用线程池兜底

- FastAPI 把同步函数丢进线程池（默认每 worker 40 线程）。
- 等 LLM 返回时 **I/O 释放 GIL**，同 worker 其他线程可继续执行。
- 只有 **CPU 密集**任务（解析大文件、Pandas 算数）才真正占住核/GIL，才需要排队。

#### 什么时候真阻塞？

1. **纯同步且无并发**（单线程串行）：请求 A 没完成 B 永远不开始（老式 CGI）。
2. **CPU 密集任务**：4 核只能同时算 4 个，算得慢是硬性的。

### 6.4 并发 vs 并行

| | 并发（concurrency） | 并行（parallelism） |
|---|---|---|
| 含义 | 多个任务**交错推进**，逻辑上"同时" | 多个任务**真正同时执行** |
| 前提 | **单核就能做到** | 必须多核 |
| 手段 | I/O 等待时切换（异步/线程） | 多进程（worker） |
| 典型例子 | 事件循环 | 4 worker 各占一核 |

**异步提升"并发吞吐"**（海量等 I/O 的请求不干等）；**多 worker 提升"并行算力"**（CPU 密集活多核分摊）。

---

## 7. 对 LLM/Agent 应用的含义

Agent 执行流程：调 LLM（等几秒~几十秒）→ 调工具抓网页/查库（等）→ 再调 LLM（等）……**从头到尾都是 I/O 密集**。

- **真正的并发吞吐靠异步**（事件循环挂起成千上万等 LLM 返回的用户），**不是靠堆 worker**。单核异步 worker 就能服务几百个并发用户。
- 多 worker 的价值：① 吃满多核；② 故障隔离；③ 一个 worker 内的 CPU 密集任务（如解析大文本）不拖累其他请求。
- 4 核 4 worker 完全够用，瓶颈在 LLM 的 API 响应速度，不在 CPU。

> 一句话：**并发吞吐是"异步换来的"，多核解决的是"CPU 密集的并行"，两件事别混。**

---

## 快速验证实验

在 [demo/create_agent.py](../demo/create_agent.py) 上把单次 invoke 改成连续两次（复用同一 `thread_id`），第二次问"我刚让你抓的 URL 是什么"，即可看到 `InMemorySaver` 在进程内确实接续了对话历史。再将 `InMemorySaver` 换成 `SqliteSaver`，重跑第二次脚本，历史仍在——直观对比内存型与持久化 checkpointer 的差异。

## 参考链接

- [LangChain agents 调用文档](https://docs.langchain.com/oss/python/langchain/agents#invocation)
- [LangGraph 持久化文档](https://docs.langchain.com/oss/python/langgraph/persistence)
