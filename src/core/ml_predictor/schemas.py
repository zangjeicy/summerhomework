"""ML 预测管道数据结构。"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

Direction = Literal["up", "down", "neutral"]


@dataclass
class FeatureImportance:
    """特征重要性（可解释性输出）。"""

    feature: str
    importance: float


@dataclass
class MLPrediction:
    """单次 ML 预测输出。"""

    stock_code: str
    stock_name: str = ""
    direction: Direction = "neutral"
    confidence: float = 0.0          # 0.0-1.0
    expected_return: float = 0.0     # 预期 N 日收益率 (%)
    score: float = 0.0               # -1.0 ~ 1.0 连续值
    top_features: list[FeatureImportance] = field(default_factory=list)
    model_version: str = ""
    prediction_date: date = field(default_factory=date.today)
    horizon_days: int = 5            # 预测窗口
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.error is None and self.confidence > 0


@dataclass
class TrainConfig:
    """训练配置。"""

    horizon_days: int = 5            # 预测 N 日涨跌
    lookback_days: int = 120         # 训练窗口（交易日）
    min_train_samples: int = 60      # 最少训练样本
    test_ratio: float = 0.2
    model_type: str = "xgboost"      # xgboost / randomforest
    max_depth: int = 6
    n_estimators: int = 200
    learning_rate: float = 0.05
    early_stopping_rounds: int = 20
    random_state: int = 42


@dataclass
class TrainResult:
    """训练结果。"""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    n_samples: int
    n_features: int
    top_features: list[FeatureImportance] = field(default_factory=list)
    model_version: str = ""
    error: Optional[str] = None