#!/usr/bin/env bash
set -euo pipefail

CONTRACT="${1:-contracts/analytics-service.openapi.yaml}"
PORT="${2:-4010}"

echo "Starting Prism Mock Server for $CONTRACT on port $PORT..."
npx prism mock "$CONTRACT" --host 0.0.0.0 --port "$PORT"
