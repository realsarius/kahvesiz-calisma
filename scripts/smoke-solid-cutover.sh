#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:5040}"

check_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"

  if ! rg -qi -- "$needle" <<<"$haystack"; then
    echo "[FAIL] ${label}: expected pattern '${needle}' not found"
    exit 1
  fi

  echo "[OK] ${label}"
}

echo "Running solid cutover smoke against: ${BASE_URL}"

home_html="$(curl -fsS "${BASE_URL}/")"
check_contains "$home_html" 'id="root"' "Solid entry on /"

home_headers="$(curl -sS -D - -o /dev/null "${BASE_URL}/")"
check_contains "$home_headers" 'cache-control: no-store' "Entry cache strategy"

asset_path="$(printf '%s' "$home_html" | rg -o '/solid/assets/[^" ]+\.js' -m 1 || true)"
if [[ -z "${asset_path}" ]]; then
  echo "[FAIL] Solid asset path was not found in entry HTML"
  exit 1
fi

curl -fsS "${BASE_URL}${asset_path}" >/dev/null
echo "[OK] Solid JS asset reachable: ${asset_path}"

asset_headers="$(curl -sS -D - -o /dev/null "${BASE_URL}${asset_path}")"
check_contains "$asset_headers" 'cache-control: public, max-age=31536000, immutable' "Asset cache strategy"

curl -fsS "${BASE_URL}/cafes" | rg -q 'id="root"'
echo "[OK] Solid entry on /cafes"

curl -fsS "${BASE_URL}/index" | rg -q 'id="root"'
echo "[OK] Solid entry on /index alias"

curl -fsS "${BASE_URL}/contact_us" | rg -q 'id="root"'
echo "[OK] Solid entry on /contact_us alias"

curl -fsS "${BASE_URL}/login" | rg -q 'id="root"'
echo "[OK] Solid entry on /login"

curl -fsS "${BASE_URL}/signup" | rg -q 'id="root"'
echo "[OK] Solid entry on /signup"

admin_headers="$(curl -sS -D - -o /dev/null "${BASE_URL}/admin")"
check_contains "$admin_headers" 'location: .*\/login' "Unauthenticated /admin redirect"

curl -fsS "${BASE_URL}/new-public-path" | rg -q 'id="root"'
echo "[OK] Solid catchall entry on unknown public route"

curl -fsS "${BASE_URL}/api/cafes" >/dev/null
echo "[OK] /api/cafes reachable"

csrf_payload="$(curl -fsS "${BASE_URL}/api/csrf-token")"
check_contains "$csrf_payload" 'csrf_token' "CSRF token endpoint"

echo "Solid cutover smoke completed successfully."
