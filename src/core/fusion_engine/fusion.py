"""信号融合核心逻辑 — 贝叶斯置信度加权融合。"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np

from src.core.fusion_engine.schemas import FusedDecision, SignalSource, ConfidenceLevel, Direction

logger = logging.getLogger(__name__)

# 历史精度衰减系数（越久远的记录权重越低）
_DECAY_FACTOR = 0.98


class FusionEngine:
    """信号融合引擎。

    将 ML 预测信号与 LLM 分析信号通过置信度加权贝叶斯方法融合，
    输出统一的融合决策信号。
    """

    def __init__(self):
        # 历史精度缓存: {signal_name: [acc_day1, acc_day2, ...]}
        self._history: dict[str, list[float]] = {}

    def fuse(
        self,
        stock_code: str,
        stock_name: str = "",
        ml_signal: Optional[SignalSource] = None,
        llm_signal: Optional[SignalSource] = None,
        extra_signals: Optional[list[SignalSource]] = None,
    ) -> FusedDecision:
        """融合多个信号源为一个决策。"""
        signals: list[SignalSource] = []
        if ml_signal:
            signals.append(ml_signal)
        if llm_signal:
            signals.append(llm_signal)
        if extra_signals:
            signals.extend(extra_signals)

        if not signals:
            return FusedDecision(
                stock_code=stock_code, stock_name=stock_name,
                error="没有可用的信号源",
            )

        # 1. 计算动态权重（基于历史表现）
        total_weight = 0.0
        weighted_score = 0.0
        max_confidence = 0.0
        primary_driver = ""

        for sig in signals:
            w = self._compute_weight(sig.name, sig.confidence)
            sig.weight = round(w, 4)
            weighted_score += sig.score * w
            total_weight += w
            if sig.confidence > max_confidence:
                max_confidence = sig.confidence
                primary_driver = sig.name

        # 2. 融合得分
        fused_score = weighted_score / total_weight if total_weight > 0 else 0.0
        fused_score = np.clip(fused_score, -1.0, 1.0)

        # 3. 决策方向
        direction = self._resolve_direction(fused_score)

        # 4. 置信度等级
        confidence_level = self._resolve_confidence_level(fused_score, max_confidence, len(signals))

        return FusedDecision(
            stock_code=stock_code,
            stock_name=stock_name,
            direction=direction,
            score=round(fused_score, 4),
            confidence_level=confidence_level,
            sources=signals,
            primary_driver=primary_driver,
            created_at=datetime.now(),
        )

    def _compute_weight(self, name: str, confidence: float) -> float:
        """基于历史精度 + 当前置信度计算权重。"""
        hist = self._history.get(name, [])
        if hist:
            # 指数衰减加权平均精度
            weights = np.array([_DECAY_FACTOR ** i for i in range(len(hist))][::-1])
            avg_accuracy = np.average(hist, weights=weights)
        else:
            avg_accuracy = 0.5  # 无历史记录，默认 50%

        # 权重 = 历史精度 × 置信度
        return max(0.05, avg_accuracy * confidence)

    def record_accuracy(self, name: str, correct: bool) -> None:
        """记录一次信号源的准确/错误，用于后续权重动态调整。"""
        if name not in self._history:
            self._history[name] = []
        self._history[name].append(1.0 if correct else 0.0)
        # 最多保留 100 条历史
        if len(self._history[name]) > 100:
            self._history[name] = self._history[name][-100:]

    @staticmethod
    def _resolve_direction(score: float) -> Direction:
        if score > 0.3:
            return "buy"
        elif score < -0.3:
            return "sell"
        elif score > 0.1:
            return "hold"
        elif score < -0.1:
            return "hold"
        return "neutral"

    @staticmethod
    def _resolve_confidence_level(score: float, max_conf: float, n_sources: int) -> ConfidenceLevel:
        raw = abs(score) * max_conf * min(n_sources / 2.0, 1.0)
        if raw > 0.5:
            return "high"
        elif raw > 0.25:
            return "medium"
        return "low"