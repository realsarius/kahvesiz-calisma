#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:5040}"
ARTIFACT_ROOT="${2:-output/playwright}"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="${ARTIFACT_ROOT}/solid-visual-${RUN_ID}"

export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export PWCLI="${CODEX_HOME}/skills/playwright/scripts/playwright_cli.sh"

if ! command -v npx >/dev/null 2>&1; then
  echo "[FAIL] npx bulunamadi. Node.js/npm kurulumu gerekli."
  exit 1
fi

if [[ ! -x "${PWCLI}" ]]; then
  echo "[FAIL] Playwright wrapper bulunamadi: ${PWCLI}"
  exit 1
fi

mkdir -p "${RUN_DIR}"

cleanup() {
  "${PWCLI}" close >/dev/null 2>&1 || true
}
trap cleanup EXIT

extract_screenshot_path() {
  local cli_output="$1"
  printf '%s' "${cli_output}" | rg -o '\.playwright-cli/[^) ]+\.png' -m 1 || true
}

take_shot() {
  local label="$1"
  local cli_output
  local screenshot_path
  cli_output="$("${PWCLI}" screenshot)"
  screenshot_path="$(extract_screenshot_path "${cli_output}")"

  if [[ -z "${screenshot_path}" || ! -f "${screenshot_path}" ]]; then
    echo "[FAIL] Screenshot yolu parse edilemedi: ${label}"
    exit 1
  fi

  cp "${screenshot_path}" "${RUN_DIR}/${label}.png"
  echo "[OK] ${label}.png"
}

capture_route() {
  local prefix="$1"
  local route="$2"
  local slug
  if [[ "${route}" == "/" ]]; then
    slug="home"
  else
    slug="$(printf '%s' "${route}" | sed 's#^/##' | tr '/' '-')"
  fi

  "${PWCLI}" goto "${BASE_URL%/}${route}" >/dev/null
  take_shot "${prefix}-${slug}"
}

capture_viewport_set() {
  local width="$1"
  local height="$2"
  local prefix="$3"
  echo "==> Viewport ${prefix}: ${width}x${height}"
  "${PWCLI}" resize "${width}" "${height}" >/dev/null

  capture_route "${prefix}" "/"
  capture_route "${prefix}" "/cafes"
  capture_route "${prefix}" "/about"
  capture_route "${prefix}" "/contact"
  capture_route "${prefix}" "/privacy"
  capture_route "${prefix}" "/license"
  capture_route "${prefix}" "/login"
  capture_route "${prefix}" "/signup"
  capture_route "${prefix}" "/admin"
}

echo "Running solid visual regression smoke against: ${BASE_URL}"
"${PWCLI}" open "${BASE_URL%/}/" >/dev/null

capture_viewport_set 1440 900 "desktop"
capture_viewport_set 390 844 "mobile"

echo "Visual regression artefactlari hazir: ${RUN_DIR}"
