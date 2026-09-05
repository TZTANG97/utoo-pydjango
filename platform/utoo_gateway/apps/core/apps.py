from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "核心"

    def ready(self) -> None:
        from apps.core.svc_proxy import validate_bff_gateway_config

        validate_bff_gateway_config(raise_error=True)
