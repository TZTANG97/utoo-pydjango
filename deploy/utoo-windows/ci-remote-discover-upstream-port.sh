#!/usr/bin/env bash
# Discover active Utoo nginx upstream gateway port (18083|18183).
# Placeholder __CONF__ replaced by deploy script.
set -euo pipefail
CONF="__CONF__"
PORTS='18083|18183'
if [ -f "$CONF" ]; then
  p=$(grep -oE "$PORTS" "$CONF" | head -1 || true)
  if [ -n "$p" ]; then
    echo "$p"
    exit 0
  fi
fi
for f in "$CONF" "/usr/local/nginx/conf/utoo_upstream_server.conf" "/data/nginx/conf/utoo_upstream_server.conf"; do
  if [ -f "$f" ]; then
    p=$(grep -oE "$PORTS" "$f" | head -1 || true)
    if [ -n "$p" ]; then
      echo "$p"
      exit 0
    fi
  fi
done
# 默认视为蓝在线，CI 将发绿槽
echo "18083"
exit 0
