"""市场状态检测器 — 识别当前市场所处阶段。

将市场分为 5 种状态：
- BULL: 趋势上涨
- BEAR: 趋势下跌
- VOLATILE: 高波动震荡
- RANGE: 低波动盘整
- EVENT_DRIVEN: 消息驱动
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class MarketRegime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    VOLATILE = "volatile"
    RANGE = "range"
    EVENT_DRIVEN = "event_driven"
    UNKNOWN = "unknown"


@dataclass
class RegimeResult:
    regime: MarketRegime = MarketRegime.UNKNOWN
    confidence: float = 0.0
    score_bull: float = 0.0
    score_bear: float = 0.0
    score_volatile: float = 0.0
    score_range: float = 0.0
    signal: str = ""
    date: date = field(default_factory=date.today)


class RegimeDetector:
    """基于指数数据和波动率的多维度市场状态检测器。"""

    def detect(self, index_df: Optional[pd.DataFrame] = None,
               stock_df: Optional[pd.DataFrame] = None) -> RegimeResult:
        """检测当前市场状态。

        Args:
            index_df: 大盘指数 K 线（如上证指数）
            stock_df: 个股 K 线（兜底用）
        """
        df = index_df if index_df is not None and len(index_df) >= 20 else stock_df
        if df is None or len(df) < 20:
            return RegimeResult(regime=MarketRegime.UNKNOWN, signal="数据不足")

        close = df["close"].values
        returns = np.diff(close) / close[:-1]

        # —— 趋势强度 ——
        ma20 = pd.Series(close).rolling(20).mean().values
        ma60 = pd.Series(close).rolling(60).mean().values if len(close) >= 60 else None

        price_vs_ma20 = (close[-1] / ma20[-1] - 1) * 100
        bull_score = max(0, price_vs_ma20 / 5.0)  # >5% above MA20 → bull
        bear_score = max(0, -price_vs_ma20 / 5.0)  # <-5% below MA20 → bear

        # 均线排列
        alignment = 0.0
        if ma60 is not None and not np.isnan(ma60[-1]):
            alignment = (ma20[-1] > ma60[-1]) * 1.0

        # —— 波动率 ——
        recent_ret = returns[-20:] if len(returns) >= 20 else returns
        volatility = np.std(recent_ret) * np.sqrt(252) * 100  # 年化波动率%

        # —— 趋势连续性 ——
        sign_changes = np.sum(np.diff(np.sign(recent_ret)) != 0) / max(len(recent_ret), 1)
        trend_consistency = 1.0 - sign_changes  # 0=频繁反转, 1=单边

        # —— 状态判定 ——
        scores = {
            MarketRegime.BULL: min(1.0, bull_score * 1.2 + alignment * 0.5),
            MarketRegime.BEAR: min(1.0, bear_score * 1.2 + (1 - alignment) * 0.3),
            MarketRegime.VOLATILE: min(1.0, volatility / 40.0),
            MarketRegime.RANGE: min(1.0, max(0, 1 - volatility / 20.0) * (1 - max(bull_score, bear_score))),
        }
        scores[MarketRegime.EVENT_DRIVEN] = min(1.0, max(0, volatility / 30.0) * (1 - trend_consistency))

        best_regime = max(scores, key=scores.get)
        confidence = scores[best_regime]

        # 信号文本
        signal_map = {
            MarketRegime.BULL: f"📈 趋势上涨 (MA20偏离={price_vs_ma20:.1f}%)",
            MarketRegime.BEAR: f"📉 趋势下跌 (MA20偏离={price_vs_ma20:.1f}%)",
            MarketRegime.VOLATILE: f"🌊 高波动震荡 (年化波动={volatility:.0f}%)",
            MarketRegime.RANGE: f"📊 低波动盘整 (波动={volatility:.0f}%)",
            MarketRegime.EVENT_DRIVEN: "📰 消息驱动 (高波动+低趋势)",
            MarketRegime.UNKNOWN: "❓ 未知",
        }

        return RegimeResult(
            regime=best_regime, confidence=round(confidence, 3),
            score_bull=round(scores[MarketRegime.BULL], 3),
            score_bear=round(scores[MarketRegime.BEAR], 3),
            score_volatile=round(scores[MarketRegime.VOLATILE], 3),
            score_range=round(scores[MarketRegime.RANGE], 3),
            signal=signal_map[best_regime],
        )