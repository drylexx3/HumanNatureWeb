#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=== HumanNature v3.6.0 Web Edition ==="
echo "Starting backend server on http://localhost:5050 ..."

exec python3.12 -m uvicorn server:app --host 0.0.0.0 --port 5050 --app-dir "$DIR"
