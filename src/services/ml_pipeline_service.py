# -*- coding: utf-8 -*-
"""ML Pipeline Service — 将 ML 预测 + 信号融合接入主分析流程。

该服务提供轻量级接口，供 pipeline.py 在每只股票分析过程中调用：
  1. 训练/加载 ML 模型
  2. 生成 ML 方向预测 + 置信度
  3. 检测市场状态 + 计算自适应权重
  4. 融合 ML + LLM + 技术因子 → 决策信号
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import pandas as pd

from src.core.ml_predictor.predictor import MLPredictor
from src.core.ml_predictor.trainer import MLTrainer
from src.core.ml_predictor.schemas import MLPrediction, TrainConfig
from src.core.fusion_engine.schemas import SignalSource
from src.core.fusion_engine.orchestrator import FusionOrchestrator
from src.core.fusion_engine.regime_detector import MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class MLAnalysisResult:
    """ML 分析结果 — 可序列化挂载到 AnalysisResult 上。"""

    stock_code: str
    stock_name: str = ""
    ml_prediction: Optional[MLPrediction] = None

    # 融合决策
    fused_direction: str = "neutral"          # buy / sell / hold / neutral
    fused_score: float = 0.0                  # -1.0 ~ 1.0
    fused_confidence: str = "low"             # high / medium / low
    fused_primary_driver: str = ""            # 主驱动信号源名称

    # 市场状态
    market_regime: str = "unknown"
    regime_confidence: float = 0.0

    # 自适应权重
    adaptive_weights: dict = field(default_factory=dict)

    # 信号源明细
    signal_sources: list[dict] = field(default_factory=list)

    # 特征重要性
    top_features: list[dict] = field(default_factory=list)

    # 错误信息
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.error is None and self.ml_prediction is not None and self.ml_prediction.is_valid

    def to_dict(self) -> dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "ml_prediction": {
                "direction": self.ml_prediction.direction if self.ml_prediction else None,
                "confidence": self.ml_prediction.confidence if self.ml_prediction else None,
                "score": self.ml_prediction.score if self.ml_prediction else None,
                "expected_return": self.ml_prediction.expected_return if self.ml_prediction else None,
                "model_version": self.ml_prediction.model_version if self.ml_prediction else None,
            },
            "fused_direction": self.fused_direction,
            "fused_score": self.fused_score,
            "fused_confidence": self.fused_confidence,
            "fused_primary_driver": self.fused_primary_driver,
            "market_regime": self.market_regime,
            "regime_confidence": self.regime_confidence,
            "adaptive_weights": self.adaptive_weights,
            "signal_sources": self.signal_sources,
            "top_features": self.top_features,
            "error": self.error,
        }


class MLPipelineService:
    """ML 流水线服务 — 在分析链路中注入 ML 预测与融合决策。"""

    def __init__(self):
        self._predictor: Optional[MLPredictor] = None
        self._trainer: Optional[MLTrainer] = None
        self._orchestrator: Optional[FusionOrchestrator] = None

    @property
    def predictor(self) -> MLPredictor:
        if self._predictor is None:
            self._predictor = MLPredictor()
        return self._predictor

    @property
    def trainer(self) -> MLTrainer:
        if self._trainer is None:
            self._trainer = MLTrainer()
        return self._trainer

    @property
    def orchestrator(self) -> FusionOrchestrator:
        if self._orchestrator is None:
            self._orchestrator = FusionOrchestrator()
        return self._orchestrator

    def analyze(
        self,
        stock_code: str,
        stock_name: str = "",
        kline_df: Optional[pd.DataFrame] = None,
        llm_signal_text: Optional[str] = None,
        train_if_missing: bool = True,
    ) -> MLAnalysisResult:
        """对单只股票执行完整的 ML 分析链路。

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            kline_df: 历史 K 线 DataFrame（col: open/high/low/close/volume）
            llm_signal_text: LLM 分析文本（用于提取方向信号）
            train_if_missing: 模型缺失时是否自动训练

        Returns:
            MLAnalysisResult
        """
        error_parts: list[str] = []
        ml_pred: Optional[MLPrediction] = None

        # ── 1. ML 预测 ──
        if kline_df is not None and len(kline_df) >= 30:
            try:
                ml_pred = self.predictor.predict(stock_code, stock_name, kline_df)
                if not ml_pred.is_valid and train_if_missing and "模型未训练" in (ml_pred.error or ""):
                    logger.info("[MLPipeline] %s 模型缺失，自动训练中...", stock_code)
                    train_result = self.trainer.train(kline_df, stock_code)
                    if train_result.error:
                        logger.warning("[MLPipeline] %s 训练失败: %s", stock_code, train_result.error)
                    else:
                        ml_pred = self.predictor.predict(stock_code, stock_name, kline_df)
            except Exception as e:
                logger.error("[MLPipeline] %s ML预测失败: %s", stock_code, e)
                error_parts.append(f"ML预测: {e}")
        else:
            error_parts.append("K线数据不足")
            logger.warning("[MLPipeline] %s K线数据不足，跳过ML预测", stock_code)

        # ── 2. 构建信号源 ──
        ml_sig: Optional[SignalSource] = None
        llm_sig: Optional[SignalSource] = None
        tech_sig: Optional[SignalSource] = None
        extra_signals: list[SignalSource] = []

        if ml_pred and ml_pred.is_valid:
            ml_direction = (
                "buy" if ml_pred.direction == "up"
                else "sell" if ml_pred.direction == "down"
                else "neutral"
            )
            ml_sig = SignalSource(
                name="ml_xgboost",
                direction=ml_direction,
                score=ml_pred.score,
                confidence=ml_pred.confidence,
                detail=f"ML预测: {ml_pred.direction} (conf={ml_pred.confidence:.2f})",
            )

        # 从 LLM 分析文本提取信号
        if llm_signal_text:
            llm_direction, llm_confidence = self._parse_llm_signal(llm_signal_text)
            llm_sig = SignalSource(
                name="llm_analysis",
                direction=llm_direction,
                score=0.5 if llm_direction == "buy" else (
                    -0.5 if llm_direction == "sell" else 0.0
                ),
                confidence=llm_confidence,
                detail="LLM综合分析",
            )

        # ── 3. 技术因子信号 ──
        if kline_df is not None and len(kline_df) >= 20:
            try:
                tech_sig = self._build_technical_signal(kline_df)
                if tech_sig:
                    extra_signals.append(tech_sig)
            except Exception as e:
                logger.debug("[MLPipeline] %s 技术因子信号构建失败: %s", stock_code, e)

        # ── 4. 融合决策 ──
        if ml_sig or llm_sig or extra_signals:
            try:
                fusion_result = self.orchestrator.analyze(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    index_df=None,
                    kline_df=kline_df,
                    ml_signal=ml_sig,
                    llm_signal=llm_sig,
                    extra_signals=extra_signals if extra_signals else None,
                )

                return MLAnalysisResult(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    ml_prediction=ml_pred,
                    fused_direction=fusion_result["fused_decision"]["direction"],
                    fused_score=fusion_result["fused_decision"]["score"],
                    fused_confidence=fusion_result["fused_decision"]["confidence_level"],
                    fused_primary_driver=fusion_result["fused_decision"]["primary_driver"],
                    market_regime=fusion_result["market_regime"]["regime"],
                    regime_confidence=fusion_result["market_regime"]["confidence"],
                    adaptive_weights=fusion_result["adaptive_weights"],
                    signal_sources=fusion_result["signal_sources"],
                    top_features=[
                        {"feature": f.feature, "importance": f.importance}
                        for f in (ml_pred.top_features[:10] if ml_pred else [])
                    ],
                )
            except Exception as e:
                logger.error("[MLPipeline] %s 融合决策失败: %s", stock_code, e)
                error_parts.append(f"融合决策: {e}")

        # 降级：只有 ML 预测，没有融合
        if ml_pred and ml_pred.is_valid:
            return MLAnalysisResult(
                stock_code=stock_code,
                stock_name=stock_name,
                ml_prediction=ml_pred,
                fused_direction="neutral",
                fused_confidence="low",
                top_features=[
                    {"feature": f.feature, "importance": f.importance}
                    for f in ml_pred.top_features[:10]
                ],
                error="; ".join(error_parts) if error_parts else None,
            )

        return MLAnalysisResult(
            stock_code=stock_code,
            stock_name=stock_name,
            error="; ".join(error_parts) if error_parts else "ML分析不可用",
        )

    def _parse_llm_signal(self, text: str) -> tuple[str, float]:
        """从 LLM 分析文本中提取方向信号和置信度。"""
        text_lower = text.lower()

        # 置信度关键词
        confidence = 0.50
        high_conf_keywords = ["strong", "强烈", "确定", "明确", "高置信", "high confidence"]
        medium_conf_keywords = ["可能", "偏多", "偏空", "建议", "likely"]
        low_conf_keywords = ["不确定", "观望", "中性", "uncertain", "neutral"]

        high_count = sum(1 for kw in high_conf_keywords if kw in text_lower)
        med_count = sum(1 for kw in medium_conf_keywords if kw in text_lower)
        low_count = sum(1 for kw in low_conf_keywords if kw in text_lower)

        if high_count > 0:
            confidence = 0.80
        elif med_count > 0:
            confidence = 0.65
        elif low_count > 0:
            confidence = 0.45

        # 方向判断
        bullish = ["买入", "看涨", "bullish", "buy", "增持", "加仓", "上涨"]
        bearish = ["卖出", "看跌", "bearish", "sell", "减持", "减仓", "下跌"]

        bull_count = sum(1 for kw in bullish if kw in text_lower)
        bear_count = sum(1 for kw in bearish if kw in text_lower)

        if bull_count > bear_count and bull_count > 0:
            return "buy", confidence
        elif bear_count > bull_count and bear_count > 0:
            return "sell", confidence
        return "neutral", 0.50

    def _build_technical_signal(self, kline_df: pd.DataFrame) -> Optional[SignalSource]:
        """从 K 线构建技术因子信号。"""
        try:
            from src.stock_analyzer import StockTrendAnalyzer
            analyzer = StockTrendAnalyzer()
            trend_result = analyzer.analyze(kline_df, "__ml__")

            # 将趋势分析结果转为融合信号
            if trend_result.buy_signal.value in ("强烈买入", "买入"):
                direction = "buy"
                score = 0.6 if trend_result.buy_signal.value == "强烈买入" else 0.35
            elif "卖出" in trend_result.buy_signal.value:
                direction = "sell"
                score = -0.6 if "强烈" in trend_result.buy_signal.value else -0.35
            else:
                direction = "neutral"
                score = 0.0

            return SignalSource(
                name="technical_trend",
                direction=direction,
                score=score,
                confidence=trend_result.signal_score / 100.0,
                detail=f"趋势: {trend_result.trend_status.value}, "
                        f"MACD: {trend_result.macd_status.value}, "
                        f"RSI: {trend_result.rsi_status.value}",
            )
        except Exception:
            return None

    def record_ml_outcome(
        self,
        stock_code: str,
        regime_str: str,
        ml_pred: Optional[MLPrediction],
        actual_direction: str,
    ) -> None:
        """记录 ML 预测结果用于在线权重进化。"""
        if ml_pred is None or not ml_pred.is_valid:
            return

        try:
            regime = MarketRegime(regime_str) if regime_str in MarketRegime._value2member_map_ else MarketRegime.UNKNOWN
        except (ValueError, AttributeError):
            regime = MarketRegime.UNKNOWN

        # 判断预测是否正确
        predicted_up = ml_pred.direction == "up"
        actual_up = actual_direction == "up"
        correct = (predicted_up and actual_up) or (not predicted_up and not actual_up)

        self.orchestrator.record_outcome("ml_xgboost", regime, correct)
