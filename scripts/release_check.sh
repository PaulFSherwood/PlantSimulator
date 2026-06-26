#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall app
python3 scripts/smoke_check.py || {
  echo "Smoke check failed. Start uvicorn first: uvicorn app.main:app --reload"
  exit 1
}
echo "Release checks passed."
