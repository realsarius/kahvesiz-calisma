#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:5040}"

check_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"

  if ! rg -q -- "$needle" <<<"$haystack"; then
    echo "[FAIL] ${label}: expected pattern '${needle}' not found"
    exit 1
  fi

  echo "[OK] ${label}"
}

echo "Running jinja rollback smoke against: ${BASE_URL}"

home_html="$(curl -fsS "${BASE_URL}/")"
check_contains "$home_html" 'Verimli Çalışma Alanları' "Jinja home on /"

contact_headers="$(curl -fsSI "${BASE_URL}/contact")"
check_contains "$contact_headers" '/contact_us' "Legacy contact redirect"

cafes_html="$(curl -fsS "${BASE_URL}/cafes")"
check_contains "$cafes_html" 'Kafeler' "Legacy cafes page rendered"

curl -fsS "${BASE_URL}/api/cafes" >/dev/null
echo "[OK] /api/cafes reachable"

echo "Jinja rollback smoke completed successfully."
