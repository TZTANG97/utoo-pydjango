"""DEPRECATED (2026-09-05): biz 开时不进 INSTALLED_APPS、不挂 _internal；正式流量 mid/utoo_biz。见 DEPRECATED.md / docs/utoo-route-inventory.md。"""
from django.apps import AppConfig


class AdminFundConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_fund"
    verbose_name = "Admin Fund [DEPRECATED twin; biz-off only]"
