"""多因子系统 — 系统化的因子计算管线。

为 ML 预测管道提供标准化特征，同时也作为独立信号源。
"""
from data_provider.factors.base import Factor, FactorRegistry
from data_provider.factors.technical_factors import TechnicalFactors
from data_provider.factors.factor_processor import FactorProcessor

__all__ = ["Factor", "FactorRegistry", "TechnicalFactors", "FactorProcessor"]