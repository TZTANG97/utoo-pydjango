"""
开发启动（对齐 FastAPI：默认 0.0.0.0:18083，前端 VITE_API_TARGET 可不变）
"""
import os
import sys

import pymysql

pymysql.install_as_MySQLdb()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

if __name__ == "__main__":
    from django.conf import settings
    from django.core.management import execute_from_command_line

    host = settings.SERVER_HOST
    port = settings.SERVER_PORT_HTTP
    execute_from_command_line(
        ["manage.py", "runserver", f"{host}:{port}", "--noreload"]
        if not settings.DEBUG_RELOAD
        else ["manage.py", "runserver", f"{host}:{port}"]
    )
