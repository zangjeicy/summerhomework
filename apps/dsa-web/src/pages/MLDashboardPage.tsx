import type React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { Brain, TrendingUp, TrendingDown, Minus, Search, Shield, Activity } from 'lucide-react';
import { mlInsightsApi } from '../api/mlInsights';
import type {
  MLModelInfo,
  MLExplainResponse,
  MLAnalyzeResponse,
  RiskMetricsResponse,
} from '../api/mlInsights';
import type { ParsedApiError } from '../api/error';
import { getParsedApiError } from '../api/error';
import { ApiErrorAlert, Card, Badge, EmptyState, StatusDot } from '../components/common';

// ============ Helpers ============

function pct(value?: number | null): string {
  if (value == null) return '--';
  return `${value.toFixed(1)}%`;
}

function num(value?: number | null | string, digits = 2): string {
  if (value == null || value === 'inf') return '--';
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '--';
  return n.toFixed(digits);
}

function directionBadge(dir: string) {
  switch (dir) {
    case 'up': case 'buy': return <Badge variant="success"><TrendingUp className="w-3 h-3 mr-1" />看涨</Badge>;
    case 'down': case 'sell': return <Badge variant="danger"><TrendingDown className="w-3 h-3 mr-1" />看跌</Badge>;
    default: return <Badge variant="info"><Minus className="w-3 h-3 mr-1" />中性</Badge>;
  }
}

function confidenceColor(conf: number): string {
  if (conf >= 0.7) return 'text-green-400';
  if (conf >= 0.5) return 'text-yellow-400';
  return 'text-red-400';
}

// ============ Sub-components ============

const ModelHealthCard: React.FC<{ models: MLModelInfo[]; loading: boolean }> = ({ models, loading }) => (
  <Card>
    <div className="flex items-center gap-2 mb-4">
      <Brain className="w-5 h-5 text-primary" />
      <h2 className="text-lg font-semibold">模型健康度</h2>
      {loading && <StatusDot tone="info" pulse />}
    </div>
    {loading ? (
      <p className="text-sm text-muted-foreground">加载中...</p>
    ) : models.length === 0 ? (
      <EmptyState icon={<Brain />} title="暂无已训练模型" description="运行一次分析后，ML 模型将自动训练" />
    ) : (
      <div className="space-y-2">
        <div className="flex gap-4 text-sm">
          <div className="flex-1 text-center p-3 rounded-lg bg-accent/50">
            <div className="text-2xl font-bold text-primary">{models.length}</div>
            <div className="text-xs text-muted-foreground">已训练模型</div>
          </div>
          <div className="flex-1 text-center p-3 rounded-lg bg-accent/50">
            <div className="text-2xl font-bold text-green-400">
              {models.reduce((s, m) => s + m.feature_count, 0)}
            </div>
            <div className="text-xs text-muted-foreground">总特征维度</div>
          </div>
        </div>
        <div className="mt-3 space-y-1 max-h-40 overflow-y-auto">
          {models.slice(0, 8).map((m) => (
            <div key={m.file} className="flex items-center justify-between text-xs py-1 px-2 rounded hover:bg-accent">
              <span className="font-mono">{m.stock_code}</span>
              <span className="text-muted-foreground">v{m.version} · {m.feature_count}维</span>
            </div>
          ))}
        </div>
      </div>
    )}
  </Card>
);

const MetricItem: React.FC<{ label: string; value: string; hint?: string; warn?: boolean }> = ({ label, value, hint, warn }) => (
  <div className="p-2 rounded-lg bg-accent/30">
    <div className={`text-lg font-bold ${warn && value !== '--' ? 'text-red-400' : ''}`}>{value}</div>
    <div className="text-xs text-muted-foreground">{label}{hint && ` (${hint})`}</div>
  </div>
);

const RiskMetricsCard: React.FC<{ metrics: RiskMetricsResponse | null; loading: boolean; error: ParsedApiError | null }> = ({ metrics, loading, error }) => (
  <Card>
    <div className="flex items-center gap-2 mb-4">
      <Shield className="w-5 h-5 text-primary" />
      <h2 className="text-lg font-semibold">风险调整指标</h2>
      {loading && <StatusDot tone="info" pulse />}
    </div>
    {error && <ApiErrorAlert error={error} />}
    {loading ? (
      <p className="text-sm text-muted-foreground">加载中...</p>
    ) : !metrics || metrics.error ? (
      <EmptyState icon={<Shield />} title="暂无风险数据" description="运行回测后可见" />
    ) : (
      <div className="grid grid-cols-2 gap-3 text-sm">
        <MetricItem label="夏普比率" value={num(metrics.sharpe_ratio, 3)} hint=">1 优秀" />
        <MetricItem label="索提诺比率" value={typeof metrics.sortino_ratio === 'number' ? num(metrics.sortino_ratio, 3) : '--'} hint=">1 优秀" />
        <MetricItem label="最大回撤" value={pct(metrics.max_drawdown_pct)} hint="越小越好" warn />
        <MetricItem label="卡玛比率" value={typeof metrics.calmar_ratio === 'number' ? num(metrics.calmar_ratio, 3) : '--'} hint=">1 优秀" />
        <MetricItem label="年化收益" value={pct(metrics.annualized_return_pct)} />
        <MetricItem label="年化波动" value={pct(metrics.annualized_volatility_pct)} />
        <MetricItem label="盈亏比" value={typeof metrics.win_loss_ratio === 'number' ? num(metrics.win_loss_ratio, 2) : '--'} />
        <MetricItem label="总收益" value={pct(metrics.total_return_pct)} />
      </div>
    )}
  </Card>
);

const ShapExplanationCard: React.FC = () => {
  const [stockCode, setStockCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [data, setData] = useState<MLExplainResponse | null>(null);

  const search = useCallback(async () => {
    if (!stockCode.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await mlInsightsApi.explain(stockCode.trim());
      setData(result);
    } catch (e: unknown) {
      setError(getParsedApiError(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [stockCode]);

  const maxAbsShap = data?.shap_values && data.shap_values.length > 0
    ? Math.max(...data.shap_values.map((s) => Math.abs(s.shap_value)))
    : 1;

  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-primary" />
        <h2 className="text-lg font-semibold">SHAP 特征解释</h2>
      </div>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={stockCode}
          onChange={(e) => setStockCode(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="输入股票代码 (如 600519)"
          className="input-surface input-focus-glow h-10 flex-1 rounded-xl border bg-transparent px-3 text-sm"
        />
        <button
          type="button"
          onClick={search}
          disabled={loading || !stockCode.trim()}
          className="btn-primary h-10 px-4 rounded-xl text-sm"
        >
          <Search className="w-4 h-4" />
        </button>
      </div>
      {error && <ApiErrorAlert error={error} />}
      {loading && <p className="text-sm text-muted-foreground py-4 text-center">分析中...</p>}
      {data && !loading && (
        <div>
          <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-accent/50">
            <span className="text-sm text-muted-foreground">ML预测：</span>
            {directionBadge(data.prediction.direction)}
            <span className={`text-sm font-bold ${confidenceColor(data.prediction.confidence)}`}>
              置信度 {(data.prediction.confidence * 100).toFixed(0)}%
            </span>
            {data.shap_available && (
              <span className="text-xs text-muted-foreground ml-auto">SHAP base: {num(data.base_value, 3)}</span>
            )}
          </div>

          {data.shap_available && data.shap_values && data.shap_values.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-muted-foreground mb-2">推动预测的关键特征（正向=推涨，负向=压跌）</p>
              {data.shap_values.slice(0, 10).map((sv) => (
                <div key={sv.feature} className="flex items-center gap-2 text-xs">
                  <span className="w-28 truncate font-mono">{sv.feature}</span>
                  <div className="flex-1 h-4 rounded-full bg-accent relative overflow-hidden">
                    <div
                      className={`absolute top-0 h-full rounded-full transition-all ${
                        sv.shap_value > 0 ? 'bg-green-500/50 left-1/2' : 'bg-red-500/50 right-1/2'
                      }`}
                      style={{
                        width: `${(Math.abs(sv.shap_value) / maxAbsShap) * 50}%`,
                        ...(sv.shap_value > 0 ? { left: '50%' } : { right: '50%' }),
                      }}
                    />
                  </div>
                  <span className={`w-16 text-right font-mono ${sv.shap_value > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {sv.shap_value > 0 ? '+' : ''}{sv.shap_value.toFixed(4)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {!data.shap_available && data.feature_importance && data.feature_importance.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs text-muted-foreground mb-2">特征重要性（SHAP 不可用时的备选）</p>
              {data.feature_importance.slice(0, 10).map((fi) => (
                <div key={fi.feature} className="flex items-center gap-2 text-xs">
                  <span className="w-28 truncate font-mono">{fi.feature}</span>
                  <div className="flex-1 h-3 rounded-full bg-accent relative overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full rounded-full bg-primary/50"
                      style={{ width: `${(fi.importance / data.feature_importance![0]!.importance) * 100}%` }}
                    />
                  </div>
                  <span className="w-16 text-right font-mono">{fi.importance.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}

          {!data.shap_available && !data.feature_importance?.length && (
            <EmptyState icon={<Activity />} title="无可解释性数据" description="模型尚未训练或 SHAP 不可用" />
          )}
        </div>
      )}
      {!data && !loading && !error && (
        <EmptyState icon={<Search />} title="搜索股票查看 SHAP 解释" description="输入股票代码查看 ML 预测的详细解释" />
      )}
    </Card>
  );
};

const FusionWeightsCard: React.FC = () => {
  const [stockCode, setStockCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [data, setData] = useState<MLAnalyzeResponse | null>(null);

  const search = useCallback(async () => {
    if (!stockCode.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await mlInsightsApi.analyze(stockCode.trim());
      setData(result);
    } catch (e: unknown) {
      setError(getParsedApiError(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [stockCode]);

  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-primary" />
        <h2 className="text-lg font-semibold">信号融合权重</h2>
      </div>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={stockCode}
          onChange={(e) => setStockCode(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="输入股票代码 (如 600519)"
          className="input-surface input-focus-glow h-10 flex-1 rounded-xl border bg-transparent px-3 text-sm"
        />
        <button
          type="button"
          onClick={search}
          disabled={loading || !stockCode.trim()}
          className="btn-primary h-10 px-4 rounded-xl text-sm"
        >
          <Search className="w-4 h-4" />
        </button>
      </div>
      {error && <ApiErrorAlert error={error} />}
      {loading && <p className="text-sm text-muted-foreground py-4 text-center">分析中...</p>}
      {data && !loading && (
        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-accent/50">
            <div className="text-xs text-muted-foreground mb-1">市场状态</div>
            <div className="flex items-center gap-2">
              <Badge variant="info">{data.market_regime.regime}</Badge>
              <span className="text-xs text-muted-foreground">
                置信度 {(data.market_regime.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-xs text-muted-foreground">信号源权重分布</div>
            {data.signal_sources.map((src) => (
              <div key={src.name} className="flex items-center gap-2 text-xs">
                <span className="w-28 font-mono">{src.name}</span>
                <div className="flex-1 h-4 rounded-full bg-accent relative overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full rounded-full bg-primary/40"
                    style={{ width: `${(src.weight || 0) * 100}%` }}
                  />
                </div>
                <span className="w-12 text-right font-mono">{num(src.weight * 100, 0)}%</span>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-lg bg-accent/50">
            <div className="text-xs text-muted-foreground mb-1">融合决策</div>
            <div className="flex items-center gap-2">
              {directionBadge(data.fused_decision.direction)}
              <span className="text-xs text-muted-foreground">
                置信度 {data.fused_decision.confidence_level} ·
                主驱动 {data.fused_decision.primary_driver}
              </span>
            </div>
          </div>
        </div>
      )}
      {!data && !loading && !error && (
        <EmptyState icon={<Search />} title="搜索股票查看融合权重" description="输入股票代码查看 ML+LLM+因子三源融合结果" />
      )}
    </Card>
  );
};

// ============ Page ============

const MLDashboardPage: React.FC = () => {
  const [models, setModels] = useState<MLModelInfo[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<ParsedApiError | null>(null);

  const [riskMetrics, setRiskMetrics] = useState<RiskMetricsResponse | null>(null);
  const [riskLoading, setRiskLoading] = useState(true);
  const [riskError, setRiskError] = useState<ParsedApiError | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const m = await mlInsightsApi.getModels();
        setModels(m.models || []);
      } catch (e: unknown) {
        setModelsError(getParsedApiError(e));
      } finally {
        setModelsLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const r = await mlInsightsApi.getRiskMetrics();
        setRiskMetrics(r);
      } catch (e: unknown) {
        setRiskError(getParsedApiError(e));
      } finally {
        setRiskLoading(false);
      }
    })();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 overflow-y-auto h-full">
      <div className="flex items-center gap-3">
        <Brain className="w-6 h-6 text-primary" />
        <h1 className="text-2xl font-bold">ML 洞察看板</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {modelsError ? (
          <ApiErrorAlert error={modelsError} />
        ) : (
          <ModelHealthCard models={models} loading={modelsLoading} />
        )}
        <RiskMetricsCard metrics={riskMetrics} loading={riskLoading} error={riskError} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ShapExplanationCard />
        <FusionWeightsCard />
      </div>
    </div>
  );
};

export default MLDashboardPage;
