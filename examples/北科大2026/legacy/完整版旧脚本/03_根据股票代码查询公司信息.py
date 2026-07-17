"""根据 A 股股票代码查询“上市公司.csv”中的公司详细信息。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


CSV_FILE = Path(__file__).with_name("上市公司.csv")


def normalize_code(value: str) -> str:
    code = value.strip()
    if not code.isdigit() or len(code) > 6:
        raise ValueError("股票代码必须是最多 6 位数字，例如：000001")
    return code.zfill(6)


def query_company(code: str) -> pd.Series:
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"未找到数据文件：{CSV_FILE}")

    data = pd.read_csv(
        CSV_FILE,
        encoding="utf-8-sig",
        dtype={"A股代码": str},
    )
    data["A股代码"] = data["A股代码"].str.zfill(6)
    result = data.loc[data["A股代码"].eq(code)]

    if result.empty:
        raise LookupError(f"未找到股票代码 {code} 对应的上市公司")
    if len(result) > 1:
        raise RuntimeError(f"股票代码 {code} 存在 {len(result)} 条重复记录")
    return result.iloc[0]


def print_company(company: pd.Series) -> None:
    print(f"股票代码 {company['A股代码']} 对应的公司详细信息：")
    print("-" * 80)
    for field, value in company.items():
        if pd.notna(value) and str(value).strip():
            print(f"{field}：{value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "code",
        nargs="?",
        default="000001",
        help="A 股股票代码，默认 000001",
    )
    args = parser.parse_args()

    code = normalize_code(args.code)
    company = query_company(code)
    print_company(company)


if __name__ == "__main__":
    main()
