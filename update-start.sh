#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

git pull --ff-only

cd "$ROOT_DIR/frontend"
npm run build

cd "$ROOT_DIR/backend"
exec bash ./start.sh
