"""使用 AKShare 获取全部 A 股上市公司概况并导出 CSV。"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import akshare as ak
import pandas as pd
import requests
from tqdm import tqdm


OUTPUT_FILE = Path(__file__).with_name("上市公司.csv")
CHECKPOINT_FILE = Path(__file__).with_name("上市公司.csv.part")

# AKShare 的公司概况接口未设置 timeout；统一补上超时，避免网络请求永久卡住。
_original_request = requests.sessions.Session.request


def _request_with_timeout(self, method, url, **kwargs):
    kwargs.setdefault("timeout", 20)
    return _original_request(self, method, url, **kwargs)


requests.sessions.Session.request = _request_with_timeout


def fetch_profile(code: str, retries: int = 3) -> dict[str, object]:
    """获取单家公司的详细资料，遇到临时网络错误时自动重试。"""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            profile = ak.stock_profile_cninfo(symbol=code)
            if profile.empty:
                return {"A股代码": code, "获取状态": "无公司概况"}
            row = profile.iloc[0].to_dict()
            row["A股代码"] = str(row.get("A股代码") or code).zfill(6)
            row["获取状态"] = "成功"
            return row
        except Exception as exc:  # 网络接口的异常类型不固定
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)

    return {
        "A股代码": code,
        "获取状态": "失败",
        "错误信息": str(last_error),
    }


def save(rows: list[dict[str, object]], path: Path) -> None:
    """使用 UTF-8 BOM 写入，使中文 CSV 可直接由 Excel 打开。"""
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def main(limit: int | None = None, workers: int = 6) -> None:
    print("正在获取沪深京 A 股上市公司清单……")
    companies = ak.stock_info_a_code_name().copy()
    companies["code"] = companies["code"].astype(str).str.zfill(6)
    companies = companies.drop_duplicates(subset="code").reset_index(drop=True)
    if limit is not None:
        companies = companies.head(limit)

    items = list(companies.itertuples(index=False))
    rows: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_profile, item.code): item for item in items}
        iterator = tqdm(as_completed(futures), total=len(items), desc="获取公司资料", unit="家")
        for future in iterator:
            item = futures[future]
            row = future.result()
        # 即使资料接口没有返回内容，也保留清单中的代码和简称。
            row["A股代码"] = item.code
            row.setdefault("A股简称", item.name)
            rows.append(row)

        # 定期保存，运行意外中断时仍可保留已获取的数据。
            if len(rows) % 50 == 0:
                save(rows, CHECKPOINT_FILE)

    save(rows, OUTPUT_FILE)
    CHECKPOINT_FILE.unlink(missing_ok=True)

    success_count = sum(row.get("获取状态") == "成功" for row in rows)
    print(f"完成：共导出 {len(rows)} 家，其中成功获取详细资料 {success_count} 家。")
    print(f"文件位置：{OUTPUT_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="仅处理前 N 家公司，便于测试；不指定则处理全部公司",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="并发请求数（默认 6）",
    )
    args = parser.parse_args()
    main(limit=args.limit, workers=args.workers)
