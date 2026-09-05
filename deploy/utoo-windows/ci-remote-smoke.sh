#!/usr/bin/env bash
# Placeholders __ROOT__ __SVC_DIR__ replaced by deploy script.
set -euo pipefail
cd "__ROOT__/__SVC_DIR__"
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="__ROOT__:__ROOT__/platform/qd_libs_common:${PYTHONPATH:-}"
.venv/bin/python manage.py check
if [ "__SVC_DIR__" = "platform/utoo_gateway" ]; then
  .venv/bin/python manage.py check_bff_config || true
fi
echo deploy_django_check_ok:__SVC_DIR__
