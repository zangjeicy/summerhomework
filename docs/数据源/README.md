# 数据源文档

本目录说明 RuyiDailyStockAnalysis 当前代码中的数据获取行为，供开发、代码审查、排障和课程编写使用。文档以当前 `dev` 分支代码为事实基线，不把规划能力描述为已实现能力。

## 推荐阅读顺序

1. [数据源总体架构](01-架构与设计/数据源总体架构.md)
2. [数据源选择与路由机制](01-架构与设计/数据源选择与路由机制.md)
3. [通用数据契约](02-数据契约/通用数据契约.md)
4. [数据质量状态与来源元数据](02-数据契约/数据质量状态与来源元数据.md)
5. [新数据源接入指南](03-开发接入/新数据源接入指南.md)
6. [数据源能力矩阵](04-数据源说明/数据源能力矩阵.md)
7. [数据源代码审查清单](05-测试与审查/数据源代码审查清单.md)
8. [常见问题排查手册](06-运维与排障/常见问题排查手册.md)
9. [常用金融数据爬取源](常用金融数据爬取源.md)

## 事实入口

- 统一日线入口和数据源管理器：`data_provider/base.py`
- 数据源初始化：`DataFetcherManager._init_default_fetchers`
- 日线选择：`DataFetcherManager.get_daily_data`
- 实时行情选择：`DataFetcherManager.get_realtime_quote`
- 基本面适配：`data_provider/fundamental_adapter.py`、`data_provider/yfinance_fundamental_adapter.py`
- 新闻检索：`src/search_service.py` 中的 `SearchService.search_stock_news`
- 数据源配置：`src/config.py` 和 `.env.example`

## 当前边界

当前实现已经具备多数据源、市场过滤、失败切换、部分健康熔断、实时行情优先级配置和运行诊断，但尚未由一份结构化能力声明统一驱动所有路由。能力矩阵因此是对当前代码的审计视图，不是运行时注册表。
