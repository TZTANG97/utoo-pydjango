#!/usr/bin/env bash
# Windows Git Bash entry for GitLab Runner (shell=bash).
# Avoids WinPS 5.1 injecting CI_COMMIT_DESCRIPTION into a .ps1 (Chinese / <email> ParserError).
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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${WIN_ROOT}\\deploy\\utoo-windows\\ci-run-all.ps1"
exit $?
