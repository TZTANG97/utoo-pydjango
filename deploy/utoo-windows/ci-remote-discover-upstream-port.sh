#!/usr/bin/env bash
# Discover active Utoo nginx upstream gateway port (18083|18183).
# Placeholder __CONF__ replaced by deploy script.
# 只认 upstream 行：server 127.0.0.1:PORT;  避免注释里的端口号误导切流。
set -euo pipefail
CONF="__CONF__"

pick_port() {
  local f="$1"
  [ -f "$f" ] || return 1
  # 仅匹配 server 行中的端口，忽略注释/历史文本
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
for f in "$CONF" "/usr/local/nginx/conf/utoo_upstream_server.conf" "/data/nginx/conf/utoo_upstream_server.conf"; do
  if pick_port "$f"; then
    exit 0
  fi
done
# 默认视为蓝在线，CI 将发绿槽
echo "18083"
exit 0
