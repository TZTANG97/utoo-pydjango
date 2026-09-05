"""utoo_consumer_routes：咨询试点不得回落 gateway twin。"""
from shared.utoo_consumer_routes import MidTarget, resolve_consumer_path


def test_consult_is_service_goes_to_order():
    d = resolve_consumer_path("/api/consult/isServiceConsult.ajax")
    assert d.target == MidTarget.ORDER
    assert d.path == "/api/consult/isServiceConsult.ajax"


def test_consult_admin_list_goes_to_platform():
    d = resolve_consumer_path("/api/consult/list.ajax")
    assert d.target == MidTarget.PLATFORM
    assert d.channel == "admin"


def test_pc_consult_add_still_order():
    d = resolve_consumer_path("/api/pc/serviceConsultAdd.ajax")
    assert d.target == MidTarget.ORDER


def test_welcome_in_vue_biz_exact_for_biz_local():
    from shared.utoo_admin_routes import AdminMidTarget, VUE_BIZ_EXACT, resolve_admin_path

    assert VUE_BIZ_EXACT == frozenset({"welcome.ajax"})
    d = resolve_admin_path("/api/vue/welcome.ajax")
    assert d.target == AdminMidTarget.BIZ_LOCAL
    assert d.path == "/api/vue/welcome.ajax"
    assert "/_internal/" not in d.path


def test_billing_not_routed_via_vue_biz_internal():
    from shared.utoo_admin_routes import VUE_BIZ_EXACT

    assert "invoice/listPage.ajax" not in VUE_BIZ_EXACT
    assert "paymentapply/applylist.ajax" not in VUE_BIZ_EXACT
    assert "retestapplication/list.ajax" not in VUE_BIZ_EXACT


def test_user_roles_is_biz_local_not_twin():
    d = resolve_consumer_path("/api/index/userRoles.ajax")
    assert d.target == MidTarget.BIZ_LOCAL


def test_internal_fallback_slim_when_biz_enabled():
    """biz 开时 _internal 只挂 wx stubs，不含 pc/digital 等应急 twin。"""
    import ast
    from pathlib import Path

    urls = (
        Path(__file__).resolve().parents[2]
        / "platform"
        / "utoo_gateway"
        / "config"
        / "urls.py"
    )
    tree = ast.parse(urls.read_text(encoding="utf-8"))
    fn = next(
        (
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "_internal_fallback_patterns"
        ),
        None,
    )
    assert fn is not None
    biz_if = None
    for node in fn.body:
        if isinstance(node, ast.If) and "svc_utoo_biz_enabled" in ast.unparse(node.test):
            biz_if = node
            break
    assert biz_if is not None, "_internal_fallback_patterns must branch on svc_utoo_biz_enabled"
    biz_on = ast.unparse(biz_if.body)
    assert "_internal/wx/" in biz_on
    assert "urls_internal_stubs" in biz_on
    assert 'include("apps.wx_mp.urls")' not in biz_on
    assert "include('apps.wx_mp.urls')" not in biz_on
    for forbidden in (
        "_internal/pc/",
        "_internal/auth/",
        "_internal/consult/",
        "userRoles",
        "urls_vue_biz",
        "admin_digital",
        "admin_inventory",
        "admin_fund",
    ):
        assert forbidden not in biz_on, f"biz-on _internal still mounts {forbidden}"
    # 未开 biz：函数其余部分仍保留完整应急挂载（整包 wx_mp.urls）
    rest = "\n".join(ast.unparse(n) for n in fn.body if n is not biz_if)
    assert "_internal/pc/" in rest
    assert "apps.wx_mp.urls" in rest
    assert "urls_internal_stubs" not in rest
    assert "admin_digital" in rest
    assert "admin_inventory" in rest
    assert "admin_fund" in rest


def test_wx_internal_stubs_only_has_wx_stubs():
    """stubs-only 模块只挂 _WX_STUBS，不含已 MID 路径 / wechatconfig。"""
    import re
    from pathlib import Path

    from shared.utoo_consumer_routes import _WX_MID, _WX_STUBS

    stubs_urls = (
        Path(__file__).resolve().parents[2]
        / "platform"
        / "utoo_gateway"
        / "apps"
        / "wx_mp"
        / "urls_internal_stubs.py"
    )
    text = stubs_urls.read_text(encoding="utf-8")
    mounted = set(re.findall(r'["\']([^"\']+\.ajax)["\']', text))
    assert mounted == set(_WX_STUBS)
    for mid_name in _WX_MID:
        assert mid_name not in mounted, f"stubs-only still mounts MID path {mid_name}"
    for forbidden in (
        "getUserInfo.ajax",
        "userInfoAdd.ajax",
        "ticketIsExist.ajax",
        "phoneCodeLogin.ajax",
        "getVerifyCodeLogin.ajax",
        "userLoginToken.ajax",
        "wechatconfig.ajax",
        "scanCodeOperate.ajax",
        "getOrderCount.ajax",
    ):
        assert forbidden not in mounted, f"stubs-only must not mount {forbidden}"


def test_add_cash_goes_to_payment():
    d = resolve_consumer_path("/api/pc/addCash.ajax")
    assert d.target == MidTarget.PAYMENT
    assert d.path == "/api/pc/addCash.ajax"
    wx = resolve_consumer_path("/api/wx/addCash.ajax")
    assert wx.target == MidTarget.PAYMENT


def test_set_password_and_register_go_to_identity():
    for path in (
        "/api/pc/setPassword.ajax",
        "/api/pc/register.ajax",
        "/api/pc/getVerifyCode.ajax",
        "/api/pc/getUserBasicInfo.ajax",
        "/api/pc/addOrUpdateUserData.ajax",
    ):
        d = resolve_consumer_path(path)
        assert d.target == MidTarget.IDENTITY, path
        assert d.path == path


def test_banner_cover_goes_to_order():
    for path in ("/api/pc/getXcxBanner.ajax", "/api/pc/getTuZheBanner.ajax"):
        d = resolve_consumer_path(path)
        assert d.target == MidTarget.ORDER, path
        assert d.path == path


def test_all_gateway_pc_mounts_are_mid_not_twin():
    """网关 pc_compat 挂载的全部 /api/pc/*.ajax 须进四白名单，禁止 BIZ→TWIN。"""
    import re
    from pathlib import Path

    from shared.utoo_consumer_routes import (
        _PC_IDENTITY,
        _PC_ORDER,
        _PC_PAYMENT,
        _PC_PLATFORM,
    )

    urls = Path(__file__).resolve().parents[2] / "platform/utoo_gateway/apps/pc_compat/urls.py"
    mounted = re.findall(r'path\(\s*"([^"]+\.ajax)"', urls.read_text(encoding="utf-8"))
    assert mounted, "pc_compat urls empty"
    wh = _PC_PAYMENT | _PC_PLATFORM | _PC_ORDER | _PC_IDENTITY
    twin = [p for p in mounted if p not in wh]
    assert twin == [], f"still BIZ→TWIN: {twin}"
    for sub in mounted:
        d = resolve_consumer_path(f"/api/pc/{sub}")
        assert d.target != MidTarget.GATEWAY_INTERNAL, sub
        assert d.path == f"/api/pc/{sub}", sub


def test_wx_login_and_profile_go_to_identity():
    for name in (
        "getVerifyCodeLogin.ajax",
        "userLoginToken.ajax",
        "phoneCodeLogin.ajax",
        "phoneOneLogin.ajax",
        "phoneOneLoginTZ.ajax",
        "getIdentifyData.ajax",
        "clearBindData.ajax",
        "myInfo.ajax",
        "getbindstatus.ajax",
        "checkLoginName.ajax",
        "updateNickName.ajax",
    ):
        path = f"/api/wx/{name}"
        d = resolve_consumer_path(path)
        assert d.target == MidTarget.IDENTITY, path
        assert d.path == path
        assert "/_internal/" not in d.path


def test_wx_catalog_order_count_scan_go_to_order():
    for name in (
        "TuZhebannerList.ajax",
        "selFirAndSecClassListTuZhe.ajax",
        "getOrderCount.ajax",
        "scanCodeOperate.ajax",
        "isFlag.ajax",
    ):
        path = f"/api/wx/{name}"
        d = resolve_consumer_path(path)
        assert d.target == MidTarget.ORDER, path
        assert d.path == path


def test_wx_qr_bind_goes_to_payment():
    for name in ("getUserInfo.ajax", "userInfoAdd.ajax", "ticketIsExist.ajax"):
        path = f"/api/wx/{name}"
        d = resolve_consumer_path(path)
        assert d.target == MidTarget.PAYMENT, name
        assert d.path == path
        assert "/_internal/" not in d.path


def test_wx_stubs_still_twin():
    from shared.utoo_consumer_routes import _WX_STUBS

    for name in ("getAuditOrderList.ajax", "bindaccount.ajax", "securebind.ajax"):
        assert name in _WX_STUBS
        d = resolve_consumer_path(f"/api/wx/{name}")
        assert d.target == MidTarget.GATEWAY_INTERNAL, name
        assert d.path.startswith("/api/_internal/wx/")


def test_wx_wechatconfig_stays_gateway_local_path():
    d = resolve_consumer_path("/api/wx/wechatconfig.ajax")
    assert d.target == MidTarget.GATEWAY_INTERNAL
    assert d.path == "/api/wx/wechatconfig.ajax"


def test_asset_prefix_never_silent_twin():
    """缺 asset 中台时路由仍指向 ASSET（由代理 503），禁止 `_internal` twin。"""
    from shared.utoo_admin_routes import AdminMidTarget, resolve_admin_path

    for path in (
        "/api/funds/list.ajax",
        "/api/digital/center.ajax",
        "/api/inventory/queryList.ajax",
    ):
        d = resolve_admin_path(path, asset_mid_configured=False)
        assert d.target == AdminMidTarget.ASSET, path
        assert "/_internal/" not in d.path
        d2 = resolve_admin_path(path, asset_mid_configured=True)
        assert d2.target == AdminMidTarget.ASSET
        assert d2.path == path


def test_experiment_main_chain_never_rewrites_internal():
    """实验主链薄透传：路径保持 /api/{prefix}/...，禁止改写 `_internal`。"""
    from shared.utoo_experiment_routes import EXPERIMENT_ORDER_PREFIXES, experiment_order_proxy_path

    assert len(EXPERIMENT_ORDER_PREFIXES) >= 11
    for prefix in EXPERIMENT_ORDER_PREFIXES:
        path = f"/api/{prefix}/list.ajax"
        assert experiment_order_proxy_path(path) == path
        assert "/_internal/" not in path
    assert experiment_order_proxy_path("/api/pc/addCash.ajax") is None


def test_order_mid_url_empty_without_explicit_config():
    """缺 UTOO_ORDER_* / SVC_ORDER_URL 时 base 为空（代理应 503），禁止默认 localhost。"""
    from shared.utoo_order_proxy import pick_order_mid_base_url

    assert pick_order_mid_base_url("", "", "") == ""
    assert pick_order_mid_base_url(None, "  ", "") == ""  # type: ignore[arg-type]
    assert pick_order_mid_base_url("", "http://127.0.0.1:18082/", "") == "http://127.0.0.1:18082"
    assert pick_order_mid_base_url("", "", "http://order:18082") == "http://order:18082"


def test_forward_first_modules_forbid_silent_twin():
    """方案 B V3：各 forward_*_first 源码不得在未配时 return view_func。"""
    import ast
    from pathlib import Path

    core = (
        Path(__file__).resolve().parents[2]
        / "platform"
        / "utoo_gateway"
        / "apps"
        / "core"
    )
    mods = (
        "identity_forward.py",
        "order_forward.py",
        "payment_forward.py",
        "invoice_forward.py",
        "entry_forward.py",
        "wx_forward.py",
        "admin_asset_forward.py",
        "admin_platform_forward.py",
    )
    for name in mods:
        src = (core / name).read_text(encoding="utf-8")
        tree = ast.parse(src)
        fn = next(
            (
                n
                for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name.endswith("_first")
            ),
            None,
        )
        assert fn is not None, name
        body = ast.unparse(fn)
        assert "view_func(" not in body, f"{name} still silent-twins via view_func"
        assert "mid_svc_unconfigured_response" in body
