"""重查并补充“上市公司.csv”中的失败数据，成功后原子覆盖源文件。"""

from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import akshare as ak
import pandas as pd
import requests
from tqdm import tqdm


CSV_FILE = Path(__file__).with_name("上市公司.csv")
TEMP_FILE = Path(__file__).with_name("上市公司.csv.tmp")

# stock_profile_cninfo 内部没有 timeout，统一补上以避免永久卡死。
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
        row["A股代码"] = code
        row["获取状态"] = "成功"
        row["错误信息"] = pd.NA
        return code, row, None
    except Exception as exc:  # 外部接口异常类型不固定
        return code, None, str(exc)


def write_csv_safely(frame: pd.DataFrame) -> None:
    frame.to_csv(TEMP_FILE, index=False, encoding="utf-8-sig")
    # 在同一磁盘上原子替换，避免写入中断破坏原 CSV。
    os.replace(TEMP_FILE, CSV_FILE)


def main(max_rounds: int = 12, workers: int = 1) -> None:
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"未找到文件：{CSV_FILE}")

    data = pd.read_csv(CSV_FILE, encoding="utf-8-sig", dtype={"A股代码": str})
    data["A股代码"] = data["A股代码"].str.zfill(6)
    failed_mask = data["获取状态"].fillna("").ne("成功")
    pending = data.loc[failed_mask, "A股代码"].drop_duplicates().tolist()
    print(f"总记录 {len(data)} 家，待补充 {len(pending)} 家。")

    if not pending:
        print("所有记录均为成功状态，无须补充。")
        return

    errors: dict[str, str] = {}
    for round_no in range(1, max_rounds + 1):
        if not pending:
            break
        print(f"第 {round_no}/{max_rounds} 轮：重查 {len(pending)} 家……")
        next_pending: list[str] = []

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
        print(f"本轮成功补充后，剩余 {len(pending)} 家。")
        if pending:
            wait_seconds = min(15 * round_no, 90)
            print(f"等待 {wait_seconds} 秒后继续，避免接口限流……")
            time.sleep(wait_seconds)

    if pending:
        details = "\n".join(f"  {code}: {errors.get(code, '未知错误')}" for code in pending)
        raise RuntimeError(
            f"仍有 {len(pending)} 家未获取成功，未覆盖原 CSV：\n{details}"
        )

    # 写入前进行硬性质量门禁。
    data["获取状态"] = data["获取状态"].fillna("")
    invalid = data["获取状态"].ne("成功")
    if invalid.any():
        raise RuntimeError(f"质量检查失败：仍有 {int(invalid.sum())} 条非成功数据")
    write_csv_safely(data)
    print(f"补充完成：{len(data)} 家全部成功，已更新 {CSV_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-rounds", type=int, default=12, help="最大重试轮数")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="并发数；py_mini_racer 多线程不安全，默认 1",
    )
    args = parser.parse_args()
    main(max_rounds=args.max_rounds, workers=args.workers)
