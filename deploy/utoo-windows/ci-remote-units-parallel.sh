#!/usr/bin/env bash
# Parallel pip + check + restart + health. No editable libs (PYTHONPATH=slot root).
# Placeholders: __ROOT__  __SPECS__  (dir|systemd_unit|port;...)
set -euo pipefail

ROOT="__ROOT__"
SPECS="__SPECS__"
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-120}"
export PIP_RETRIES="${PIP_RETRIES:-10}"
export PYTHONPATH="${ROOT}:${ROOT}/platform/qd_libs_common:${PYTHONPATH:-}"

run_one() {
  local dir="$1" svc="$2" port="$3"
  local safe
  safe=$(echo "$dir" | tr '/.' '__')
  local log="/tmp/qd_unit_${safe}.log"
  {
    echo "deploy_unit_start:${dir}:${svc}:${port}"
    cd "${ROOT}/${dir}"
    if [ ! -x .venv/bin/pip ]; then
      if [ -x /opt/qd-mall/.python/bin/python ]; then
        /opt/qd-mall/.python/bin/python -m venv .venv
      elif [ -x /opt/utoo/.python/bin/python ]; then
        /opt/utoo/.python/bin/python -m venv .venv
      else
        (python3 -m venv .venv || python -m venv .venv)
      fi
    fi
    local i
    for i in 1 2 3; do
      echo "deploy_pip_attempt:${dir}:$i/3"
      if .venv/bin/python -m pip install -r requirements.txt gunicorn -i "$PIP_INDEX_URL" --retries "$PIP_RETRIES" --timeout "$PIP_DEFAULT_TIMEOUT" --progress-bar off; then
        break
      fi
      if [ "$i" -eq 3 ]; then
        echo "deploy_pip_failed:${dir}"
        return 1
      fi
      sleep $((20 * i))
    done
    echo "deploy_pip_ok:${dir}"
    chown -R "${DEPLOY_USER:-deploy}:${DEPLOY_USER:-deploy}" .venv 2>/dev/null || true

    export DJANGO_SETTINGS_MODULE=config.settings
    export PYTHONPATH="${ROOT}:${ROOT}/platform/qd_libs_common:${PYTHONPATH:-}"
    .venv/bin/python manage.py check
    echo "deploy_django_check_ok:${dir}"

    systemctl restart "${svc}"
    local j=1
    while [ "$j" -le 60 ]; do
      if curl -sf "http://127.0.0.1:${port}/health" >/dev/null || curl -sf "http://127.0.0.1:${port}/health/" >/dev/null; then
        echo "deploy_health_ok:${svc}"
        return 0
      fi
      sleep 1
      j=$((j + 1))
    done
    echo "deploy_health_fail:${svc}" >&2
    systemctl --no-pager status "${svc}" -l || true
    journalctl -u "${svc}" -n 80 --no-pager || true
    return 1
  } >"$log" 2>&1
}

IFS=';' read -ra ITEMS <<< "$SPECS"
pids=()
dirs=()
logs=()
for item in "${ITEMS[@]}"; do
  [ -z "$item" ] && continue
  IFS='|' read -r dir svc port <<< "$item"
  dirs+=("$dir")
  safe=$(echo "$dir" | tr '/.' '__')
  logs+=("/tmp/qd_unit_${safe}.log")
  run_one "$dir" "$svc" "$port" &
  pids+=($!)
done

ec=0
failed_dirs=()
for i in "${!pids[@]}"; do
  if ! wait "${pids[$i]}"; then
    ec=1
    failed_dirs+=("${dirs[$i]}")
  fi
done

echo "----- deploy units summary -----"
for i in "${!dirs[@]}"; do
  if grep -q 'deploy_health_ok:' "${logs[$i]}" 2>/dev/null; then
    echo "OK: ${dirs[$i]}"
  else
    echo "FAILED: ${dirs[$i]}"
  fi
done
for i in "${!dirs[@]}"; do
  echo "----- log ${dirs[$i]} -----"
  cat "${logs[$i]}" 2>/dev/null || true
done

if [ "$ec" -ne 0 ]; then
  echo "deploy_units_parallel_failed dirs=${failed_dirs[*]}" >&2
  exit 1
fi
echo "deploy_units_parallel_ok"
