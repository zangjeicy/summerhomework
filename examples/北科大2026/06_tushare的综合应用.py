"""综合使用 Tushare 基础信息、日线、复权、每日指标和资金流向接口。"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KEY_FILE = REPO_ROOT / "key.txt"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def read_tushare_token(path: Path) -> str:
    """兼容单行、TUSHARE_TOKEN=xxx 和 tushare 标签分段格式。"""
    lines = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()]
    for line in lines:
        if line.upper().startswith("TUSHARE_TOKEN="):
            return line.split("=", 1)[1].strip().strip("'\"")
    for index, line in enumerate(lines):
        if line.lower() == "tushare":
            return next((candidate for candidate in lines[index + 1 :] if candidate), "")
    values = [line for line in lines if line]
    return values[0] if len(values) == 1 else ""


def ensure_data(frame: pd.DataFrame, interface: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        raise RuntimeError(f"{interface} 未返回数据")
    return frame.copy()


def fetch_comprehensive_data(
    token: str, ts_code: str, days: int
) -> tuple[pd.Series, pd.DataFrame, list[str]]:
    import tushare as ts

    pro = ts.pro_api(token)
    end = date.today()
    start = end - timedelta(days=max(days * 2, 60))
    start_date = start.strftime("%Y%m%d")
    end_date = end.strftime("%Y%m%d")

    calendar = None
    try:
        calendar = ensure_data(
            pro.trade_cal(
                exchange="SSE",
                start_date=start_date,
                end_date=end_date,
                is_open="1",
                fields="exchange,cal_date,is_open,pretrade_date",
            ),
            "trade_cal",
        )
    except Exception as exc:
        if "频率超限" not in str(exc) and "rate" not in str(exc).lower():
            raise
        print("提示：trade_cal 触发账号频控，本次改用 daily 的交易日期继续。")
    company = ensure_data(
        pro.stock_basic(
            ts_code=ts_code,
            fields="ts_code,symbol,name,area,industry,market,exchange,list_date",
        ),
        "stock_basic",
    ).iloc[0]
    daily = ensure_data(
        pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date), "daily"
    )
    adj = ensure_data(
        pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date),
        "adj_factor",
    )
    basic = ensure_data(
        pro.daily_basic(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            fields=(
                "ts_code,trade_date,turnover_rate,volume_ratio,pe_ttm,pb,dv_ttm,"
                "total_mv,circ_mv"
            ),
        ),
        "daily_basic",
    )
    optional_issues: list[str] = []
    flow = None
    try:
        flow = ensure_data(
            pro.moneyflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields=(
                    "ts_code,trade_date,buy_lg_amount,sell_lg_amount,"
                    "buy_elg_amount,sell_elg_amount,net_mf_amount"
                ),
            ),
            "moneyflow",
        )
    except Exception as exc:
        optional_issues.append(f"moneyflow 不可用：{exc}")

    data = daily.merge(adj, on=["ts_code", "trade_date"], how="left")
    data = data.merge(basic, on=["ts_code", "trade_date"], how="left")
    if flow is None:
        for column in (
            "buy_lg_amount",
            "sell_lg_amount",
            "buy_elg_amount",
            "sell_elg_amount",
            "net_mf_amount",
        ):
            data[column] = pd.NA
    else:
        data = data.merge(flow, on=["ts_code", "trade_date"], how="left")
    data = data.sort_values("trade_date").tail(days).reset_index(drop=True)
    latest_factor = data["adj_factor"].dropna().iloc[-1]
    data["qfq_close"] = data["close"] * data["adj_factor"] / latest_factor
    data["ma5"] = data["qfq_close"].rolling(5).mean()
    data["ma10"] = data["qfq_close"].rolling(10).mean()
    data["large_order_net"] = data["buy_lg_amount"] - data["sell_lg_amount"]
    data["extra_large_order_net"] = data["buy_elg_amount"] - data["sell_elg_amount"]
    if calendar is None:
        data["is_trade_date"] = True
    else:
        data["is_trade_date"] = data["trade_date"].isin(calendar["cal_date"].astype(str))
    return (
        company,
        data.sort_values("trade_date", ascending=False).reset_index(drop=True),
        optional_issues,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ts-code", default="600519.SH", help="Tushare 股票代码")
    parser.add_argument("--days", type=int, default=20, help="输出最近 N 个交易日")
    parser.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    args = parser.parse_args()
    if args.days < 10:
        parser.error("--days 至少为 10，才能计算 MA10")

    try:
        token = read_tushare_token(args.key_file.resolve())
        if not token:
            raise ValueError("未在 key.txt 中找到 Tushare Token")
        company, data, optional_issues = fetch_comprehensive_data(
            token, args.ts_code, args.days
        )
    except Exception as exc:
        print(f"Tushare 综合应用执行失败：{exc}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / f"tushare_{args.ts_code.replace('.', '_')}_综合数据.csv"
    data.to_csv(output, index=False, encoding="utf-8-sig")
    latest = data.iloc[0]
    print(f"公司：{company['name']}（{company['ts_code']}）")
    print(f"行业：{company['industry']}；市场：{company['market']}；上市日期：{company['list_date']}")
    print(f"最新交易日：{latest['trade_date']}；收盘价：{latest['close']:.2f}")
    print(f"前复权 MA5：{latest['ma5']:.2f}；MA10：{latest['ma10']:.2f}")
    print(f"换手率：{latest['turnover_rate']:.4f}%；量比：{latest['volume_ratio']:.2f}")
    print(f"PE(TTM)：{latest['pe_ttm']:.2f}；PB：{latest['pb']:.2f}")
    if pd.notna(latest["net_mf_amount"]):
        print(f"主力净流入：{latest['net_mf_amount']:.2f} 万元")
    else:
        print("主力净流入：当前 Token 无 moneyflow 权限")
    for issue in optional_issues:
        print(f"可选接口提示：{issue}")
    print(f"已合并 {len(data)} 个交易日，输出：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
