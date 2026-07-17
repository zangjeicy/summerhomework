from __future__ import annotations

from pathlib import Path

import akshare as ak
import pandas as pd


OUTPUT_FILE = Path(__file__).resolve().parent / "上市公司信息.csv"
REQUIRED_COLUMNS = {"code", "name"}


def fetch_listed_companies() -> pd.DataFrame:
    """获取 A 股上市公司代码和简称，并转换为课程使用的中文字段。"""
    source = ak.stock_info_a_code_name()
    if source.empty:
        raise RuntimeError("AKShare 返回了空数据")
    missing = REQUIRED_COLUMNS.difference(source.columns)
    if missing:
        raise RuntimeError(f"AKShare 返回结果缺少字段：{', '.join(sorted(missing))}")

    result = source.loc[:, ["code", "name"]].rename(
        columns={"code": "股票代码", "name": "股票简称"}
    )
    result["股票代码"] = result["股票代码"].astype(str).str.zfill(6)
    result["股票简称"] = result["股票简称"].astype(str).str.strip()
    return result.drop_duplicates(subset=["股票代码"]).reset_index(drop=True)


def main() -> int:
    try:
        companies = fetch_listed_companies()
        companies.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    except Exception as exc:
        print(f"获取上市公司信息失败：{exc}")
        return 1

    print(f"已导出 {len(companies)} 家上市公司")
    print(f"CSV 文件：{OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
