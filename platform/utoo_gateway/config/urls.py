from django.contrib import admin
from django.urls import include, path, re_path

from apps.admin_auth import views as admin_auth_views
from apps.core import views as core_views
from apps.core.svc_proxy import (
    gateway_twin_public_enabled,
    svc_admin_asset_enabled,
    svc_order_enabled,
    svc_payment_enabled,
    svc_utoo_biz_enabled,
    svc_wx_enabled,
)
from apps.wx_mp import views_index as wx_index_views

from shared.utoo_admin_routes import ASSET_PREFIXES, VUE_BIZ_EXACT
from shared.utoo_experiment_routes import EXPERIMENT_ORDER_PREFIXES


# 阶段 A：实验订单主链 → utoo_biz（业务）→ platform/order（中台）
_UTOO_BIZ_ORDER_PREFIXES = EXPERIMENT_ORDER_PREFIXES


def _utoo_biz_order_patterns():
    if not svc_utoo_biz_enabled():
        return []
    from apps.core.utoo_biz_forward import proxy_utoo_biz_request

    patterns = []
    for prefix in _UTOO_BIZ_ORDER_PREFIXES:
        patterns.append(
            re_path(
                rf"^api/{prefix}/(?P<subpath>.+)$",
                proxy_utoo_biz_request,
            )
        )
    return patterns


# 阶段 B：C 端 / 登录 / 小程序 → utoo_biz
_UTOO_BIZ_CONSUMER_PREFIXES = (
    "pc",
    "auth",
    "wx",
    "consult",
)


def _utoo_biz_consumer_patterns():
    if not svc_utoo_biz_enabled():
        return []
    from apps.core.utoo_biz_forward import proxy_utoo_biz_request

    patterns = []
    for prefix in _UTOO_BIZ_CONSUMER_PREFIXES:
        patterns.append(
            re_path(
                rf"^api/{prefix}/(?P<subpath>.+)$",
                proxy_utoo_biz_request,
            )
        )
    patterns.append(path("api/index/userRoles.ajax", proxy_utoo_biz_request))
    return patterns


def _internal_fallback_patterns():
    """网关 `_internal` twin 挂载（P3 瘦身）。

    - **biz 开启**：仅 `api/_internal/wx/` → stubs-only（`_WX_STUBS`；活跃路径已 MID/BIZ_LOCAL）。
      与 `config.twin_install` / INSTALLED_APPS 一致：不挂 digital/inventory/fund/pc；
      `admin_inventory`/`admin_fund` 亦不进 INSTALLED_APPS。
    - **未开 biz**：保留完整应急挂载（整包 wx_mp.urls + twin 包），便于本地无 biz 开发。
    本批条件卸载 INSTALLED_APPS，不删 apps 代码本体。
    """
    if svc_utoo_biz_enabled():
        return [
            path("api/_internal/wx/", include("apps.wx_mp.urls_internal_stubs")),
        ]
    from apps.orders import consult_urls as orders_consult_urls

    return [
        path("api/_internal/pc/", include("apps.pc_compat.urls")),
        path("api/_internal/wx/", include("apps.wx_mp.urls")),
        path("api/_internal/auth/", include("apps.auth_pc.urls")),
        path("api/_internal/consult/", include(orders_consult_urls)),
        path("api/_internal/index/userRoles.ajax", wx_index_views.user_roles),
        path("api/_internal/vue/", include("apps.admin_auth.urls_vue_biz")),
        path("api/_internal/", include("apps.admin_digital.urls")),
        path("api/_internal/", include("apps.admin_inventory.urls")),
        path("api/_internal/", include("apps.admin_fund.urls")),
    ]


def _utoo_biz_admin_patterns():
    """阶段 C：welcome / billing / asset 资金·数字化 → utoo_biz。"""
    if not svc_utoo_biz_enabled():
        return []
    from apps.core.utoo_biz_forward import proxy_utoo_biz_request

    patterns = []
    for exact in VUE_BIZ_EXACT:
        patterns.append(path(f"api/vue/{exact}", proxy_utoo_biz_request))
    for prefix in ASSET_PREFIXES:
        if "/" in prefix or prefix.endswith(".ajax"):
            patterns.append(path(f"api/{prefix}", proxy_utoo_biz_request))
        else:
            patterns.append(
                re_path(
                    rf"^api/{prefix}/(?P<subpath>.+)$",
                    proxy_utoo_biz_request,
                )
            )
            patterns.append(path(f"api/{prefix}/", proxy_utoo_biz_request))
    return patterns


def _invoice_patterns():
    """Platform 域：永不 twin；缺 SVC_INVOICE/PLATFORM → proxy 503。"""
    from apps.core.invoice_forward import proxy_invoice_request

    return [
        re_path(
            r"^api/invoice/(?P<subpath>.+)$",
            proxy_invoice_request,
        ),
    ]


def _entry_patterns():
    """Platform 域：永不 twin；缺 SVC_ENTRY/PLATFORM → proxy 503。"""
    from apps.core.entry_forward import proxy_entry_request

    return [
        re_path(
            r"^api/entry/(?P<subpath>.+)$",
            proxy_entry_request,
        ),
    ]


def _order_extra_patterns():
    if svc_utoo_biz_enabled():
        if svc_order_enabled():
            from apps.core.order_forward import proxy_order_request

            # IOT 回调仍直转 order 中台（HMAC 验签 + 状态机）
            return [
                re_path(
                    r"^api/iot/(?P<subpath>.+)$",
                    proxy_order_request,
                ),
            ]
        return []
    if svc_order_enabled():
        from apps.core.order_forward import proxy_order_request

        return [
            re_path(
                r"^api/ordersampleinfomation/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/sampleAttributeManage/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/retestapplication/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/adminExperiment/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/experimentManage/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/experimentProject/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/experimentGoods/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/iot/(?P<subpath>.+)$",
                proxy_order_request,
            ),
        ]
    if not gateway_twin_public_enabled():
        return []
    return [
        path("api/ordersampleinfomation/", include("apps.orders.sample_urls")),
        path("api/sampleAttributeManage/", include("apps.orders.sample_attr_urls")),
        path("api/retestapplication/", include("apps.orders.retest_urls")),
        path("api/", include("apps.admin_experiment.urls")),
        path("api/", include("apps.admin_experiment.mp_catalog_urls")),
    ]


# 可转发到 payment 的扫码/预约/反馈接口；wechatconfig 始终网关本地（需纯文本/XML）
_WX_PROXY_EXACT = (
    "WeChatQRCodeGenerator.ajax",
    "qrScanStatusCheck.ajax",
    "reservationDetail.ajax",
    "addFeedBack.ajax",
)


def _wx_gateway_local_patterns():
    """wechatconfig / payment 扫码：必须在 utoo_biz consumer 之前匹配。"""
    from apps.wx.views import wechatconfig

    patterns = [path("api/wx/wechatconfig.ajax", wechatconfig)]
    if svc_wx_enabled():
        from apps.core.wx_forward import proxy_wx_request

        for exact in _WX_PROXY_EXACT:
            patterns.append(path(f"api/wx/{exact}", proxy_wx_request))
    else:
        if gateway_twin_public_enabled():
            patterns.append(path("api/wx/", include("apps.wx.urls")))
    return patterns


def _wx_patterns():
    patterns = []
    # 小程序登录 / 业务别名：未启用 utoo_biz 时挂网关本地
    if not svc_utoo_biz_enabled():
        patterns.append(path("api/wx/", include("apps.wx_mp.urls")))
    return patterns


def _payment_extra_patterns():
    if svc_payment_enabled():
        from apps.core.payment_forward import proxy_payment_request

        return [
            re_path(
                r"^api/paymentapply/(?P<subpath>.+)$",
                proxy_payment_request,
            ),
            re_path(
                r"^api/offlineRecharge/(?P<subpath>.+)$",
                proxy_payment_request,
            ),
            # redeem：勿整段代理。payment 服务尚未同步 userredeemloglist 等路由会
            # 返回 HTML 404 → 网关变成 502；本地 urls_redeem 内已有 forward_payment_first。
            path("api/redeem/", include("apps.payments.urls_redeem")),
        ]
    if not gateway_twin_public_enabled():
        return []
    return [
        path("api/paymentapply/", include("apps.payments.urls_compat")),
        path("api/offlineRecharge/", include("apps.payments.urls_offline")),
        path("api/redeem/", include("apps.payments.urls_redeem")),
    ]


def _consult_patterns():
    """未走 utoo_biz 时：C 端 isServiceConsult → order；后台 list 由 platform 精确路径覆盖。"""
    if svc_utoo_biz_enabled():
        # 由 consumer 前缀进 biz；shared/utoo_consumer_routes 已指向 order/platform
        return []
    if svc_order_enabled():
        from apps.core.order_forward import proxy_order_request

        return [
            re_path(
                r"^api/consult/(?P<subpath>.+)$",
                proxy_order_request,
            ),
        ]
    if not gateway_twin_public_enabled():
        return []
    return [
        path("api/consult/", include("apps.orders.consult_urls")),
    ]


def _seller_patterns():
    from apps.pc_compat import views_seller

    return [
        path("api/seller/swf_upload.ajax", views_seller.swf_upload),
    ]


# 后台 Asset：数字化 / 库存 / 资金（SVC_ADMIN_ASSET_URL → :18090；前缀表见 shared/utoo_admin_routes.py）


def _admin_asset_patterns():
    if svc_utoo_biz_enabled():
        return []
    if svc_admin_asset_enabled():
        from apps.core.admin_asset_forward import proxy_admin_asset_request

        patterns = []
        for prefix in ASSET_PREFIXES:
            if "/" in prefix or prefix.endswith(".ajax"):
                patterns.append(path(f"api/{prefix}", proxy_admin_asset_request))
            else:
                patterns.append(
                    re_path(
                        rf"^api/{prefix}/(?P<subpath>.+)$",
                        proxy_admin_asset_request,
                    )
                )
                patterns.append(path(f"api/{prefix}/", proxy_admin_asset_request))
        return patterns
    if not gateway_twin_public_enabled():
        return []
    return [
        path("api/", include("apps.admin_digital.urls")),
        path("api/", include("apps.admin_inventory.urls")),
        path("api/", include("apps.admin_fund.urls")),
    ]


# 后台 Platform：系统/会员/运营/服务/订单设置（SVC_ADMIN_PLATFORM_URL → :18091）
# 注意：勿把与 C 端共用的 experimentOrder/consult 整段抢走；用精确路径转发后台专用接口
_ADMIN_PLATFORM_PREFIXES = (
    "sys",
    "district",
    "userCompany",
    "supplier",
    "appUser",
    "testaddress",
    "companyaccount",
    "member",
    "memberAccount",
    "companyinvoicelog",
    "userinvoicelog",
    "payLog",
    "applyVip",
    "integral",
    "banner",
    "edit",
    "whitelist",
    "goods",
    "goodspec",
    "goodsbrand",
    "goodstype",
    "goodsclass",
    "album",
    "evaluate",
    "apply",
    "records",
    "productOrder",
    "expOpenid",
    "caliOrder",
    "taxesConfig",
    "consumePaytype",
    "billtype",
    "orderType",
    # admin / offlineRecharge / redeem / seller：与登录或 C 端冲突，见 EXACT
)

_ADMIN_PLATFORM_EXACT = (
    "entry/entryList.ajax",
    "entry/entryDetail.ajax",
    "entry/auditEntry.ajax",
    "entry/commentList.ajax",
    "entry/commentDetail.ajax",
    "entry/auditComment.ajax",
    "entry/deletecomment.ajax",
    "consult/list.ajax",
    "consult/consultDetail.ajax",
    "consult/consultDetailxq.ajax",
    "consult/cancelConsult.ajax",
    "consult/updateConsult.ajax",
    "consult/saveOrder.ajax",
    "consult/querySampleList.ajax",
    "consult/settingGet.ajax",
    "consult/settingSave.ajax",
    "consult/isshowGet.ajax",
    "consult/isshowSave.ajax",
    "consult/consultConfigGet.ajax",
    "consult/consultConfigSave.ajax",
    "experimentOrder/evaluate_list_dpt.ajax",
    "experimentSubOrder/sublist_dpt.ajax",
    "offlineRecharge/offRechargeList.ajax",
    "offlineRecharge/rechargeDetail.ajax",
    "offlineRecharge/userList.ajax",
    "offlineRecharge/recharge_add.ajax",
    "redeem/redeemloglist.ajax",
    "redeem/redeemGoodsLogDetail.ajax",
    "redeem/shipment.ajax",
    "admin/advert_list.ajax",
    "admin/advert_detail.ajax",
    "admin/advert_save.ajax",
    "admin/advert_del.ajax",
    "admin/adv_pos_list.ajax",
    "admin/adv_pos_detail.ajax",
    "admin/adv_pos_save.ajax",
    "admin/adv_pos_del.ajax",
    "admin/adv_pos_options.ajax",
    # 勿整段代理 seller/（C 端 swf_upload 仍 GW-LOCAL）
    "seller/goods_img_album.ajax",
)


def _admin_platform_patterns():
    """Platform 路由组永不 twin：始终挂 proxy；缺 SVC_ADMIN_PLATFORM_URL → 503。"""
    from apps.core.admin_platform_forward import proxy_admin_platform_request

    patterns = []
    for exact in _ADMIN_PLATFORM_EXACT:
        patterns.append(path(f"api/{exact}", proxy_admin_platform_request))
    for prefix in _ADMIN_PLATFORM_PREFIXES:
        patterns.append(
            re_path(
                rf"^api/{prefix}/(?P<subpath>.+)$",
                proxy_admin_platform_request,
            )
        )
        patterns.append(path(f"api/{prefix}/", proxy_admin_platform_request))
    return patterns


def _experiment_order_patterns():
    if svc_utoo_biz_enabled():
        return []
    if svc_order_enabled():
        from apps.core.order_forward import proxy_order_request

        return [
            re_path(
                r"^api/experimentOrder/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/experimentSubOrder/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/experimentChildOrder/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/expSubPurchaseOrder/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/saleOrder/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/bill/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/eveluateCompany/(?P<subpath>.+)$",
                proxy_order_request,
            ),
        ]
    if not gateway_twin_public_enabled():
        return []
    return [
        path("api/experimentOrder/", include("apps.orders.urls")),
        path("api/experimentSubOrder/", include("apps.orders.sub_urls")),
        path("api/experimentChildOrder/", include("apps.orders.child_urls")),
        path("api/expSubPurchaseOrder/", include("apps.orders.child_urls")),
        path("api/saleOrder/", include("apps.orders.sale_urls")),
        path("api/bill/", include("apps.orders.bill_urls")),
        path("api/eveluateCompany/", include("apps.orders.eveluate_urls")),
    ]


def _lab_sale_perf_local_patterns():
    """销售绩效订单明细：始终挂网关本地，且排在 Asset 前缀代理之前。"""
    from apps.admin_digital.views import digital as digital_views

    return [
        path(
            "api/labPerformanceSaleuser/expOrderList.ajax",
            digital_views.lab_sale_order_list,
        ),
        # 非 Asset 前缀，避免旧网关/代理误转发
        path(
            "api/adminLabSale/expOrderList.ajax",
            digital_views.lab_sale_order_list,
        ),
    ]


def _identity_mid_patterns():
    """青岛 IDENTITY_MID_SERVICE_URL 与订单共用公网 VIP；仅白名单路径转发中台。"""
    from apps.core.identity_forward import proxy_identity_request

    return [
        re_path(
            r"^api/v1/identity/(?P<subpath>.+)$",
            proxy_identity_request,
        ),
    ]


def _public_consumer_patterns():
    if svc_utoo_biz_enabled() or not gateway_twin_public_enabled():
        return []
    return [
        path("api/auth/", include("apps.auth_pc.urls")),
        path("api/pc/", include("apps.pc_compat.urls")),
    ]


def _public_vue_patterns():
    """启用 utoo_biz 时：登录/菜单/me/开票付款复测留网关 BFF；welcome 走 biz。"""
    from apps.admin_auth import views as vue_views
    from apps.admin_auth import views_billing as billing_views

    if svc_utoo_biz_enabled() or not gateway_twin_public_enabled():
        return [
            path("api/vue/userLogin.ajax", vue_views.user_login),
            path("api/vue/getEncryption.ajax", vue_views.get_encryption),
            path("api/vue/main.ajax", vue_views.main),
            path("api/vue/usercenter.ajax", vue_views.usercenter),
            path("api/vue/sysLogs.ajax", vue_views.sys_logs),
            # 开票/付款/复测：网关 BFF 直挂（不再经 biz→_internal）
            path("api/vue/invoice/listPage.ajax", billing_views.invoice_list_page),
            path("api/vue/invoice/invoiceDetail.ajax", billing_views.invoice_detail),
            path("api/vue/invoice/bohuiInvoice.ajax", billing_views.invoice_reject),
            path("api/vue/invoice/openPreview.ajax", billing_views.invoice_open_preview),
            path("api/vue/invoice/agreeInvoice.ajax", billing_views.invoice_agree),
            path("api/vue/bill/addBillDataInvoice.ajax", billing_views.invoice_agree),
            path("api/vue/payLog/payList.ajax", billing_views.pay_log_list),
            path("api/vue/paymentapply/applylist.ajax", billing_views.payment_apply_list),
            path("api/vue/paymentapply/applyDetail.ajax", billing_views.payment_apply_detail),
            path("api/vue/bill/agreepayment.ajax", billing_views.payment_apply_agree),
            path("api/vue/bill/refusepayment.ajax", billing_views.payment_apply_refuse),
            path("api/vue/retestapplication/list.ajax", billing_views.retest_list),
            path("api/vue/retestapplication/retestDetail.ajax", billing_views.retest_detail),
            path("api/vue/retestapplication/agreeretestapplication.ajax", billing_views.retest_agree),
            path("api/vue/retestapplication/refusetestapplication.ajax", billing_views.retest_refuse),
        ]
    return [path("api/vue/", include("apps.admin_auth.urls_vue"))]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.root),
    path("health", core_views.health),
    path("health/", core_views.health),
    *_identity_mid_patterns(),
    path("api/", include("apps.core.urls")),
    *_public_consumer_patterns(),
    *_public_vue_patterns(),
    # 仅精确挂登录，避免 path(api/admin/) 吞掉运营广告等 Platform 路由
    path("api/admin/userLogin.ajax", admin_auth_views.user_login),
    path("api/admin/getEncryption.ajax", admin_auth_views.get_encryption),
    *_internal_fallback_patterns(),
    *_wx_gateway_local_patterns(),
    *_utoo_biz_consumer_patterns(),
    *_utoo_biz_order_patterns(),
    *_lab_sale_perf_local_patterns(),
    *_utoo_biz_admin_patterns(),
    *_admin_asset_patterns(),
    *_admin_platform_patterns(),
    *_invoice_patterns(),
    *_entry_patterns(),
    *_wx_patterns(),
    *_experiment_order_patterns(),
    *_order_extra_patterns(),
    *_payment_extra_patterns(),
    *_consult_patterns(),
    *_seller_patterns(),
]
