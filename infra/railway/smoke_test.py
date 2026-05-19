#!/usr/bin/env python3
"""Smoke test for the local or deployed app stack.

Reads service names and paths from environment variables that the Makefile
populates from ``infra/railway/project.env``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


def railway_url(path: str, service: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["railway", "domain", "--service", service, "--json"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    data = json.loads(out)
    domains = data.get("domains") or []
    if not domains:
        return None
    base = domains[0].rstrip("/")
    if not base.startswith("http"):
        base = f"https://{base}"
    return f"{base}{path}"


def check_backend(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            body = response.read(512).decode("utf-8", errors="replace")
            return 200 <= response.status < 300 and "Index of" not in body
    except urllib.error.URLError:
        return False


def check_frontend(url: str) -> bool:
    """Accept 2xx or auth redirect (302/307) for unauthenticated protected pages."""
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=15) as response:
            status = response.status
            if status in (302, 307):
                return True
            body = response.read(512).decode("utf-8", errors="replace")
            return 200 <= status < 300 and "Index of" not in body
    except urllib.error.HTTPError as exc:
        if exc.code in (302, 307):
            return True
        return False
    except urllib.error.URLError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    backend_path = os.getenv("SMOKE_BACKEND_PATH", "/health")
    frontend_path = os.getenv("SMOKE_FRONTEND_PATH", "/")

    if args.local:
        backend = os.getenv("BACKEND_URL", f"http://localhost:8000{backend_path}")
        frontend = os.getenv("FRONTEND_URL", f"http://localhost:4321{frontend_path}")
    else:
        backend_service = os.getenv("RAILWAY_BACKEND_SERVICE")
        frontend_service = os.getenv("RAILWAY_FRONTEND_SERVICE")
        backend = os.getenv("BACKEND_URL") or (
            railway_url(backend_path, backend_service) if backend_service else None
        )
        frontend = os.getenv("FRONTEND_URL") or (
            railway_url(frontend_path, frontend_service) if frontend_service else None
        )
        if not backend or not frontend:
            print(
                "Set BACKEND_URL and FRONTEND_URL, or run via `make railway-smoke` "
                "so RAILWAY_BACKEND_SERVICE / RAILWAY_FRONTEND_SERVICE are exported.",
                file=sys.stderr,
            )
            return 1

    ok_backend = check_backend(backend)
    ok_frontend = check_frontend(frontend)
    print(f"backend={backend} ok={ok_backend}")
    print(f"frontend={frontend} ok={ok_frontend}")
    return 0 if ok_backend and ok_frontend else 1


if __name__ == "__main__":
    raise SystemExit(main())
