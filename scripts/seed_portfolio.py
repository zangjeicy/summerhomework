# -*- coding: utf-8 -*-
"""创建 1-2 个模拟持仓账户，让持仓管理页面有数据可看。

用法：
    python scripts/seed_portfolio.py              # 创建/覆盖全部数据
    python scripts/seed_portfolio.py --clean-only  # 仅清理历史数据
    python scripts/seed_portfolio.py --account cn  # 仅创建 A 股账户
    python scripts/seed_portfolio.py --account us  # 仅创建美股账户
"""

import argparse
import json
import logging
import urllib.error
import urllib.request
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("seed_portfolio")

BASE_URL = "http://localhost:8000/api/v1/portfolio"

# ============================================================
# 工具函数
# ============================================================


def api_request(method: str, path: str, body: dict | None = None) -> dict:
    """发送 HTTP 请求到本地 API。"""
    url = f"{BASE_URL}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        logger.error("HTTP %d %s %s: %s", e.code, method, path, body_text)
        raise


def delete_all(account_id: int):
    """删除某账户下的所有交易和流水。"""
    for endpoint, key in [
        ("/trades", "trades"),
        ("/cash-ledger", "entries"),
        ("/corporate-actions", "items"),
    ]:
        try:
            result = api_request("GET", f"{endpoint}?account_id={account_id}")
            items = result.get(key, [])
            for item in items:
                item_id = item["id"]
                try:
                    api_request("DELETE", f"{endpoint}/{item_id}")
                except Exception as exc:
                    logger.warning("删除 %s/%s 失败: %s", endpoint, item_id, exc)
            logger.info("已清理 %d 条 %s", len(items), endpoint)
        except Exception as exc:
            logger.warning("清理 %s 出错: %s", endpoint, exc)


# ============================================================
# A 股账户
# ============================================================


def seed_cn_account():
    """创建 A 股模拟账户。"""
    logger.info("=" * 50)
    logger.info("创建 A 股模拟账户")
    logger.info("=" * 50)

    # 1. 创建账户
    acct = api_request(
        "POST",
        "/accounts",
        {
            "name": "A股模拟账户",
            "broker": "中信证券",
            "market": "cn",
            "base_currency": "CNY",
            "owner_id": "demo",
        },
    )
    account_id = acct["id"]
    logger.info("账户已创建: id=%d, name=%s", account_id, acct["name"])

    # 2. 资金流水 — 初始入金 500,000 CNY
    api_request(
        "POST",
        "/cash-ledger",
        {
            "account_id": account_id,
            "event_date": "2025-09-01",
            "direction": "in",
            "amount": 500000,
            "currency": "CNY",
            "note": "初始入金",
        },
    )
    logger.info("初始入金: 500,000 CNY")

    # 3. 交易记录 — 模拟 2025 年 9 月～2026 年 6 月的买卖
    cn_trades = [
        # 茅台 600519 — 分两次买入，一次卖出
        {"symbol": "600519", "date": "2025-09-05", "side": "buy", "qty": 100, "price": 1650.0, "fee": 5.0, "note": "茅台建仓"},
        {"symbol": "600519", "date": "2025-10-20", "side": "buy", "qty": 100, "price": 1720.0, "fee": 5.0, "note": "茅台加仓"},
        {"symbol": "600519", "date": "2026-03-15", "side": "sell", "qty": 50, "price": 1890.0, "fee": 5.0, "note": "茅台减仓止盈"},
        # 五粮液 000858
        {"symbol": "000858", "date": "2025-09-10", "side": "buy", "qty": 500, "price": 148.0, "fee": 3.0, "note": "五粮液建仓"},
        {"symbol": "000858", "date": "2025-11-05", "side": "buy", "qty": 300, "price": 155.0, "fee": 3.0, "note": "五粮液加仓"},
        # 宁德时代 300750
        {"symbol": "300750", "date": "2025-10-08", "side": "buy", "qty": 200, "price": 210.0, "fee": 3.0, "note": "宁德时代建仓"},
        {"symbol": "300750", "date": "2025-12-15", "side": "buy", "qty": 200, "price": 225.0, "fee": 3.0, "note": "宁德时代加仓"},
        {"symbol": "300750", "date": "2026-05-20", "side": "sell", "qty": 100, "price": 248.0, "fee": 3.0, "note": "宁德时代减仓"},
        # 中国平安 601318
        {"symbol": "601318", "date": "2025-09-15", "side": "buy", "qty": 1000, "price": 42.5, "fee": 5.0, "note": "平安建仓"},
        {"symbol": "601318", "date": "2026-01-10", "side": "buy", "qty": 500, "price": 46.0, "fee": 3.0, "note": "平安加仓"},
        {"symbol": "601318", "date": "2026-06-01", "side": "sell", "qty": 300, "price": 49.5, "fee": 3.0, "note": "平安小减仓"},
    ]

    for t in cn_trades:
        api_request(
            "POST",
            "/trades",
            {
                "account_id": account_id,
                "symbol": t["symbol"],
                "market": "cn",
                "currency": "CNY",
                "trade_date": t["date"],
                "side": t["side"],
                "quantity": t["qty"],
                "price": t["price"],
                "fee": t["fee"],
                "note": t["note"],
            },
        )
        logger.info("  交易: %s %s %s %s %s股 @ %.2f", t["date"], t["symbol"], t["side"], t["note"], t["qty"], t["price"])

    # 4. 公司行为 — 茅台 2025 年分红
    api_request(
        "POST",
        "/corporate-actions",
        {
            "account_id": account_id,
            "symbol": "600519",
            "market": "cn",
            "currency": "CNY",
            "effective_date": "2025-12-25",
            "action_type": "cash_dividend",
            "cash_dividend_per_share": 49.98,
            "note": "茅台2025年度分红",
        },
    )
    logger.info("公司行为: 600519 分红 49.98元/股")

    # 5. 生成快照
    try:
        today = date.today().isoformat()
        snapshot = api_request(
            "GET",
            f"/snapshot?account_id={account_id}&cost_method=fifo&as_of={today}",
        )
        positions = snapshot.get("positions", [])
        logger.info("快照已生成: equity=%.2f, positions=%d", snapshot.get("totalEquity", 0), len(positions))
        for p in positions:
            logger.info(
                "  持仓: %s %s 数量=%d 成本=%.2f 市值=%.2f 盈亏=%.2f (%.1f%%)",
                p.get("accountName", ""),
                p["symbol"],
                p["quantity"],
                p["avgCost"],
                p.get("marketValueBase", 0),
                p.get("unrealizedPnlBase", 0),
                p.get("unrealizedPnlPct", 0),
            )
    except Exception as exc:
        logger.warning("生成快照失败（持仓表格可能仍为空）: %s", exc)

    logger.info("A 股账户创建完毕: account_id=%d", account_id)
    return account_id


# ============================================================
# 美股账户
# ============================================================


def seed_us_account():
    """创建美股模拟账户。"""
    logger.info("\n" + "=" * 50)
    logger.info("创建美股模拟账户")
    logger.info("=" * 50)

    # 1. 创建账户
    acct = api_request(
        "POST",
        "/accounts",
        {
            "name": "美股模拟账户",
            "broker": "盈透证券",
            "market": "us",
            "base_currency": "USD",
            "owner_id": "demo",
        },
    )
    account_id = acct["id"]
    logger.info("账户已创建: id=%d, name=%s", account_id, acct["name"])

    # 2. 资金流水 — 初始入金 100,000 USD
    api_request(
        "POST",
        "/cash-ledger",
        {
            "account_id": account_id,
            "event_date": "2025-09-01",
            "direction": "in",
            "amount": 100000,
            "currency": "USD",
            "note": "初始入金",
        },
    )
    logger.info("初始入金: 100,000 USD")

    # 3. 交易记录 — 模拟美股交易
    us_trades = [
        # AAPL
        {"symbol": "AAPL", "date": "2025-09-03", "side": "buy", "qty": 100, "price": 228.0, "fee": 1.0, "note": "苹果建仓"},
        {"symbol": "AAPL", "date": "2025-11-20", "side": "buy", "qty": 50, "price": 242.0, "fee": 1.0, "note": "苹果加仓"},
        {"symbol": "AAPL", "date": "2026-04-10", "side": "sell", "qty": 30, "price": 265.0, "fee": 1.0, "note": "苹果减仓"},
        # TSLA
        {"symbol": "TSLA", "date": "2025-09-10", "side": "buy", "qty": 80, "price": 245.0, "fee": 1.0, "note": "特斯拉建仓"},
        {"symbol": "TSLA", "date": "2025-12-05", "side": "buy", "qty": 40, "price": 355.0, "fee": 1.0, "note": "特斯拉追高加仓"},
        # NVDA
        {"symbol": "NVDA", "date": "2025-10-15", "side": "buy", "qty": 200, "price": 138.0, "fee": 1.0, "note": "英伟达建仓"},
        {"symbol": "NVDA", "date": "2026-01-25", "side": "buy", "qty": 100, "price": 152.0, "fee": 1.0, "note": "英伟达加仓"},
        {"symbol": "NVDA", "date": "2026-06-15", "side": "sell", "qty": 80, "price": 178.0, "fee": 1.0, "note": "英伟达止盈"},
        # MSFT
        {"symbol": "MSFT", "date": "2025-09-20", "side": "buy", "qty": 60, "price": 435.0, "fee": 1.0, "note": "微软建仓"},
        {"symbol": "MSFT", "date": "2026-02-10", "side": "buy", "qty": 40, "price": 418.0, "fee": 1.0, "note": "微软低位加仓"},
        # AMZN
        {"symbol": "AMZN", "date": "2025-11-01", "side": "buy", "qty": 150, "price": 198.0, "fee": 1.0, "note": "亚马逊建仓"},
        {"symbol": "AMZN", "date": "2026-03-20", "side": "buy", "qty": 50, "price": 215.0, "fee": 1.0, "note": "亚马逊加仓"},
        {"symbol": "AMZN", "date": "2026-05-30", "side": "sell", "qty": 40, "price": 232.0, "fee": 1.0, "note": "亚马逊减仓"},
    ]

    for t in us_trades:
        api_request(
            "POST",
            "/trades",
            {
                "account_id": account_id,
                "symbol": t["symbol"],
                "market": "us",
                "currency": "USD",
                "trade_date": t["date"],
                "side": t["side"],
                "quantity": t["qty"],
                "price": t["price"],
                "fee": t["fee"],
                "note": t["note"],
            },
        )
        logger.info("  交易: %s %s %s %s %s股 @ %.2f", t["date"], t["symbol"], t["side"], t["note"], t["qty"], t["price"])

    # 4. 生成快照
    try:
        today = date.today().isoformat()
        snapshot = api_request(
            "GET",
            f"/snapshot?account_id={account_id}&cost_method=fifo&as_of={today}",
        )
        positions = snapshot.get("positions", [])
        logger.info("快照已生成: equity=%.2f, positions=%d", snapshot.get("totalEquity", 0), len(positions))
        for p in positions:
            logger.info(
                "  持仓: %s %s 数量=%d 成本=%.2f 市值=%.2f 盈亏=%.2f (%.1f%%)",
                p.get("accountName", ""),
                p["symbol"],
                p["quantity"],
                p["avgCost"],
                p.get("marketValueBase", 0),
                p.get("unrealizedPnlBase", 0),
                p.get("unrealizedPnlPct", 0),
            )
    except Exception as exc:
        logger.warning("生成快照失败: %s", exc)

    logger.info("美股账户创建完毕: account_id=%d", account_id)
    return account_id


# ============================================================
# 港股账户
# ============================================================


def seed_hk_account():
    """创建港股模拟账户。"""
    logger.info("\n" + "=" * 50)
    logger.info("创建港股模拟账户")
    logger.info("=" * 50)

    acct = api_request(
        "POST",
        "/accounts",
        {
            "name": "港股模拟账户",
            "broker": "富途证券",
            "market": "hk",
            "base_currency": "HKD",
            "owner_id": "demo",
        },
    )
    account_id = acct["id"]
    logger.info("账户已创建: id=%d, name=%s", account_id, acct["name"])

    api_request(
        "POST",
        "/cash-ledger",
        {
            "account_id": account_id,
            "event_date": "2025-09-01",
            "direction": "in",
            "amount": 800000,
            "currency": "HKD",
            "note": "初始入金",
        },
    )
    logger.info("初始入金: 800,000 HKD")

    hk_trades = [
        # 腾讯 00700
        {"symbol": "hk00700", "date": "2025-09-05", "side": "buy", "qty": 200, "price": 380.0, "fee": 10.0, "note": "腾讯建仓"},
        {"symbol": "hk00700", "date": "2025-11-15", "side": "buy", "qty": 100, "price": 420.0, "fee": 5.0, "note": "腾讯加仓"},
        {"symbol": "hk00700", "date": "2026-04-20", "side": "sell", "qty": 80, "price": 510.0, "fee": 5.0, "note": "腾讯止盈"},
        # 阿里巴巴 09988
        {"symbol": "hk09988", "date": "2025-09-20", "side": "buy", "qty": 500, "price": 88.0, "fee": 5.0, "note": "阿里建仓"},
        {"symbol": "hk09988", "date": "2025-12-10", "side": "buy", "qty": 300, "price": 95.0, "fee": 5.0, "note": "阿里加仓"},
        # 港交所 00388
        {"symbol": "hk00388", "date": "2025-10-05", "side": "buy", "qty": 300, "price": 310.0, "fee": 5.0, "note": "港交所建仓"},
        {"symbol": "hk00388", "date": "2026-02-15", "side": "buy", "qty": 150, "price": 335.0, "fee": 5.0, "note": "港交所加仓"},
        {"symbol": "hk00388", "date": "2026-06-10", "side": "sell", "qty": 100, "price": 365.0, "fee": 5.0, "note": "港交所减仓"},
        # 小米 01810
        {"symbol": "hk01810", "date": "2025-09-25", "side": "buy", "qty": 2000, "price": 20.5, "fee": 5.0, "note": "小米建仓"},
        {"symbol": "hk01810", "date": "2026-01-05", "side": "buy", "qty": 1000, "price": 35.0, "fee": 5.0, "note": "小米追高加仓"},
        {"symbol": "hk01810", "date": "2026-05-25", "side": "sell", "qty": 500, "price": 48.0, "fee": 5.0, "note": "小米止盈"},
        # 美团 03690
        {"symbol": "hk03690", "date": "2025-10-15", "side": "buy", "qty": 300, "price": 165.0, "fee": 5.0, "note": "美团建仓"},
        {"symbol": "hk03690", "date": "2026-03-10", "side": "buy", "qty": 150, "price": 178.0, "fee": 5.0, "note": "美团追加"},
    ]

    for t in hk_trades:
        api_request(
            "POST",
            "/trades",
            {
                "account_id": account_id,
                "symbol": t["symbol"],
                "market": "hk",
                "currency": "HKD",
                "trade_date": t["date"],
                "side": t["side"],
                "quantity": t["qty"],
                "price": t["price"],
                "fee": t["fee"],
                "note": t["note"],
            },
        )
        logger.info("  交易: %s %s %s %s %s股 @ %.2f", t["date"], t["symbol"], t["side"], t["note"], t["qty"], t["price"])

    try:
        today = date.today().isoformat()
        snapshot = api_request("GET", f"/snapshot?account_id={account_id}&cost_method=fifo&as_of={today}")
        positions = snapshot.get("positions", [])
        logger.info("快照已生成: equity=%.2f, positions=%d", snapshot.get("totalEquity", 0), len(positions))
        for p in positions:
            logger.info("  持仓: %s %s 数量=%d 成本=%.2f 市值=%.2f 盈亏=%.2f (%.1f%%)",
                        p.get("accountName", ""), p["symbol"], p["quantity"],
                        p["avgCost"], p.get("marketValueBase", 0),
                        p.get("unrealizedPnlBase", 0), p.get("unrealizedPnlPct", 0))
    except Exception as exc:
        logger.warning("生成快照失败: %s", exc)

    logger.info("港股账户创建完毕: account_id=%d", account_id)
    return account_id


# ============================================================
# A 股成长型账户
# ============================================================


def seed_cn_growth_account():
    """创建 A 股成长型模拟账户（偏科技/新能源/医药）。"""
    logger.info("\n" + "=" * 50)
    logger.info("创建 A 股成长型账户")
    logger.info("=" * 50)

    acct = api_request(
        "POST",
        "/accounts",
        {
            "name": "A股成长精选",
            "broker": "华泰证券",
            "market": "cn",
            "base_currency": "CNY",
            "owner_id": "demo",
        },
    )
    account_id = acct["id"]
    logger.info("账户已创建: id=%d, name=%s", account_id, acct["name"])

    api_request(
        "POST",
        "/cash-ledger",
        {
            "account_id": account_id,
            "event_date": "2025-09-01",
            "direction": "in",
            "amount": 300000,
            "currency": "CNY",
            "note": "初始入金",
        },
    )
    logger.info("初始入金: 300,000 CNY")

    cn_growth_trades = [
        # 比亚迪 002594
        {"symbol": "002594", "date": "2025-09-08", "side": "buy", "qty": 200, "price": 280.0, "fee": 5.0, "note": "比亚迪建仓"},
        {"symbol": "002594", "date": "2025-12-20", "side": "buy", "qty": 100, "price": 310.0, "fee": 5.0, "note": "比亚迪加仓"},
        {"symbol": "002594", "date": "2026-06-05", "side": "sell", "qty": 50, "price": 355.0, "fee": 3.0, "note": "比亚迪止盈"},
        # 隆基绿能 601012
        {"symbol": "601012", "date": "2025-09-15", "side": "buy", "qty": 600, "price": 18.5, "fee": 3.0, "note": "隆基建仓"},
        {"symbol": "601012", "date": "2026-02-20", "side": "sell", "qty": 200, "price": 14.8, "fee": 3.0, "note": "隆基止损"},
        # 中芯国际 688981
        {"symbol": "688981", "date": "2025-10-10", "side": "buy", "qty": 300, "price": 55.0, "fee": 3.0, "note": "中芯国际建仓"},
        {"symbol": "688981", "date": "2026-01-20", "side": "buy", "qty": 200, "price": 70.0, "fee": 3.0, "note": "中芯国际加仓"},
        {"symbol": "688981", "date": "2026-05-15", "side": "sell", "qty": 100, "price": 95.0, "fee": 3.0, "note": "中芯国际减仓"},
        # 药明康德 603259
        {"symbol": "603259", "date": "2025-11-01", "side": "buy", "qty": 400, "price": 52.0, "fee": 3.0, "note": "药明康德建仓"},
        {"symbol": "603259", "date": "2026-03-15", "side": "buy", "qty": 200, "price": 48.0, "fee": 3.0, "note": "药明康德加仓"},
        # 立讯精密 002475
        {"symbol": "002475", "date": "2025-09-25", "side": "buy", "qty": 800, "price": 32.5, "fee": 3.0, "note": "立讯精密建仓"},
        {"symbol": "002475", "date": "2026-04-10", "side": "sell", "qty": 200, "price": 38.5, "fee": 3.0, "note": "立讯精密止盈"},
    ]

    for t in cn_growth_trades:
        api_request(
            "POST",
            "/trades",
            {
                "account_id": account_id,
                "symbol": t["symbol"],
                "market": "cn",
                "currency": "CNY",
                "trade_date": t["date"],
                "side": t["side"],
                "quantity": t["qty"],
                "price": t["price"],
                "fee": t["fee"],
                "note": t["note"],
            },
        )
        logger.info("  交易: %s %s %s %s %s股 @ %.2f", t["date"], t["symbol"], t["side"], t["note"], t["qty"], t["price"])

    try:
        today = date.today().isoformat()
        snapshot = api_request("GET", f"/snapshot?account_id={account_id}&cost_method=fifo&as_of={today}")
        positions = snapshot.get("positions", [])
        logger.info("快照已生成: equity=%.2f, positions=%d", snapshot.get("totalEquity", 0), len(positions))
        for p in positions:
            logger.info("  持仓: %s %s 数量=%d 成本=%.2f 市值=%.2f 盈亏=%.2f (%.1f%%)",
                        p.get("accountName", ""), p["symbol"], p["quantity"],
                        p["avgCost"], p.get("marketValueBase", 0),
                        p.get("unrealizedPnlBase", 0), p.get("unrealizedPnlPct", 0))
    except Exception as exc:
        logger.warning("生成快照失败: %s", exc)

    logger.info("A 股成长型账户创建完毕: account_id=%d", account_id)
    return account_id


# ============================================================
# A 股基金定投账户
# ============================================================


def seed_cn_fund_account():
    """创建 A 股 ETF/基金模拟账户。"""
    logger.info("\n" + "=" * 50)
    logger.info("创建 A 股 ETF 基金账户")
    logger.info("=" * 50)

    acct = api_request(
        "POST",
        "/accounts",
        {
            "name": "A股ETF定投",
            "broker": "东方财富",
            "market": "cn",
            "base_currency": "CNY",
            "owner_id": "demo",
        },
    )
    account_id = acct["id"]
    logger.info("账户已创建: id=%d, name=%s", account_id, acct["name"])

    api_request(
        "POST",
        "/cash-ledger",
        {
            "account_id": account_id,
            "event_date": "2025-09-01",
            "direction": "in",
            "amount": 200000,
            "currency": "CNY",
            "note": "初始入金",
        },
    )
    logger.info("初始入金: 200,000 CNY")

    fund_trades = [
        # 沪深300ETF 510300 — 每月定投
        {"symbol": "510300", "date": "2025-09-05", "side": "buy", "qty": 5000, "price": 3.85, "fee": 3.0, "note": "沪深300定投#1"},
        {"symbol": "510300", "date": "2025-10-08", "side": "buy", "qty": 5000, "price": 4.10, "fee": 3.0, "note": "沪深300定投#2"},
        {"symbol": "510300", "date": "2025-11-05", "side": "buy", "qty": 5000, "price": 3.95, "fee": 3.0, "note": "沪深300定投#3"},
        {"symbol": "510300", "date": "2025-12-05", "side": "buy", "qty": 5000, "price": 4.05, "fee": 3.0, "note": "沪深300定投#4"},
        {"symbol": "510300", "date": "2026-01-05", "side": "buy", "qty": 5000, "price": 3.80, "fee": 3.0, "note": "沪深300定投#5"},
        {"symbol": "510300", "date": "2026-02-05", "side": "buy", "qty": 5000, "price": 3.72, "fee": 3.0, "note": "沪深300定投#6"},
        {"symbol": "510300", "date": "2026-03-05", "side": "buy", "qty": 5000, "price": 3.88, "fee": 3.0, "note": "沪深300定投#7"},
        {"symbol": "510300", "date": "2026-04-07", "side": "buy", "qty": 5000, "price": 3.78, "fee": 3.0, "note": "沪深300定投#8"},
        # 科创50ETF 588000 — 每两月配置
        {"symbol": "588000", "date": "2025-09-10", "side": "buy", "qty": 3000, "price": 0.85, "fee": 2.0, "note": "科创50配置#1"},
        {"symbol": "588000", "date": "2025-11-10", "side": "buy", "qty": 3000, "price": 0.92, "fee": 2.0, "note": "科创50配置#2"},
        {"symbol": "588000", "date": "2026-01-10", "side": "buy", "qty": 3000, "price": 1.05, "fee": 2.0, "note": "科创50配置#3"},
        {"symbol": "588000", "date": "2026-03-10", "side": "buy", "qty": 3000, "price": 1.18, "fee": 2.0, "note": "科创50配置#4"},
        {"symbol": "588000", "date": "2026-05-10", "side": "buy", "qty": 3000, "price": 1.35, "fee": 2.0, "note": "科创50配置#5"},
        # 红利ETF 510880 — 高股息防御
        {"symbol": "510880", "date": "2025-10-20", "side": "buy", "qty": 3000, "price": 2.95, "fee": 2.0, "note": "红利ETF配置"},
        {"symbol": "510880", "date": "2026-01-20", "side": "buy", "qty": 3000, "price": 3.10, "fee": 2.0, "note": "红利ETF追加"},
    ]

    for t in fund_trades:
        api_request(
            "POST",
            "/trades",
            {
                "account_id": account_id,
                "symbol": t["symbol"],
                "market": "cn",
                "currency": "CNY",
                "trade_date": t["date"],
                "side": t["side"],
                "quantity": t["qty"],
                "price": t["price"],
                "fee": t["fee"],
                "note": t["note"],
            },
        )
        logger.info("  交易: %s %s %s %s %s股 @ %.2f", t["date"], t["symbol"], t["side"], t["note"], t["qty"], t["price"])

    try:
        today = date.today().isoformat()
        snapshot = api_request("GET", f"/snapshot?account_id={account_id}&cost_method=fifo&as_of={today}")
        positions = snapshot.get("positions", [])
        logger.info("快照已生成: equity=%.2f, positions=%d", snapshot.get("totalEquity", 0), len(positions))
        for p in positions:
            logger.info("  持仓: %s %s 数量=%d 成本=%.2f 市值=%.2f 盈亏=%.2f (%.1f%%)",
                        p.get("accountName", ""), p["symbol"], p["quantity"],
                        p["avgCost"], p.get("marketValueBase", 0),
                        p.get("unrealizedPnlBase", 0), p.get("unrealizedPnlPct", 0))
    except Exception as exc:
        logger.warning("生成快照失败: %s", exc)

    logger.info("ETF 基金账户创建完毕: account_id=%d", account_id)
    return account_id


# ============================================================
# 主入口
# ============================================================


def main():
    parser = argparse.ArgumentParser(description="创建模拟持仓账户数据")
    parser.add_argument("--account", choices=["cn", "us", "hk", "growth", "fund", "all"], default="all", help="创建哪个账户")
    parser.add_argument("--clean-only", action="store_true", help="仅清理已有数据")
    args = parser.parse_args()

    ACCOUNT_CLEAN_MARKET = {"cn": "cn", "us": "us", "hk": "hk"}  # growth/fund 不清除已有
    target_market = ACCOUNT_CLEAN_MARKET.get(args.account)

    # 先列出已有账户并清理（仅清理严格匹配市场的账户）
    try:
        existing = api_request("GET", "/accounts")
        for acct in existing.get("accounts", []):
            aid = acct["id"]
            should_clean = args.clean_only or (target_market and acct.get("market", "") == target_market)
            if args.clean_only or should_clean:
                logger.info("清理账户 %d (%s, %s)", aid, acct["name"], acct.get("market", ""))
                delete_all(aid)
                try:
                    api_request("DELETE", f"/accounts/{aid}")
                except Exception:
                    pass
    except Exception as exc:
        logger.warning("列出/清理已有账户失败: %s", exc)

    if args.clean_only:
        logger.info("清理完毕。")
        return

    if args.account in ("all", "cn"):
        seed_cn_account()

    if args.account in ("all", "us"):
        seed_us_account()

    if args.account in ("all", "hk"):
        seed_hk_account()

    if args.account in ("all", "growth"):
        seed_cn_growth_account()

    if args.account in ("all", "fund"):
        seed_cn_fund_account()

    logger.info("\n全部完成。访问 http://localhost:8000/portfolio 查看持仓管理页面。")


if __name__ == "__main__":
    main()
