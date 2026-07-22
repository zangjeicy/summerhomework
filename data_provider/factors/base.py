"""因子基类与注册器。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class Factor:
    """单个因子快照。"""
    name: str
    category: str  # technical / fundamental / market
    value: float
    zscore: float = 0.0
    rank: float = 0.0
    ic: float = 0.0  # 信息系数
    timestamp: date = field(default_factory=date.today)


class FactorCalculator(ABC):
    """因子计算器基类。"""

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        ...

    @property
    @abstractmethod
    def factor_names(self) -> list[str]:
        ...


class FactorRegistry:
    """因子注册器 — 管理所有可用因子。"""

    def __init__(self):
        self._calculators: dict[str, FactorCalculator] = {}

    def register(self, name: str, calc: FactorCalculator) -> None:
        self._calculators[name] = calc

    def get(self, name: str) -> FactorCalculator | None:
        return self._calculators.get(name)

    @property
    def all_names(self) -> list[str]:
        return list(self._calculators.keys())

    def compute_all(self, df: pd.DataFrame) -> pd.DataFrame:
        for name, calc in self._calculators.items():
            df = calc.compute(df)
        return df