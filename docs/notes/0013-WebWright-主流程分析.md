---
id: 13
title: "WebWright 主流程分析"
created: "2026-06-11 13:54:05"
source: "conversation"
tags:
  - python
  - webwright
  - architecture
---

# WebWright 主流程分析

# WebWright 主流程分析

## 一、整体架构

```
CLI 入口 (cli.py)
  ├── 加载配置（YAML 合并）
  ├── 创建 Model（LLM 后端）
  ├── 创建 Environment（执行环境）
  └── 创建 Agent → agent.run(task)
        └── agent.run() 内的主循环
              ├── query() — 向 LLM 发送消息，获取 JSON 响应
              ├── execute_actions() — 执行模型生成的动作
              └── 循环直到 done=true 或超限
```

---

## 二、CLI 入口层 (cli.py)

`run_one()` 是整个流程的编排函数：

1. **配置合并** — 将多个 YAML 配置（如 base.yaml + model_openai.yaml）通过 `recursive_merge` 深度合并
2. **创建三大核心组件：**
   - **Model** — LLM 后端（Anthropic / OpenAI / OpenRouter），负责与大模型通信、解析 JSON 响应
   - **Environment** — 执行环境（`LocalWorkspaceEnvironment` 或 `LocalBrowserEnvironment`），负责执行 bash 命令
   - **Agent** — 核心循环控制器（`DefaultAgent`）
3. 调用 `env.prepare()` — 创建工作目录、task.json、日志/截图子目录
4. 调用 `agent.run()` — 进入主循环（见下文）
5. **异常处理** — 捕获运行异常和环境关闭异常
6. **结果输出** — 打印 final_response，返回结果字典

---

## 三、Agent 主循环（DefaultAgent.run()）⭐ 核心

```
while True:
  1. step()
     ├── query() → LLM 返回 JSON
     └── execute_actions()
           ├── 如果 done=true → 校验过关 → exit
           └── 否则执行动作 → 返回 observation

  2. 检查最后一条消息 → role == "exit"? → 跳出循环
  3. 检查是否需要压缩历史 → _compact_history()
  4. 每次循环后保存 trajectory.json
```

### 3.1 step() 方法

```python
def step(self) -> list[dict[str, Any]]:
    return self.execute_actions(self.query())
```

两步走：先 `query` 再 `execute`。

### 3.2 query() 方法 — 调用 LLM

```python
def query(self) -> dict[str, Any]:
    # 检查 step_limit
    # 调用 model.query(self.messages) → LLM API
    # self.n_calls += 1
    # 将回复加入 self.messages
    # 返回 message
```

- 检查步骤上限 `step_limit`（默认 100），超限抛出 `LimitsExceeded`
- 将整个 `self.messages` 历史发送给 LLM
- LLM 返回严格 JSON 格式：

```json
{
  "thought": "<推理过程>",
  "bash_command": "<shell 命令或空字符串>",
  "done": false,
  "final_response": ""
}
```

- **`BaseModel.query()` 内部机制：**
  - **JSON 解析重试** — 最多 3 次解析失败的自动修复
  - **bash 语法校验** — `bash -n` 检查命令合法性
  - **HTTP 重试** — 429 (rate limit) 最多 5 次退避重试；5xx 最多 5 次退避重试
  - **工具门控强制** — 如果同时有 `done=true` 和非空 `bash_command`，自动降级 `done=false`

### 3.3 execute_actions() 方法 — 执行并观察

```python
def execute_actions(self, message):
    extra = message["extra"]

    # 分支 A: done=true → 完成门控检查
    if extra.get("done"):
        gate_error = self._self_reflection_gate_error()
        if gate_error:
            # 未通过自评，拒绝完成，返回错误消息给 LLM
            extra["done"] = False
            return self.add_messages(format_message(role="user", ...))
        # 通过门控 → 写入 exit 消息退出循环
        return self.add_messages(format_message(role="exit", ...))

    # 分支 B: 有动作 → 执行
    outputs = [self.env.execute(action) for action in extra["actions"]]
    # 格式化观察结果 → 作为 user 消息加入 messages
    observation_messages = self.model.format_observation_messages(...)
    return self.add_messages(*observation_messages)
```

**完成门控（Completion Gate）：** 当模型声明 `done=true` 时，如果配置了 `require_self_reflection_success=true`，必须校验：
1. `plan.md` 存在且包含所有关键点
2. `self_reflect_config.json` 存在
3. `final_script.py` 已在 `final_runs/run_<id>/` 中执行成功
4. `self_reflection` 工具运行并通过（`predicted_label=1`）
5. 人工确认最终产物存在

任一条件不满足，模型会被驳回并要求先完成质检步骤。

### 3.4 历史压缩（_compact_history()）

当 `summary_every_n_steps > 0` 且 `n_calls % summary_every_n_steps == 0` 时触发：
1. 保留最初的 system message
2. 将所有历史对话发送给 LLM，要求生成压缩摘要
3. 用 `[system, compressed_summary]` 替换整个消息列表
4. 默认每 20 步压缩一次

### 3.5 ARIA 快照修剪（_prune_old_observation_aria_snapshots）

当 `keep_last_n_observations > 0`（如 local_browser 模式设为 1），仅保留最近 N 条 observation 中的 aria_snapshot，旧的被替换为占位文本，以控制上下文长度。

---

## 四、Environment 执行层（LocalWorkspaceEnvironment.execute()）

```python
action["bash_command"] → subprocess.run(shell=True)
```

- 持久化命令到 `steps/step_NNNN.sh`
- 设置环境变量（`WORKSPACE_DIR`, `BROWSER_MODE` 等）
- 执行命令（timeout 240s）
- 返回 observation（含 `command_output`, `screenshot_path`, `workspace_files` 等）

每个 bash 命令执行后，Environment 返回一个 observation 字典，包含：
- 命令输出（截断到 `output_truncation_chars`，默认 24000 字符）
- 最新截图路径
- 最近文件列表
- `final_script.py` 预览
- 错误信息

---

## 五、LLM 消息流（对话结构）

| 序号 | 角色 | 内容 |
|------|------|------|
| 1 | System | system_template (Jinja2 渲染，含完整指令) |
| 2 | User | instance_template (Jinja2 渲染，含任务描述) |
| 3 | User | [可选] Explore History — 前次探索的历史 |
| 4 | Assistant | 模型回复的 JSON (thought + action) |
| 5 | User | Observation (命令执行结果) |
| 6 | Assistant | 模型回复的 JSON |
| 7 | User | Observation |
| ... | ... | ...循环... |
| N | Assistant | `{done=true, final_response=...}` |
| N+1 | Exit | 跳出循环 |

---

## 六、关键设计模式

| 特性 | 说明 |
|------|------|
| **ReAct 循环** | 推理(thought) → 行动(bash_command) → 观察(observation) 的严格三步循环 |
| **JSON 约束输出** | 模型必须返回严格 JSON schema，不符合则解析重试或报错 |
| **完成门控** | done=true 必须通过 self_reflection 门控，防止模型过早声明完成 |
| **历史压缩** | 每 N 步用 LLM 生成摘要替换历史，控制 token 消耗 |
| **配置驱动** | 所有行为（模型、模板、限制、重试策略）由 YAML 配置文件驱动 |
| **异常容错** | Rate limit 重试、HTTP 5xx 重试、JSON 解析重试、bash 语法校验 |
| **逐步持久化** | 每步命令、日志、截图自动保存，支持轨迹回放和调试 |

---

## 七、典型执行流程

```
CLI: python -m webwright.run.cli -t "任务"
  │
  ├── 加载并合并配置
  ├── 创建 Model / Environment / Agent
  ├── env.prepare: 创建 workspace
  │
  └── agent.run: 开始循环
        │
        ├── 检查 step_limit?
        │     ├── 未超限 → query: 发消息给 LLM
        │     │              │
        │     │              └── LLM 返回 JSON (thought + bash_command + done)
        │     │                    │
        │     │                    ├── done=true? → 完成门控检查
        │     │                    │     ├── 通过 → 写 exit 消息, 保存 trajectory, 结束
        │     │                    │     └── 不通过 → 驳回, 发 user 消息要求补全
        │     │                    │
        │     │                    └── done=false → 执行 bash_command
        │     │                                    │
        │     │                                    └── 返回 observation
        │     │                                          │
        │     │                                          ├── 需要历史压缩? → 压缩历史后重置 messages
        │     │                                          └── 保存 trajectory
        │     │                                                │
        │     │                                                └── 回到循环开头
        │     │
        │     └── 超限 → 抛出 LimitsExceeded
        │
        └── 结束
```