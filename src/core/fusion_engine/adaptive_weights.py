"""自适应权重进化器 — 基于市场状态的信号源权重动态调整。

核心创新：不同市场状态下不同信号源的预测能力不同，
系统自动追踪每个信号源在每个市场状态下的历史表现，
并据此动态调整融合权重。
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from src.core.fusion_engine.regime_detector import MarketRegime

_DECAY = 0.95  # 指数衰减，近期表现权重更高


@dataclass
class PerRegimeStats:
    correct: int = 1
    total: int = 2  # 初始 1/2 避免除零，相当于无先验知识
    accuracy: float = 0.5

    def update(self, correct: bool) -> None:
        self.total += 1
        if correct:
            self.correct += 1
        # 指数移动平均
        self.accuracy = self.accuracy * _DECAY + (1.0 if correct else 0.0) * (1 - _DECAY)

    @property
    def smoothed_accuracy(self) -> float:
        return self.correct / max(self.total, 1)


@dataclass
class SignalSourceProfile:
    name: str
    per_regime: dict[MarketRegime, PerRegimeStats] = field(default_factory=dict)

    def get_regime_stats(self, regime: MarketRegime) -> PerRegimeStats:
        if regime not in self.per_regime:
            self.per_regime[regime] = PerRegimeStats()
        return self.per_regime[regime]

    def record(self, regime: MarketRegime, correct: bool) -> None:
        self.get_regime_stats(regime).update(correct)

    def weight_for(self, regime: MarketRegime, base_confidence: float = 0.5) -> float:
        stats = self.get_regime_stats(regime)
        # weight = smoothed_accuracy × base_confidence
        return max(0.05, stats.smoothed_accuracy * base_confidence)


class AdaptiveWeightEvolver:
    """自适应权重进化器 — 追踪每个信号源在每个市场状态下的表现，
    动态调整融合权重。"""

    def __init__(self):
        self._profiles: dict[str, SignalSourceProfile] = {}

    def get_or_create(self, name: str) -> SignalSourceProfile:
        if name not in self._profiles:
            self._profiles[name] = SignalSourceProfile(name=name)
        return self._profiles[name]

    def record_outcome(self, name: str, regime: MarketRegime, correct: bool) -> None:
        """记录一次信号预测的准确/错误。"""
        self.get_or_create(name).record(regime, correct)

    def get_weight(self, name: str, regime: MarketRegime, base_confidence: float = 0.5) -> float:
        """获取某信号源在当前市场状态下的动态权重。"""
        return self.get_or_create(name).weight_for(regime, base_confidence)

    def get_all_weights(self, regime: MarketRegime,
                        signals: list[tuple[str, float]]) -> dict[str, float]:
        """批量获取所有信号源在当前市场状态下的权重。"""
        weights = {}
        for name, confidence in signals:
            weights[name] = self.get_weight(name, regime, confidence)
        return weights

    def summary(self, regime: MarketRegime) -> dict:
        """生成当前状态下的权重摘要（用于展示）。"""
        result = {}
        for name, profile in self._profiles.items():
            stats = profile.get_regime_stats(regime)
            result[name] = {
                "weight": round(profile.weight_for(regime, 0.6), 4),
                "accuracy": round(stats.smoothed_accuracy, 4),
                "samples": stats.total - 2,  # 减去初始虚样本
            }
        return result