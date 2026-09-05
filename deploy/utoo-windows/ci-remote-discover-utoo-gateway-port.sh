#!/usr/bin/env bash
# Discover active UTOO gateway port (18083|18183).
set -euo pipefail
CONF="__CONF__"

pick_port() {
  local f="$1"
  [ -f "$f" ] || return 1
  local p
  p=$(grep -E '^[[:space:]]*server[[:space:]]+127\.0\.0\.1:(18083|18183)[[:space:]]*;' "$f" \
    | grep -oE '18083|18183' \
    | head -1 || true)
  if [ -n "$p" ]; then
    echo "$p"
    return 0
  fi
  return 1
}

if pick_port "$CONF"; then
  exit 0
fi
for f in "$CONF" "/usr/local/nginx/conf/utoo_upstream_server.conf" "/usr/local/nginx/conf/qd_mall_upstream_utoo_gateway.conf"; do
  if pick_port "$f"; then
    exit 0
  fi
done
echo "18083"
exit 0
