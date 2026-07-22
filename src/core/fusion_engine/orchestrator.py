"""融合编排器 — 串联市场状态检测 → 自适应权重 → 信号融合。"""

import logging
from datetime import datetime

from src.core.fusion_engine.schemas import FusedDecision, SignalSource
from src.core.fusion_engine.fusion import FusionEngine
from src.core.fusion_engine.regime_detector import RegimeDetector, MarketRegime, RegimeResult
from src.core.fusion_engine.adaptive_weights import AdaptiveWeightEvolver

logger = logging.getLogger(__name__)


class FusionOrchestrator:
    """市场状态感知的融合编排器 — 核心创新入口。"""

    def __init__(self):
        self.detector = RegimeDetector()
        self.weight_evolver = AdaptiveWeightEvolver()
        self.fusion_engine = FusionEngine()

    def analyze(self, stock_code: str, stock_name: str = "",
                index_df=None, kline_df=None,
                ml_prediction: SignalSource | None = None,
                llm_signal: SignalSource | None = None) -> dict:
        """全流程分析：检测市场状态 → 计算动态权重 → 融合决策。"""

        # 1. 市场状态检测
        regime_result = self.detector.detect(index_df, kline_df)
        regime = regime_result.regime

        # 2. 获取自适应权重
        signals_list = []
        if ml_prediction:
            w = self.weight_evolver.get_weight(ml_prediction.name, regime, ml_prediction.confidence)
            signals_list.append((ml_prediction.name, ml_prediction.confidence))
        if llm_signal:
            w = self.weight_evolver.get_weight(llm_signal.name, regime, llm_signal.confidence)
            signals_list.append((llm_signal.name, llm_signal.confidence))

        weights = self.weight_evolver.get_all_weights(regime, signals_list)

        # 3. 融合决策
        decision = self.fusion_engine.fuse(stock_code, stock_name, ml_prediction, llm_signal)

        # 4. 构建完整返回
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "timestamp": datetime.now().isoformat(),
            "market_regime": {
                "regime": regime.value,
                "confidence": regime_result.confidence,
                "signal": regime_result.signal,
                "scores": {
                    "bull": regime_result.score_bull,
                    "bear": regime_result.score_bear,
                    "volatile": regime_result.score_volatile,
                    "range": regime_result.score_range,
                },
            },
            "adaptive_weights": weights,
            "fused_decision": {
                "direction": decision.direction,
                "score": decision.score,
                "confidence_level": decision.confidence_level,
                "primary_driver": decision.primary_driver,
            },
            "signal_sources": [
                {"name": s.name, "score": s.score, "confidence": s.confidence, "weight": s.weight, "detail": s.detail}
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