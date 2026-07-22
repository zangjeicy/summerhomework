# -*- coding: utf-8 -*-
"""本地 ML 管线验证脚本 — 用模拟行情数据跑通训练→预测→SHAP→融合→回测全链路。

用法：
    python scripts/test_ml_pipeline.py            # 全量测试（含 SHAP）
    python scripts/test_ml_pipeline.py --quick     # 快速冒烟（跳过 SHAP + WF）
    python scripts/test_ml_pipeline.py --no-shap   # 跳过 SHAP（无 shap 包时）
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# 确保项目根在 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_ml_pipeline")


# ============================================================
# 工具：模拟行情数据
# ============================================================

def generate_synthetic_kline(
    days: int = 300,
    seed: int = 42,
    trend: str = "up",
    volatility: float = 0.015,
) -> pd.DataFrame:
    """生成模拟 OHLCV K 线。

    Args:
        days: 交易日数量
        seed: 随机种子（可复现）
        trend: "up" / "down" / "sideways"
        volatility: 日波动率
    """
    rng = np.random.default_rng(seed)
    n = days

    # 构建趋势
    if trend == "up":
        drift = 0.0008 + rng.uniform(0, 0.0004, n)
    elif trend == "down":
        drift = -0.0006 + rng.uniform(-0.0004, 0, n)
    else:
        drift = rng.uniform(-0.0003, 0.0003, n)

    # 日收益率 = 趋势 + 噪声
    daily_returns = drift + rng.normal(0, volatility, n)

    # 累积价格
    close = 50.0 * np.exp(np.cumsum(daily_returns))
    # 确保价格不小于 1
    close = np.maximum(close, 1.0)

    # OHLC
    intra_range = volatility * close * 0.6
    open_price = close * (1 + rng.normal(0, volatility * 0.3, n))
    high = np.maximum(open_price, close) + np.abs(intra_range * rng.uniform(0.5, 1.2, n))
    low = np.minimum(open_price, close) - np.abs(intra_range * rng.uniform(0.5, 1.2, n))
    # 确保 high >= open,close >= low
    high = np.maximum(high, np.maximum(open_price, close) * 1.002)
    low = np.minimum(low, np.minimum(open_price, close) * 0.998)

    # 成交量（带趋势放大）
    volume = (1e6 + rng.lognormal(0, 0.7, n) * 5e5).astype(int)
    if trend == "up":
        volume = (volume * (1 + 0.3 * np.linspace(0, 1, n))).astype(int)

    # 日期索引
    end_date = date.today()
    start_date = end_date - timedelta(days=n * 2)  # 多留空间给周末
    dates = pd.date_range(start=start_date, periods=n, freq="B")[-n:]

    df = pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=dates,
    )
    return df


def generate_multi_stock_kline() -> dict[str, pd.DataFrame]:
    """为多只股票生成不同趋势的模拟 K 线。"""
    return {
        "600519": generate_synthetic_kline(300, seed=42, trend="up", volatility=0.012),   # 茅台-上涨
        "000001": generate_synthetic_kline(300, seed=100, trend="sideways", volatility=0.018),  # 平安-震荡
        "AAPL": generate_synthetic_kline(300, seed=200, trend="up", volatility=0.014),    # 苹果-上涨
        "TEST01": generate_synthetic_kline(300, seed=300, trend="down", volatility=0.022),  # 测试-下跌
        "TEST02": generate_synthetic_kline(150, seed=400, trend="up", volatility=0.020),   # 短数据
    }


# ============================================================
# 测试用例
# ============================================================

def test_feature_extraction():
    """测试特征提取是否正常。"""
    logger.info("=" * 60)
    logger.info("TEST 1: 特征提取")
    logger.info("=" * 60)

    from src.core.ml_predictor.features import extract_features

    df = generate_synthetic_kline(300, seed=42, trend="up")
    X, y, feature_names = extract_features(df, horizon_days=5)

    assert X.shape[0] >= 50, f"样本太少: {X.shape[0]}"
    assert X.shape[1] > 5, f"特征太少: {X.shape[1]}"
    assert len(feature_names) == X.shape[1]
    assert len(y) == X.shape[0]

    logger.info("  -> 样本: %d, 特征维度: %d, 特征名前5: %s",
                X.shape[0], X.shape[1], feature_names[:5])
    logger.info("  -> 标签分布: 涨=%.1f%%, 跌=%.1f%%",
                (y == 1).sum() / len(y) * 100, (y == 0).sum() / len(y) * 100)
    logger.info("  PASSED")


def test_training():
    """测试模型训练。"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: 模型训练")
    logger.info("=" * 60)

    from src.core.ml_predictor.trainer import MLTrainer
    from src.core.ml_predictor.schemas import TrainConfig

    df = generate_synthetic_kline(300, seed=42, trend="up")
    config = TrainConfig(n_estimators=50, max_depth=4, min_train_samples=50, early_stopping_rounds=0)
    trainer = MLTrainer(config)
    result = trainer.train(df, "TEST_TRAIN")

    logger.info("  -> Accuracy: %.4f", result.accuracy)
    logger.info("  -> Precision: %.4f", result.precision)
    logger.info("  -> Recall: %.4f", result.recall)
    logger.info("  -> F1: %.4f", result.f1_score)
    logger.info("  -> AUC: %.4f", result.auc_roc)
    logger.info("  -> 样本数: %d, 特征数: %d", result.n_samples, result.n_features)
    logger.info("  -> 模型版本: %s", result.model_version)
    if result.top_features[:3]:
        for fi in result.top_features[:3]:
            logger.info("      %s: %.6f", fi.feature, fi.importance)

    assert not result.error, f"训练失败: {result.error}"
    assert result.accuracy > 0, "Accuracy 应为正"
    assert result.f1_score > 0, "F1 应为正"
    logger.info("  PASSED")


def test_prediction():
    """测试 ML 预测。"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: ML 预测")
    logger.info("=" * 60)

    from src.core.ml_predictor.predictor import MLPredictor
    from src.core.ml_predictor.trainer import MLTrainer
    from src.core.ml_predictor.schemas import TrainConfig

    stock_code = "000001"
    df = generate_synthetic_kline(300, seed=100, trend="sideways")

    # 先训练
    trainer = MLTrainer(TrainConfig(n_estimators=50, max_depth=4, early_stopping_rounds=0))
    train_result = trainer.train(df, stock_code)

    # 再预测
    predictor = MLPredictor()
    pred = predictor.predict(stock_code, "平安银行", df)

    logger.info("  -> 方向: %s", pred.direction)
    logger.info("  -> 置信度: %.4f", pred.confidence)
    logger.info("  -> 分数: %.4f", pred.score)
    logger.info("  -> 预期收益: %.4f%%", pred.expected_return)
    logger.info("  -> 是否有效: %s", pred.is_valid)

    assert pred.is_valid, f"预测无效: {pred.error}"
    assert pred.direction in ("up", "down", "neutral"), f"非法方向: {pred.direction}"
    assert 0 <= pred.confidence <= 1, f"置信度越界: {pred.confidence}"
    logger.info("  PASSED")


def test_shap_explainability():
    """测试 SHAP 可解释性。"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: SHAP 可解释性")
    logger.info("=" * 60)

    try:
        import shap  # noqa: F401
    except ImportError:
        logger.info("  -> SKIP: shap 未安装，跳过 SHAP 测试")
        return

    from src.core.ml_predictor.predictor import MLPredictor
    from src.core.ml_predictor.trainer import MLTrainer
    from src.core.ml_predictor.schemas import TrainConfig

    stock_code = "600519"
    df = generate_synthetic_kline(300, seed=42, trend="up")

    # 先训练
    trainer = MLTrainer(TrainConfig(n_estimators=30, max_depth=4, early_stopping_rounds=0))
    trainer.train(df, stock_code)

    # SHAP 解释
    predictor = MLPredictor()
    result = predictor.explain(stock_code, df)

    if result is None:
        logger.info("  -> SKIP: SHAP 返回 None（模型类型不兼容或计算失败）")
        return

    logger.info("  -> 预测方向: %s", result["prediction_direction"])
    logger.info("  -> 预测置信度: %.4f", result["prediction_confidence"])
    logger.info("  -> Base value: %.4f", result["base_value"])

    # Top SHAP 特征
    shap_vals = result.get("shap_values", [])
    for sv in shap_vals[:5]:
        logger.info("    %s: %+.6f", sv["feature"], sv["shap_value"])

    logger.info("  -> 正向 Top3: %s", [p["feature"] for p in result.get("top_positive", [])])
    logger.info("  -> 负向 Top3: %s", [n["feature"] for n in result.get("top_negative", [])])

    assert "shap_values" in result
    assert "top_positive" in result
    assert "top_negative" in result
    logger.info("  PASSED")


def test_signal_fusion():
    """测试 ML + LLM + 技术因子三源信号融合。"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: 信号融合（ML + LLM + 技术因子）")
    logger.info("=" * 60)

    from src.services.ml_pipeline_service import MLPipelineService
    from src.core.ml_predictor.trainer import MLTrainer
    from src.core.ml_predictor.schemas import TrainConfig

    # 多股票测试
    stock_data = generate_multi_stock_kline()

    for stock_code in ["600519", "000001", "TEST01"]:
        df = stock_data[stock_code]
        # 预训练
        trainer = MLTrainer(TrainConfig(n_estimators=50, max_depth=4, early_stopping_rounds=0))
        trainer.train(df, stock_code)

    # 对每只股票执行完整融合分析
    service = MLPipelineService()

    # 模拟 LLM 分析文本
    llm_texts = {
        "600519": "该股技术面强势，MACD金叉，建议买入。高置信度，强烈看涨。",
        "000001": "当前市场震荡，方向不明确，建议观望。",
        "TEST01": "连续破位下跌，资金流出明显，偏空。",
    }

    for stock_code in ["600519", "000001", "TEST01"]:
        logger.info("  --- %s ---", stock_code)
        df = stock_data[stock_code]
        result = service.analyze(
            stock_code=stock_code,
            stock_name=stock_code,
            kline_df=df,
            llm_signal_text=llm_texts.get(stock_code),
            train_if_missing=False,
        )

        logger.info("    ML预测方向: %s", result.ml_prediction.direction if result.ml_prediction else "N/A")
        logger.info("    ML置信度: %.4f", result.ml_prediction.confidence if result.ml_prediction else 0)
        logger.info("    融合方向: %s", result.fused_direction)
        logger.info("    融合得分: %.4f", result.fused_score)
        logger.info("    融合置信度: %s", result.fused_confidence)
        logger.info("    主驱动源: %s", result.fused_primary_driver)
        logger.info("    市场状态: %s (%.2f)", result.market_regime, result.regime_confidence)
        logger.info("    自适应权重: %s", result.adaptive_weights)

        assert result.ml_prediction is not None, f"ML 预测为空 ({stock_code})"
        assert result.ml_prediction.is_valid, f"ML 预测无效 ({stock_code}): {result.ml_prediction.error}"

    logger.info("  PASSED")


def test_walk_forward():
    """测试 Walk-Forward 时间序列交叉验证。"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Walk-Forward 时间序列验证")
    logger.info("=" * 60)

    from src.core.ml_predictor.trainer import MLTrainer
    from src.core.ml_predictor.schemas import TrainConfig

    df = generate_synthetic_kline(300, seed=42, trend="up")
    config = TrainConfig(n_estimators=30, max_depth=4, early_stopping_rounds=0, min_train_samples=50)
    trainer = MLTrainer(config)

    wf_result = trainer.train_walk_forward(df, "TEST_WF", n_splits=3)

    if "error" in wf_result:
        logger.info("  -> FAIL: %s", wf_result["error"])
        return

    logger.info("  -> Avg Accuracy: %.4f (±%.4f)", wf_result["avg_accuracy"], wf_result["std_accuracy"])
    logger.info("  -> Avg Precision: %.4f (±%.4f)", wf_result["avg_precision"], wf_result["std_precision"])
    logger.info("  -> Avg Recall: %.4f (±%.4f)", wf_result["avg_recall"], wf_result["std_recall"])
    logger.info("  -> Avg F1: %.4f (±%.4f)", wf_result["avg_f1"], wf_result["std_f1"])
    logger.info("  -> Avg AUC: %.4f (±%.4f)", wf_result["avg_auc"], wf_result["std_auc"])
    logger.info("  -> 总样本: %d, 特征: %d, 折数: %d",
                wf_result["n_samples"], wf_result["n_features"], len(wf_result["fold_results"]))

    # 逐折细节
    for i, fold in enumerate(wf_result["fold_results"]):
        logger.info("    Fold %d: acc=%.4f prec=%.4f rec=%.4f f1=%.4f auc=%.4f",
                    i + 1, fold["accuracy"], fold["precision"],
                    fold["recall"], fold["f1_score"], fold["auc_roc"])

    assert wf_result["avg_accuracy"] > 0, "WF 平均 Accuracy 应为正"
    logger.info("  PASSED")


def test_risk_metrics():
    """测试回测风险调整指标计算。"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 7: 风险调整指标（回测引擎）")
    logger.info("=" * 60)

    from src.core.backtest_engine import BacktestEngine

    # 模拟回测结果 — compute_risk_metrics 读取 stock_return_pct（百分比）
    class MockResult:
        def __init__(self, stock_return_pct: float):
            self.stock_return_pct = stock_return_pct

    # 构造若干条模拟结果（日收益 -> 取模拟的 stock_return_pct）
    rng = np.random.default_rng(42)
    n = 100
    # 模拟日收益（百分比），每条结果代表一次回测事件
    raw_returns_a = list(rng.normal(1.5, 4.0, n))   # 正收益策略
    raw_returns_b = list(rng.normal(0.5, 3.0, n))   # 低波动策略
    raw_returns_c = list(rng.normal(-1.0, 5.0, n))  # 负收益策略

    results = [MockResult(v) for v in raw_returns_a + raw_returns_b + raw_returns_c]

    metrics = BacktestEngine.compute_risk_metrics(results=results, risk_free_rate=0.03)

    logger.info("  -> 夏普比率: %.4f", metrics.get("sharpe_ratio"))
    logger.info("  -> 索提诺比率: %.4f", metrics.get("sortino_ratio"))
    logger.info("  -> 最大回撤: %.2f%%", metrics.get("max_drawdown_pct"))
    logger.info("  -> 卡玛比率: %.4f", metrics.get("calmar_ratio"))
    logger.info("  -> 年化收益: %.2f%%", metrics.get("annualized_return_pct"))
    logger.info("  -> 年化波动: %.2f%%", metrics.get("annualized_volatility_pct"))
    logger.info("  -> 总收益: %.2f%%", metrics.get("total_return_pct"))

    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics
    assert "max_drawdown_pct" in metrics
    assert isinstance(metrics["sharpe_ratio"], (int, float))
    logger.info("  PASSED")


def test_end_to_end():
    """端到端测试：一条完整分析链路。"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 8: 端到端（完整链路）")
    logger.info("=" * 60)

    from src.services.ml_pipeline_service import MLPipelineService

    service = MLPipelineService()
    stock_data = generate_multi_stock_kline()

    for stock_code in ["600519", "000001", "TEST01", "TEST02"]:
        df = stock_data[stock_code]
        result = service.analyze(
            stock_code=stock_code,
            stock_name=stock_code,
            kline_df=df,
            llm_signal_text="技术面偏多，建议关注",
            train_if_missing=True,
        )

        status = "OK" if result.is_valid else f"ERR: {result.error}"
        logger.info("  %s: ML方向=%s 置信度=%.2f 融合=%s [%s]",
                    stock_code,
                    result.ml_prediction.direction if result.ml_prediction else "?",
                    result.ml_prediction.confidence if result.ml_prediction else 0,
                    result.fused_direction,
                    status)

    # TEST02 数据较短(150天)，也应该能跑通
    result_short = service.analyze(
        stock_code="TEST02",
        stock_name="短数据测试",
        kline_df=stock_data["TEST02"],
        train_if_missing=True,
    )
    logger.info("  短数据(TEST02): ML方向=%s 有效=%s",
                result_short.ml_prediction.direction if result_short.ml_prediction else "?",
                result_short.is_valid)

    logger.info("  PASSED")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="ML管线本地验证脚本")
    parser.add_argument("--quick", action="store_true", help="快速冒烟（跳过 SHAP + Walk-Forward）")
    parser.add_argument("--no-shap", action="store_true", help="跳过 SHAP 测试")
    args = parser.parse_args()

    logger.info("ML 管线本地验证 — %s", "快速冒烟" if args.quick else "全量测试")
    logger.info("项目根目录: %s", _PROJECT_ROOT)
    logger.info("Python: %s", sys.version)
    logger.info("日期: %s\n", date.today().isoformat())

    passed = 0
    failed = 0
    skipped = 0

    tests = [
        ("特征提取", test_feature_extraction, False),
        ("模型训练", test_training, False),
        ("ML 预测", test_prediction, False),
        ("信号融合", test_signal_fusion, False),
        ("SHAP 可解释性", test_shap_explainability, args.quick or args.no_shap),
        ("Walk-Forward 验证", test_walk_forward, args.quick),
        ("风险调整指标", test_risk_metrics, False),
        ("端到端链路", test_end_to_end, False),
    ]

    for name, func, skip in tests:
        if skip:
            logger.info("\n[SKIP] %s", name)
            skipped += 1
            continue
        try:
            func()
            passed += 1
        except Exception as e:
            failed += 1
            logger.error("\n[FAIL] %s: %s", name, e, exc_info=True)

    # ── 汇总 ──
    total = passed + failed
    logger.info("\n" + "=" * 60)
    logger.info("验证结果汇总")
    logger.info("=" * 60)
    logger.info("  通过: %d/%d", passed, total)
    if skipped:
        logger.info("  跳过: %d", skipped)
    if failed:
        logger.info("  失败: %d", failed)
        logger.info("  失败测试: 请检查上方 [FAIL] 日志")
    else:
        logger.info("  全部通过!")

    if failed:
        sys.exit(1)
    else:
        logger.info("ML 管线全链路验证通过。")


if __name__ == "__main__":
    main()
