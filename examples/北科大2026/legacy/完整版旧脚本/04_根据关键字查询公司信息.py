"""根据关键字查询上市公司，并导出匹配公司的全部详细信息。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "上市公司.csv"
SEARCH_COLUMNS = ["公司名称", "A股简称", "曾用简称", "英文名称"]
SUMMARY_COLUMNS = ["A股代码", "A股简称", "公司名称", "所属市场", "所属行业", "上市日期"]


def safe_filename(keyword: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", keyword).strip(" .")
    return name or "关键字"


def query_companies(keyword: str) -> pd.DataFrame:
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"未找到数据文件：{CSV_FILE}")

    data = pd.read_csv(CSV_FILE, encoding="utf-8-sig", dtype={"A股代码": str})
    data["A股代码"] = data["A股代码"].str.zfill(6)

    missing = [column for column in SEARCH_COLUMNS if column not in data.columns]
    if missing:
        raise RuntimeError(f"CSV 缺少查询字段：{', '.join(missing)}")

    # regex=False：将用户输入作为普通文本，而不是正则表达式。
    matched = data[SEARCH_COLUMNS].fillna("").astype(str).apply(
        lambda column: column.str.contains(keyword, case=False, regex=False)
    )
    return data.loc[matched.any(axis=1)].copy()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keyword", nargs="?", default="银行", help="查询关键字，默认：银行")
    args = parser.parse_args()
    keyword = args.keyword.strip()
    if not keyword:
        parser.error("关键字不能为空")

    result = query_companies(keyword)
    if result.empty:
        print(f"未找到名称中包含“{keyword}”的上市公司。")
        return

    output_file = BASE_DIR / f"{safe_filename(keyword)}_查询结果.csv"
    result.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"关键字：{keyword}")
    print(f"匹配数量：{len(result)} 家")
    print("匹配公司：")
    print(result[SUMMARY_COLUMNS].to_string(index=False))
    print(f"\n全部详细信息（{len(result.columns)} 列）已导出：{output_file}")


if __name__ == "__main__":
    main()
