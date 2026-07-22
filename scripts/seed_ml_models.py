# -*- coding: utf-8 -*-
"""训练几只股票的 ML 模型，填充模型健康度面板。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("seed_ml_models")

ML_PREDICTOR_DIR = Path(__file__).resolve().parent.parent / "src" / "core" / "ml_predictor"
MODELS_DIR = ML_PREDICTOR_DIR / "models"


def train_models():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    from src.core.ml_predictor.trainer import MLTrainer
    from src.core.ml_predictor.schemas import TrainConfig
    from src.storage import DatabaseManager
    from src.repositories.stock_repo import StockRepository

    db = DatabaseManager.get_instance()
    stock_repo = StockRepository(db)

    stocks = ["600519", "300750", "601318", "000858", "002594", "600000"]
    trained = 0

    for code in stocks:
        try:
            bars = stock_repo.get_forward_bars(code=code, analysis_date=pd.Timestamp("2026-01-01").date(), eval_window_days=300)
            if not bars or len(bars) < 60:
                logger.warning("[%s] 日线数据不足 (%d bars)，跳过", code, len(bars) if bars else 0)
                continue

            df = pd.DataFrame([{
                "open": b.open, "high": b.high, "low": b.low,
                "close": b.close, "volume": getattr(b, "volume", 0),
            } for b in bars])

            logger.info("[%s] 训练 ML 模型 (n=%d bars)", code, len(df))
            trainer = MLTrainer(TrainConfig(n_estimators=100, early_stopping_rounds=20))
            result = trainer.train(df, code)

            logger.info("[%s] 训练完成: accuracy=%.4f f1=%.4f features=%d",
                        code, result.accuracy, result.f1_score, len(result.features))
            trained += 1
        except Exception as e:
            logger.error("[%s] 训练失败: %s", code, e)

    if trained == 0:
        # fallback: 用模拟数据训练
        logger.info("数据库中无可训练数据，使用模拟数据训练...")
        import numpy as np
        np.random.seed(42)
        for code in ["600519", "300750", "601318"]:
            try:
                n = 300
                price = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.008))
                df = pd.DataFrame({
                    "open":   price * (1 + np.random.randn(n) * 0.005),
                    "high":   price * (1 + np.abs(np.random.randn(n)) * 0.012),
                    "low":    price * (1 - np.abs(np.random.randn(n)) * 0.012),
                    "close":  price,
                    "volume": np.random.randint(100000, 10000000, n),
                })

                logger.info("[%s] 模拟数据训练 (n=%d)", code, len(df))
                trainer = MLTrainer(TrainConfig(n_estimators=100, early_stopping_rounds=20))
                result = trainer.train(df, code)
                logger.info("[%s] 训练完成: accuracy=%.4f f1=%.4f",
                            code, result.accuracy, result.f1_score)
                trained += 1
            except Exception as e:
                logger.error("[%s] 模拟训练失败: %s", code, e)

    logger.info("共训练 %d 个模型", trained)
    return trained


if __name__ == "__main__":
    train_models()
