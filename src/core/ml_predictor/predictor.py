"""模型推理 — 加载训练好的模型并生成预测。"""

import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date
from typing import Optional

from src.core.ml_predictor.schemas import MLPrediction, FeatureImportance
from src.core.ml_predictor.features import extract_features

logger = logging.getLogger(__name__)

_MODELS_DIR = Path(__file__).resolve().parent / "models"


class MLPredictor:
    """ML 预测推理器。对单只股票生成价格方向预测。"""

    def __init__(self):
        self._model_cache: dict[str, dict] = {}

    def predict(
        self,
        stock_code: str,
        stock_name: str = "",
        kline_df: Optional[pd.DataFrame] = None,
        model_version: Optional[str] = None,
    ) -> MLPrediction:
        """对单只股票生成 ML 预测。

        Args:
            stock_code: 股票代码
            stock_name: 股票名称（可选）
            kline_df: 包含 OHLCV 的历史 K 线 DataFrame
            model_version: 指定模型版本，默认最新

        Returns:
            MLPrediction
        """
        if kline_df is None or len(kline_df) < 30:
            return MLPrediction(
                stock_code=stock_code, stock_name=stock_name,
                error=f"K线数据不足 ({len(kline_df) if kline_df is not None else 0})",
            )

        model_data = self._load_model(stock_code, model_version)
        if model_data is None:
            return MLPrediction(
                stock_code=stock_code, stock_name=stock_name,
                error=f"模型未训练 (stock={stock_code})",
            )

        model = model_data["model"]
        trained_features = model_data["features"]

        # 提取最新特征
        X, _, current_features = extract_features(kline_df, horizon_days=0)

        if len(X) == 0:
            return MLPrediction(
                stock_code=stock_code, stock_name=stock_name,
                error="特征提取结果为空",
            )

        # 对齐训练用的特征列
        X_aligned = np.zeros((X.shape[0], len(trained_features)), dtype=np.float32)
        feat_map = {f: i for i, f in enumerate(current_features)}
        for j, f in enumerate(trained_features):
            if f in feat_map:
                X_aligned[:, j] = X[:, feat_map[f]]

        # 用最新一期数据做预测
        latest_X = X_aligned[-1:]

        direction_score = model.predict_proba(latest_X)[0, 1] if hasattr(model, "predict_proba") else float(model.predict(latest_X)[0])
        pred_class = model.predict(latest_X)[0]

        # 方向与置信度
        direction = "up" if pred_class == 1 else ("down" if direction_score < 0.4 else "neutral")
        confidence = abs(direction_score - 0.5) * 2  # 0.0 ~ 1.0
        score = direction_score * 2 - 1  # -1.0 ~ 1.0

        # 预期收益（使用未来 N 日收益的最近平均值作为粗略估计）
        expected_return = self._estimate_return(kline_df)

        # 特征重要性
        top_features = []
        if hasattr(model, "feature_importances_"):
            scores = model.feature_importances_
            paired = sorted(zip(trained_features, scores), key=lambda x: x[1], reverse=True)
            top_features = [FeatureImportance(feature=f, importance=round(s, 6)) for f, s in paired[:10]]

        return MLPrediction(
            stock_code=stock_code,
            stock_name=stock_name,
            direction=direction,
            confidence=round(confidence, 4),
            expected_return=round(expected_return, 4),
            score=round(score, 4),
            top_features=top_features,
            model_version=model_data.get("version", ""),
            prediction_date=date.today(),
            horizon_days=5,
        )

    def _load_model(self, stock_code: str, version: Optional[str] = None) -> Optional[dict]:
        cache_key = f"{stock_code}_{version or 'latest'}"
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        _MODELS_DIR.mkdir(parents=True, exist_ok=True)
        if version:
            path = _MODELS_DIR / f"{stock_code}_{version}.pkl"
        else:
            files = sorted(_MODELS_DIR.glob(f"{stock_code}_*.pkl"))
            path = files[-1] if files else None

        if path and path.exists():
            with open(path, "rb") as f:
                data = pickle.load(f)
            self._model_cache[cache_key] = data
            return data
        return None

    @staticmethod
    def _estimate_return(kline_df: pd.DataFrame, window: int = 5) -> float:
        """用最近 window 日的平均收益率粗略估计预期收益。"""
        if "close" not in kline_df.columns or len(kline_df) < window + 1:
            return 0.0
        returns = kline_df["close"].pct_change(window).dropna()
        return float(returns.tail(min(5, len(returns))).mean() * 100)