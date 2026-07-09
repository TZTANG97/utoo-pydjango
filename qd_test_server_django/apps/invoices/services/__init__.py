from apps.invoices.services.apply import apply_invoice
from apps.invoices.services.billable_orders import count_billable_orders, list_billable_orders
from apps.invoices.services.cancel_apply import cancel_invoice_apply
from apps.invoices.services.detail import get_invoice_apply_detail
from apps.invoices.services.list_service import get_invoice_list_page
from apps.invoices.services.log_list import get_invoice_log_list_page
from apps.invoices.services.summary import stay_apply_money
from apps.invoices.services.tax_info_crud import (
    delete_or_set_default_invoice,
    insert_invoice_info,
    list_invoice_infos,
    update_invoice_info,
    upsert_legacy_invoice_info,
)
from apps.invoices.services.user_tax_info import get_user_invoice_info


class InvoiceService:
    get_invoice_list_page = staticmethod(get_invoice_list_page)
    stay_apply_money = staticmethod(stay_apply_money)
    count_billable_orders = staticmethod(count_billable_orders)
    list_billable_orders = staticmethod(list_billable_orders)
    apply_invoice = staticmethod(apply_invoice)
    get_invoice_log_list_page = staticmethod(get_invoice_log_list_page)
    cancel_invoice_apply = staticmethod(cancel_invoice_apply)
    get_invoice_apply_detail = staticmethod(get_invoice_apply_detail)
    get_user_invoice_info = staticmethod(get_user_invoice_info)
    list_invoice_infos = staticmethod(list_invoice_infos)
    insert_invoice_info = staticmethod(insert_invoice_info)
    update_invoice_info = staticmethod(update_invoice_info)
    delete_or_set_default_invoice = staticmethod(delete_or_set_default_invoice)
    upsert_legacy_invoice_info = staticmethod(upsert_legacy_invoice_info)
