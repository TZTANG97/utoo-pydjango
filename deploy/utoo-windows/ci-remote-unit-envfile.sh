#!/bin/bash
# Ensure systemd unit has EnvironmentFile lines; reload+restart if patched.
# Placeholders: __UNIT_FILE__ __ENV_FILE__ __UNIT_NAME__
# Also attaches shared-database.env for utoo_biz (MySQL VIP vars).
set -euo pipefail
UF="__UNIT_FILE__"
EF="__ENV_FILE__"
UN="__UNIT_NAME__"
SHARED="/opt/qd-mall/config/shared-database.env"
if [ ! -f "$EF" ]; then
  echo "unit_envfile_missing_env:${EF}" >&2
  exit 1
fi
if [ ! -f "$UF" ]; then
  echo "unit_envfile_missing_unit:${UF}" >&2
  exit 1
fi

need_patch=0
if ! grep -q "EnvironmentFile=-${EF}" "$UF"; then
  need_patch=1
fi
if [[ "$UN" == qd-utoo-biz-* ]] && [ -f "$SHARED" ] && ! grep -q "EnvironmentFile=-${SHARED}" "$UF"; then
  need_patch=1
fi
if [ "$need_patch" -eq 0 ]; then
  echo "unit_envfile_already:${UN}"
  exit 0
fi

awk -v envf="$EF" -v shared="$SHARED" -v unit="$UN" '
  BEGIN { inserted=0 }
  /^\[Service\]/ && !inserted {
    print
    if (unit ~ /^qd-utoo-biz-/ && shared != "") {
      print "EnvironmentFile=-" shared
    }
    inserted=1
    next
  }
  /^WorkingDirectory=/ {
    print
    print "EnvironmentFile=-" envf
    next
  }
  { print }
' "$UF" > /tmp/unit_envfile.$$
# Deduplicate EnvironmentFile lines
awk '!seen[$0]++' /tmp/unit_envfile.$$ > /tmp/unit_envfile2.$$
mv /tmp/unit_envfile2.$$ "$UF"
rm -f /tmp/unit_envfile.$$
systemctl daemon-reload
systemctl restart "$UN"
echo "unit_envfile_patched:${UN}"
