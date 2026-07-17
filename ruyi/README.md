# ruyi/ —— 如意二开层资产目录

> 本目录集中存放**如意二开层**（相对上游 `ZhuLinsen/daily_stock_analysis` 的差异化资产）：二开专属文档、脚本、验证工具。
> 隔离原则：二开资产优先收敛到本目录与**新增文件**，不侵入上游主干文件；确需挂接上游代码时（如注册新数据源），只做最小挂接点并配置门控（不配置即不生效）。
> 参照范式：`RuyiDocsGPT` 的 `ruyi/` 隔离层（同步上游几乎零冲突）。

## 目录约定

| 路径 | 用途 |
|---|---|
| `ruyi/docs/` | 二开层文档（发布通道、二开方案、上游同步纪律） |
| `ruyi/scripts/` | 二开层脚本（环境探针、验证工具） |

## 二开路线（差异化核心）

上游给不了、贴合中国散户实际玩法的本土化增强：

1. **QMT 接入**（xtquant）：行情/竞价数据直连券商 miniQMT 终端；
2. **集合竞价**：9:15-9:25 竞价快照采集与竞价指标计算（匹配价、竞价量、竞价金额、竞价换手、竞昨比等）；
3. **自研策略**：接入自己的选股/择时策略。

> **节奏（2026-07-04 决策）**：配套课程定位**入门**，当前主线是以上游原有功能带读者跑通 AI 量化分析（书 1-8 章）；**QMT/竞价二开后置**，不作为近期开发主线。竞价模块将来实现时采用「免费源默认（东财/pytdx，复用 `data_provider/` 现有 fetcher）+ QMT 可选增强」的可插拔设计，不把券商开户门槛加给读者。本目录的骨架与探针是为后置阶段预留的长期资产。

进度与任务看板：`E:\RuyiTypora\如意\任务\RuyiDailyStockAnalysis\active.md`（RDS-*）。

## QMT 环境前置

QMT 数据链路的三个前置条件（缺一不可）：

1. 券商 QMT 客户端已安装且**开启 miniQMT 模式**（本机：国金 QMT，`C:/dev/guojin_qmt_shipan`）；
2. QMT 终端**处于登录运行状态**（xtquant 是连接本地终端取数，终端不开则连不上）;
3. Python 环境安装 `xtquant`（`pip install xtquant`，属二开层可选依赖，**不进** `requirements.txt`，未安装不影响上游主流程）。

环境自检：

```bash
python ruyi/scripts/qmt_probe.py            # 全链路探针：库 → 连接 → 行情字段
python ruyi/scripts/qmt_probe.py 600519 000001   # 指定探测标的
```

## 上游同步纪律

- `upstream` 已配置 `tagOpt = --no-tags`（`git config remote.upstream.tagOpt`）：**不拉取上游 tag**，避免与自有发版 tag 撞名。
- 同步节奏：每周 `git fetch upstream && git merge upstream/main`；二开资产集中在本目录与新增文件，冲突面极小。
- 从 upstream 同步进来的提交保持原貌；我们自己的提交遵循 `.claude/rules/git.md`（详细中文 message）。

## 与书的双向绑定

本仓库是《大鹏 AI 量化实战：从零打造每日金股分析系统》的主线项目（书稿在 `D:\notes\RuyiBookCourse\图书\金融量化\`）：改项目要联想对应章节，写章节拿项目真实运行结果反向验证；本目录的 QMT/竞价二开对应书第九章。
