#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${CI_PROJECT_DIR:-}" ]]; then
  echo "CI_PROJECT_DIR is empty" >&2
  exit 1
fi
cd "$CI_PROJECT_DIR"
if command -v cygpath >/dev/null 2>&1; then
  WIN_ROOT="$(cygpath -w "$CI_PROJECT_DIR")"
else
  WIN_ROOT="$CI_PROJECT_DIR"
fi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${WIN_ROOT}\\deploy\\utoo-windows\\ci-deploy-windows.ps1"
exit $?
