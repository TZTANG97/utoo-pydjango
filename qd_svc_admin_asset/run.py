"""qd_svc_admin_asset 开发启动 — 默认 0.0.0.0:18090"""
import os

import pymysql

pymysql.install_as_MySQLdb()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

if __name__ == "__main__":
    from django.conf import settings
    from django.core.management import execute_from_command_line

    args = ["manage.py", "runserver", f"{settings.SERVER_HOST}:{settings.SERVER_PORT_HTTP}"]
    if not settings.DEBUG_RELOAD:
        args.append("--noreload")
    execute_from_command_line(args)
