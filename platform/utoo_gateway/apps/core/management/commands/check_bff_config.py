from django.core.management.base import BaseCommand

from apps.core.svc_proxy import (
    bff_services_configured,
    gateway_bff_only_enabled,
    gateway_enforce_mid_config,
    gateway_production_env,
    validate_bff_gateway_config,
)


class Command(BaseCommand):
    help = "校验愉兔网关生产/BFF-only 启动门禁所需 SVC_* / UTOO_BIZ 环境变量（P3）"

    def handle(self, *args, **options):
        if not gateway_enforce_mid_config():
            self.stdout.write(
                self.style.WARNING(
                    "未启用生产门禁（APP_ENV≠production 且未开 "
                    "UTOO_GATEWAY_BFF_ONLY/GATEWAY_BFF_ONLY），跳过校验"
                )
            )
            return

        missing = validate_bff_gateway_config(raise_error=False)
        if missing:
            mode = []
            if gateway_production_env():
                mode.append("production")
            if gateway_bff_only_enabled():
                mode.append("BFF-only")
            self.stderr.write(
                self.style.ERROR(
                    f"启动门禁（{'+'.join(mode)}）配置不完整，缺少: "
                    + ", ".join(missing)
                )
            )
            raise SystemExit(1)

        ok, _ = bff_services_configured()
        if ok:
            self.stdout.write(self.style.SUCCESS("网关启动门禁配置完整（公开 twin 已禁用）"))
        else:
            raise SystemExit(1)
