"""融合决策数据结构。"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

Direction = Literal["buy", "sell", "hold", "neutral"]
ConfidenceLevel = Literal["high", "medium", "low"]


@dataclass
class SignalSource:
    """单个信号源快照。"""
    name: str                  # "ml_xgboost" / "llm_gemini" / "technical_rsi" 等
    direction: Direction = "neutral"
    score: float = 0.0         # -1.0 ~ 1.0
    confidence: float = 0.0    # 0.0 ~ 1.0
    weight: float = 0.5        # 融合权重
    detail: str = ""


@dataclass
class FusedDecision:
    """融合决策输出。"""
    stock_code: str
    stock_name: str = ""
    direction: Direction = "neutral"
    score: float = 0.0          # -1.0 ~ 1.0
    confidence_level: ConfidenceLevel = "low"
    sources: list[SignalSource] = field(default_factory=list)
    primary_driver: str = ""    # 主驱动信号源名称
    created_at: datetime = field(default_factory=datetime.now)
    ml_prediction: str = ""     # 原始 ML 预测摘要
    llm_analysis: str = ""      # 原始 LLM 分析摘要
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.error is None and len(self.sources) > 0