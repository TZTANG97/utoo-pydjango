#!/usr/bin/env bash
# Placeholders __ROOT__ __SVC_DIR__ replaced by deploy script before remote exec.
set -euo pipefail
cd "__ROOT__/__SVC_DIR__"
if [ ! -x .venv/bin/pip ]; then
  (python3 -m venv .venv || python -m venv .venv)
fi
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT:-120}
export PIP_RETRIES=${PIP_RETRIES:-10}
PIP_INDEX_URL=${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}
echo deploy_pip_index_url:$PIP_INDEX_URL
echo deploy_pip_svc:__SVC_DIR__
.venv/bin/python -V || true
for i in 1 2 3; do
  echo deploy_pip_attempt:$i/3
  if .venv/bin/python -m pip install --upgrade pip -i "$PIP_INDEX_URL" --retries "$PIP_RETRIES" --timeout "$PIP_DEFAULT_TIMEOUT" --progress-bar off \
    && .venv/bin/python -m pip install -r requirements.txt gunicorn -i "$PIP_INDEX_URL" --retries "$PIP_RETRIES" --timeout "$PIP_DEFAULT_TIMEOUT" --progress-bar off; then
    break
  fi
  if [ "$i" -eq 3 ]; then echo deploy_pip_failed; exit 1; fi
  sleep $((20 * i))
done
echo deploy_pip_ok
