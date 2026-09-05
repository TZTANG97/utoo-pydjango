"""P3：biz 开时 INSTALLED_APPS 不含纯应急 twin 包。"""
from __future__ import annotations

from django.conf import settings


def test_twin_apps_for_installed_biz_on_excludes_emergency():
    from config.twin_install import (
        TWIN_EMERGENCY_ONLY_APPS,
        TWIN_GW_LOCAL_APPS,
        twin_apps_for_installed,
    )

    apps = twin_apps_for_installed(biz_enabled=True)
    assert "apps.admin_fund" not in apps
    assert "apps.admin_inventory" not in apps
    for name in TWIN_EMERGENCY_ONLY_APPS:
        assert name not in apps
    for name in TWIN_GW_LOCAL_APPS:
        assert name in apps


def test_twin_apps_for_installed_biz_off_includes_all():
    from config.twin_install import TWIN_ALL_CANDIDATE_APPS, twin_apps_for_installed

    apps = twin_apps_for_installed(biz_enabled=False)
    assert set(apps) == set(TWIN_ALL_CANDIDATE_APPS)


def test_live_installed_apps_match_startup_biz_flag():
    """运行中 INSTALLED_APPS 须与启动时 UTOO_BIZ_SERVICE_URL 判据一致。"""
    from config.twin_install import TWIN_EMERGENCY_ONLY_APPS, twin_apps_for_installed

    biz = bool((getattr(settings, "UTOO_BIZ_SERVICE_URL", "") or "").strip())
    expected = twin_apps_for_installed(biz_enabled=biz)
    for name in expected:
        assert name in settings.INSTALLED_APPS
    if biz:
        for name in TWIN_EMERGENCY_ONLY_APPS:
            assert name not in settings.INSTALLED_APPS
        assert "apps.admin_fund" not in settings.INSTALLED_APPS
        assert "apps.admin_inventory" not in settings.INSTALLED_APPS
