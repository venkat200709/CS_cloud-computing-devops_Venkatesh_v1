#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/bin:/mingw64/bin:/c/Users/venka/.gemini/antigravity/bin:$PATH"

PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"
APP_VERSION="${APP_VERSION:-v1.0.0}"
DEP_PATH="${DEPENDENCY_PATH:-data/dependency.ok}"

mkdir -p data
touch "$DEP_PATH"

PORT="$PORT" HOST="$HOST" APP_VERSION="$APP_VERSION" DEPENDENCY_PATH="$DEP_PATH" python -m app.main &
APP_PID=$!

cleanup() {
  if kill -0 "$APP_PID" 2>/dev/null; then
    kill "$APP_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

for i in $(seq 1 30); do
  if curl -s "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

echo "=== HEALTH CHECK (INITIAL) ==="
curl -i -s "http://${HOST}:${PORT}/health"
echo ""

echo "=== READY CHECK (DEPENDENCY PRESENT) ==="
curl -i -s "http://${HOST}:${PORT}/ready"
echo ""

echo "=== SIMULATING OUTAGE: REMOVING DEPENDENCY ==="
rm -f "$DEP_PATH"

echo "=== READY CHECK (DEPENDENCY REMOVED) ==="
curl -i -s "http://${HOST}:${PORT}/ready"
echo ""

echo "=== HEALTH CHECK (DURING OUTAGE) ==="
curl -i -s "http://${HOST}:${PORT}/health"
echo ""

echo "=== SIMULATING RECOVERY: RESTORING DEPENDENCY ==="
touch "$DEP_PATH"

echo "=== READY CHECK (DEPENDENCY RESTORED) ==="
curl -i -s "http://${HOST}:${PORT}/ready"
echo ""

echo "=== OPERATOR STATUS DASHBOARD (HTML PROBE) ==="
curl -s "http://${HOST}:${PORT}/" | grep -E "(CareerSwami Service Monitor|READY \(200\)|Metric-label)" || true
echo ""

echo "=== RUNNING PYTEST SUITE ==="
pytest -v

echo "=== RUNNING GIT HISTORY SECRET AUDIT ==="
SCAN_MATCHES=$(git log -p | grep -E -i "(api[_-]?key\s*[:=]\s*['\"][^'\"]{8,}|password\s*[:=]\s*['\"][^'\"]+|bearer\s+[a-z0-9_\-\.]{15,}|BEGIN PRIVATE KEY)" || true)
if [ -n "$SCAN_MATCHES" ]; then
  echo "AUDIT FAILED: Secrets detected in git history!"
  exit 1
else
  echo "AUDIT PASSED: Zero secret or credential patterns found in git history."
fi

echo "=== CLEAN START PROTOCOL COMPLETE ==="
