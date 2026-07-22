import apiClient from './index';

export interface ShapValue {
  feature: string;
  shap_value: number;
}

export interface MLPredictionInfo {
  direction: string;
  confidence: number;
  score?: number;
}

export interface MLExplainResponse {
  stock_code: string;
  shap_available: boolean;
  base_value?: number;
  prediction: MLPredictionInfo;
  shap_values?: ShapValue[];
  top_positive?: ShapValue[];
  top_negative?: ShapValue[];
  feature_importance?: { feature: string; importance: number }[];
}

export interface MLModelInfo {
  stock_code: string;
  version: string;
  feature_count: number;
  file: string;
}

export interface MLModelsResponse {
  models: MLModelInfo[];
  count: number;
}

export interface FusedDecision {
  direction: string;
  score: number;
  confidence_level: string;
  primary_driver: string;
}

export interface MarketRegimeInfo {
  regime: string;
  confidence: number;
  signal: string;
}

export interface MLAnalyzeResponse {
  stock_code: string;
  stock_name: string;
  timestamp: string;
  market_regime: MarketRegimeInfo;
  ml_prediction: MLPredictionInfo & { expected_return?: number; model_version?: string };
  features_importance: { name: string; importance: number }[];
  adaptive_weights: Record<string, number>;
  fused_decision: FusedDecision;
  signal_sources: { name: string; score: number; weight: number; detail: string }[];
}

export interface RiskMetricsResponse {
  total_return_pct?: number;
  annualized_return_pct?: number;
  annualized_volatility_pct?: number;
  sharpe_ratio?: number;
  sortino_ratio?: number | string;
  max_drawdown_pct?: number;
  calmar_ratio?: number | string;
  win_loss_ratio?: number | string;
  avg_win_pct?: number;
  avg_loss_pct?: number;
  count?: number;
  error?: string;
}

export const mlInsightsApi = {
  getModels: async (): Promise<MLModelsResponse> => {
    const response = await apiClient.get<MLModelsResponse>('/api/v1/ml/models');
    return response.data;
  },

  explain: async (stockCode: string): Promise<MLExplainResponse> => {
    const response = await apiClient.get<MLExplainResponse>(
      `/api/v1/ml/explain/${encodeURIComponent(stockCode)}`,
    );
    return response.data;
  },

  analyze: async (stockCode: string, stockName = ''): Promise<MLAnalyzeResponse> => {
    const response = await apiClient.get<MLAnalyzeResponse>(
      `/api/v1/ml/analyze/${encodeURIComponent(stockCode)}`,
      { params: { stock_name: stockName } },
    );
    return response.data;
  },

  getRiskMetrics: async (_code?: string): Promise<RiskMetricsResponse> => {
    const response = await apiClient.get<RiskMetricsResponse>(
      '/api/v1/ml/risk-metrics',
    );
    return response.data;
  },
};
