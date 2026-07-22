# ML+LLM 融合轻量 AI 量化交易预测系统 — 项目背景与改进建议

---

## 一、项目背景

### 1.1 现有项目能力

当前项目（金股睿析 / 前身 RuyiDailyStockAnalysis）是一个成熟的**AI 股票分析系统**，覆盖 A 股/港股/美股，核心能力包括：

| 模块 | 能力 | 技术路线 |
|------|------|---------|
| 📊 **多数据源聚合** | 行情、K线、技术指标、新闻、公告、基本面 | 8 个数据源 + 自动降级 |
| 🤖 **LLM 分析** | 技术面+消息面+AI 生成决策报告 | LiteLLM（Gemini/OpenAI/Claude 等统一网关） |
| 🧠 **Agent 策略问股** | 15 种内置策略（均线/缠论/波浪/热点等） | 多 Agent 编排 |
| 📈 **技术指标** | 多头排列、乖离率、量能、筹码结构 | 规则引擎 + pandas/numpy |
| 🚀 **自动化推送** | 企业微信/飞书/Telegram/Discord/Slack/邮件 | 多通道通知 |
| 🌐 **Web 工作台** | 手动分析、回测、持仓、配置管理 | React + FastAPI |

### 1.2 现有局限

尽管系统已相当完善，但存在三个关键缺失：

1. **无 ML 预测模型** — 所有分析依赖规则指标 + LLM 文本分析，没有从历史数据中学习价格模式的 ML 模型
2. **特征工程空白** — 虽有技术指标计算，但缺少系统性的特征提取、选择和标准化流程
3. **LLM 与信号未融合** — LLM 分析结果和量化信号各自独立，没有统一的置信度加权融合框架

### 1.3 目标定位

**轻量 ML + LLM 融合量化交易预测系统** — 在现有基础上：
- 保持系统的轻量化和易部署（不引入 GPU/大规模训练基础设施）
- 用 ML 模型从历史数据中学习可预测的模式
- 将 ML 预测信号与 LLM 语义分析信号融合，产生更稳健的决策
- 所有新增模块可独立开关，不破坏现有功能

---

## 二、改进建议

### 建议一：轻量 ML 预测管道（Lightweight ML Prediction Pipeline）

**核心思路**：在 `src/core/` 下新增 `ml_predictor` 模块，使用 sklearn 级轻量模型（RandomForest / XGBoost / LogisticRegression）从历史 K 线 + 技术指标中训练价格方向预测。

**具体实现**：

```
src/core/ml_predictor/
├── __init__.py
├── trainer.py          # 模型训练：特征准备 -> 训练 -> 保存/加载
├── predictor.py        # 推理：对当前股票生成预测信号
├── features.py         # 特征工程：从 K 线 + 技术指标提取特征向量
├── models/             # 训练好的模型文件存储位置
└── schemas.py          # 预测结果数据结构
```

**关键设计**：

| 维度 | 设计 |
|------|------|
| **模型选型** | XGBoost（优先）/ RandomForest（兜底）— 轻量、无需 GPU、可解释性强 |
| **预测目标** | 二分类：未来 N 日涨/跌；回归：未来 N 日预期收益率；多分类：强涨/弱涨/盘整/弱跌/强跌 |
| **特征来源** | 现有计算好的技术指标（MA/RSI/KDJ/MACD/量比/换手率/乖离率）+ 价格序列特征 |
| **训练频率** | 自动周训练 + 手动触发；滚动窗口训练避免概念漂移 |
| **无需 GPU** | 纯 CPU 训练，单次训练 < 5 分钟 |

**输出信号**（通过现有 `DecisionSignal` 管道注入）：

```python
@dataclass
class MLPrediction:
    stock_code: str
    direction: Literal["up", "down", "neutral"]
    confidence: float        # 0.0 ~ 1.0
    expected_return: float   # 预期收益率
    model_version: str
    feature_importance: dict  # 特征贡献度（可解释性）
    prediction_date: date
```

---

### 建议二：特征工程与多维因子系统（Feature Engineering & Multi-Factor System）

**核心思路**：在 `data_provider/` 下新增 `factors/` 模块，构建系统化的因子计算管线，作为 ML 模型的特征源和独立信号源。

**具体实现**：

```
data_provider/factors/
├── __init__.py
├── base.py               # 因子基类 + 因子注册器
├── technical_factors.py  # 技术因子：动量、波动率、均线排列、量价关系
├── fundamental_factors.py# 基本面因子：PE/PB/ROE/营收增长（基于现有基本面数据）
├── market_factors.py     # 市场因子：大盘联动、板块热度、资金流向
├── factor_processor.py   # 因子归一化、中性化、正交化
└── factor_utils.py       # 因子存储、加载、更新
```

**因子分类**：

| 类别 | 示例因子 | 数据来源 |
|------|---------|---------|
| 📉 **动量因子** | N 日收益率、N 日波动率、RSI、KDJ | K 线数据 |
| 📊 **均线因子** | 均线排列强度、乖离率、均线斜率 | 技术指标 |
| 📈 **量价因子** | 量比、换手率、资金流向、成交量变异系数 | 量价数据 |
| 🏢 **基本面因子** | PE、PB、ROE、营收增长率、净利润增长率 | 基本面数据 |
| 🌐 **市场因子** | 板块涨跌幅、大盘相关系数、市场阶段 | 市场数据 |
| 📰 **情绪因子** | 新闻情感得分、舆情热度 | 搜索服务 |

**关键设计**：

- **因子缓存**：计算结果按日期存入 SQLite，避免重复计算
- **因子归一化**：Z-score / Min-Max / Rank 三种方式可选
- **因子正交化**：通过 PCA 去冗余，减少多重共线性
- **因子评价**：IC（信息系数）、IR（信息比率）自动计算，定期淘汰无效因子

---

### 建议三：LLM↔ML 信号融合决策引擎（Signal Fusion Decision Engine）

**核心思路**：在 `src/core/` 下新增 `fusion_engine` 模块，将 ML 预测信号与 LLM 分析信号加权融合，输出统一的 "融合决策信号"。

**具体实现**：

```
src/core/fusion_engine/
├── __init__.py
├── fusion.py             # 信号融合核心逻辑
├── weights.py            # 动态权重计算（基于历史表现）
├── schemas.py            # 融合决策数据结构
├── backtest.py           # 融合策略回测
└── registry.py           # 信号源注册器
```

**融合架构**：

```
┌──────────────────┐     ┌──────────────────┐
│   ML 预测管道      │     │   LLM 分析层      │
│  ┌──────────────┐ │     │  ┌──────────────┐ │
│  │ XGBoost 预测  │ │     │  │ GeminiAnalyzer│ │
│  │ Random Forest │ │     │  │ Agent 分析    │ │
│  │ LightGBM      │ │     │  │ 策略问股     │ │
│  └──────┬───────┘ │     │  └──────┬───────┘ │
└─────────┼─────────┘     └─────────┼─────────┘
          │                         │
          ▼                         ▼
    ┌─────────────────────────────────┐
    │       信号融合引擎               │
    │  ┌───────────────────────────┐  │
    │  │ 权重计算 (Bayesian/EWMA)  │  │
    │  │ 置信度加权融合             │  │
    │  │ 分歧检测与降级             │  │
    │  │ 历史校准 (Calibration)    │  │
    │  └───────────────────────────┘  │
    └──────────────┬──────────────────┘
                   ▼
          ┌──────────────────┐
          │ 融合决策信号      │
          │ score: 0.85      │
          │ direction: BUY   │
          │ confidence: HIGH │
          │ evidence: {...}  │
          └──────────────────┘
```

**核心算法 — 置信度加权贝叶斯融合**：

```python
def fuse_signals(ml_signal, llm_signal, history):
    """
    使用历史校准的置信度加权融合两个信号源。
    
    融合权重 = 信号源历史准确率 / (1 + 衰减系数 × 天数)
    融合得分 = Σ(信号得分 × 归一化权重) / Σ(归一化权重)
    """
    ml_weight = calibrate(ml_signal.confidence, history.ml_accuracy)
    llm_weight = calibrate(llm_signal.confidence, history.llm_accuracy)
    
    fused_score = (
        ml_signal.score * ml_weight +
        llm_signal.score * llm_weight
    ) / (ml_weight + llm_weight)
    
    return FusedDecision(
        score=fused_score,
        direction=resolve_direction(fused_score),
        confidence_level=compute_confidence(fused_score, ml_weight, llm_weight),
        signal_breakdown={
            "ml": {"score": ml_signal.score, "weight": ml_weight},
            "llm": {"score": llm_signal.score, "weight": llm_weight},
        }
    )
```

**融合信号通过现有 Web UI 展示**：在分析报告"决策仪表盘"中新增融合信号视图，展示 ML 和 LLM 各自的观点及融合结果，让用户理解决策依据。

---

## 三、实现路线图

| 阶段 | 内容 | 预计工作量 |
|:----:|------|:---------:|
| **Phase 1** | 建议一：ML 预测管道（XGBoost 训练 + 推理） | ~3 天 |
| **Phase 2** | 建议二：因子工程系统（技术/基本面/市场因子） | ~2 天 |
| **Phase 3** | 建议三：信号融合引擎 + 回测 + Web 展示 | ~2 天 |

> **轻量原则**：全部模块使用 CPU-only 推理，不引入 GPU 依赖；新增依赖控制在 2-3 个 PyPI 包内（xgboost、scikit-learn）。