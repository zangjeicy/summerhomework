from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DATA_FILE = Path(__file__).resolve().parent / "上市公司信息.csv"
REQUIRED_COLUMNS = {"股票代码", "股票简称"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="根据关键字筛选上市公司")
    parser.add_argument("keyword", help="公司简称关键字，例如 银行")
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
    keyword = args.keyword.strip()
    if not keyword:
        print("关键字不能为空")
        return 2

    try:
        companies = load_companies()
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"读取上市公司信息失败：{exc}")
        return 3

    names = companies["股票简称"].astype("string")
    matched = companies.loc[
        names.str.contains(keyword, case=False, na=False, regex=False),
        ["股票代码", "股票简称"],
    ]
    if matched.empty:
        print(f"未找到简称包含“{keyword}”的上市公司")
        return 1

    print(f"关键字“{keyword}”共匹配 {len(matched)} 家上市公司")
    print(matched.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
