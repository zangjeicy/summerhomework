from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


DATA_FILE = Path(__file__).resolve().parent / "上市公司信息.csv"
REQUIRED_COLUMNS = {"股票代码", "股票简称"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="根据股票代码查询上市公司信息")
    parser.add_argument("stock_code", help="6 位股票代码，例如 000001")
    return parser


def load_companies() -> pd.DataFrame:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"未找到 {DATA_FILE.name}，请先运行 01_获取上市公司信息.py")

    companies = pd.read_csv(DATA_FILE, dtype={"股票代码": "string"})
    if companies.empty:
        raise ValueError("上市公司信息.csv 为空")
    missing = REQUIRED_COLUMNS.difference(companies.columns)
    if missing:
        raise ValueError(f"CSV 缺少字段：{', '.join(sorted(missing))}")
    companies["股票代码"] = companies["股票代码"].str.zfill(6)
    return companies


def main() -> int:
    args = build_parser().parse_args()
    stock_code = args.stock_code.strip()
    if re.fullmatch(r"\d{6}", stock_code) is None:
        print("股票代码必须是 6 位数字，例如 000001")
        return 2

    try:
        companies = load_companies()
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"读取上市公司信息失败：{exc}")
        return 3

    matched = companies.loc[companies["股票代码"] == stock_code]
    if matched.empty:
        print(f"未找到股票代码 {stock_code} 对应的上市公司")
        return 1

    company = matched.iloc[0]
    print(f"股票代码：{company['股票代码']}")
    print(f"股票简称：{company['股票简称']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
