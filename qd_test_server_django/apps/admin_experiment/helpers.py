from __future__ import annotations

from typing import Any

from rest_framework.request import Request

from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.helpers import page_clause
from apps.admin_system.views.common import merge_payload


def to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "merge_payload",
    "parse_datatable_params",
    "datatable_payload",
    "page_clause",
    "to_int",
]
