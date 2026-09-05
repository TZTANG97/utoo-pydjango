"""DEPRECATED (2026-09-05): biz 开时不进 INSTALLED_APPS、不挂 _internal；正式流量 mid/utoo_biz。见 DEPRECATED.md / docs/utoo-route-inventory.md。"""
from django.apps import AppConfig


class AdminInventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_inventory"
    verbose_name = "Admin Inventory [DEPRECATED twin; biz-off only]"
