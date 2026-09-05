#!/usr/bin/env bash
# CI 发版后：确保 idle 槽 mall/.env 存在，JWT/OSS/DB 对齐
# Placeholders: __SLOT_ROOT__ __MALL_UNIT__ __MALL_PORT__ __PEER_SLOT_ROOT__
set -euo pipefail

SLOT_ROOT="__SLOT_ROOT__"
PEER_ROOT="__PEER_SLOT_ROOT__"
MALL_UNIT="__MALL_UNIT__"
MALL_PORT="__MALL_PORT__"
MALL_ENV="${SLOT_ROOT}/services/mall/.env"
PEER_MALL_ENV="${PEER_ROOT}/services/mall/.env"
GW_ENV="${SLOT_ROOT}/gateway/.env"
PEER_GW_ENV="${PEER_ROOT}/gateway/.env"
IDENTITY_ENV=/opt/utoo-blue/qd_svc_identity/.env
PAY_ENV=/opt/utoo-blue/qd_svc_payment/.env
ORDER_ENV=/opt/utoo-blue/qd_svc_order/.env
SHARED_DB=/opt/qd-mall/config/shared-database.env
UNIT_FILE="/etc/systemd/system/${MALL_UNIT}.service"

mkdir -p "${SLOT_ROOT}/services/mall"
if [ ! -f "$MALL_ENV" ]; then
  if [ -f "$PEER_MALL_ENV" ]; then
    cp -a "$PEER_MALL_ENV" "$MALL_ENV"
    chown deploy:deploy "$MALL_ENV"
    echo post_mall_env_seeded_from_peer
  else
    touch "$MALL_ENV"
    chown deploy:deploy "$MALL_ENV"
    chmod 600 "$MALL_ENV"
    echo post_mall_env_created_empty
  fi
fi

patch_kv() {
  local file="$1" key="$2" val="$3"
  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$file"
  else
    echo "${key}=${val}" >>"$file"
  fi
}

JWT_SECRET=""
JWT_ISSUER="qd-mall-identity"
for src in "$GW_ENV" "$PEER_GW_ENV" "$IDENTITY_ENV"; do
  [ -f "$src" ] || continue
  if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(grep '^JWT_SECRET=' "$src" 2>/dev/null | head -1 | cut -d= -f2- || true)
    [ -z "$JWT_SECRET" ] && JWT_SECRET=$(grep '^MALL_JWT_SECRET=' "$src" 2>/dev/null | head -1 | cut -d= -f2- || true)
    [ -z "$JWT_SECRET" ] && JWT_SECRET=$(grep '^JWT_SECRET_KEY=' "$src" 2>/dev/null | head -1 | cut -d= -f2- || true)
  fi
  if [ "$JWT_ISSUER" = "qd-mall-identity" ]; then
    JWT_ISSUER=$(grep '^JWT_ISSUER=' "$src" 2>/dev/null | head -1 | cut -d= -f2- || true)
    [ -z "$JWT_ISSUER" ] && JWT_ISSUER=$(grep '^MALL_JWT_ISSUER=' "$src" 2>/dev/null | head -1 | cut -d= -f2- || true)
  fi
  [ -n "$JWT_SECRET" ] && break
done
[ -n "$JWT_SECRET" ] && patch_kv "$MALL_ENV" JWT_SECRET "$JWT_SECRET"
[ -n "$JWT_ISSUER" ] && patch_kv "$MALL_ENV" JWT_ISSUER "$JWT_ISSUER"
echo post_mall_jwt_ok

SRC="$PAY_ENV"
[ -f "$SRC" ] || SRC="$ORDER_ENV"
if [ -f "$SRC" ]; then
  OSS_KEYS="OSS_ENDPOINT OSS_BUCKET OSS_PUBLIC_BASE_URL OSS_ACCESS_KEY_ID OSS_ACCESS_KEY_SECRET IMAGE_WEB_SERVER OSS_PREFIX OSS_DOC_PREVIEW_ENABLE OSS_DOC_PREVIEW_PROCESS UPLOAD_DIR"
  synced=0
  for key in $OSS_KEYS; do
    line=$(grep -E "^${key}=" "$SRC" | head -1 || true)
    [ -n "$line" ] || continue
    val="${line#*=}"
    [ -n "$val" ] || continue
    patch_kv "$MALL_ENV" "$key" "$val"
    synced=$((synced + 1))
  done
  echo "post_mall_oss_ok keys=$synced"
fi

if [ -f "$SHARED_DB" ] && ! grep -q '^DB_HOST=' "$MALL_ENV"; then
  set -a
  # shellcheck disable=SC1091
  . "$SHARED_DB"
  set +a
  for key in DB_NAME DB_HOST DB_PORT DB_USER DB_PASSWORD DB_ENGINE; do
    val="${!key:-}"
    [ -n "$val" ] && patch_kv "$MALL_ENV" "$key" "$val"
  done
  grep -q '^DB_ENGINE=' "$MALL_ENV" || patch_kv "$MALL_ENV" DB_ENGINE "shared.db_backends.legacy_mysql"
  echo post_mall_db_ok
fi

# 经营域写门禁：未显式配置时默认打开（对齐 scripts/dev.env；prod 可在 .env 写 false）
for key in SALES_WRITE_ENABLED RENTAL_WRITE_ENABLED PROCUREMENT_WRITE_ENABLED; do
  if ! grep -q "^${key}=" "$MALL_ENV"; then
    patch_kv "$MALL_ENV" "$key" true
    echo "post_mall_write_flag_default ${key}=true"
  fi
done

chmod 600 "$MALL_ENV"
chown deploy:deploy "$MALL_ENV"

if [ -f "$UNIT_FILE" ] && ! grep -q "EnvironmentFile=-${MALL_ENV}" "$UNIT_FILE"; then
  sed -i "/^WorkingDirectory=/a EnvironmentFile=-${MALL_ENV}" "$UNIT_FILE"
  systemctl daemon-reload
  echo post_mall_systemd_envfile_ok
fi

systemctl restart "${MALL_UNIT}"
sleep 2
curl -sf "http://127.0.0.1:${MALL_PORT}/health" >/dev/null

# JWT 冒烟：identity 签发的 token 须能访问 welcome
TOK=$(
  cd /opt/utoo-blue/qd_svc_identity 2>/dev/null && .venv/bin/python <<'PY' || exit 0
import os, jwt, time, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.conf import settings
now = int(time.time())
p = {"sub":"1","user_id":"1","user_name":"p","true_name":"p","dept_id":None,"type":"1",
"scope":{"filter_list":1,"role_name":"x","visible_sales_ids":["1"],"company_ids":[]},
"role_ids":[],"permissions":[],"channel":"mall_qd","platform":"1","account_kind":"sy_user",
"iat":now,"exp":now+3600,"iss":settings.MALL_JWT_ISSUER}
print(jwt.encode(p, settings.MALL_JWT_SECRET, algorithm="HS256"))
PY
)
if [ -n "${TOK:-}" ]; then
  code=$(curl -sS -m 8 -o /tmp/post_mall_jwt.json -w '%{http_code}' \
    -H "Authorization: Bearer $TOK" -H 'X-Channel: mall_qd' \
    "http://127.0.0.1:${MALL_PORT}/api/v1/reporting/welcome" || echo 000)
  if [ "$code" != "200" ]; then
    echo "post_mall_jwt_smoke_fail:http=${code}" >&2
    exit 1
  fi
  echo post_mall_jwt_smoke_ok
fi

echo "post_mall_env_ok:${MALL_UNIT}:${MALL_PORT}"
