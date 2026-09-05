"""DEPRECATED (2026-09-05): biz 开仍装（GW-LOCAL seller）；不挂 _internal/pc。见 DEPRECATED.md。"""
from django.apps import AppConfig


class PcCompatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pc_compat"
    verbose_name = "PC .ajax 兼容 [DEPRECATED twin; GW-LOCAL seller kept]"
