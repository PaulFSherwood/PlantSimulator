#!/usr/bin/env bash
set -euo pipefail
find .   -path './.git' -prune -o   -path './.venv' -prune -o   -path './__pycache__' -prune -o   -path './app/data/*.sqlite3' -prune -o   -path './app/data/logs' -prune -o   -path './archive' -prune -o   -print | sed     -e 's/[^-][^\/]*\//  |/g'     -e 's/|\([^ ]\)/|-/'
