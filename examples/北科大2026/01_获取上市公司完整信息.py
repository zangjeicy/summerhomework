"""获取全部 A 股上市公司详细资料并写入 data/上市公司.csv。"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import akshare as ak
import pandas as pd
import requests
from tqdm import tqdm


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "上市公司.csv"
CHECKPOINT_FILE = BASE_DIR / "data" / "上市公司.csv.part"
_original_request = requests.sessions.Session.request


def _request_with_timeout(self, method, url, **kwargs):
    kwargs.setdefault("timeout", 20)
    return _original_request(self, method, url, **kwargs)


requests.sessions.Session.request = _request_with_timeout


def fetch_profile(code: str, retries: int = 3) -> dict[str, object]:
    """获取一家公司的详细资料，临时失败时按指数退避重试。"""
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
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    return {"A股代码": code, "获取状态": "失败", "错误信息": str(last_error)}


def save(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def main(limit: int | None = None, workers: int = 6) -> int:
    print("正在获取沪深京 A 股上市公司清单……")
    companies = ak.stock_info_a_code_name().copy()
    companies["code"] = companies["code"].astype(str).str.zfill(6)
    companies = companies.drop_duplicates(subset="code").reset_index(drop=True)
    if limit is not None:
        companies = companies.head(limit)

    rows: list[dict[str, object]] = []
    items = list(companies.itertuples(index=False))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_profile, item.code): item for item in items}
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="获取公司资料", unit="家"
        ):
            item = futures[future]
            row = future.result()
            row["A股代码"] = item.code
            row.setdefault("A股简称", item.name)
            rows.append(row)
            if len(rows) % 50 == 0:
                save(rows, CHECKPOINT_FILE)

    save(rows, DATA_FILE)
    CHECKPOINT_FILE.unlink(missing_ok=True)
    success_count = sum(row.get("获取状态") == "成功" for row in rows)
    print(f"完成：共导出 {len(rows)} 家，详细资料成功 {success_count} 家。")
    print(f"文件位置：{DATA_FILE}")
    return 0 if success_count == len(rows) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="仅处理前 N 家，便于测试")
    parser.add_argument("--workers", type=int, default=6, help="并发请求数，默认 6")
    args = parser.parse_args()
    raise SystemExit(main(limit=args.limit, workers=args.workers))
