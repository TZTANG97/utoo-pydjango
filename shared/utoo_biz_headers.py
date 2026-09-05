"""utoo_biz → platform/order 内部头（阶段 A：scope / 审核前置）。"""
from __future__ import annotations

import base64
import json
from typing import Any

LIST_SCOPE_HEADER = "X-Utoo-List-Scope"
AUDIT_VALIDATED_HEADER = "X-Utoo-Audit-Validated"


def encode_list_scope(scope: dict[str, Any]) -> str:
    raw = json.dumps(scope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_list_scope(header: str | None) -> dict[str, Any] | None:
    if not header:
        return None
    try:
        data = base64.urlsafe_b64decode(header.encode("ascii"))
        obj = json.loads(data.decode("utf-8"))
        return obj if isinstance(obj, dict) else None
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def audit_validated(header: str | None) -> bool:
    return (header or "").strip() == "1"
