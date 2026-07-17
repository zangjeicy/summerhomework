"""QMT environment probe for the Ruyi secondary-development layer.

Verifies the three prerequisites of the QMT data path, in order:
1. xtquant library importable
2. local miniQMT terminal reachable (xtdata.connect)
3. full tick snapshot readable (fields used by call-auction analysis)

Usage:
    python ruyi/scripts/qmt_probe.py [stock_code ...]

Exit codes:
    0 all checks passed
    2 xtquant not installed
    3 QMT terminal not reachable
    4 tick data empty/unreadable
"""

import sys

# 竞价分析关心的核心 tick 字段（get_full_tick 返回字典中的键）：
# lastPrice 在 9:15-9:25 竞价时段即虚拟撮合价（匹配价），volume/amount 为匹配量/额，
# bidPrice/bidVol、askPrice/askVol 五档在竞价时段反映未匹配委托。
TICK_FIELDS = [
    "time", "lastPrice", "lastClose", "open", "high", "low",
    "volume", "amount", "pvolume",
    "bidPrice", "bidVol", "askPrice", "askVol",
]

DEFAULT_CODES = ["600519.SH", "000001.SZ"]


def normalize_code(code: str) -> str:
    """Append exchange suffix when missing (6xxxxx -> .SH, others -> .SZ)."""
    code = code.strip().upper()
    if "." in code:
        return code
    return f"{code}.SH" if code.startswith("6") else f"{code}.SZ"


def main(argv: list[str]) -> int:
    # Windows 控制台可能是 GBK，统一切 UTF-8 防中文输出乱码
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    codes = [normalize_code(c) for c in argv] or DEFAULT_CODES

    print("=" * 60)
    print("QMT 环境探针（如意二开层） —— 检查 xtquant 数据链路")
    print("=" * 60)

    # Step 1: xtquant 库
    try:
        from xtquant import xtdata  # noqa: PLC0415
    except ImportError:
        print("[1/3] xtquant 库 ...... 未安装")
        print("      处理：pip install xtquant（二开层可选依赖，不影响上游主流程）")
        return 2
    print("[1/3] xtquant 库 ...... OK")

    # Step 2: 连接本地 miniQMT 终端
    try:
        xtdata.connect()
    except Exception as exc:
        print(f"[2/3] miniQMT 连接 ... 失败：{exc}")
        print("      处理：启动券商 QMT 客户端并登录（勾选/进入 miniQMT 模式），再重跑本探针")
        print("      本机安装位置参考 ruyi/README.md「QMT 环境前置」")
        return 3
    print("[2/3] miniQMT 连接 ... OK")

    # Step 3: 全量 tick 快照
    try:
        ticks = xtdata.get_full_tick(codes)
    except Exception as exc:
        print(f"[3/3] tick 快照 ...... 读取异常：{exc}")
        return 4

    ok = 0
    for code in codes:
        data = ticks.get(code) or {}
        if not data:
            print(f"[3/3] {code} tick 为空（检查代码是否有效、行情权限是否开通）")
            continue
        ok += 1
        print(f"[3/3] {code} tick 字段：")
        for field in TICK_FIELDS:
            if field in data:
                print(f"      {field:>10} = {data[field]}")

    if ok == 0:
        return 4

    print("-" * 60)
    print(f"探针通过：{ok}/{len(codes)} 只标的取到快照。")
    print("提示：竞价语义（匹配价/未匹配量）需在交易日 9:15-9:25 运行本探针观察字段变化。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
