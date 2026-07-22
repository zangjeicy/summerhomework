"""模型推理 — 加载训练好的模型并生成预测，支持 SHAP 可解释性。"""

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
    """ML 预测推理器。对单只股票生成价格方向预测 + SHAP 可解释性。"""

    def __init__(self):
        self._model_cache: dict[str, dict] = {}
        self._shap_explainer_cache: dict[str, object] = {}

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

    def explain(
        self,
        stock_code: str,
        kline_df: pd.DataFrame,
        model_version: Optional[str] = None,
    ) -> Optional[dict]:
        """生成 SHAP 可解释性分析。

        Args:
            stock_code: 股票代码
            kline_df: 包含 OHLCV 的历史 K 线 DataFrame
            model_version: 指定模型版本

        Returns:
            dict with keys:
                - shap_values: list[{feature, shap_value}] 排序后的 SHAP 值
                - base_value: float SHAP 基准值
                - prediction_direction: str 预测方向
                - prediction_confidence: float 预测置信度
                - top_positive: list[{feature, shap_value}] 正向贡献 top3
                - top_negative: list[{feature, shap_value}] 负向贡献 top3
                或 None（不可用时）
        """
        model_data = self._load_model(stock_code, model_version)
        if model_data is None:
            return None

        model = model_data["model"]
        trained_features = model_data["features"]

        X, _, current_features = extract_features(kline_df, horizon_days=0)
        if len(X) == 0:
            return None

        X_aligned = np.zeros((X.shape[0], len(trained_features)), dtype=np.float32)
        feat_map = {f: i for i, f in enumerate(current_features)}
        for j, f in enumerate(trained_features):
            if f in feat_map:
                X_aligned[:, j] = X[:, feat_map[f]]

        # ── SHAP 解释 ──
        try:
            import shap
            from src.core.ml_predictor.trainer import MLTrainer

            model_type = type(model).__module__

            if "xgboost" in model_type:
                explainer = shap.TreeExplainer(model)
            elif "sklearn" in model_type and hasattr(model, "estimators_"):
                explainer = shap.TreeExplainer(model)
            else:
                # 使用 KernelExplainer 作为后备（采样）
                background = X_aligned[:min(50, X_aligned.shape[0])]
                explainer = shap.KernelExplainer(model.predict_proba, background)

            # 计算 SHAP 值（对最新一期数据）
            latest_X = X_aligned[-1:]
            shap_values = explainer.shap_values(latest_X)

            # XGBoost/Sklearn TreeExplainer shap_values shape:
            #   binary: (n_samples, n_features) 或 [neg_class, pos_class] 各 (n_samples, n_features)
            if isinstance(shap_values, list):
                # 多类输出，取 class 1（上涨）
                shap_arr = np.array(shap_values[1]) if len(shap_values) > 1 else np.array(shap_values[0])
            else:
                shap_arr = np.array(shap_values)

            shap_flat = shap_arr.flatten()
            base_value = float(explainer.expected_value if not isinstance(explainer.expected_value, list)
                               else explainer.expected_value[1] if len(explainer.expected_value) > 1
                               else explainer.expected_value[0])

            # 构建 feature→shap_value 映射
            shap_list = []
            for i, f_name in enumerate(trained_features):
                if i < len(shap_flat):
                    shap_list.append({
                        "feature": f_name,
                        "shap_value": round(float(shap_flat[i]), 6),
                    })

            # 按 shap_value 排序（绝对值大的在前）
            shap_list.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

            # 正向/负向 top3
            positive = sorted(
                [s for s in shap_list if s["shap_value"] > 0],
                key=lambda x: -x["shap_value"],
            )[:3]
            negative = sorted(
                [s for s in shap_list if s["shap_value"] < 0],
                key=lambda x: x["shap_value"],
            )[:3]

            # 获取预测
            pred = self.predict(stock_code, "", kline_df, model_version)

            return {
                "shap_values": shap_list,
                "base_value": base_value,
                "prediction_direction": pred.direction,
                "prediction_confidence": pred.confidence,
                "top_positive": positive,
                "top_negative": negative,
            }
        except Exception as e:
            logger.warning("[ML] SHAP 解释生成失败: %s", e)
            return None

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