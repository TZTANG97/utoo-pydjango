from datetime import date, datetime
from decimal import Decimal
from typing import Any


def to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def row_to_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "_mapping"):
        return {k: to_jsonable(v) for k, v in row._mapping.items()}
    if isinstance(row, dict):
        return {k: to_jsonable(v) for k, v in row.items()}
    return {k: to_jsonable(v) for k, v in dict(row).items()}
