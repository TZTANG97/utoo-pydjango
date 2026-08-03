#!/usr/bin/env bash
# Write all four service upstream confs then nginx -t && reload once.
# Placeholders: __NGINX_CONF_DIR__ __ORDER_PORT__ __PAYMENT_PORT__ __ASSET_PORT__ __PLATFORM_PORT__
set -euo pipefail

NGINX_CONF_DIR="__NGINX_CONF_DIR__"
ORDER_PORT="__ORDER_PORT__"
PAYMENT_PORT="__PAYMENT_PORT__"
ASSET_PORT="__ASSET_PORT__"
PLATFORM_PORT="__PLATFORM_PORT__"

NGINX_BIN="${UTOO_NGINX_BIN:-}"
if [[ -z "$NGINX_BIN" ]]; then
  if [[ -x /usr/local/nginx/sbin/nginx ]]; then
    NGINX_BIN=/usr/local/nginx/sbin/nginx
  elif command -v nginx >/dev/null 2>&1; then
    NGINX_BIN=$(command -v nginx)
  else
    echo "nginx binary not found; set UTOO_NGINX_BIN" >&2
    exit 1
  fi
fi

mkdir -p "$NGINX_CONF_DIR"
printf 'server 127.0.0.1:%s;\n' "$ORDER_PORT" >"${NGINX_CONF_DIR}/utoo_upstream_order.conf"
printf 'server 127.0.0.1:%s;\n' "$PAYMENT_PORT" >"${NGINX_CONF_DIR}/utoo_upstream_payment.conf"
printf 'server 127.0.0.1:%s;\n' "$ASSET_PORT" >"${NGINX_CONF_DIR}/utoo_upstream_admin_asset.conf"
printf 'server 127.0.0.1:%s;\n' "$PLATFORM_PORT" >"${NGINX_CONF_DIR}/utoo_upstream_admin_platform.conf"

echo "utoo batch switch: order=${ORDER_PORT} payment=${PAYMENT_PORT} admin_asset=${ASSET_PORT} admin_platform=${PLATFORM_PORT}"

"$NGINX_BIN" -t
if "$NGINX_BIN" -s reload 2>/dev/null; then
  echo "nginx reloaded"
elif [[ -f /usr/local/nginx/conf/nginx.conf ]]; then
  "$NGINX_BIN" -c /usr/local/nginx/conf/nginx.conf -s reload
  echo "nginx reloaded (-c conf)"
else
  echo "nginx reload failed" >&2
  exit 1
fi
