from django.apps import AppConfig


class AdminCoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_core"
    verbose_name = "管理端基础"
