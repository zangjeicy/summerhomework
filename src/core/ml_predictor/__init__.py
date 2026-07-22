"""轻量 ML 预测管道 — 基于 XGBoost 的价格方向预测。

从历史 K 线 + 技术指标提取特征，训练轻量模型，
为后续信号融合引擎提供 ML 预测信号。

设计原则：
- CPU-only 推理，无 GPU 依赖
- 滚动窗口训练，自动适应市场变化
- 可解释性优先（特征重要性输出）
"""
from src.core.ml_predictor.schemas import (
    MLPrediction,
    TrainConfig,
    TrainResult,
    FeatureImportance,
)
from src.core.ml_predictor.predictor import MLPredictor
from src.core.ml_predictor.trainer import MLTrainer

__all__ = [
    "MLPrediction",
    "TrainConfig",
    "TrainResult",
    "FeatureImportance",
    "MLPredictor",
    "MLTrainer",
]