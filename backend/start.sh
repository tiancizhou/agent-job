#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -r requirements.txt -q

PORT="${SERVER_PORT:-8000}"
.venv/bin/uvicorn main:app --host 0.0.0.0 --port "$PORT"
