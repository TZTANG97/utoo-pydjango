from django.apps import AppConfig


class UtooAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.utoo_admin"
    label = "utoo_admin"

    def ready(self) -> None:
        # P3：生产缺关键 mid URL 拒绝启动（与网关门禁对齐）
        import os

        env = (os.getenv("APP_ENV") or "").strip().lower()
        if env not in ("production", "prod"):
            return
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured

        required = (
            "UTOO_IDENTITY_MID_SERVICE_URL",
            "UTOO_ORDER_MID_SERVICE_URL",
            "UTOO_PAYMENT_MID_SERVICE_URL",
            "UTOO_ASSET_MID_SERVICE_URL",
            "UTOO_PLATFORM_MID_SERVICE_URL",
        )
        missing = [
            key
            for key in required
            if not (getattr(settings, key, "") or "").strip()
        ]
        if missing:
            raise ImproperlyConfigured(
                "utoo_biz 生产启动门禁缺少 mid URL："
                + ", ".join(missing)
                + "（可设 UTOO_*_MID_SERVICE_URL 或对应 SVC_*_URL）"
            )
