#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOLID_PORT="${SOLID_PORT:-5042}"

SOLID_PID=""

cleanup() {
  if [[ -n "${SOLID_PID}" ]]; then
    kill "${SOLID_PID}" >/dev/null 2>&1 || true
    wait "${SOLID_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

wait_for_http() {
  local url="$1"
  local label="$2"

  for _ in {1..30}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[OK] ${label} hazir: ${url}"
      return 0
    fi
    sleep 0.4
  done

  echo "[FAIL] ${label} zamaninda ayaga kalkmadi: ${url}"
  return 1
}

cd "${REPO_ROOT}"

echo "==> Solid build"
npm run solid:build

echo "==> Solid dry-run"
python3 -m flask --app main run --host=127.0.0.1 --port="${SOLID_PORT}" \
  > /tmp/kahvesiz-solid-dryrun.log 2>&1 &
SOLID_PID="$!"

wait_for_http "http://127.0.0.1:${SOLID_PORT}/" "Solid Flask"
npm run solid:smoke -- "http://127.0.0.1:${SOLID_PORT}"
echo "Dry-run tamamlandi: Solid akisi basarili."
