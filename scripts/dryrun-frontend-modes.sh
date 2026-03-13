#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOLID_PORT="${SOLID_PORT:-5042}"
JINJA_PORT="${JINJA_PORT:-5043}"

SOLID_PID=""
JINJA_PID=""

cleanup() {
  if [[ -n "${SOLID_PID}" ]]; then
    kill "${SOLID_PID}" >/dev/null 2>&1 || true
    wait "${SOLID_PID}" >/dev/null 2>&1 || true
  fi

  if [[ -n "${JINJA_PID}" ]]; then
    kill "${JINJA_PID}" >/dev/null 2>&1 || true
    wait "${JINJA_PID}" >/dev/null 2>&1 || true
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

echo "==> Solid mode dry-run"
FRONTEND_RENDER_MODE=solid python3 -m flask --app main run --host=127.0.0.1 --port="${SOLID_PORT}" \
  > /tmp/kahvesiz-solid-dryrun.log 2>&1 &
SOLID_PID="$!"

wait_for_http "http://127.0.0.1:${SOLID_PORT}/" "Solid Flask"
npm run solid:smoke -- "http://127.0.0.1:${SOLID_PORT}"

kill "${SOLID_PID}" >/dev/null 2>&1 || true
wait "${SOLID_PID}" >/dev/null 2>&1 || true
SOLID_PID=""

echo "==> Jinja rollback dry-run"
FRONTEND_RENDER_MODE=jinja python3 -m flask --app main run --host=127.0.0.1 --port="${JINJA_PORT}" \
  > /tmp/kahvesiz-jinja-dryrun.log 2>&1 &
JINJA_PID="$!"

wait_for_http "http://127.0.0.1:${JINJA_PORT}/" "Jinja Flask"
npm run jinja:smoke -- "http://127.0.0.1:${JINJA_PORT}"

echo "Dry-run tamamlandi: Solid cutover + Jinja rollback akislari basarili."
