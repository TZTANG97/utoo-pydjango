#!/usr/bin/env bash
# Parallel pip + django check + restart + health for multiple idle-slot units.
# Placeholders: __ROOT__  __SPECS__   (SPECS = dir|systemd_unit|port;dir|...)
set -euo pipefail

ROOT="__ROOT__"
SPECS="__SPECS__"
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-120}"
export PIP_RETRIES="${PIP_RETRIES:-10}"
LIBS_LOCK="${LIBS_LOCK:-/tmp/utoo_qd_libs_common_pip.lock}"

pip_install_libs_editable() {
  # Serialize editable installs of the shared source tree — concurrent
  # `pip install -e qd_libs_common` races on build/metadata (often first cold deploy).
  if command -v flock >/dev/null 2>&1; then
    (
      flock 9
      .venv/bin/python -m pip install -e "${ROOT}/qd_libs_common" -i "$PIP_INDEX_URL" --retries "$PIP_RETRIES" --timeout "$PIP_DEFAULT_TIMEOUT" --progress-bar off
    ) 9>"$LIBS_LOCK"
    return $?
  fi
  local lockdir="${LIBS_LOCK}.d" n=0 ec=0
  while ! mkdir "$lockdir" 2>/dev/null; do
    n=$((n + 1))
    if [ "$n" -gt 180 ]; then
      echo "deploy_libs_lock_timeout:${lockdir}" >&2
      return 1
    fi
    sleep 1
  done
  .venv/bin/python -m pip install -e "${ROOT}/qd_libs_common" -i "$PIP_INDEX_URL" --retries "$PIP_RETRIES" --timeout "$PIP_DEFAULT_TIMEOUT" --progress-bar off || ec=$?
  rmdir "$lockdir" 2>/dev/null || true
  return "$ec"
}

run_one() {
  local dir="$1" svc="$2" port="$3"
  local log="/tmp/utoo_unit_${dir}.log"
  {
    echo "deploy_unit_start:${dir}:${svc}:${port}"
    cd "${ROOT}/${dir}"
    if [ ! -x .venv/bin/pip ]; then
      if [ -x /opt/utoo/.python/bin/python ]; then
        /opt/utoo/.python/bin/python -m venv .venv
      else
        (python3 -m venv .venv || python -m venv .venv)
      fi
    fi
    local ok=0 i
    for i in 1 2 3; do
      echo "deploy_pip_attempt:${dir}:$i/3"
      if .venv/bin/python -m pip install -r requirements.txt gunicorn -i "$PIP_INDEX_URL" --retries "$PIP_RETRIES" --timeout "$PIP_DEFAULT_TIMEOUT" --progress-bar off; then
        if pip_install_libs_editable; then
          ok=1
          break
        fi
      fi
      if [ "$i" -eq 3 ]; then
        echo "deploy_pip_failed:${dir}"
        return 1
      fi
      sleep $((20 * i))
    done
    [ "$ok" -eq 1 ]
    echo "deploy_pip_ok:${dir}"

    export DJANGO_SETTINGS_MODULE=config.settings
    .venv/bin/python manage.py check
    echo "deploy_django_check_ok:${dir}"

    systemctl restart "${svc}"
    local j=1
    while [ "$j" -le 60 ]; do
      if curl -sf "http://127.0.0.1:${port}/health" >/dev/null; then
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
for item in "${ITEMS[@]}"; do
  [ -z "$item" ] && continue
  IFS='|' read -r dir svc port <<< "$item"
  dirs+=("$dir")
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
for dir in "${dirs[@]}"; do
  if grep -q 'deploy_health_ok:' "/tmp/utoo_unit_${dir}.log" 2>/dev/null; then
    echo "OK: ${dir}"
  else
    echo "FAILED: ${dir}"
  fi
done

for dir in "${dirs[@]}"; do
  echo "----- log ${dir} -----"
  cat "/tmp/utoo_unit_${dir}.log" 2>/dev/null || true
done

if [ "$ec" -ne 0 ]; then
  echo "----- failed units highlights -----" >&2
  for dir in "${failed_dirs[@]}"; do
    echo "### ${dir}" >&2
    grep -E 'deploy_pip_failed|deploy_health_fail|Error|ERROR|Traceback|FAILED|Exception' "/tmp/utoo_unit_${dir}.log" 2>/dev/null | tail -n 50 >&2 || true
  done
  echo "deploy_units_parallel_failed dirs=${failed_dirs[*]}" >&2
  exit 1
fi
echo "deploy_units_parallel_ok"
