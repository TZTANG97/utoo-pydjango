from django.contrib import admin
from django.urls import include, path, re_path

from apps.core import views as core_views
from apps.core.svc_proxy import (
    svc_entry_enabled,
    svc_invoice_enabled,
    svc_order_enabled,
    svc_payment_enabled,
    svc_wx_enabled,
)


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
        ]
    return [
        path("api/ordersampleinfomation/", include("apps.orders.sample_urls")),
        path("api/sampleAttributeManage/", include("apps.orders.sample_attr_urls")),
        path("api/retestapplication/", include("apps.orders.retest_urls")),
    ]


def _wx_patterns():
    if svc_wx_enabled():
        from apps.core.wx_forward import proxy_wx_request

        return [
            re_path(
                r"^api/wx/(?P<subpath>.+)$",
                proxy_wx_request,
            ),
        ]
    return [
        path("api/wx/", include("apps.wx.urls")),
    ]


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


def _experiment_order_patterns():
    if svc_order_enabled():
        from apps.core.order_forward import proxy_order_request

        return [
            re_path(
                r"^api/experimentOrder/(?P<subpath>.+)$",
                proxy_order_request,
            ),
            re_path(
                r"^api/experimentChildOrder/(?P<subpath>.+)$",
                proxy_order_request,
            ),
        ]
    return [
        path("api/experimentOrder/", include("apps.orders.urls")),
        path("api/experimentChildOrder/", include("apps.orders.child_urls")),
    ]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.root),
    path("health", core_views.health),
    path("health/", core_views.health),
    path("api/", include("apps.core.urls")),
    path("api/auth/", include("apps.auth_pc.urls")),
    path("api/pc/", include("apps.pc_compat.urls")),
    *_invoice_patterns(),
    *_entry_patterns(),
    *_wx_patterns(),
    *_experiment_order_patterns(),
    *_order_extra_patterns(),
    *_payment_extra_patterns(),
    *_consult_patterns(),
    *_seller_patterns(),
]
