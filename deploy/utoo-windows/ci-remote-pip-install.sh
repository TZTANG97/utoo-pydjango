#!/usr/bin/env bash
# Placeholders __ROOT__ __SVC_DIR__ replaced by deploy script.
set -euo pipefail
DEPLOY_USER="${DEPLOY_USER:-deploy}"
SVC_DIR='__SVC_DIR__'
cd "__ROOT__/__SVC_DIR__"

seed_venv_from_utoo() {
  local donor=""
  for candidate in \
    /opt/utoo-blue/qd_svc_order/.venv \
    /opt/utoo-green/qd_svc_order/.venv \
    /opt/qd-mall-blue/services/mall/.venv \
    /opt/qd-mall-green/services/mall/.venv; do
    if [ -x "${candidate}/bin/pip" ]; then
      donor="$candidate"
      break
    fi
  done
  if [ -n "$donor" ]; then
    echo "deploy_pip_seed_venv:${donor}"
    rm -rf .venv
    cp -a "$donor" .venv
  fi
}

if [ ! -x .venv/bin/pip ]; then
  seed_venv_from_utoo
fi
# 从 utoo order 复制的 venv 常带错误 shebang，导致 systemd 启不起来、端口被僵尸进程占用
if [ -f .venv/bin/gunicorn ] && head -1 .venv/bin/gunicorn | grep -qE '/opt/utoo|qd_svc_order|/qd-mall-green'; then
  echo deploy_pip_recreate_venv_bad_shebang
  donor=/opt/qd-mall-green/services/mall/.venv
  if [ "$SVC_DIR" = "services/mall" ] && [ -x "${donor}/bin/python" ]; then
    rm -rf .venv
    cp -a "$donor" .venv
    py="$(pwd)/.venv/bin/python"
    for f in .venv/bin/*; do
      [ -f "$f" ] || continue
      if head -1 "$f" 2>/dev/null | grep -q '^#!'; then
        sed -i "1s|^#![^ ]*|#!${py}|" "$f"
      fi
    done
  else
    SEED_PY=
    if [ -x /opt/qd-mall-green/services/mall/.venv/bin/python ]; then
      SEED_PY=/opt/qd-mall-green/services/mall/.venv/bin/python
    elif [ -x /opt/qd-mall/.python/bin/python ]; then
      SEED_PY=/opt/qd-mall/.python/bin/python
    else
      SEED_PY=python3
    fi
    rm -rf .venv
    "$SEED_PY" -m venv .venv
  fi
fi
if [ ! -x .venv/bin/pip ]; then
  if [ -x /opt/qd-mall/.python/bin/python ]; then
    /opt/qd-mall/.python/bin/python -m venv .venv
  elif [ -x /opt/utoo/.python/bin/python ]; then
    /opt/utoo/.python/bin/python -m venv .venv
  else
    (python3 -m venv .venv || python -m venv .venv)
  fi
fi
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT:-120}
export PIP_RETRIES=${PIP_RETRIES:-10}
PIP_INDEX_URL=${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}
echo deploy_pip_index_url:$PIP_INDEX_URL
echo "deploy_pip_svc:${SVC_DIR}"
.venv/bin/python -V || true
pip_install() {
  .venv/bin/python -m pip install -r requirements.txt gunicorn \
    -i "$PIP_INDEX_URL" --retries "$PIP_RETRIES" --timeout "$PIP_DEFAULT_TIMEOUT" --progress-bar off "$@"
}
for i in 1 2 3; do
  echo deploy_pip_attempt:$i/3
  if pip_install; then
    break
  fi
  if pip_install --only-binary=:all:; then
    break
  fi
  if [ "$i" -eq 3 ]; then echo deploy_pip_failed; exit 1; fi
  sleep $((20 * i))
done
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" .venv
echo deploy_pip_ok
