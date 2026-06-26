#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
PATHS = [
    "/dashboard", "/process-flow", "/equipment", "/alarms", "/production",
    "/maintenance", "/loto", "/reports", "/scenarios", "/playback",
    "/plant-config", "/diagnostics", "/help", "/api/state", "/api/health",
    "/api/reports/daily", "/api/playback/summary", "/api/scenarios",
]

ok = True
for path in PATHS:
    url = BASE.rstrip("/") + path
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.status
            print(f"{status:3} {path}")
            if status >= 400:
                ok = False
    except Exception as exc:
        ok = False
        print(f"ERR {path}: {exc}")

sys.exit(0 if ok else 1)
