#!/usr/bin/env bash
# Discover active Qingdao nginx gateway port (18080|18180).
# Placeholder __CONF__ replaced by deploy script.
set -euo pipefail
CONF="__CONF__"

pick_port() {
  local f="$1"
  [ -f "$f" ] || return 1
  local p
  p=$(grep -E '^[[:space:]]*server[[:space:]]+127\.0\.0\.1:(18080|18180)[[:space:]]*;' "$f" \
    | grep -oE '18080|18180' \
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
for f in "$CONF" "/usr/local/nginx/conf/qd_mall_upstream_gateway.conf" "/data/nginx/conf/qd_mall_upstream_gateway.conf"; do
  if pick_port "$f"; then
    exit 0
  fi
done
echo "18080"
exit 0
