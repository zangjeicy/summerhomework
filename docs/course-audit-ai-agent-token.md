# RuyiDailyStockAnalysis v0.1.0 AI、Agent、工具调用与 Token 核验报告

> 任务编号：RDSA-AI-AGENT-TOKEN-AUDIT-008  
> 核验日期：2026-07-12  
> 第一真相源：`D:\tmp\RuyiDailyStockAnalysis_v0.1.0`  
> 差异对照：`D:\quant\RuyiDailyStockAnalysis` 的 `dev` 工作树  
> 结论等级：A=代码、数据库、日志可相互印证；B=代码存在但现场无运行记录；C=仅 UI/文案或尚未确认

本报告只核验、记录和提出课程修订建议；未修改业务代码、测试、模型配置、数据库或 PPT，未发起真实模型请求。

## 1. 执行摘要

1. 教学目录的 1006 个 Git 跟踪文件与 `version/v0.1.0` 提交 `4eb23fbb1242b773e789373e7035e570f7075798` 逐文件 Git blob 一致；ZIP 内 1006 个文件与教学目录逐文件大小和 CRC 一致。ZIP SHA-256 为 `FA96F2E15082E12E8C92259CAFD1AE3E11B675DFED5C01752967248A2240B2FD`。
2. `v0.1.0` 已实现真正的单 Agent ReAct 循环、18 个工具、15 个 YAML 技能、多轮会话、工具轨迹、模型级回退和上下文压缩；不是只有界面。但是教学现场配置为 `AGENT_ARCH=single`、上下文压缩关闭、无 Agent 备用模型，数据库中也没有 AI 问股会话、摘要、工具轨迹或 Agent Token 记录。因此“代码已实现”不能写成“教学现场已成功运行”。
3. 教学库只有 3 条真实普通分析 LLM 记录，共 36,218 Token；三条都带供应商 usage 快照，Prompt/Completion/Total 完整。教学日志证明其中 Seed 模型成功、Qwen 模型曾返回无效 JSON并降级为文本，不证明 AI 问股或工具调用成功。
4. 现有 AI 问股、Token 用量、系统设置截图来自 `dev` 页面审计，不是 `v0.1.0` 教学现场截图。AI 问股截图是空状态；Token 截图精确对应 dev 数据库 168 条记录；系统设置截图对应 dev 的 DeepSeek 主模型配置。
5. 截图中的 `Prompt=0、Completion=0、Total>0` 不是页面求和错误，也不是教学库旧记录。162 条 Agent 记录在几秒内密集写入，供应商快照为空，数值和 Agent 单测的模拟 usage 一致。根因是测试模拟只提供 `total_tokens`，持久化层把缺失分项写成 0，同时部分 Agent 单测未隔离默认数据库，污染了 dev 数据库。
6. 项目只展示 Token 数量和峰值，不计算或展示真实费用。LiteLLM 的价格注册只为调用兼容，不构成账单、成本估算或实际费用统计。
7. `version/v0.1.0..dev` 的已提交差异只有页面审计脚本、目录、package scripts 和文档；AI、Agent、工具、上下文、回退、Token 业务代码无差异。当前 dev 的未提交 `src/stock_analyzer.py` 改动也与本专题无关。

## 2. 教学目录与运行环境

| 项目 | 核验结果 | 证据等级 |
| --- | --- | --- |
| ZIP 与教学目录 | ZIP 1006/1006 文件匹配；未重复解压 | A |
| Git 来源 | 1006/1006 跟踪 blob 匹配 `version/v0.1.0` | A |
| Python | 教学 `.venv` 为 Python 3.11.15；FastAPI 0.139.0、Pydantic 2.13.4、HTTPX 0.28.1 可导入 | A |
| 启动方式 | `main.py --webui-only` / Uvicorn；日志记录曾监听 `127.0.0.1:8000` | A |
| 当前运行状态 | 核验时 8000/4173 均无监听；未重新启动 | A |
| 数据库 | `data/stock_analysis.db`，970,752 字节；WAL 存在且为 0 字节 | A |
| 会话 | `conversation_messages=0`、`conversation_summaries=0`、`agent_provider_turns=0` | A |
| Token | `llm_usage=3`，均为 `analysis`，不是 `agent` | A |
| 运行结果 | 1 条 600519 普通分析、43 条日线、2 条基本面快照、1 条决策信号 | A |
| 模型配置 | 当前教学本地 `.env`：主分析和 Agent 均为 Seed；OpenAI 兼容协议走 SiliconFlow；无 Agent 模型 fallback | A |
| 密钥边界 | 教学本地 `.env` 有非空本地凭据，但 ZIP 不包含 `.env`，只包含 `.env.example`；本次未读取、输出或调用凭据 | A |

已有日志表明教学环境在 2026-07-11 05:41～07:04 之间多次运行。07:03～07:04 的 API 日志明确把数据库解析为教学目录下的 `data\stock_analysis.db`。现有环境具备再次启动的文件基础，但由于本任务禁止真实调用、改配置和写正式数据，本次只做导入级验证，不声称已重新复现完整 Web/模型流程。

## 3. 截图和验收材料来源核验

| 截图 | 来源结论 | 状态结论 | 能否作为 v0.1.0 成功证据 |
| --- | --- | --- | --- |
| `02_AI问股.png` | dev 页面审计 | 空状态，无历史会话、无回答、无工具轨迹 | 不能 |
| `08_Token用量.png` | dev 页面 + dev 数据库 | 有统计，但混合 6 条早期普通分析与 162 条测试模拟 Agent 数据 | 不能 |
| `09_系统设置.png` | dev 页面 + dev 配置 | 配置可读取；显示 DeepSeek 主模型、Agent 继承主渠道 | 不能 |

来源证据：

- 验收 JSON 和图片全部位于 `D:\quant\RuyiDailyStockAnalysis\.tmp\page-audit\页面截图`，生成时间是 `2026-07-11T23:11:02.468Z`，即北京时间 2026-07-12 07:11:02。
- 生成脚本 `apps/dsa-web/e2e/page-audit.spec.ts` 只存在于 dev 提交 `605fd015...` 的改动中，`version/v0.1.0` 没有该脚本。
- Playwright 默认从 dev 仓库根启动后端；Token 截图的 22,267 Token、168 次调用、模型和峰值与 dev 数据库逐项一致，与教学库的 36,218 Token、3 次调用明显不一致。
- 验收脚本只访问页面、等待元素、检查 HTTP/Console 错误并截图；它没有发送 AI 问股问题，也没有断言工具调用或模型成功。
- 验收脚本只对登录状态做 mock；AI 问股、Token 和系统设置没有 mock，但“不 mock”仍只代表读取了当时 dev 后端状态，不代表数据是真实供应商调用。

因此，这三张图可以作为 dev UI 布局素材，不能作为 `v0.1.0` 教学功能成功截图。

## 4. 关键代码与模块映射

| 层 | 关键文件 | 关键职责 |
| --- | --- | --- |
| Web 页面 | `apps/dsa-web/src/pages/ChatPage.tsx:585` | 组装消息、会话 ID、技能和股票/报告上下文 |
| Web 状态 | `apps/dsa-web/src/stores/agentChatStore.ts:232` | 发起 SSE、展示阶段/工具事件、处理完成和失败 |
| Web API | `apps/dsa-web/src/api/agent.ts:86` | POST `/api/v1/agent/chat/stream` |
| Agent API | `api/v1/endpoints/agent.py:373` | 校验 Agent 可用性、创建执行器、把事件转成 SSE |
| 工厂 | `src/agent/factory.py:176`、`:297` | 注册 18 个工具、加载技能、按 `AGENT_ARCH` 构建单 Agent/多 Agent |
| Prompt/会话 | `src/agent/executor.py:565` | 构建系统 Prompt、拼历史和报告上下文、保存用户/助手消息 |
| 上下文压缩 | `src/agent/chat_context.py:221` | 阈值、滚动摘要、保护尾部、失败回退、摘要持久化 |
| Agent 循环 | `src/agent/runner.py:392` | LLM → tool_calls → 工具结果 → LLM，直到答案或上限 |
| 模型适配 | `src/agent/llm_adapter.py:586` | LiteLLM 统一调用、模型回退、usage 归一化 |
| 工具注册 | `src/agent/tools/registry.py:27`、`:161` | 参数 schema、工具描述、处理函数注册 |
| 工具执行 | `src/agent/tools/execution.py:248` | 股票范围保护、异常包装、不可重试缓存、结果序列化 |
| Token 归一化 | `src/llm/usage.py:275` | 供应商 usage、缓存/推理字段归一化和有效性检查 |
| Token 存储/聚合 | `src/storage.py:3061`、`:3086`、`:3229` | 单次写入、按类型/模型聚合、最近调用 |
| Token API/UI | `api/v1/endpoints/usage.py:89`、`apps/dsa-web/src/pages/TokenUsagePage.tsx` | 时间范围查询和页面展示 |

## 5. AI 问股真实调用链

```text
ChatPage.handleSend
  → agentChatStore.startStream
  → POST /api/v1/agent/chat/stream
  → agent_chat_stream.run_sync
  → factory.build_agent_executor
  → AgentExecutor.chat
  → build_agent_chat_context_bundle
  → runner.run_agent_loop
      → LLMToolAdapter.call_with_tools
      → 模型返回 tool_calls 或最终文本
      → ToolRegistry.execute / 工具处理函数 / 数据源
      → 工具结果作为 role=tool 回填下一轮
      → 每次有 usage 的模型调用写 llm_usage
  → 保存用户与助手可见消息；必要时保存 provider trace
  → SSE done/error
  → 页面追加回答或显示错误
```

该链路是实际代码链路，不是概念图。现场数据库却没有任何 AI 问股消息、工具轨迹或 Agent usage，所以当前只能把它标为“`v0.1.0` 代码已实现，教学运行未留成功证据”。

普通每日分析走 `src/analyzer.py`，不是上述 AI 问股链路。教学库的 3 条 Token 和 1 条报告属于普通分析，不能拿来证明 Agent 工具调用。

## 6. Prompt 与上下文

### 概念在项目中的真实含义

| 概念 | v0.1.0 真实实现 |
| --- | --- |
| 大语言模型 | LiteLLM 背后的具体部署；普通分析和 Agent 可配置不同主模型 |
| 系统 Prompt | `CHAT_SYSTEM_PROMPT`/`AGENT_SYSTEM_PROMPT`，包含角色、输出规则、市场规则、技能说明 |
| 用户 Prompt | 当前输入；报告跟问时还会插入一组“系统提供的历史分析上下文”用户消息 |
| 上下文 | 历史可见消息 + 可选摘要 + 必须回放的供应商工具/思考轨迹 + 可选报告上下文 + 当前用户消息 |
| Agent | 具有最多 N 轮“模型选择工具—执行—回填—再推理”的执行循环 |
| 技能 | YAML/Markdown 加载成 `Skill` 对象，核心是 Prompt 指令和所需工具元数据；单 Agent 模式不会为每个技能创建独立进程 |
| 工具 | `ToolDefinition` 代码对象，包含名称、描述、参数 schema、处理函数和策略元数据 |
| 工具调用 | 模型返回结构化 tool_calls，runner 执行 Python handler，再把 JSON 结果回填模型 |
| 会话 | SQLite 中的可见 user/assistant 消息；进程内对象只管理 TTL 和最近活跃时间 |
| 实时数据 | 工具运行时从 FetcherManager 请求的行情；可能失败、缓存或降级，不等于每个回答都必然有实时行情 |

### 上下文包含项

| 项目 | 结论 |
| --- | --- |
| 当前股票 | 有。页面传 stock context，后端再次解析并设置股票范围保护 |
| 当前报告 | 部分。有 `recordId` 跟问时注入价格、涨跌幅、分析摘要、策略和市场上下文；普通问答不自动加载整份报告 |
| 历史会话 | 有。压缩关闭时最多最近 20 条可见消息；开启时可保留完整未压缩段和摘要 |
| 实时行情 | 不默认预取；模型选择 `get_realtime_quote` 后才获得 |
| 新闻 | 不默认预取；通过新闻工具获得；报告跟问可能只带上次摘要 |
| 基本面 | 不默认预取；通过 `get_stock_info` 或报告跟问摘要获得 |
| 系统配置 | 影响模型、循环、压缩等行为，但不会整份注入 Prompt |
| 技能 | 会作为“激活的交易技能”注入系统 Prompt |
| 工具结果 | 会以 `role=tool` 消息回填下一轮模型 |

教学库保存的一条普通分析 context snapshot 含实时行情、技术面、基本面、数据质量和市场阶段；该快照属于普通分析，不会自动变成任意 AI 问股的上下文。

## 7. 上下文压缩

状态：**后端真实实现，教学配置关闭，现场未触发。**

- UI 开关写入 `AGENT_CONTEXT_COMPRESSION_ENABLED`，后端读取同一配置，前后端一致。
- 教学配置：`enabled=false`、profile=`balanced`、触发 12,000 Token、保护最近 4 个用户轮次、摘要目标 1,500 Token、历史预算 8,000 Token。
- 关闭时只取最近 20 条可见消息。
- 开启后先估算 Token；LiteLLM tokenizer 失败时按约 3 字符/Token 估算。
- 超阈值后调用当前 Agent 模型，温度 0、20 秒超时，生成固定五段 Markdown 摘要。
- 摘要保存到 `conversation_summaries`，记录覆盖到的消息 ID、源消息数和估算 Token。
- 摘要失败：有旧摘要时保留旧摘要+未覆盖消息；无旧摘要时回退最近 20 条。
- 最近保护轮次本身超过阈值时不会强制截断，因此仍可能超上下文窗口。
- 摘要是模型生成文本，虽 Prompt 要求保留标的、成本、条件、数据时效和工具失败，仍可能遗漏或改写事实；项目没有摘要事实一致性校验。
- 供应商必须回放的 tool/thinking trace 只有在模型匹配、锚点未被摘要且预算充足时才注入，否则丢弃并记内部 diagnostics；UI 不展示这些丢弃诊断。

## 8. Agent、技能与工具调用

### Agent

- 教学现场是 `AGENT_ARCH=single`。普通 AI 问股本身就是 Agent，不存在另一个“普通聊天不调用工具”的独立模式。
- 单 Agent 最多 10 次 LLM round-trip，总预算 600 秒；剩余不足 8 秒时从第二步起提前停止。
- 多工具同一轮最多 5 个线程并行；有总体/工具批次超时处理。
- 每次工具调用在内存结果里记录 step、名称、参数、成功、耗时、结果长度和是否缓存；成功会话可额外保存必须回放的 provider trace。
- 没有通用任务队列/任务状态机；状态主要是本次 loop 的 messages、步骤和 SSE 事件。
- `AGENT_ARCH=multi`、专业子 Agent、聚合和风险决策代码存在，但教学配置未启用，不能写成现场运行形态。

### 技能

- 内置 15 个 YAML 技能；默认激活 `bull_trend`。
- 技能对象包含名称、说明、完整指令、required_tools、市场状态和优先级。
- 页面最多显式选择 3 个技能；显式选择覆盖默认选择。
- 在单 Agent 模式中，技能主要是 Prompt 注入；`required_tools` 是元数据，并未把单 Agent 的可见工具集严格裁剪到技能所需工具。
- 多 Agent 模式存在 `SkillAgent`，但现场未启用。

### 工具

已注册 18 个：实时行情、日线、筹码、历史分析、股票信息、组合快照、资金流、趋势、均线、量能、形态、新闻、综合情报、市场指数、板块排行以及三类回测查询。

参数由 JSON Schema 提示模型；legacy runner 最终依赖 Python handler 签名和函数内部校验，不是统一的 Pydantic 运行时校验。未知工具、缺参、错类型和 handler 异常会转成错误 JSON回填模型。

## 9. 实时数据与工具失败

1. AI 问股**有能力**获得实时行情，但只有模型实际选择 `get_realtime_quote` 且 FetcherManager 成功时才获得；不能把“工具已注册”写成“每次回答都使用实时数据”。
2. 工具事实是工具 JSON 中的行情、日线、新闻、基本面和来源字段；模型对这些事实的归纳、趋势判断和操作建议属于模型解释。
3. 实时行情失败会返回 `error`、`retriable=false` 和“改用历史数据继续”的提示；runner 会把错误结果回填模型。因此工具失败后模型仍可能生成外观完整的回答。
4. 日线工具可能读数据库缓存，也可能拉取外部源后写回 `stock_daily`；“实时/历史”必须看返回的 `source`、`cache_hit`、`partial_cache` 等字段。
5. 新闻搜索需要可用搜索服务；教学配置没有搜索 API key，代码会直接返回“无搜索引擎”。
6. 页面运行时用颜色区分 `tool_done.success`，但当前阶段标题无论成功失败都写“完成”；成功回答内只显示工具名称、耗时和红/绿色，不展示错误原因。若整个 Agent 失败，store 清除进度并只显示总错误，工具失败轨迹不会持久显示。
7. 当前教学数据库和日志没有任何 AI 问股工具调用证据，不能声称 02_AI问股截图取得过实时数据。

## 10. 模型配置、回退和失败

### 教学现场

| 角色 | 当前配置 |
| --- | --- |
| 普通分析主模型 | `openai/ByteDance-Seed/Seed-OSS-36B-Instruct` |
| Agent 模型 | 同上，显式配置为同一模型 |
| 视觉模型 | 未配置有效值；本任务没有视觉调用证据 |
| 备用模型 | 空 |
| 协议/供应商 | LiteLLM + OpenAI 兼容协议；实际 API base 是 SiliconFlow |
| Agent 回退顺序 | 只有 Seed 一项 |

代码会按“Agent 主模型 + 全局 fallback 列表”顺序尝试；限流、上下文超限和一般异常都会进入下一模型。同供应商限流会做受总超时约束的短退避，不同供应商直接切换。全部失败时返回 `provider=error`，API 的 SSE done.success=false，页面显示大模型调用错误。

教学日志中 Qwen 的 invalid JSON 后使用“文本 fallback”是输出解析降级，不是切换备用模型；Seed 成功是另一次配置/运行。数据库能记录每次使用的模型，但没有专门的“从 A 回退到 B”事件表。

### dev 现场

dev 本地配置是 DeepSeek-V3.2 主模型、Qwen3 Thinking fallback，Agent 继承主模型。该配置解释了系统设置截图，但不属于 `v0.1.0` 教学配置。

## 11. Token 数据链路

```text
LiteLLM response.usage / usage_metadata / hidden usage
  → extract_usage_payload
  → normalize_litellm_usage
     prompt/completion/total
     cache read/write/miss
     reasoning_tokens 等允许字段写入 provider_usage_json
  → runner 每次模型调用 persist_llm_usage(call_type="agent")
    或 analyzer 写 analysis/market_review
  → SQLite llm_usage
  → DatabaseManager 按时间、call_type、model SUM/MAX
  → GET /api/v1/usage/dashboard
  → TokenUsagePage
```

页面当前展示：Prompt、Completion、Total、调用次数、按模型、按调用类型、模型单次峰值和最近调用。数据库虽保存缓存和推理等归一化字段，公开 dashboard schema 和页面没有展示缓存 Token、推理 Token、成本或供应商原始细节。

教学库真实数据：

| 时间 | 类型 | 模型 | Prompt | Completion | Total | 原始 usage |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 2026-07-11 05:38:06 | analysis | DeepSeek-V3.2 | 3,886 | 2,363 | 6,249 | 有 |
| 2026-07-11 05:43:29 | analysis | Qwen2.5-7B | 12,401 | 8,192 | 20,593 | 有 |
| 2026-07-11 05:52:56 | analysis | Seed-OSS-36B | 5,392 | 3,984 | 9,376 | 有 |

合计 Prompt 21,679、Completion 14,539、Total 36,218。三条满足 `Prompt + Completion = Total`。

## 12. Token 异常原因

截图对应的 dev 库有 168 条记录：6 条普通分析/市场复盘基本可信，162 条 Agent 记录不具备真实供应商证据。

关键证据：

- 162 条 Agent 记录集中在 2026-07-11 07:32:31 和 07:35:00 附近写入。
- 它们全部 `prompt_tokens=0`、`completion_tokens=0`、`provider_usage_json=NULL`，模型和 Total 值（10、20、30、50、80、100 等）与 `tests/test_agent_executor.py`、`tests/test_multi_agent.py` 的 mock response 高度一致。
- `runner.py:458-459` 看到只含 `total_tokens` 的 usage 仍会持久化。
- `storage.py:3242-3244` 把缺失 Prompt/Completion 转成 0；`:3254-3267` 又把 normalized 分项回填为 0，无法在页面层区分“供应商明确返回 0”和“字段缺失”。
- 聚合 API只是数据库 SUM，截图精确复现 dev 表，因此不是 UI 聚合问题。

判定矩阵：

| 候选原因 | 判定 |
| --- | --- |
| 旧记录缺失 | 不是截图主因；记录是同日单测模拟写入 |
| 供应商只返回总量 | 代码允许这种情况，但现有 162 条没有供应商快照，且与 mock 值吻合，不能归因供应商 |
| 兼容层处理 | 是共同机制：缺失分项默认写 0 |
| 数据迁移 | 无证据 |
| 页面聚合 | 否；页面正确展示数据库值 |
| 默认值 | 是：存储层把缺失分项转 0 |
| 真实缺陷 | 是：测试隔离缺失污染 dev 数据库；缺失值与真实 0 混淆 |

## 13. 成本统计与费用风险

- 项目当前只统计 Token，不估算页面费用，也不计算供应商真实账单。
- LiteLLM adapter 注册个别模型价格或零价格 fallback，是为避免调用/价格映射错误；代码没有调用 `completion_cost`，`llm_usage` 也没有费用字段。
- 没有按历史价格、供应商差异、缓存折扣、回退、重试计算费用。
- 每一次 fallback 或重试若供应商已计费，可能产生额外费用；当前页面只能通过多条 Token 记录间接观察，不能给出实际金额。
- PPT 禁止写“显示实际费用”或“精准成本”；可写“记录供应商返回的 Token 用量，尚未形成费用核算”。

## 14. 测试覆盖

| 场景 | 静态测试覆盖 | 现场运行证据 |
| --- | --- | --- |
| 模型成功/失败 | 有：Agent success、error provider、unsupported tool backend | 无本轮重跑 |
| 工具失败/未知工具 | 有：handler error、unknown tool、stock scope | 无真实工具日志 |
| 工具超时 | 有：单工具和并行批次超时 | 无现场工具超时 |
| 模型回退 | 有：超时重算、限流退避、上下文超限、全失败 | 教学配置无 fallback，未现场触发 |
| Token 缺失/异常 | 有：空 usage、仅 total、负值、不可能总量、缓存形状 | 教学真实三条正常；dev 被测试污染 |
| 上下文截断/压缩 | 有：关闭最近 20、阈值、旧摘要、保护尾部 | 教学配置关闭 |
| 压缩失败 | 有：有/无旧摘要两种 fallback | 无现场触发 |
| 多轮会话 | 有：会话和压缩历史注入 | 教学库无会话 |
| 重复请求 | 前端 loading 阻止重复点击；通知发送有重复保护 | Agent API 无幂等键，缺少网络重放级测试 |

教学目录没有可信的完整 pytest 通过报告；`.pytest_cache` 只保留缓存/失败键，不能当作验收报告。本任务未重跑全套测试，避免再次写入默认数据库或触发外部依赖。

## 15. PPT 02 / PPT 03 修订建议

| 概念/页面 | v0.1.0 状态 | PPT 处理 |
| --- | --- | --- |
| 大模型与普通分析 | 已实现且有真实运行 | PPT 02 可用教学库 3 条完整 usage 和 Seed 成功日志 |
| AI 问股 | 代码已实现，现场无成功会话 | PPT 03 标“代码能力已实现；本次教学资产未留成功调用证据” |
| Agent 循环 | 已实现 | 拆成“循环原理”和“现场证据边界”两页 |
| 技能 | 已实现为 YAML + Prompt/元数据 | 不要讲成插件进程或独立模型 |
| 工具调用 | 已实现，现场无真实轨迹 | 使用代码流程图；不要用空截图证明实时工具成功 |
| 实时数据 | 部分实现/按需调用 | 加“工具成功、缓存、降级、失败”四态限制页 |
| 多 Agent | 代码存在、现场未启用 | 标后续版本/高级内容，不写成当前运行架构 |
| 上下文压缩 | 后端已实现、现场关闭 | UI 开关可讲；必须标默认关闭和摘要风险 |
| 模型回退 | 代码支持、现场未配置 | 区分“输出解析降级”和“模型切换回退” |
| Token 用量 | 已实现 | 改用教学库 3 条真实记录重做证据；弃用 168 条截图 |
| Token 异常 | dev 测试污染 + 缺失值默认 0 | 单独增加“为什么 0+0≠Total”问题分析页 |
| 成本 | 当前没有 | 删除“实际费用”表述；增加“Token≠账单”限制页 |
| 系统设置 | 已实现 | 使用教学配置截图时需脱敏，并标清主模型/Agent继承/备用为空 |

内容不足时建议新增：AI 问股端到端链路、工具事实与模型解释、上下文压缩状态机、Token 异常取证、当前限制与后续版本五页；不制作备注或口播稿。

## 16. v0.1.0 当前限制

1. 教学资产没有成功 AI 问股会话、工具轨迹或 Agent Token 证据。
2. 教学默认单 Agent；多 Agent 只是可配置代码能力。
3. 技能在单 Agent 中主要是 Prompt，不强制限定工具集合。
4. 普通聊天不预取实时行情/新闻/基本面；是否调用由模型决定。
5. 工具失败后模型仍可继续生成；最终文本可能掩盖数据缺失。
6. 工具事件 UI 不显示错误原因，失败会话还会清空临时进度。
7. 压缩默认关闭；开启后有事实丢失风险，且保护尾部过大时可能仍超上下文。
8. Agent fallback 现场为空；代码支持不等于已验证。
9. usage 缺失字段被存为 0，无法区分缺失与真实零值。
10. Token dashboard 不展示缓存/推理细分，也不统计费用。
11. Agent API 无请求幂等键，网络级重复提交可能重复写消息和 Token。
12. 现有 E2E 页面审计只验证页面可访问，不验证 AI、工具和 Token 真实性。

## 17. dev 差异与后续版本候选

### 已确认差异

- `version/v0.1.0..dev` 仅新增页面审计 spec/catalog、package scripts、Playwright 配置和 changelog；AI 业务代码无提交差异。
- 当前 dev 未提交 `src/stock_analyzer.py` 改动只是技术分析阈值注入，与 AI 问股/Token 无关。
- dev 本地配置为 DeepSeek 主模型 + Qwen fallback；教学配置为 Seed 且无 fallback。
- dev 数据库有较早普通分析数据和单测污染；教学数据库更干净。

### 后续版本候选

1. 测试强制使用临时数据库，禁止默认落到开发库。
2. Token 字段使用 nullable/observed 标志区分“缺失”和“0”。
3. 页面显示 usage 证据状态、缓存/推理 Token 和数据来源。
4. 保存并展示脱敏工具轨迹与失败原因。
5. 增加 Agent 请求幂等键和重复提交测试。
6. 为上下文摘要增加事实校验/可视化和丢弃 trace 诊断。
7. 建立真实但低成本的 AI 问股 smoke fixture，并明确费用上限。

这些都是候选，不代表 dev 已实现或承诺进入 v0.1.1。

## 18. 金融数据源专题候选

- 实时行情多源 fallback、缓存、熔断和时效字段。
- 日线缓存与“实时行情/历史 K 线”的口径区别。
- 新闻搜索 API 的可用性、授权、成本和结果时效。
- 基本面 provider chain 的 not_supported/failed/partial 状态。
- 数据源失败后模型仍生成回答的金融风险。
- 免费数据源与商业数据源的稳定性、授权和教学成本。

本报告只登记候选，不在当前课件展开。

## 19. 新增或更新的问题

- 更新 `RDSA-COURSE-ISSUE-001`：ZIP 已映射到 `4eb23fbb...`，追溯缺口闭环。
- 更新 `RDSA-COURSE-ISSUE-008`：确认截图异常来自 dev 测试模拟数据 + 缺失字段默认 0，不是教学库或 UI 求和错误。
- 新增 `RDSA-COURSE-ISSUE-013`：Agent 单测可把 mock usage 写入默认数据库，污染 Token 页面证据。

## 20. 本次落盘文件

- `docs/course-audit-ai-agent-token.md`：本报告。
- `docs/course-issues.md`：更新 001/008，新增 013。
- `E:\RuyiTypora\如意\任务\RuyiDailyStockAnalysis\active.md`：任务状态、报告和结论摘要。

## 21. 未确认事项

1. 教学本地凭据当前是否仍有效：未测试，也不应在审计中测试。
2. AI 问股在教学配置下真实调用 Seed 模型是否成功：无现有会话/日志，本次未付费重跑。
3. 18 个工具在教学现场的逐工具在线成功率：无现有 Agent 轨迹，本次未发起外部请求。
4. 压缩开启后的真实摘要质量和事实保真度：只有单测，无教学现场样本。
5. 模型 fallback 在教学现场的真实切换和计费：教学配置无 fallback。
6. 视觉模型的最终运行选择：教学配置未提供有效视觉模型，本任务未调用图像理解。
7. 全量测试当前通过率：没有可信的现成完整报告，本次未执行全套测试。

以上未确认项均不得写成 `v0.1.0` 已验证功能。
