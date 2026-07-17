"""读取项目根目录 key.txt，真实验证 Tushare Pro Token 是否可用。"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KEY_FILE = REPO_ROOT / "key.txt"
REQUIRED_COLUMNS = {"exchange", "cal_date", "is_open"}


def read_token(path: Path) -> str:
    """读取纯 Token、环境变量赋值或带 tushare 标签的分段格式。"""
    try:
        content = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ValueError(f"未找到 Token 文件：{path}") from exc
    except OSError as exc:
        raise ValueError(f"无法读取 Token 文件：{path}（{exc}）") from exc

    lines = [line.strip() for line in content.splitlines()]
    value = ""
    for line in lines:
        if line.upper().startswith("TUSHARE_TOKEN="):
            value = line.split("=", 1)[1].strip().strip("'\"")
            break

    if not value:
        for index, line in enumerate(lines):
            if line.lower() != "tushare":
                continue
            value = next((candidate for candidate in lines[index + 1 :] if candidate), "")
            break

    non_empty_lines = [line for line in lines if line]
    if not value and len(non_empty_lines) == 1:
        value = non_empty_lines[0]

    if not value:
        raise ValueError(
            "未找到 Tushare Token；请使用单行 Token、TUSHARE_TOKEN=xxx，"
            "或在 tushare 标签后的下一行保存 Token"
        )
    if any(char.isspace() for char in value):
        raise ValueError("Token 中包含空白字符，请确认 key.txt 只保存一个 Token")
    return value


def verify_token(token: str, lookback_days: int = 14) -> tuple[int, int, str, str]:
    """调用交易日历接口，返回总记录数、开市日数和日期范围。"""
    try:
        import tushare as ts
    except ImportError as exc:
        raise RuntimeError("未安装 tushare，请先安装项目依赖") from exc

    end = date.today()
    start = end - timedelta(days=lookback_days)
    api = ts.pro_api(token)
    calendar = api.trade_cal(
        exchange="SSE",
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
        fields="exchange,cal_date,is_open,pretrade_date",
    )
    if calendar is None or calendar.empty:
        raise RuntimeError("Tushare 鉴权成功但交易日历接口返回空数据")
    missing = REQUIRED_COLUMNS.difference(calendar.columns)
    if missing:
        raise RuntimeError(f"交易日历响应缺少字段：{', '.join(sorted(missing))}")

    open_days = int(calendar["is_open"].astype(int).sum())
    return len(calendar), open_days, str(calendar["cal_date"].min()), str(calendar["cal_date"].max())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--key-file",
        type=Path,
        default=DEFAULT_KEY_FILE,
        help=f"Token 文件，默认：{DEFAULT_KEY_FILE}",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=14,
        help="验证交易日历的回看天数，默认 14",
    )
    args = parser.parse_args()
    if args.lookback_days < 1:
        parser.error("--lookback-days 必须大于 0")

    try:
        token = read_token(args.key_file.resolve())
        rows, open_days, start_date, end_date = verify_token(token, args.lookback_days)
    except Exception as exc:
        print(f"Tushare Token 验证失败：{exc}", file=sys.stderr)
        return 1

    print("Tushare Token 可用")
    print("接口：trade_cal（上交所交易日历）")
    print(f"返回记录：{rows} 条，其中开市日 {open_days} 天")
    print(f"日期范围：{start_date} 至 {end_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
