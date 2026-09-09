#!/bin/bash
# Seed utoo_gateway / utoo_biz .env on idle slot so P5 deploys never fall back to
# Django default UTOO_BIZ_SERVICE_URL=http://127.0.0.1:18103 (nothing listens there on prod).
# Placeholders: __SLOT_ROOT__ __PEER_SLOT_ROOT__ __KIND__
# KIND=utoo_gateway | utoo_biz
set -euo pipefail
SLOT_ROOT="__SLOT_ROOT__"
PEER_ROOT="__PEER_SLOT_ROOT__"
KIND="__KIND__"

if [ "$KIND" = "utoo_gateway" ]; then
  DEST="${SLOT_ROOT}/platform/utoo_gateway/.env"
  PEER="${PEER_ROOT}/platform/utoo_gateway/.env"
  QD_GW="${SLOT_ROOT}/gateway/.env"
  [ -f "$QD_GW" ] || QD_GW="${PEER_ROOT}/gateway/.env"
  mkdir -p "${SLOT_ROOT}/platform/utoo_gateway"
elif [ "$KIND" = "utoo_biz" ]; then
  DEST="${SLOT_ROOT}/services/utoo_biz/.env"
  PEER="${PEER_ROOT}/services/utoo_biz/.env"
  QD_GW="${SLOT_ROOT}/gateway/.env"
  [ -f "$QD_GW" ] || QD_GW="${PEER_ROOT}/gateway/.env"
  mkdir -p "${SLOT_ROOT}/services/utoo_biz"
else
  echo "seed_utoo_env_bad_kind:${KIND}" >&2
  exit 1
fi

ensure_key() {
  local file="$1" key="$2" val="$3"
  if ! grep -q "^${key}=" "$file" 2>/dev/null; then
    echo "${key}=${val}" >> "$file"
  fi
}

if [ -f "$DEST" ]; then
  echo "seed_utoo_env_exists:${DEST}"
elif [ -f "$PEER" ]; then
  cp -a "$PEER" "$DEST"
  echo "seed_utoo_env_from_peer:${DEST}"
else
  # Bootstrap from Qingdao gateway VIP map (same host /opt/qd-mall-*)
  : > "$DEST"
  if [ -f "$QD_GW" ]; then
    # copy safe URL + JWT/OSS only — NEVER copy WEIXIN_* from Qingdao gateway
    # (UTOO 公众号 wxab3aa… 与青岛 wxde3a… 不是同一个号；误拷会导致扫码 40164)
    grep -E "^(DJANGO_SECRET_KEY|JWT_SECRET_KEY|JWT_SECRET|MALL_JWT_SECRET|UTOO_JWT_SECRET_KEY|OSS_|SMS_|IMAGE_WEB_SERVER|CORS_HTTPS)=" "$QD_GW" >> "$DEST" || true
  fi
  if [ "$KIND" = "utoo_gateway" ]; then
    ensure_key "$DEST" UTOO_BIZ_SERVICE_URL "http://127.0.0.1:19093"
    ensure_key "$DEST" SVC_IDENTITY_URL "http://127.0.0.1:19081"
    ensure_key "$DEST" SVC_ORDER_URL "http://127.0.0.1:19082"
    ensure_key "$DEST" SVC_PAYMENT_URL "http://127.0.0.1:19084"
    # 预约/反馈等仍可转 payment；扫码登录在网关本地（见 apps/wx/views.py）
    ensure_key "$DEST" SVC_WX_URL "http://127.0.0.1:19084"
    ensure_key "$DEST" SVC_ADMIN_ASSET_URL "http://127.0.0.1:19090"
    ensure_key "$DEST" SVC_ADMIN_PLATFORM_URL "http://127.0.0.1:19091"
    ensure_key "$DEST" SVC_INVOICE_URL "http://127.0.0.1:19091"
    ensure_key "$DEST" SVC_ENTRY_URL "http://127.0.0.1:19091"
  else
    ensure_key "$DEST" IDENTITY_MID_SERVICE_URL "http://127.0.0.1:19081"
    ensure_key "$DEST" SVC_IDENTITY_URL "http://127.0.0.1:19081"
    ensure_key "$DEST" UTOO_ORDER_MID_SERVICE_URL "http://127.0.0.1:19082"
    ensure_key "$DEST" SVC_ORDER_URL "http://127.0.0.1:19082"
    ensure_key "$DEST" SVC_PAYMENT_URL "http://127.0.0.1:19084"
    ensure_key "$DEST" SVC_ADMIN_ASSET_URL "http://127.0.0.1:19090"
    ensure_key "$DEST" SVC_ADMIN_PLATFORM_URL "http://127.0.0.1:19091"
    ensure_key "$DEST" UTOO_GATEWAY_INTERNAL_URL "http://127.0.0.1:19083"
    ensure_key "$DEST" DB_ENGINE "shared.db_backends.legacy_mysql"
  fi
  echo "seed_utoo_env_bootstrapped:${DEST}"
fi

# Always fill missing critical VIP keys (do not overwrite existing)
if [ "$KIND" = "utoo_gateway" ]; then
  ensure_key "$DEST" UTOO_BIZ_SERVICE_URL "http://127.0.0.1:19093"
  ensure_key "$DEST" SVC_IDENTITY_URL "http://127.0.0.1:19081"
  ensure_key "$DEST" SVC_ORDER_URL "http://127.0.0.1:19082"
  ensure_key "$DEST" SVC_PAYMENT_URL "http://127.0.0.1:19084"
  ensure_key "$DEST" SVC_WX_URL "http://127.0.0.1:19084"
  ensure_key "$DEST" SVC_ADMIN_ASSET_URL "http://127.0.0.1:19090"
  ensure_key "$DEST" SVC_ADMIN_PLATFORM_URL "http://127.0.0.1:19091"
elif [ "$KIND" = "utoo_biz" ]; then
  ensure_key "$DEST" IDENTITY_MID_SERVICE_URL "http://127.0.0.1:19081"
  ensure_key "$DEST" SVC_IDENTITY_URL "http://127.0.0.1:19081"
  ensure_key "$DEST" UTOO_ORDER_MID_SERVICE_URL "http://127.0.0.1:19082"
  ensure_key "$DEST" SVC_ORDER_URL "http://127.0.0.1:19082"
  ensure_key "$DEST" SVC_PAYMENT_URL "http://127.0.0.1:19084"
  ensure_key "$DEST" SVC_ADMIN_ASSET_URL "http://127.0.0.1:19090"
  ensure_key "$DEST" SVC_ADMIN_PLATFORM_URL "http://127.0.0.1:19091"
  ensure_key "$DEST" DB_ENGINE "shared.db_backends.legacy_mysql"
fi

# Guard: refuse known-bad local-only default port on prod slots
if grep -qE '^UTOO_BIZ_SERVICE_URL=http://127\.0\.0\.1:18103/?$' "$DEST" 2>/dev/null; then
  echo "seed_utoo_env_fix_bad_18103:${DEST}"
  sed -i 's|^UTOO_BIZ_SERVICE_URL=http://127\.0\.0\.1:18103/*$|UTOO_BIZ_SERVICE_URL=http://127.0.0.1:19093|' "$DEST"
fi

chmod 600 "$DEST"
chown deploy:deploy "$DEST" || true
echo "seed_utoo_env_ok:${DEST}"
