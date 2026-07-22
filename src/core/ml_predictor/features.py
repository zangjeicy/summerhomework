"""特征工程 — 从 K 线 + 技术指标提取 ML 特征向量。"""

import logging
import numpy as np
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


def _safe_isnan(arr: np.ndarray) -> np.ndarray:
    """兼容 NumPy 2.x：整数数组不能直接调用 isnan。"""
    if np.issubdtype(arr.dtype, np.floating):
        return np.isnan(arr)
    return np.zeros(arr.shape, dtype=bool)


def extract_features(
    kline_df: pd.DataFrame,
    horizon_days: int = 5,
) -> tuple[np.ndarray, Optional[np.ndarray], list[str]]:
    """从 K 线 DataFrame 提取特征和标签。

    Args:
        kline_df: 包含 OHLCV 的 DataFrame
        horizon_days: 预测 N 日方向

    Returns:
        (feature_matrix, labels, feature_names)
        labels = 1 if future_return > 2% else 0
    """
    if kline_df is None or len(kline_df) < 30:
        return np.empty((0, 0), dtype=np.float32), None, []

    df = kline_df.copy()

    # ── 基础价格特征 ──
    df["return_1d"] = df["close"].pct_change(1)
    df["return_5d"] = df["close"].pct_change(5)
    df["return_10d"] = df["close"].pct_change(10)
    df["return_20d"] = df["close"].pct_change(20)
    df["log_return_1d"] = np.log(df["close"] / df["close"].shift(1))

    high_20 = df["high"].rolling(20).max()
    low_20 = df["low"].rolling(20).min()
    df["price_position"] = (df["close"] - low_20) / (high_20 - low_20 + 1e-10)

    df["volatility_5d"] = df["return_1d"].rolling(5).std()
    df["volatility_10d"] = df["return_1d"].rolling(10).std()
    df["volatility_20d"] = df["return_1d"].rolling(20).std()

    # ── 量价特征 ──
    df["volume_ratio"] = df["volume"] / df["volume"].rolling(5).mean()
    df["volume_change"] = df["volume"].pct_change(1)
    ma5_close = df["close"].rolling(5).mean()
    ma5_vol = df["volume"].rolling(5).mean()
    df["amount_ratio"] = (df["close"] * df["volume"]) / (ma5_close * ma5_vol + 1e-10)
    vwap_5 = (df["close"] * df["volume"]).rolling(5).sum() / (df["volume"].rolling(5).sum() + 1e-10)
    df["vwap_deviation"] = (df["close"] - vwap_5) / vwap_5

    # ── 均线特征 ──
    for ma in [5, 10, 20, 30, 60]:
        df[f"ma_{ma}"] = df["close"].rolling(ma).mean()
        df[f"ma_{ma}_slope"] = df[f"ma_{ma}"].pct_change(5)
        df[f"close_ma_{ma}_ratio"] = df["close"] / df[f"ma_{ma}"] - 1

    df["ma_alignment"] = (
        (df["ma_5"] > df["ma_10"]).astype(int)
        + (df["ma_10"] > df["ma_20"]).astype(int)
        + (df["ma_20"] > df["ma_30"]).astype(int)
        + (df["ma_30"] > df["ma_60"]).astype(int)
    ) / 4.0

    # ── 动量特征 ──
    df["momentum_5d"] = df["close"] / df["close"].shift(5) - 1
    df["momentum_10d"] = df["close"] / df["close"].shift(10) - 1
    df["momentum_20d"] = df["close"] / df["close"].shift(20) - 1

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = df["close"].ewm(span=12).mean()
    ema_26 = df["close"].ewm(span=26).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # ── 波动特征 ──
    df["high_low_ratio"] = (df["high"] - df["low"]) / df["close"]
    df["open_close_ratio"] = (df["close"] - df["open"]).abs() / df["open"]

    # ── 定义特征列 ──
    feature_cols = [
        "return_1d", "return_5d", "return_10d", "return_20d",
        "log_return_1d", "price_position",
        "volatility_5d", "volatility_10d", "volatility_20d",
        "volume_ratio", "volume_change", "amount_ratio", "vwap_deviation",
        "ma_alignment",
        "close_ma_5_ratio", "close_ma_10_ratio", "close_ma_20_ratio",
        "ma_5_slope", "ma_10_slope", "ma_20_slope",
        "momentum_5d", "momentum_10d", "momentum_20d",
        "rsi_14",
        "macd", "macd_signal", "macd_hist",
        "high_low_ratio", "open_close_ratio",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]

    # ── 生成标签 ──
    labels = None
    if horizon_days > 0:
        future_return = df["close"].shift(-horizon_days) / df["close"] - 1
        labels = (future_return > 0.02).astype(np.float32).values

    # ── 清理 NaN ──
    feature_data = df[feature_cols].values.astype(np.float32)
    mask = ~_safe_isnan(feature_data).any(axis=1)
    if labels is not None:
        mask &= ~_safe_isnan(labels)
    feature_data = feature_data[mask]
    if labels is not None:
        labels = labels[mask]

    if len(feature_data) == 0:
        return np.empty((0, 0), dtype=np.float32), None, []

    return feature_data, labels, feature_cols