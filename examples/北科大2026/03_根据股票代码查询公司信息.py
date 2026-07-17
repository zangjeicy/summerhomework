"""根据 A 股代码查询完整上市公司资料。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DATA_FILE = Path(__file__).resolve().parent / "data" / "上市公司.csv"


def normalize_code(value: str) -> str:
    code = value.strip()
    if not code.isdigit() or len(code) > 6:
        raise ValueError("股票代码必须是最多 6 位数字，例如：000001")
    return code.zfill(6)


def query_company(code: str) -> pd.Series:
    data = pd.read_csv(DATA_FILE, encoding="utf-8-sig", dtype={"A股代码": str})
    data["A股代码"] = data["A股代码"].str.zfill(6)
    result = data.loc[data["A股代码"].eq(code)]
    if result.empty:
        raise LookupError(f"未找到股票代码 {code} 对应的上市公司")
    if len(result) > 1:
        raise RuntimeError(f"股票代码 {code} 存在 {len(result)} 条重复记录")
    return result.iloc[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", nargs="?", default="000001", help="A 股股票代码")
    args = parser.parse_args()
    try:
        company = query_company(normalize_code(args.code))
    except (ValueError, FileNotFoundError, LookupError, RuntimeError) as exc:
        print(f"查询失败：{exc}")
        return 1
    for field, value in company.items():
        if pd.notna(value) and str(value).strip():
            print(f"{field}：{value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
