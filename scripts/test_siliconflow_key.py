#!/usr/bin/env python3
"""Test whether a SiliconFlow API key can authenticate successfully.

By default the script reads ``key.txt`` from the repository root and calls the
read-only models endpoint, so the check does not consume model inference quota.

Usage:
    python scripts/test_siliconflow_key.py
    python scripts/test_siliconflow_key.py --key-file C:\\path\\to\\key.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEY_FILE = REPO_ROOT / "key.txt"
DEFAULT_BASE_URL = "https://api.siliconflow.cn/v1"


def _read_key(path: Path) -> str:
    try:
        key = path.read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError as exc:
        raise ValueError(f"Key file not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read key file: {path} ({exc})") from exc

    if not key:
        raise ValueError(f"Key file is empty: {path}")
    if any(char.isspace() for char in key):
        raise ValueError("Key contains whitespace; keep only the API key in the file")
    return key


def _response_message(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    message = payload.get("message") or payload.get("error")
    if isinstance(message, dict):
        message = message.get("message")
    return str(message or "").strip()


def check_key(key: str, base_url: str, timeout: float) -> tuple[bool, str]:
    url = f"{base_url.rstrip('/')}/models"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "RuyiDailyStockAnalysis-key-check/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        message = _response_message(payload)
        detail = f"HTTP {exc.code}" + (f": {message}" if message else "")
        if exc.code == 401:
            detail += " (Key is invalid or expired)"
        elif exc.code == 403:
            detail += " (Account balance or permission may be insufficient)"
        return False, detail
    except urllib.error.URLError as exc:
        return False, f"Network error: {exc.reason}"
    except TimeoutError:
        return False, f"Request timed out after {timeout:g} seconds"
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return False, f"Provider returned an invalid JSON response: {exc}"

    models = payload.get("data", []) if isinstance(payload, dict) else []
    if status == 200 and isinstance(models, list):
        return True, f"HTTP 200; {len(models)} model(s) visible to this account"
    return False, f"Unexpected response: HTTP {status}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a SiliconFlow API key without running paid inference."
    )
    parser.add_argument(
        "--key-file",
        type=Path,
        default=DEFAULT_KEY_FILE,
        help=f"Key file path (default: {DEFAULT_KEY_FILE})",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"SiliconFlow OpenAI-compatible base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Request timeout in seconds (default: 15)",
    )
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    try:
        key = _read_key(args.key_file.resolve())
    except ValueError as exc:
        print(f"SiliconFlow key check failed: {exc}", file=sys.stderr)
        return 2

    available, detail = check_key(key, args.base_url, args.timeout)
    if available:
        print(f"SiliconFlow key is available: {detail}")
        return 0

    print(f"SiliconFlow key is unavailable: {detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
