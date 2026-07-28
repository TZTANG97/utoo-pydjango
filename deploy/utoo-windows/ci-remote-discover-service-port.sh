#!/usr/bin/env bash
# Discover one service's active Utoo upstream port.
# Placeholders are replaced by ci-deploy-windows.ps1.
set -euo pipefail

CONF="__CONF__"
PORTS="__PORTS__"
DEFAULT_PORT="__DEFAULT_PORT__"

if [[ -f "$CONF" ]]; then
  port=$(grep -oE "$PORTS" "$CONF" | head -1 || true)
  if [[ -n "$port" ]]; then
    echo "$port"
    exit 0
  fi
fi

echo "$DEFAULT_PORT"
