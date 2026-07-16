#!/usr/bin/env bash
# Placeholders __ROOT__ __SVC_DIR__ replaced by deploy script before remote exec.
set -euo pipefail
cd "__ROOT__/__SVC_DIR__"
export DJANGO_SETTINGS_MODULE=config.settings
.venv/bin/python manage.py check
echo deploy_django_check_ok:__SVC_DIR__
