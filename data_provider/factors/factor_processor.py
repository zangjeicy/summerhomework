"""因子处理器 — 归一化、去极值、中性化。"""

import numpy as np
import pandas as pd


class FactorProcessor:
    """因子后处理管线：去极值 → Z-score 标准化。"""

    @staticmethod
    def winsorize(df: pd.DataFrame, factor_cols: list[str], lo: float = 0.01, hi: float = 0.99) -> pd.DataFrame:
        """去极值（缩尾）。"""
        result = df.copy()
        for col in factor_cols:
            if col in result.columns:
                q_lo, q_hi = result[col].quantile(lo), result[col].quantile(hi)
                result[col] = result[col].clip(q_lo, q_hi)
        return result

    @staticmethod
    def zscore(df: pd.DataFrame, factor_cols: list[str]) -> pd.DataFrame:
        """Z-score 标准化。"""
        result = df.copy()
        for col in factor_cols:
            if col in result.columns:
                m, s = result[col].mean(), result[col].std()
                result[f"{col}_z"] = (result[col] - m) / (s + 1e-10)
        return result

    @staticmethod
    def rank_pct(df: pd.DataFrame, factor_cols: list[str]) -> pd.DataFrame:
        """排序百分位标准化。"""
        result = df.copy()
        for col in factor_cols:
            if col in result.columns:
                result[f"{col}_rank"] = result[col].rank(pct=True)
        return result

    @staticmethod
    def neutralize(df: pd.DataFrame, factor_cols: list[str], market_col: str = "market_return") -> pd.DataFrame:
        """市场中性化（numpy 最小二乘残差）。"""
        result = df.copy()
        if market_col not in result.columns:
            return result
        for col in factor_cols:
            if col not in result.columns:
                continue
            valid = result[[col, market_col]].dropna()
            if len(valid) < 10:
                continue
            X = np.c_[np.ones(len(valid)), valid[market_col].values]
            y = valid[col].values
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            resid = y - X @ beta
            result.loc[valid.index, f"{col}_neutral"] = resid
        return result

    @staticmethod
    def pipe(df: pd.DataFrame, factor_cols: list[str]) -> pd.DataFrame:
        """标准管线：去极值 → Z-score。"""
        return FactorProcessor.zscore(FactorProcessor.winsorize(df, factor_cols), factor_cols)