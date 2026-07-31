from django.contrib import admin
from django.urls import include, path, re_path

from apps.admin_auth import views as admin_auth_views
from apps.core import views as core_views
from apps.core.svc_proxy import (
    svc_admin_asset_enabled,
    svc_admin_platform_enabled,
    svc_entry_enabled,
    svc_invoice_enabled,
    svc_order_enabled,
    svc_payment_enabled,
    svc_wx_enabled,
)
from apps.wx_mp import views_index as wx_index_views


def _invoice_patterns():
    if svc_invoice_enabled():
        from apps.core.invoice_forward import proxy_invoice_request

        return [
            re_path(
                r"^api/invoice/(?P<subpath>.+)$",
                proxy_invoice_request,
            ),
        ]
    return [
        path("api/invoice/", include("apps.invoices.urls")),
    ]


def _entry_patterns():
    if svc_entry_enabled():
        from apps.core.entry_forward import proxy_entry_request

        return [
            re_path(
                r"^api/entry/(?P<subpath>.+)$",
                proxy_entry_request,
            ),
        ]
    return [
        path("api/entry/", include("apps.entry.urls")),
    ]


def _order_extra_patterns():
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
        ]
    return [
        path("api/ordersampleinfomation/", include("apps.orders.sample_urls")),
        path("api/sampleAttributeManage/", include("apps.orders.sample_attr_urls")),
        path("api/retestapplication/", include("apps.orders.retest_urls")),
        # 本地孪生：未配置 SVC_ORDER_URL 时由网关直连 DB 服务实验管理
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


def _wx_patterns():
    patterns = []
    # 公众号服务器回调必须本地处理（echostr/XML），与 payment 共用 Redis
    from apps.wx.views import wechatconfig

    patterns.append(path("api/wx/wechatconfig.ajax", wechatconfig))
    if svc_wx_enabled():
        from apps.core.wx_forward import proxy_wx_request

        for exact in _WX_PROXY_EXACT:
            patterns.append(path(f"api/wx/{exact}", proxy_wx_request))
    else:
        patterns.append(path("api/wx/", include("apps.wx.urls")))
    # 小程序登录 / 业务别名（始终本地，不被 SVC_WX_URL 整段代理）
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
            re_path(
                r"^api/redeem/(?P<subpath>.+)$",
                proxy_payment_request,
            ),
        ]
    return [
        path("api/paymentapply/", include("apps.payments.urls_compat")),
        path("api/offlineRecharge/", include("apps.payments.urls_offline")),
        path("api/redeem/", include("apps.payments.urls_redeem")),
    ]


def _consult_patterns():
    if svc_order_enabled():
        from apps.core.order_forward import proxy_order_request

        return [
            re_path(
                r"^api/consult/(?P<subpath>.+)$",
                proxy_order_request,
            ),
        ]
    return [
        path("api/consult/", include("apps.orders.consult_urls")),
    ]


def _seller_patterns():
    from apps.pc_compat import views_seller

    return [
        path("api/seller/swf_upload.ajax", views_seller.swf_upload),
    ]


# 后台 Asset：数字化 / 库存 / 资金（SVC_ADMIN_ASSET_URL → :18090）
_ADMIN_ASSET_PREFIXES = (
    "digital",
    "testUserStats",
    "testUserPerformance",
    "saleUserPerformance",
    "labPerformanceSaleuser",
    "labPerformance",
    "storeHouse",
    "samplestoreHouse",
    "sampleremainstoreHouse",
    "inventory",
    "lab",
    "inTreasury",
    "expLog",
    "inIncome",
    "funds",
    "companyPay",
    "userPay",
    "companyLoanPay",
    "projectPay",
    "digitalManage",
    "getLog.ajax",
    "getAccountLog.ajax",
    "selExpSumByYear.ajax",
    "selExpSumByYearxcx.ajax",
    "yesterdayIncome.ajax",
    "yesterdayIncomexcx.ajax",
    "account_User.ajax",
    "pass.ajax",
    "supplier/queryAllPay.ajax",
)


def _admin_asset_patterns():
    if svc_admin_asset_enabled():
        from apps.core.admin_asset_forward import proxy_admin_asset_request

        patterns = []
        for prefix in _ADMIN_ASSET_PREFIXES:
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
    # admin / offlineRecharge / redeem：与登录或 C 端 payment 冲突，见 EXACT
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
    "consult/cancelConsult.ajax",
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
)


def _admin_platform_patterns():
    if svc_admin_platform_enabled():
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
    return [
        path("api/", include("apps.admin_settings.urls")),
        path("api/", include("apps.admin_system.urls")),
        path("api/", include("apps.admin_service.urls")),
        path("api/", include("apps.admin_ops.urls")),
        path("api/", include("apps.admin_member.urls")),
    ]


def _experiment_order_patterns():
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


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.root),
    path("health", core_views.health),
    path("health/", core_views.health),
    path("api/", include("apps.core.urls")),
    path("api/auth/", include("apps.auth_pc.urls")),
    # 仅精确挂登录，避免 path(api/admin/) 吞掉运营广告等 Platform 路由
    path("api/admin/userLogin.ajax", admin_auth_views.user_login),
    path("api/admin/getEncryption.ajax", admin_auth_views.get_encryption),
    path("api/vue/", include("apps.admin_auth.urls_vue")),
    path("api/pc/", include("apps.pc_compat.urls")),
    # 小程序登录后拉取用户类型/权限 map（原 Java /index/userRoles.ajax）
    path("api/index/userRoles.ajax", wx_index_views.user_roles),
    *_lab_sale_perf_local_patterns(),
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
