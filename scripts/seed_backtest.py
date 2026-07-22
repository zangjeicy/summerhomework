# -*- coding: utf-8 -*-
"""填充模拟分析历史 records 和日线数据，然后触发回测，让回测页面有数据可看。

用法：
    python scripts/seed_backtest.py           # 插入模拟数据 + 触发回测
    python scripts/seed_backtest.py --clean   # 清除回测数据
"""

import argparse
import json
import logging
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("seed_backtest")

DB_PATH = "data/stock_analysis.db"
BASE_URL = "http://localhost:8000/api/v1/backtest"


# ============================================================
# 模拟分析记录 — 模拟系统对各股票在不同日期的 AI 分析结果
# ============================================================

STOCKS = [
    {
        "code": "600519", "name": "贵州茅台",
        "analysis_date": "2026-05-15",
        "operation": "建议买入",
        "trend": "短线看涨，白酒板块季节性反弹，估值处于历史中低位",
        "stop_loss": 1280.0,
        "take_profit": 1480.0,
        "start_price": 1320.0,
    },
    {
        "code": "600519", "name": "贵州茅台",
        "analysis_date": "2026-06-01",
        "operation": "建议持有",
        "trend": "横盘整理，短期方向不明，等待突破信号",
        "stop_loss": 1250.0,
        "take_profit": 1400.0,
        "start_price": 1295.0,
    },
    {
        "code": "600519", "name": "贵州茅台",
        "analysis_date": "2026-06-15",
        "operation": "建议卖出",
        "trend": "放量下跌，MACD 顶背离，建议减仓止盈",
        "stop_loss": 1220.0,
        "take_profit": 1380.0,
        "start_price": 1305.0,
    },
    {
        "code": "000858", "name": "五粮液",
        "analysis_date": "2026-05-10",
        "operation": "观望",
        "trend": "消费板块整体偏弱，等待板块轮动信号",
        "stop_loss": 72.0,
        "take_profit": 85.0,
        "start_price": 78.5,
    },
    {
        "code": "000858", "name": "五粮液",
        "analysis_date": "2026-06-10",
        "operation": "建议买入",
        "trend": "底部放量反弹，北上资金连续净流入",
        "stop_loss": 68.0,
        "take_profit": 82.0,
        "start_price": 74.0,
    },
    {
        "code": "300750", "name": "宁德时代",
        "analysis_date": "2026-05-20",
        "operation": "建议买入",
        "trend": "新能源汽车政策利好，电池技术突破预期",
        "stop_loss": 350.0,
        "take_profit": 420.0,
        "start_price": 375.0,
    },
    {
        "code": "300750", "name": "宁德时代",
        "analysis_date": "2026-06-20",
        "operation": "建议卖出",
        "trend": "短期涨幅过大，获利盘抛压明显",
        "stop_loss": 380.0,
        "take_profit": 430.0,
        "start_price": 410.0,
    },
    {
        "code": "601318", "name": "中国平安",
        "analysis_date": "2026-05-25",
        "operation": "建议买入",
        "trend": "保险板块估值修复，A/H 溢价收窄",
        "stop_loss": 48.0,
        "take_profit": 58.0,
        "start_price": 52.0,
    },
    {
        "code": "601318", "name": "中国平安",
        "analysis_date": "2026-07-01",
        "operation": "建议持有",
        "trend": "慢牛走势，均线多头排列，继续持有",
        "stop_loss": 50.0,
        "take_profit": 60.0,
        "start_price": 54.0,
    },
    {
        "code": "002594", "name": "比亚迪",
        "analysis_date": "2026-06-05",
        "operation": "建议买入",
        "trend": "比亚迪高端车型发布在即，海外市场拓展加速",
        "stop_loss": 290.0,
        "take_profit": 370.0,
        "start_price": 320.0,
    },
    {
        "code": "002594", "name": "比亚迪",
        "analysis_date": "2026-07-05",
        "operation": "建议持有",
        "trend": "高位震荡，等待催化剂突破前高",
        "stop_loss": 330.0,
        "take_profit": 390.0,
        "start_price": 355.0,
    },
    {
        "code": "601012", "name": "隆基绿能",
        "analysis_date": "2026-05-30",
        "operation": "建议卖出",
        "trend": "光伏产能过剩，价格战持续，短期回避",
        "stop_loss": 16.0,
        "take_profit": 22.0,
        "start_price": 19.0,
    },
    {
        "code": "688981", "name": "中芯国际",
        "analysis_date": "2026-06-12",
        "operation": "建议买入",
        "trend": "AI 芯片需求爆发，先进制程突破预期",
        "stop_loss": 62.0,
        "take_profit": 100.0,
        "start_price": 78.0,
    },
    {
        "code": "603259", "name": "药明康德",
        "analysis_date": "2026-06-25",
        "operation": "观望",
        "trend": "CXO 行业去库存尚未结束，等待 Q3 拐点",
        "stop_loss": 45.0,
        "take_profit": 58.0,
        "start_price": 51.0,
    },
    {
        "code": "002475", "name": "立讯精密",
        "analysis_date": "2026-07-10",
        "operation": "建议买入",
        "trend": "苹果 MR 发布在即，消费电子景气回升",
        "stop_loss": 33.0,
        "take_profit": 45.0,
        "start_price": 38.5,
    },
]

# 每股日线 forward 数据: {date_str: (open, high, low, close)}
FORWARD_BARS = {
    "600519": {
        "2026-05-16": (1325, 1335, 1318, 1328),
        "2026-05-19": (1328, 1340, 1325, 1335),
        "2026-05-20": (1335, 1345, 1330, 1340),
        "2026-05-21": (1340, 1348, 1335, 1342),
        "2026-05-22": (1342, 1350, 1338, 1345),
        "2026-05-23": (1345, 1355, 1340, 1350),
        "2026-05-26": (1350, 1352, 1340, 1345),
        "2026-05-27": (1345, 1350, 1335, 1340),
        "2026-05-28": (1340, 1345, 1330, 1335),
        "2026-05-29": (1335, 1340, 1328, 1330),
        # 6月1日 analysis
        "2026-06-02": (1295, 1305, 1290, 1300),
        "2026-06-03": (1300, 1308, 1295, 1305),
        "2026-06-04": (1305, 1310, 1298, 1302),
        "2026-06-05": (1302, 1305, 1290, 1295),
        "2026-06-06": (1295, 1300, 1285, 1290),
        "2026-06-09": (1290, 1295, 1280, 1285),
        "2026-06-10": (1285, 1290, 1275, 1280),
        "2026-06-11": (1280, 1285, 1270, 1275),
        "2026-06-12": (1275, 1280, 1265, 1270),
        "2026-06-13": (1270, 1275, 1260, 1265),
        # 6月15日 analysis
        "2026-06-16": (1305, 1315, 1300, 1310),
        "2026-06-17": (1310, 1315, 1305, 1308),
        "2026-06-18": (1308, 1310, 1300, 1305),
        "2026-06-19": (1305, 1310, 1295, 1300),
        "2026-06-20": (1300, 1305, 1290, 1295),
        "2026-06-23": (1295, 1300, 1285, 1290),
        "2026-06-24": (1290, 1295, 1280, 1285),
        "2026-06-25": (1285, 1290, 1275, 1280),
        "2026-06-26": (1280, 1280, 1270, 1275),
        "2026-06-27": (1275, 1280, 1265, 1270),
    },
    "000858": {
        "2026-05-12": (78.5, 79.5, 78.0, 79.0),
        "2026-05-13": (79.0, 80.0, 78.5, 79.5),
        "2026-05-14": (79.5, 80.5, 79.0, 80.0),
        "2026-05-15": (80.0, 80.5, 79.5, 79.8),
        "2026-05-16": (79.8, 80.0, 79.0, 79.5),
        "2026-05-19": (79.5, 80.0, 78.5, 79.0),
        "2026-05-20": (79.0, 79.5, 78.0, 78.5),
        "2026-05-21": (78.5, 79.0, 77.5, 78.0),
        "2026-05-22": (78.0, 78.5, 77.0, 77.5),
        "2026-05-23": (77.5, 78.0, 76.5, 77.0),
        # 6月10日
        "2026-06-11": (74.0, 75.5, 73.5, 75.0),
        "2026-06-12": (75.0, 76.0, 74.5, 75.5),
        "2026-06-13": (75.5, 76.5, 75.0, 76.0),
        "2026-06-14": (76.0, 76.5, 75.5, 76.2),
        "2026-06-17": (76.2, 77.0, 76.0, 76.8),
        "2026-06-18": (76.8, 77.5, 76.5, 77.0),
        "2026-06-19": (77.0, 77.5, 76.8, 77.2),
        "2026-06-20": (77.2, 77.8, 76.5, 76.8),
        "2026-06-23": (76.8, 77.0, 76.0, 76.5),
        "2026-06-24": (76.5, 76.5, 75.5, 75.8),
    },
    "300750": {
        "2026-05-21": (375, 385, 374, 382),
        "2026-05-22": (382, 390, 380, 388),
        "2026-05-23": (388, 395, 385, 392),
        "2026-05-26": (392, 398, 390, 395),
        "2026-05-27": (395, 400, 392, 398),
        "2026-05-28": (398, 405, 395, 402),
        "2026-05-29": (402, 408, 400, 405),
        "2026-05-30": (405, 410, 402, 408),
        "2026-06-02": (408, 415, 405, 412),
        "2026-06-03": (412, 418, 410, 415),
        # 6月20日
        "2026-06-23": (410, 415, 405, 412),
        "2026-06-24": (412, 418, 410, 415),
        "2026-06-25": (415, 418, 410, 415),
        "2026-06-26": (415, 420, 412, 418),
        "2026-06-27": (418, 422, 415, 420),
        "2026-06-30": (420, 425, 418, 422),
        "2026-07-01": (422, 425, 418, 420),
        "2026-07-02": (420, 425, 418, 422),
        "2026-07-03": (422, 428, 420, 425),
        "2026-07-04": (425, 430, 422, 428),
    },
    "601318": {
        "2026-05-26": (52.0, 52.8, 51.8, 52.5),
        "2026-05-27": (52.5, 53.0, 52.2, 52.8),
        "2026-05-28": (52.8, 53.5, 52.5, 53.2),
        "2026-05-29": (53.2, 53.8, 53.0, 53.5),
        "2026-05-30": (53.5, 54.0, 53.2, 53.8),
        "2026-06-02": (53.8, 54.5, 53.5, 54.2),
        "2026-06-03": (54.2, 54.8, 54.0, 54.5),
        "2026-06-04": (54.5, 55.0, 54.2, 54.8),
        "2026-06-05": (54.8, 55.5, 54.5, 55.2),
        "2026-06-06": (55.2, 55.8, 55.0, 55.5),
        # 7月1日
        "2026-07-02": (54.0, 54.5, 53.5, 54.2),
        "2026-07-03": (54.2, 54.8, 54.0, 54.5),
        "2026-07-04": (54.5, 55.0, 54.2, 54.8),
        "2026-07-07": (54.8, 55.5, 54.5, 55.2),
        "2026-07-08": (55.2, 55.8, 55.0, 55.5),
        "2026-07-09": (55.5, 56.0, 55.2, 55.8),
        "2026-07-10": (55.8, 56.5, 55.5, 56.2),
        "2026-07-11": (56.2, 56.8, 56.0, 56.5),
        "2026-07-14": (56.5, 57.0, 56.2, 56.8),
        "2026-07-15": (56.8, 57.5, 56.5, 57.2),
    },
    "002594": {
        "2026-06-06": (320, 330, 318, 328),
        "2026-06-09": (328, 335, 325, 332),
        "2026-06-10": (332, 340, 330, 338),
        "2026-06-11": (338, 345, 335, 342),
        "2026-06-12": (342, 350, 340, 348),
        "2026-06-13": (348, 355, 345, 352),
        "2026-06-16": (352, 358, 350, 355),
        "2026-06-17": (355, 360, 352, 358),
        "2026-06-18": (358, 362, 355, 360),
        "2026-06-19": (360, 365, 358, 362),
        # 7月5日
        "2026-07-07": (355, 362, 352, 360),
        "2026-07-08": (360, 365, 358, 362),
        "2026-07-09": (362, 368, 360, 365),
        "2026-07-10": (365, 370, 362, 368),
        "2026-07-11": (368, 375, 365, 372),
        "2026-07-14": (372, 378, 370, 375),
        "2026-07-15": (375, 380, 372, 378),
        "2026-07-16": (378, 382, 375, 380),
        "2026-07-17": (380, 385, 378, 382),
        "2026-07-18": (382, 385, 378, 380),
    },
    "601012": {
        "2026-06-02": (19.0, 19.5, 18.8, 19.2),
        "2026-06-03": (19.2, 19.5, 18.8, 19.0),
        "2026-06-04": (19.0, 19.2, 18.5, 18.8),
        "2026-06-05": (18.8, 19.0, 18.2, 18.5),
        "2026-06-06": (18.5, 18.8, 18.0, 18.2),
        "2026-06-09": (18.2, 18.5, 17.8, 18.0),
        "2026-06-10": (18.0, 18.2, 17.5, 17.8),
        "2026-06-11": (17.8, 18.0, 17.2, 17.5),
        "2026-06-12": (17.5, 17.8, 17.0, 17.2),
        "2026-06-13": (17.2, 17.5, 16.8, 17.0),
    },
    "688981": {
        "2026-06-13": (78.0, 82.0, 77.5, 81.0),
        "2026-06-16": (81.0, 84.0, 80.5, 83.5),
        "2026-06-17": (83.5, 86.0, 83.0, 85.5),
        "2026-06-18": (85.5, 88.0, 85.0, 87.0),
        "2026-06-19": (87.0, 90.0, 86.5, 89.5),
        "2026-06-20": (89.5, 92.0, 89.0, 91.0),
        "2026-06-23": (91.0, 94.0, 90.5, 93.5),
        "2026-06-24": (93.5, 95.0, 92.0, 94.0),
        "2026-06-25": (94.0, 96.0, 93.5, 95.5),
        "2026-06-26": (95.5, 98.0, 95.0, 97.0),
    },
    "603259": {
        "2026-06-26": (51.0, 52.0, 50.5, 51.5),
        "2026-06-27": (51.5, 52.5, 51.0, 52.0),
        "2026-06-30": (52.0, 53.0, 51.5, 52.5),
        "2026-07-01": (52.5, 53.0, 51.8, 52.2),
        "2026-07-02": (52.2, 52.5, 51.5, 52.0),
        "2026-07-03": (52.0, 52.5, 51.0, 51.5),
        "2026-07-04": (51.5, 52.0, 50.5, 51.0),
        "2026-07-07": (51.0, 51.5, 50.0, 50.5),
        "2026-07-08": (50.5, 51.0, 49.8, 50.0),
        "2026-07-09": (50.0, 50.5, 49.0, 49.5),
    },
    "002475": {
        "2026-07-11": (38.5, 39.5, 38.2, 39.2),
        "2026-07-14": (39.2, 40.0, 39.0, 39.8),
        "2026-07-15": (39.8, 40.5, 39.5, 40.2),
        "2026-07-16": (40.2, 41.0, 40.0, 40.8),
        "2026-07-17": (40.8, 41.5, 40.5, 41.2),
        "2026-07-18": (41.2, 41.8, 41.0, 41.5),
        "2026-07-21": (41.5, 42.0, 41.2, 41.8),
        "2026-07-22": (41.8, 42.5, 41.5, 42.2),
        "2026-07-23": (42.2, 42.8, 42.0, 42.5),
        "2026-07-24": (42.5, 43.0, 42.2, 42.8),
    },
}


def _daily_date(dt: date) -> str:
    """将日期转为 stock_daily 表需要的文本格式（YYYY-MM-DD）."""
    return dt.strftime("%Y-%m-%d")


def _analysis_date(dt_str: str) -> str:
    """将 YYYY-MM-DD 转为回测需要的格式."""
    return dt_str


def seed_analysis_history_and_daily():
    """向 SQLite 插入分析记录与日线数据."""
    logger.info("正在连接数据库 %s", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # 清理旧数据
    cur.execute("DELETE FROM analysis_history WHERE report_type = 'stock_analysis'")
    cur.execute("DELETE FROM backtest_results")
    cur.execute("DELETE FROM backtest_summaries")
    cur.execute("DELETE FROM stock_daily WHERE code IN ('600519','000858','300750','601318','002594','601012','688981','603259','002475')")
    logger.info("已清理旧数据: analysis_history, backtest_results, backtest_summaries, stock_daily (test stocks)")

    # 插入 stock_daily — 覆盖分析日 + forward bars
    daily_count = 0
    for code, bars in FORWARD_BARS.items():
        # 也插入分析日当天的 bar
        for s in STOCKS:
            if s["code"] == code:
                d = _daily_date(datetime.strptime(s["analysis_date"], "%Y-%m-%d").date())
                cur.execute(
                    "INSERT OR IGNORE INTO stock_daily (code, date, open, high, low, close) VALUES (?,?,?,?,?,?)",
                    (code, d, s["start_price"], s["start_price"] * 1.02, s["start_price"] * 0.98, s["start_price"]),
                )
                daily_count += 1
        for date_str, (o, h, l, c) in bars.items():
            d = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
            cur.execute(
                "INSERT OR IGNORE INTO stock_daily (code, date, open, high, low, close) VALUES (?,?,?,?,?,?)",
                (code, d, o, h, l, c),
            )
            daily_count += 1
    logger.info("已写入 %d 条日线数据", daily_count)

    # 插入 analysis_history
    analysis_count = 0
    analysis_ids = []
    for s in STOCKS:
        created_at = datetime.strptime(s["analysis_date"], "%Y-%m-%d").replace(hour=9, minute=0, second=0)
        context_snapshot = json.dumps({"enhanced_context": {"date": s["analysis_date"]}}, ensure_ascii=False)
        cur.execute(
            """INSERT INTO analysis_history
               (code, name, operation_advice, trend_prediction, sentiment_score,
                stop_loss, take_profit, context_snapshot, report_type, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                s["code"], s["name"], s["operation"], s["trend"], 0.5,
                s["stop_loss"], s["take_profit"], context_snapshot,
                "stock_analysis", created_at.isoformat(),
            ),
        )
        analysis_ids.append(cur.lastrowid)
        analysis_count += 1
    conn.commit()
    logger.info("已写入 %d 条分析历史记录", analysis_count)
    conn.close()
    logger.info("数据库写入完成")
    return analysis_count


def trigger_backtest():
    """通过 API 触发回测."""
    url = f"{BASE_URL}/run"
    body = json.dumps({"min_age_days": 0, "limit": 200}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            logger.info("回测完成: processed=%d saved=%d completed=%d insufficient=%d errors=%d",
                        result.get("processed", 0), result.get("saved", 0),
                        result.get("completed", 0), result.get("insufficient", 0),
                        result.get("errors", 0))
            if result.get("message"):
                logger.info("诊断: %s", result["message"])
            return result
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        logger.error("回测 API 调用失败: HTTP %d %s", e.code, body_text)
        raise


def verify():
    """验证回测结果数量."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM backtest_results")
    total = cur.fetchone()[0]
    cur.execute("SELECT eval_status, COUNT(*) FROM backtest_results GROUP BY eval_status")
    statuses = cur.fetchall()
    logger.info("backtest_results: %d 条", total)
    for status, count in statuses:
        logger.info("  %s: %d", status, count)
    cur.execute("SELECT COUNT(*) FROM backtest_summaries")
    summary = cur.fetchone()[0]
    logger.info("backtest_summaries: %d 条", summary)
    conn.close()
    return total


def main():
    parser = argparse.ArgumentParser(description="回测种子数据脚本")
    parser.add_argument("--clean", action="store_true", help="仅清除回测数据")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    if args.clean:
        cur = conn.cursor()
        cur.execute("DELETE FROM backtest_results")
        cur.execute("DELETE FROM backtest_summaries")
        cur.execute("DELETE FROM analysis_history WHERE report_type = 'stock_analysis'")
        cur.execute("DELETE FROM stock_daily WHERE code IN ('600519','000858','300750','601318','002594','601012','688981','603259','002475')")
        conn.commit()
        conn.close()
        logger.info("已清除全部回测相关数据")
        return

    # 检查服务器是否运行
    try:
        urllib.request.urlopen("http://localhost:8000/api/v1/backtest/results?page=1&limit=1", timeout=5)
    except Exception:
        logger.error("后端服务未运行，请先启动 python main.py --serve-only --port 8000")
        sys.exit(1)

    # 1. 写入种子数据
    n = seed_analysis_history_and_daily()

    # 2. 触发回测
    logger.info("正在触发回测...")
    trigger_backtest()

    # 3. 验证
    total = verify()
    if total > 0:
        logger.info("成功！回测页面现在有 %d 条记录可查看", total)
        logger.info("访问 http://localhost:8000/backtest")
    else:
        # 重试一次
        logger.warning("未生成回测结果，等待 2 秒后重试...")
        import time
        time.sleep(2)
        trigger_backtest()
        verify()


if __name__ == "__main__":
    main()
