"""技术因子 — 动量、波动率、均线排列、量价关系。"""

import numpy as np
import pandas as pd

from .base import FactorCalculator


class TechnicalFactors(FactorCalculator):
    """系统化技术因子计算。"""

    @property
    def factor_names(self) -> list[str]:
        return [
            # 动量
            "momentum_1m", "momentum_3m",
            # 波动率
            "volatility_1m", "volatility_3m",
            # 均线排列
            "ma_short_long_ratio", "ma_alignment_score",
            # 量价
            "volume_price_corr", "volume_shock",
            # 超买超卖
            "rsi", "macd_signal_cross",
            # 价格位置
            "price_percentile_3m",
        ]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """在 df 上原地计算并追加因子列。"""
        c = df["close"]
        v = df["volume"]

        # 动量因子
        df["factor_momentum_1m"] = c.pct_change(20)
        df["factor_momentum_3m"] = c.pct_change(60)

        # 波动率因子
        ret = c.pct_change(1)
        df["factor_volatility_1m"] = ret.rolling(20).std()
        df["factor_volatility_3m"] = ret.rolling(60).std()

        # 均线排列
        ma20 = c.rolling(20).mean()
        ma60 = c.rolling(60).mean()
        df["factor_ma_short_long_ratio"] = ma20 / ma60 - 1

        ma5 = c.rolling(5).mean()
        ma10 = c.rolling(10).mean()
        df["factor_ma_alignment_score"] = (
            (ma5 > ma10).astype(int) + (ma10 > ma20).astype(int) + (ma20 > ma60).astype(int)
        ) / 3.0

        # 量价
        df["factor_volume_price_corr"] = ret.rolling(20).corr(v.pct_change(1))
        vol_ma = v.rolling(20).mean()
        df["factor_volume_shock"] = v / vol_ma - 1

        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rsi = gain / (loss + 1e-10)
        df["factor_rsi"] = 100 - (100 / (1 + rsi))

        # MACD 信号交叉
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        df["factor_macd_signal_cross"] = (macd > signal).astype(int) - (macd.shift(1) > signal.shift(1)).astype(int)

        # 价格百分位
        roll_min = c.rolling(60).min()
        roll_max = c.rolling(60).max()
        df["factor_price_percentile_3m"] = (c - roll_min) / (roll_max - roll_min + 1e-10)

        return df