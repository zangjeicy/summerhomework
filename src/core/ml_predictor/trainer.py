"""模型训练 — XGBoost / RandomForest 滚动训练。"""

import logging
import pickle
from pathlib import Path
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

from src.core.ml_predictor.schemas import TrainConfig, TrainResult, FeatureImportance
from src.core.ml_predictor.features import extract_features

logger = logging.getLogger(__name__)

_MODELS_DIR = Path(__file__).resolve().parent / "models"


class MLTrainer:
    """轻量 ML 模型训练器。"""

    def __init__(self, config: Optional[TrainConfig] = None):
        self.config = config or TrainConfig()

    def train(self, kline_df: pd.DataFrame, stock_code: str = "all") -> TrainResult:
        X, y, feature_names = extract_features(kline_df, self.config.horizon_days)
        if len(X) < self.config.min_train_samples:
            return TrainResult(
                accuracy=0, precision=0, recall=0, f1_score=0, auc_roc=0,
                n_samples=len(X), n_features=0,
                error=f"样本不足 ({len(X)} < {self.config.min_train_samples})",
            )
        return self._fit_model(X, y, feature_names, stock_code)

    def train_from_cache(self, stock_codes: list[str], data_provider, days: int = 240) -> dict[str, TrainResult]:
        results = {}
        for code in stock_codes:
            try:
                kline = data_provider.get_daily_kline(code, days)
                if kline is None or len(kline) < 60:
                    logger.warning("[ML] %s K线不足，跳过", code)
                    continue
                results[code] = self.train(kline, code)
            except Exception as e:
                logger.error("[ML] %s 训练失败: %s", code, e)
                results[code] = TrainResult(accuracy=0, precision=0, recall=0, f1_score=0, auc_roc=0, n_samples=0, n_features=0, error=str(e))
        return results

    def _fit_model(self, X: np.ndarray, y: np.ndarray, feature_names: list[str], stock_code: str) -> TrainResult:
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.config.test_ratio,
            random_state=self.config.random_state, stratify=y,
        )
        model = self._build_model()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.5

        imp = self._get_importance(model, feature_names)
        ver = date.today().strftime("%Y%m%d")
        _MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(_MODELS_DIR / f"{stock_code}_{ver}.pkl", "wb") as f:
            pickle.dump({"model": model, "features": feature_names, "version": ver}, f)

        logger.info("[ML] %s acc=%.3f prec=%.3f rec=%.3f f1=%.3f auc=%.3f | %d samples %d features",
                     stock_code, acc, prec, rec, f1, auc, len(X), len(feature_names))

        return TrainResult(accuracy=round(acc, 4), precision=round(prec, 4), recall=round(rec, 4),
                           f1_score=round(f1, 4), auc_roc=round(auc, 4),
                           n_samples=len(X), n_features=len(feature_names),
                           top_features=imp[:15], model_version=ver)

    def _build_model(self):
        if self.config.model_type == "xgboost":
            import xgboost as xgb
            return xgb.XGBClassifier(n_estimators=self.config.n_estimators, max_depth=self.config.max_depth,
                                     learning_rate=self.config.learning_rate, random_state=self.config.random_state,
                                     eval_metric="logloss", verbosity=0)
        else:
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(n_estimators=self.config.n_estimators, max_depth=self.config.max_depth,
                                          random_state=self.config.random_state, n_jobs=-1)

    def _get_importance(self, model, feature_names: list[str]) -> list[FeatureImportance]:
        scores = model.feature_importances_ if hasattr(model, "feature_importances_") else (np.abs(model.coef_).flatten() if hasattr(model, "coef_") else [])
        if len(scores) == 0:
            return []
        paired = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
        return [FeatureImportance(feature=f, importance=round(s, 6)) for f, s in paired]

    @staticmethod
    def load_model(stock_code: str, version: Optional[str] = None):
        _MODELS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(_MODELS_DIR.glob(f"{stock_code}_{version or '*'}.pkl"))
        path = files[-1] if files else None
        if path and path.exists():
            with open(path, "rb") as f:
                return pickle.load(f)
        return None