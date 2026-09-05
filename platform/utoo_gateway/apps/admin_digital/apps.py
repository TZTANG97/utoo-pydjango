"""DEPRECATED (2026-09-05): biz 开仍装（GW-LOCAL expOrderList/celery）；不挂 _internal。见 DEPRECATED.md。"""
from django.apps import AppConfig


class AdminDigitalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_digital"
    verbose_name = "Admin Digital Center [DEPRECATED twin; GW-LOCAL kept]"
