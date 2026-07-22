"""融合编排器 — 串联市场状态检测 → 自适应权重 → 信号融合。"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.core.fusion_engine.schemas import FusedDecision, SignalSource
from src.core.fusion_engine.fusion import FusionEngine
from src.core.fusion_engine.regime_detector import RegimeDetector, MarketRegime, RegimeResult
from src.core.fusion_engine.adaptive_weights import AdaptiveWeightEvolver, SignalSourceProfile

logger = logging.getLogger(__name__)


class FusionOrchestrator:
    """市场状态感知的融合编排器 — 核心创新入口。"""

    def __init__(self):
        self.detector = RegimeDetector()
        self.weight_evolver = AdaptiveWeightEvolver()
        self.fusion_engine = FusionEngine()

    def analyze(
        self,
        stock_code: str,
        stock_name: str = "",
        index_df: Optional[pd.DataFrame] = None,
        kline_df: Optional[pd.DataFrame] = None,
        ml_signal: Optional[SignalSource] = None,
        llm_signal: Optional[SignalSource] = None,
        extra_signals: Optional[list[SignalSource]] = None,
    ) -> dict:
        """全流程分析：检测市场状态 → 计算动态权重 → 融合决策。"""

        regime_result = self.detector.detect(index_df, kline_df)
        regime = regime_result.regime

        all_signals = []
        if ml_signal:
            all_signals.append(ml_signal)
        if llm_signal:
            all_signals.append(llm_signal)
        if extra_signals:
            all_signals.extend(extra_signals)

        for sig in all_signals:
            w = self.weight_evolver.get_weight(sig.name, regime, sig.confidence)
            sig.weight = round(w, 4)

        decision = self.fusion_engine.fuse(stock_code, stock_name, ml_signal, llm_signal, extra_signals)

        weights_summary = {}
        for sig in all_signals:
            profile = self.weight_evolver.get_or_create(sig.name)
            stats = profile.get_regime_stats(regime)
            weights_summary[sig.name] = {
                "weight": sig.weight,
                "accuracy": round(stats.smoothed_accuracy, 4),
            }

        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "timestamp": datetime.now().isoformat(),
            "market_regime": {
                "regime": regime.value,
                "confidence": regime_result.confidence,
                "signal": regime_result.signal,
                "scores": {
                    "bull": round(regime_result.score_bull, 3),
                    "bear": round(regime_result.score_bear, 3),
                    "volatile": round(regime_result.score_volatile, 3),
                    "range": round(regime_result.score_range, 3),
                },
            },
            "adaptive_weights": weights_summary,
            "fused_decision": {
                "direction": decision.direction,
                "score": decision.score,
                "confidence_level": decision.confidence_level,
                "primary_driver": decision.primary_driver,
            },
            "signal_sources": [
                {
                    "name": s.name,
                    "score": s.score,
                    "confidence": s.confidence,
                    "weight": s.weight,
                    "detail": s.detail,
                }
                for s in decision.sources
            ],
        }

    def record_outcome(self, signal_name: str, regime: MarketRegime, correct: bool) -> None:
        """记录信号预测结果（用于在线权重进化）。"""
        self.weight_evolver.record_outcome(signal_name, regime, correct)
        self.fusion_engine.record_accuracy(signal_name, correct)

    def get_weight_summary(self, regime: MarketRegime) -> dict:
        """获取各信号源在当前市场状态下的权重快照。"""
        return self.weight_evolver.summary(regime)