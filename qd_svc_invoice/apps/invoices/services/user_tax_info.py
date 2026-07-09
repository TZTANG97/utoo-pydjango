from typing import Any

from apps.invoices.services.tax_info_crud import get_default_invoice_info


def get_user_invoice_info(user_id: int) -> dict[str, Any]:
    return get_default_invoice_info(user_id)
