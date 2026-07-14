from django.urls import path

from apps.pc_invoice import views_invoice

urlpatterns = [
    path("center/getInvoiceList.ajax", views_invoice.get_invoice_list),
    path("center/getInvoiceOrderList.ajax", views_invoice.get_invoice_order_list),
    path("center/applyInvoice.ajax", views_invoice.apply_invoice),
    path("center/getInvoiceLogList.ajax", views_invoice.get_invoice_log_list),
    path("center/getInvoiceInfo.ajax", views_invoice.get_invoice_info),
    path("getinvoiceInfo.ajax", views_invoice.get_invoice_info_list),
    path("insertinvoiceInfo.ajax", views_invoice.insert_invoice_info),
    path("updateinvoiceInfo.ajax", views_invoice.update_invoice_info),
    path("delinvoiceInfo.ajax", views_invoice.del_invoice_info),
    path("addInvoiceInfo.ajax", views_invoice.add_invoice_info_legacy),
    path("cancelInvoiceInfo.ajax", views_invoice.cancel_invoice_info),
]
