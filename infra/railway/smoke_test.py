#!/usr/bin/env python3
"""Smoke test for local or deployed chat stack."""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request


def check(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return 200 <= response.status < 300
    except urllib.error.URLError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    if args.local:
        backend = os.getenv("BACKEND_URL", "http://localhost:8000/health")
        frontend = os.getenv("FRONTEND_URL", "http://localhost:4321/chat")
    else:
        backend = os.getenv("BACKEND_URL", "")
        frontend = os.getenv("FRONTEND_URL", "")
        if not backend or not frontend:
            print("Set BACKEND_URL and FRONTEND_URL for deployed smoke test.", file=sys.stderr)
            return 1

    ok_backend = check(backend)
    ok_frontend = check(frontend)
    print(f"backend={backend} ok={ok_backend}")
    print(f"frontend={frontend} ok={ok_frontend}")
    return 0 if ok_backend and ok_frontend else 1


if __name__ == "__main__":
    raise SystemExit(main())
