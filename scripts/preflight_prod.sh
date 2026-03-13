#!/usr/bin/env bash
set -euo pipefail

# Prod preflight checks for Kahvesiz Calisma.
# Usage:
#   scripts/preflight_prod.sh
#   DOMAIN=kahvesizcalisma.com NGINX_PROD_PORT=80 scripts/preflight_prod.sh

DOMAIN="${DOMAIN:-kahvesizcalisma.com}"
NGINX_PROD_PORT="${NGINX_PROD_PORT:-80}"
STRICT="${STRICT:-0}"

warn_count=0
error_count=0

warn() {
  warn_count=$((warn_count + 1))
  echo "[warn] $*"
}

fail() {
  error_count=$((error_count + 1))
  echo "[error] $*"
}

ok() {
  echo "[ok] $*"
}

require_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "Komut bulundu: $cmd"
  else
    fail "Komut bulunamadi: $cmd"
  fi
}

check_dns() {
  local ip_list=""
  if command -v dig >/dev/null 2>&1; then
    ip_list="$(dig +short A "$DOMAIN" | tr '\n' ' ' | xargs)"
  elif command -v nslookup >/dev/null 2>&1; then
    ip_list="$(nslookup "$DOMAIN" 2>/dev/null | awk '/^Address: /{print $2}' | tr '\n' ' ' | xargs)"
  else
    warn "DNS kontrolu atlandi (dig veya nslookup bulunamadi)."
    return
  fi

  if [[ -n "$ip_list" ]]; then
    ok "DNS kaydi bulundu ($DOMAIN): $ip_list"
  else
    warn "DNS kaydi bulunamadi: $DOMAIN"
  fi
}

check_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/tmp/kc_preflight_port.txt 2>/dev/null; then
      warn "Port kullanimda: $port"
      sed -n '2,6p' /tmp/kc_preflight_port.txt | sed 's/^/[port] /'
    else
      ok "Port musait: $port"
    fi
    rm -f /tmp/kc_preflight_port.txt
  else
    warn "Port kontrolu atlandi (lsof bulunamadi)."
  fi
}

validate_secret() {
  local key="$1"
  local insecure_value="$2"
  local value="${!key:-}"
  if [[ -z "$value" ]]; then
    warn "Ortam degiskeni bos: $key"
  elif [[ "$value" == "$insecure_value" ]]; then
    warn "Ortam degiskeni varsayilan/insecure gorunuyor: $key"
  else
    ok "Ortam degiskeni ayarli: $key"
  fi
}

load_env_file() {
  if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
    ok ".env yuklendi"
  else
    warn ".env dosyasi bulunamadi, sadece mevcut shell env degerleri kullanilacak."
  fi
}

main() {
  echo "== Kahvesiz Calisma / Prod Preflight =="
  echo "[info] Domain: $DOMAIN"
  echo "[info] Nginx prod port: $NGINX_PROD_PORT"

  require_cmd docker
  require_cmd curl

  load_env_file

  if docker compose config >/dev/null; then
    ok "docker compose config gecerli"
  else
    fail "docker compose config hatasi"
  fi

  check_dns
  check_port "$NGINX_PROD_PORT"

  validate_secret SECRET_KEY "change-me"
  validate_secret POSTGRES_PROD_PASSWORD "pass"
  validate_secret RESEND_API_KEY ""

  local frontend_url="${FRONTEND_URL_PROD:-}"
  if [[ "$frontend_url" == https://* ]]; then
    ok "FRONTEND_URL_PROD HTTPS: $frontend_url"
  elif [[ -z "$frontend_url" ]]; then
    warn "FRONTEND_URL_PROD bos"
  else
    warn "FRONTEND_URL_PROD HTTPS degil: $frontend_url"
  fi

  echo
  echo "[summary] warning=$warn_count error=$error_count strict=$STRICT"

  if [[ "$error_count" -gt 0 ]]; then
    exit 1
  fi

  if [[ "$STRICT" == "1" && "$warn_count" -gt 0 ]]; then
    exit 2
  fi

  exit 0
}

main "$@"
