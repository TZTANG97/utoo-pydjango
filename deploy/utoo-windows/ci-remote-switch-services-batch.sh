#!/usr/bin/env bash
# Write mid-platform + mall + utoo_biz upstreams, one nginx reload.
# Placeholders replaced by CI.
set -euo pipefail

NGINX_CONF_DIR="__NGINX_CONF_DIR__"
ORDER_PORT="__ORDER_PORT__"
IDENTITY_PORT="__IDENTITY_PORT__"
PAYMENT_PORT="__PAYMENT_PORT__"
ASSET_PORT="__ASSET_PORT__"
PLATFORM_PORT="__PLATFORM_PORT__"
MALL_PORT="__MALL_PORT__"
UTOO_BIZ_PORT="__UTOO_BIZ_PORT__"

NGINX_BIN="${QD_MALL_NGINX_BIN:-${UTOO_NGINX_BIN:-}}"
if [[ -z "$NGINX_BIN" ]]; then
  if [[ -x /usr/local/nginx/sbin/nginx ]]; then
    NGINX_BIN=/usr/local/nginx/sbin/nginx
  elif command -v nginx >/dev/null 2>&1; then
    NGINX_BIN=$(command -v nginx)
  else
    echo "nginx binary not found" >&2
    exit 1
  fi
fi

mkdir -p "$NGINX_CONF_DIR"
write_pair() {
  local primary="$1" legacy="$2" port="$3"
  printf 'server 127.0.0.1:%s;\n' "$port" >"${NGINX_CONF_DIR}/${primary}"
  if [[ -n "$legacy" ]]; then
    printf 'server 127.0.0.1:%s;\n' "$port" >"${NGINX_CONF_DIR}/${legacy}"
  fi
}

write_pair qd_mall_upstream_order.conf utoo_upstream_order.conf "$ORDER_PORT"
write_pair qd_mall_upstream_identity.conf utoo_upstream_identity.conf "$IDENTITY_PORT"
write_pair qd_mall_upstream_payment.conf utoo_upstream_payment.conf "$PAYMENT_PORT"
write_pair qd_mall_upstream_admin_asset.conf utoo_upstream_admin_asset.conf "$ASSET_PORT"
write_pair qd_mall_upstream_admin_platform.conf utoo_upstream_admin_platform.conf "$PLATFORM_PORT"
write_pair qd_mall_upstream_mall.conf "" "$MALL_PORT"
write_pair qd_mall_upstream_utoo_biz.conf "" "$UTOO_BIZ_PORT"

echo "qd-mall batch switch: identity=${IDENTITY_PORT} order=${ORDER_PORT} payment=${PAYMENT_PORT} asset=${ASSET_PORT} platform=${PLATFORM_PORT} mall=${MALL_PORT} utoo_biz=${UTOO_BIZ_PORT}"

"$NGINX_BIN" -t
if "$NGINX_BIN" -s reload 2>/dev/null; then
  echo "nginx reloaded"
elif [[ -f /usr/local/nginx/conf/nginx.conf ]]; then
  "$NGINX_BIN" -c /usr/local/nginx/conf/nginx.conf -s reload
else
  echo "nginx reload failed" >&2
  exit 1
fi
