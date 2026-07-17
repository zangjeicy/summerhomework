"""重查 data/上市公司.csv 中的失败记录，全部成功后安全更新主数据。"""

from __future__ import annotations

import argparse
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import akshare as ak
import pandas as pd
import requests
from tqdm import tqdm


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "上市公司.csv"
TEMP_FILE = BASE_DIR / "data" / "上市公司.csv.tmp"
BACKUP_DIR = BASE_DIR / "data" / "backup"
_original_request = requests.sessions.Session.request


def _request_with_timeout(self, method, url, **kwargs):
    kwargs.setdefault("timeout", 30)
    return _original_request(self, method, url, **kwargs)


requests.sessions.Session.request = _request_with_timeout


def fetch_profile(code: str) -> tuple[str, dict[str, object] | None, str | None]:
    try:
        frame = ak.stock_profile_cninfo(symbol=code)
        if frame.empty:
            return code, None, "接口未返回公司概况"
        row = frame.iloc[0].to_dict()
        row.update({"A股代码": code, "获取状态": "成功", "错误信息": pd.NA})
        return code, row, None
    except Exception as exc:
        return code, None, str(exc)


def backup_current_data() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"上市公司_更新前备份_{timestamp}.csv"
    shutil.copy2(DATA_FILE, backup)
    return backup


def write_csv_safely(frame: pd.DataFrame) -> None:
    frame.to_csv(TEMP_FILE, index=False, encoding="utf-8-sig")
    os.replace(TEMP_FILE, DATA_FILE)


def main(max_rounds: int = 12, workers: int = 1) -> int:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"未找到文件：{DATA_FILE}")

    data = pd.read_csv(DATA_FILE, encoding="utf-8-sig", dtype={"A股代码": str})
    data["A股代码"] = data["A股代码"].str.zfill(6)
    pending = data.loc[
        data["获取状态"].fillna("").ne("成功"), "A股代码"
    ].drop_duplicates().tolist()
    print(f"总记录 {len(data)} 家，待补充 {len(pending)} 家。")
    if not pending:
        print("所有记录均为成功状态，无需补充。")
        return 0

    errors: dict[str, str] = {}
    for round_no in range(1, max_rounds + 1):
        if not pending:
            break
        next_pending: list[str] = []
        print(f"第 {round_no}/{max_rounds} 轮：重查 {len(pending)} 家……")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(fetch_profile, code): code for code in pending}
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="补充资料", unit="家"
            ):
                code, profile, error = future.result()
                if profile is None:
                    next_pending.append(code)
                    errors[code] = error or "未知错误"
                    continue
                index = data.index[data["A股代码"].eq(code)]
                for column, value in profile.items():
                    if column not in data.columns:
                        data[column] = pd.NA
                    data.loc[index, column] = value
                errors.pop(code, None)
        pending = next_pending
        if pending and round_no < max_rounds:
            time.sleep(min(15 * round_no, 90))

    if pending:
        print(f"仍有 {len(pending)} 家失败，主数据未覆盖。")
        for code in pending:
            print(f"  {code}: {errors.get(code, '未知错误')}")
        return 1

    backup = backup_current_data()
    write_csv_safely(data)
    print(f"补充完成，更新前数据已备份至：{backup}")
    print(f"主数据已更新：{DATA_FILE}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-rounds", type=int, default=12, help="最大重试轮数")
    parser.add_argument("--workers", type=int, default=1, help="并发数，默认 1")
    args = parser.parse_args()
    raise SystemExit(main(max_rounds=args.max_rounds, workers=args.workers))
