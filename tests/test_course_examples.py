"""Smoke test for every executable course example."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.stock_analyzer import StockTrendAnalyzer


def test_all_course_examples_execute_successfully() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "examples" / "运行全部示例.py")],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "全部课程示例真实执行通过" in result.stdout


def test_explicit_bias_threshold_keeps_offline_analyzer_config_independent() -> None:
    analyzer = StockTrendAnalyzer(bias_threshold=5.0)
    assert analyzer.bias_threshold == 5.0
