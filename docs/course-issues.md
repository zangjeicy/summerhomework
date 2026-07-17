# 课程问题索引

本索引记录课程开发中需要核验或闭环的问题。除已有证据确认的治理缺口外，初始状态保持“待核验”，不得据此断言项目存在缺陷或提前承诺修复版本。

## 优先级

- P0：数据、安全或严重业务错误。
- P1：核心功能或课程被阻塞。
- P2：设计、体验、架构或可维护性问题。
- P3：文案、命名、提示或一般优化。

## 问题模板

每个问题至少维护：问题编号、来源任务、描述、证据、影响、优先级、关联课件/模块、后续核验任务、状态，以及以下版本与教学字段：

- 发现于课程版本
- 影响课程版本
- 当前版本处理方式
- 计划修复版本
- `dev` 状态
- 是否需要新增升级课程
- 是否影响 PPT
- 是否影响讲师备注
- 是否影响学生代码包
- 关联升级课件

无法确认计划版本时写“后续版本候选”，不能提前承诺 `v0.1.1`。

## 初始问题基线

| 问题编号 | 来源任务 | 问题描述 | 当前证据 | 影响 | 优先级 | 关联课件/模块 | 后续核验任务 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RDSA-COURSE-ISSUE-001 | RDSA-PPT01-REVISION-AUDIT-003 / RDSA-COURSE-CONTROL-BASELINE-006 / RDSA-AI-AGENT-TOKEN-AUDIT-008 | `v0.1.0` 教学 ZIP 与历史 Git commit 的映射暂不完整 | ZIP 内 1006 个文件与教学目录逐文件匹配；教学目录 1006 个跟踪 blob 全部匹配 `version/v0.1.0` 提交 `4eb23fbb1242b773e789373e7035e570f7075798` | 追溯缺口已闭环 | P2 | PPT 01；版本/代码包 | 后续 manifest 可直接记录已确认 commit 和 ZIP SHA-256 | 已确认 |
| RDSA-COURSE-ISSUE-002 | RDSA-PPT01-REVISION-AUDIT-003 / RDSA-COURSE-CONTROL-BASELINE-006-REV1 | PPT 01 旧控制文件仍为 15 页，与正式 PPTX 32 页不同步 | 正式 PPTX 有 32 个 slide XML；07:09 的 outline/actual/comparison/progress 为 15 页 | 后续自动比对可能使用过期状态 | P2 | PPT 01；RuyiWriter 状态资产 | PPT 01 正式重构前重建控制状态 | 已确认 |
| RDSA-COURSE-ISSUE-003 | RDSA-PPT01-REVISION-AUDIT-003 | PPT 01 缺少完整可复现生成源 | 尚未形成输入、模板、字体、生成命令和最终 32 页控制快照清单 | 无法稳定重建或审计 | P1 | PPT 01；RuyiWriter/PPT 生成链 | PPT 01 正式重构任务 | 待核验 |
| RDSA-COURSE-ISSUE-004 | RDSA-PPT02-OUTLINE-DESIGN-004 / RDSA-PORTFOLIO-TRUTH-AUDIT-007 | 账户成本法与收益口径需要按真实实现修订 | 已确认同时支持 FIFO 与 AVG；买入费用/税进入成本、卖出费用/税扣减收入；现金分红不计 realized；无总收益/TWR/XIRR/仓位字段；后端 93 项、前端 32 项测试通过 | 原 PPT 若写单一成本法、总收益或仓位既有字段会误教 | P1 | PPT 02；Portfolio | PPT 02 正式修订 | 口径已确认，课程待修订 |
| RDSA-COURSE-ISSUE-005 | RDSA-PPT02-OUTLINE-DESIGN-004 / RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | Cookie 与 Bearer Token 的讲解需按 `v0.1.0` 真实实现修正 | 管理 API 只检查签名会话 Cookie；Bearer Token 仅用于模型、搜索、Slack/ntfy/自定义 Webhook 等外部服务出站认证 | 把 Bearer 写成管理员登录方式会误教 | P1 | PPT 02/03；Auth | PPT 02/03 按认证边界修订 | 已确认，课程待修订 |
| RDSA-COURSE-ISSUE-006 | RDSA-PPT03-RESTRUCTURE-AUDIT-005 / RDSA-PORTFOLIO-TRUTH-AUDIT-007 / RDSA-AUTOMATION-FEATURE-AUDIT-009 | 多个页面截图只有空状态或未启用状态 | Portfolio 为 8 表全空；智能选股为 AlphaSift 禁用、回测为合法 404 空态、告警为 0 规则/0 触发/0 通知；截图均来自 `D:\quant` dev 运行目录和开发库 | 页面可打开和空状态不能证明 `v0.1.0` 业务写操作或成功态 | P1 | PPT 03；Web/API/Service | PPT 03 按模块标注空态；后续仅在隔离库补固定成功案例 | 007/009 子项已确认 |
| RDSA-COURSE-ISSUE-007 | RDSA-PPT03-RESTRUCTURE-AUDIT-005 / RDSA-PORTFOLIO-TRUTH-AUDIT-007 / RDSA-AUTOMATION-FEATURE-AUDIT-009 | 第 25 页“不是 Mock”的证据不足 | Portfolio 只有真实 GET 无写操作；自动化截图来自 dev，教学库只证明核心分析/报告真实运行，不能证明选股、回测、告警、调度和通知完成 | 页面/API 可访问不等于真实业务闭环；绝对表述有真实性风险 | P1 | PPT 03 第 25 页 | 删除断言，按页面、API、数据库/日志和测试分层说明 | 007/009 子项已确认 |
| RDSA-COURSE-ISSUE-008 | RDSA-PPT03-RESTRUCTURE-AUDIT-005 / RDSA-AI-AGENT-TOKEN-AUDIT-008 | Token 分项为 0、总量非 0 的统计口径疑点 | 截图对应 dev 库 162 条 Agent mock usage；供应商快照为空，数值与单测一致；持久化把缺失 Prompt/Completion 写成 0；教学库 3 条真实 analysis usage 分项完整 | 现有 Token 截图不能作为 `v0.1.0` 或真实 Agent 用量证据；缺失值与真实 0 混淆 | P1 | PPT 03；Agent/Token | 报告 `course-audit-ai-agent-token.md`；后续版本候选为 usage 证据状态和 nullable 语义 | 已确认 |
| RDSA-COURSE-ISSUE-009 | RDSA-PPT03-RESTRUCTURE-AUDIT-005 / RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 登录截图被误当作普通登录或真实首次设密证据 | Playwright 明确 mock `/api/v1/auth/status` 为认证开启、未登录、未设密码；教学目录实际认证关闭且无密码/会话文件 | 页面名称和教学步骤误导，无法证明真实登录流程 | P1 | PPT 03；Auth/Login | 登录截图标为 mock 首次设置 UI；真实流程后续单独验收 | 已确认，课程待修订 |
| RDSA-COURSE-ISSUE-010 | RDSA-PPT02-OUTLINE-DESIGN-004 / RDSA-PPT03-RESTRUCTURE-AUDIT-005 / RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 管理 API 认证边界与公开部署条件需要明确 | 认证开启时除白名单外 `/api/v1/*` 只接受 Cookie；认证关闭时统一放行；无管理员 Bearer 或角色模型 | API 演示和公网部署可能越权或误配 | P1 | PPT 02/03；Auth/Admin API | 按 Cookie/关闭门禁/白名单矩阵讲解并增加公网限制页 | 已确认，课程待修订 |
| RDSA-COURSE-ISSUE-011 | RDSA-COURSE-CONTROL-BASELINE-006 / RDSA-COURSE-CONTROL-BASELINE-006-REV1 | `v0.1.0` PPT 页面与教学 ZIP 内代码路径缺少稳定映射 | PPT 01/02/03 明确属于 `v0.1.0`，ZIP 是代码真相源；`dev` 仅供后续版本参考 | 影响逐页复查和升级影响评估 | P1 | PPT 01/02/03；ZIP/docs | 007～010 + manifest 补证 | 已确认 |
| RDSA-COURSE-ISSUE-012 | RDSA-COURSE-CONTROL-BASELINE-006 | 缺少统一的问题收集、修复和复验闭环 | 本索引和总控说明已建立最小闭环 | 问题容易重复或失联 | P2 | 全课程；docs/RuyiTypora | RDSA-COURSE-CONTROL-BASELINE-006-REV1 验收 | 文档已更新 |
| RDSA-COURSE-ISSUE-013 | RDSA-AI-AGENT-TOKEN-AUDIT-008 | Agent 单测的 mock usage 可写入默认开发数据库 | dev 库在数秒内写入 162 条 `agent` 记录；模型和 Token 数值与 `test_agent_executor.py` / `test_multi_agent.py` mock 一致；非 usage 专项测试未统一 patch `src.agent.runner._persist_usage` | 污染 Token 页面、模型统计和课程截图，无法区分真实供应商调用与测试记录 | P1 | PPT 03；Agent/Token；测试隔离 | 后续版本候选：测试强制临时数据库或全局禁用真实 usage 持久化 | 已确认 |
| RDSA-COURSE-ISSUE-014 | RDSA-PORTFOLIO-TRUTH-AUDIT-007 | 多币种估值在缺汇率和 JP/KR/TW 默认币种上存在不真实口径 | 缺 FX 时 `_convert_amount` 按 1:1 返回并标 stale；旧缓存不按年龄自动 stale；Web 交易/公司行为不传 currency，后端仅 hk/us 有正确默认币种，其余默认 CNY；JP/KR/TW 被标 partial | 可显著误算跨市场现金、市值、权益、盈亏与风险 | P1 | PPT 02/03；Portfolio/FX | 后续版本候选：币种契约、freshness、缺失估值策略 | 已确认 |
| RDSA-COURSE-ISSUE-015 | RDSA-PORTFOLIO-TRUTH-AUDIT-007 | 总收益/净值未实现，现有回撤受外部现金流和自然日回填影响 | API 只有 realized/unrealized；现金分红不进入 realized；无 TWR/XIRR；回撤直接使用 total_equity 并逐自然日回填 | 易把账户权益变化误讲成投资收益或标准净值回撤 | P1 | PPT 02/03；收益/风险 | 后续版本候选：净现金流调整、净值、TWR/XIRR 和交易日序列 | 已确认 |
| RDSA-COURSE-ISSUE-016 | RDSA-PORTFOLIO-TRUTH-AUDIT-007 | 公司行为仅支持现金分红和拆并股，且分红税/资格边界简化 | action type 只有 `cash_dividend/split_adjustment`；同日固定公司行为先于交易；无股票分红、送股、配股、碎股、现金替代、预扣税或自动抓取 | 不能把当前实现讲成完整公司行为处理 | P2 | PPT 02/03；Portfolio/公司行为 | 后续版本候选：扩展 action model 与税费/资格规则 | 已确认 |
| RDSA-COURSE-ISSUE-017 | RDSA-PORTFOLIO-TRUTH-AUDIT-007 | Portfolio CSV 导入缺少批次事务、整批回滚和完整错误/市场契约 | 仅 CSV；逐条 `record_trade`；无批次 ID 或整体回滚；多数非法行只计 skipped；不解析 market；Excel 属于另一自选股导入入口 | 批量导入可部分成功，课程和用户可能误以为全有或全无 | P2 | PPT 03；Portfolio/CSV | 后续版本候选：批次、事务策略、逐行错误、market/Excel 规格 | 已确认 |
| RDSA-COURSE-ISSUE-018 | RDSA-AUTOMATION-FEATURE-AUDIT-009 | 后台任务缺少取消、跨重启恢复、跨实例去重和通用失败重试闭环 | 任务、future、在途股票和 SSE 事件仅在进程内；有 cancel 状态/UI 但无取消 API/队列方法；无任务表和持久游标 | 若讲成可靠队列、断点续跑或自动重试将与实现不符 | P1 | PPT 02/03；后台任务/SSE | 后续版本候选：持久任务、取消协议、恢复、分布式幂等 | 已确认 |
| RDSA-COURSE-ISSUE-019 | RDSA-AUTOMATION-FEATURE-AUDIT-009 | 自动化模块缺少 v0.1.0 教学环境成功态业务证据 | 教学库回测/告警/通知均为 0，AlphaSift 和调度关闭；只有核心分析与报告有真实运行证据 | 选股、回测、告警、通知成功/失败/降级素材不足 | P1 | PPT 02/03；选股/回测/告警/调度/通知 | 在隔离、可重置数据副本中设计固定案例 | 已确认 |
| RDSA-COURSE-ISSUE-020 | RDSA-AUTOMATION-FEATURE-AUDIT-009 | 告警市场区域的前端选项、后端约束与测试期待漂移 | Vitest 70 项中 1 项失败：测试期待日/韩，当前前端仅中/港/美；后端市场灯测试又明确拒绝日/韩 | 测试红灯且课程可能误讲市场覆盖 | P2 | PPT 03；告警表单/市场灯 | 先确认产品范围，再统一前端、后端、测试和文档 | 已确认，待产品决策 |
| RDSA-COURSE-ISSUE-021 | RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 页面验收缺少版本、工作树、配置、数据库、认证和数据 provenance，登录页还使用 mock | JSON 只保存路由、错误数组、截图路径/哈希；截图来自 dev 工作树，登录状态由 route fulfill 构造；`src/stock_analyzer.py` 的未提交修改早于截图 | 不能把十页报告整体当作 `v0.1.0` 同一会话或纯净工作树业务验收 | P1 | PPT 03；页面截图/验收 | 后续验收报告补 commit/worktree/config/db/auth/data/操作元数据 | 已确认 |
| RDSA-COURSE-ISSUE-022 | RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 多数敏感配置未服务端遮盖，认证关闭时配置 API 无管理员门禁 | `get_config()` 只遮盖 5 类特殊键；认证中间件关闭时放行 `/api/v1/system/config`；教学 `.env` 保存了真实模型凭据 | 局域网/公网可能读取敏感配置，课程不能宣传为安全默认 | P0 | PPT 02/03；设置/Auth/部署 | 后续版本候选：统一服务端遮盖并强制高风险配置门禁 | 已确认，未修复 |
| RDSA-COURSE-ISSUE-023 | RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 首次就绪检查可把占位通知凭据判为已配置，简短试跑只证明任务受理 | 当前占位 App Key/Secret 被判 configured，但日志记录无有效通知；按钮仅取得异步 task ID/accepted，不轮询终态 | “配置完成/连接成功/全部能力通过”会被夸大 | P1 | PPT 02/03；首次设置/验收 | 课程改口径；后续版本增加占位识别与终态证据 | 已确认 |
| RDSA-COURSE-ISSUE-024 | RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 登录限流为内存单进程，XFF 信任缺少可信代理 allowlist | 5 次/300 秒计数只在进程内；`TRUST_X_FORWARDED_FOR=true` 时直接取最右地址，未验证请求代理来源 | 多实例、重启和不可信反代下不能视为完整防暴力破解 | P1 | PPT 02/03；安全/部署 | 增加限制页；后续版本候选为共享限流和可信代理模型 | 已确认 |
| RDSA-COURSE-ISSUE-025 | RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 密码恢复与会话注销语义有限 | 无 Web 找回；仅 CLI 交互重置；改密不旋转 session secret；退出会旋转全局 secret 使全部会话失效 | 课程若讲成完整账号恢复或单会话退出会失真 | P2 | PPT 03；登录/密码恢复 | 工程附录明确边界；后续版本候选为受控恢复和会话管理 | 已确认 |
| RDSA-COURSE-ISSUE-026 | RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 配置测试与真实 `.env` 存在混跑顺序污染 | 372 项混跑为 354 通过/18 失败；拆分并在配置套件启动前指定空 `ENV_FILE` 后 241 项全过，其他 131 项全过 | “全量测试全绿”不可直接声称，执行顺序可能制造假失败 | P1 | 工程验收；测试隔离 | 后续版本候选：全局临时 ENV_FILE/数据库隔离 | 已确认 |
| RDSA-COURSE-ISSUE-027 | RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010 | 课程/API/Web/登录视觉版本标签不统一 | 课程为 v0.1.0，API 写 1.0.0，Web package 为 0.0.0 后回退 build ID，登录页固定写 V3.X | 学生难以判断真实代码和构建版本 | P2 | PPT 02/03；版本信息 | 课程解释标签层级；后续版本统一发布元数据 | 已确认 |

## 版本与教学处理台账

| 问题 | 发现于课程版本 | 影响课程版本 | 当前版本处理方式 | 计划修复版本 | dev 状态 | 新增升级课程 | 影响 PPT | 影响讲师备注 | 影响学生代码包 | 关联升级课件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | v0.1.0 | v0.1.0 追溯资料 | 记录 ZIP SHA-256 与已确认 commit `4eb23fbb...` | 已完成文档补证，不改变课程版本 | 已确认同一基线 | 否 | 是，补充资产说明 | 是 | 否 | 无 |
| 002 | v0.1.0 | v0.1.0 PPT 01 制作控制 | 以正式 PPTX 32 页为准，旧 15 页控制文件标记过期 | v0.1.0 制作资料修订 | 不涉及代码 | 否 | 是 | 是 | 否 | 无 |
| 003 | v0.1.0 | v0.1.0 PPT 01 | 发布前补齐可复现生成资料 | v0.1.0 课程资产完善 | 不涉及代码 | 否 | 是 | 是 | 否 | 无 |
| 004 | v0.1.0 | v0.1.0 PPT 02 | 按 FIFO/AVG、费用税、realized/unrealized 真实公式重写；总收益和仓位标为未实现 | 课程资产修订；业务增强为后续版本候选 | 与 v0.1.0 无 portfolio 差异 | 是 | 是 | 否（不使用讲师备注） | 否 | 后续 Portfolio 增量课候选 |
| 005 | v0.1.0 | v0.1.0 PPT 02/03 | 管理 API 讲 Cookie；Bearer 仅讲外部服务出站认证 | 课程修订；业务增强为后续版本候选 | 与 v0.1.0 无认证业务差异 | 是 | 是 | 否 | 否 | 认证边界 |
| 006 | v0.1.0 | v0.1.0 PPT 03 | Portfolio/选股/回测/告警截图仅用于空态；成功态需隔离演示数据 | 课程证据补强；代码能力后续按问题处理 | `dev` 仅新增验收工具，相关截图仍为空/禁用 | 是 | 是 | 否（不使用讲师备注） | 否 | 页面成功状态案例 |
| 007 | v0.1.0 | v0.1.0 PPT 03 | 删除“业务已真实完成”绝对断言；按页面/API/库日志/测试分层 | 课程证据补强 | 页面验收工具未增加业务写操作证据 | 可能 | 是 | 否（不使用讲师备注） | 否 | 证据可信度 |
| 008 | v0.1.0 | v0.1.0 PPT 03 | 弃用 168 条 dev 截图；改用教学库 3 条分项完整记录，并增加异常取证限制页 | 后续版本候选：缺失值语义和证据状态 | dev 当前仍受污染 | 是 | 是 | 否（不改代码包） | 否 | Token 异常与数据可信度 |
| 009 | v0.1.0 | v0.1.0 PPT 03 | 登录图标为 mock 首次设置 UI，不当作真实登录证据 | 后续版本候选：真实状态矩阵验收 | dev 只有 mock 预览工具 | 是 | 是 | 否 | 否 | 登录状态矩阵 |
| 010 | v0.1.0 | v0.1.0 PPT 02/03 | 按 Cookie/白名单/认证关闭放行矩阵讲解 | 后续版本候选：细粒度权限 | 无相关业务差异 | 是 | 是 | 否 | 是，若安全修复 | 管理 API 安全 |
| 011 | v0.1.0 | v0.1.0 全课程 | 建立 PPT 页面到 ZIP 代码路径映射；dev 单列差异 | 文档补证 + 后续版本持续维护 | 未开始 | 否 | 是 | 是 | 否 | 无 |
| 012 | v0.1.0 | 所有版本 | 使用现有编号、状态和双层落盘闭环 | 已完成基线 | 不涉及代码 | 否 | 否 | 是 | 否 | 无 |
| 013 | v0.1.0 | PPT 03 的 Token 证据和开发验收 | 当前课程明确标注截图污染，不把 mock 数据当真实用量 | 后续版本候选 | 未修复 | 是 | 是 | 否 | 待定 | 测试隔离与可观测性 |
| 014 | v0.1.0 | v0.1.0 PPT 02/03 与跨市场持仓 | 明示 1:1 stale 降级与 JP/KR/TW partial；A/H/美为主讲范围 | 后续版本候选 | 无差异 | 是 | 是 | 否（不使用讲师备注） | 是，若修复后重发 | 汇率与跨市场增量课候选 |
| 015 | v0.1.0 | v0.1.0 PPT 02/03 收益/风险 | 不宣称总收益/标准净值回撤；展示当前权益回撤限制 | 后续版本候选 | 无差异 | 是 | 是 | 否（不使用讲师备注） | 是，若修复后重发 | 收益与风险增量课候选 |
| 016 | v0.1.0 | v0.1.0 PPT 02/03 公司行为 | 只讲现金分红与拆并股，列出未支持项 | 后续版本候选 | 无差异 | 可能 | 是 | 否（不使用讲师备注） | 是，若扩展模型 | 公司行为专题候选 |
| 017 | v0.1.0 | v0.1.0 PPT 03 CSV | 明示 CSV、逐条提交、部分成功、无批次回滚/Excel/market | 后续版本候选 | 无差异 | 可能 | 是 | 否（不使用讲师备注） | 是，若改变导入契约 | 券商数据格式专题候选 |
| 018 | v0.1.0 | PPT 02/03 后台任务 | 只讲单进程内存队列、SSE 重连和用户重提，明确无持久恢复/取消闭环 | 后续版本候选 | 无相关业务差异 | 是 | 是 | 否 | 待定 | 可靠任务与恢复机制 |
| 019 | v0.1.0 | PPT 02/03 自动化证据 | 展示当前空态与限制；成功态仅在隔离副本采集 | 后续版本候选 | 业务代码与 v0.1.0 相同 | 是 | 是 | 否 | 否 | 自动化固定案例 |
| 020 | v0.1.0 | PPT 03 告警市场覆盖 | 暂按后端已验收范围讲中/港/美，日/韩标为未确认 | 后续版本候选 | 未修复 | 可能 | 是 | 否 | 待定 | 告警市场覆盖 |
| 021 | v0.1.0 | PPT 03 页面证据 | 页面截图只作渲染/空态证据，单列 dev 与 mock | 后续版本候选：provenance 报告 | dev 仅有基础审计工具 | 是 | 是 | 否 | 否 | 页面证据工程 |
| 022 | v0.1.0 | PPT 02/03 配置安全 | 明示认证关闭和服务端遮盖限制，不用于公网安全示范 | 后续版本候选 | 未修复 | 是 | 是 | 否 | 是，修复后重发 | 配置与秘密管理 |
| 023 | v0.1.0 | PPT 02/03 首次设置 | “已配置”改为静态检查，“试跑”改为任务受理 | 后续版本候选 | 无相关业务差异 | 是 | 是 | 否 | 是，若改变状态语义 | 分层验收 |
| 024 | v0.1.0 | PPT 02/03 安全部署 | 讲清单进程限流、XFF 和可信代理限制 | 后续版本候选 | 未修复 | 是 | 是 | 否 | 是，修复后重发 | 反向代理安全 |
| 025 | v0.1.0 | PPT 03 密码恢复 | 只讲页面改密和 CLI 重置，明确无 Web 找回及会话语义 | 后续版本候选 | 无相关业务差异 | 可能 | 是 | 否 | 是，若扩展恢复 | 账号恢复与会话 |
| 026 | v0.1.0 | 工程验收 | 分套件记录 241+131 通过，同时披露混跑污染 | 后续版本候选 | 未修复 | 是 | 是 | 否 | 是，若测试基线变化 | 测试隔离 |
| 027 | v0.1.0 | PPT 02/03 版本信息 | 分开说明课程版/API版/Web build/视觉文案 | 后续版本候选 | 无相关业务差异 | 否 | 是 | 否 | 是，若统一版本 | 发布与追溯 |

## 更新规则

- 新问题先按描述、页面/API/模块和证据指纹去重，同一根因只保留一个主问题编号。
- 007～010 必须分别记录 `v0.1.0` ZIP 事实、PPT 讲法、已知问题、`dev` 差异、下一版本候选、docs 和教学互动价值。
- 状态推进必须附证据；`dev` 修复不能自动等同于当前课程已修复，也不能自动承诺进入 `v0.1.1`。
- 问题关闭后保留记录，并补充实际进入的课程版本、代码包和升级课件；不得删除历史。

## 计划中的专项报告

- `RDSA-PORTFOLIO-TRUTH-AUDIT-007` → `docs/course-audit-portfolio-truth.md`
- `RDSA-AI-AGENT-TOKEN-AUDIT-008` → `docs/course-audit-ai-agent-token.md`
- `RDSA-AUTOMATION-FEATURE-AUDIT-009` → `docs/course-audit-automation-features.md`
- `RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010` → `docs/course-audit-config-auth-evidence.md`

`RDSA-PORTFOLIO-TRUTH-AUDIT-007`、`RDSA-AI-AGENT-TOKEN-AUDIT-008`、`RDSA-AUTOMATION-FEATURE-AUDIT-009` 与 `RDSA-CONFIG-AUTH-EVIDENCE-AUDIT-010` 均已完成并生成专项报告。
