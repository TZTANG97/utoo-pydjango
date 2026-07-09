from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from django.conf import settings

from apps.core import redis_client
from apps.payments.repositories import pay_info as pay_info_repo
from apps.payments.repositories import user_account as user_account_repo

logger = logging.getLogger(__name__)


def lock_pay_info_log_for_update(log_id: int) -> dict[str, Any] | None:
    return pay_info_repo.lock_pay_info_log_for_update(log_id)


def lock_user_account_for_update(user_id: int) -> dict[str, Any]:
    user_account_repo.get_or_create(user_id)
    return user_account_repo.lock_for_update(user_id)


@contextmanager
def pay_notify_redis_lock(out_trade_no: str) -> Iterator[None]:
    key = f"pay:lock:notify:{out_trade_no}"
    token = redis_client.try_acquire_lock(
        key, ttl_sec=settings.PAY_NOTIFY_LOCK_SECONDS
    )
    if token is None:
        logger.info("pay notify redis lock busy, rely on row lock: %s", out_trade_no)
    try:
        yield
    finally:
        if token:
            redis_client.release_lock(key, token)


@contextmanager
def user_pay_redis_lock(user_id: int) -> Iterator[bool]:
    key = f"pay:lock:user:{user_id}"
    token = redis_client.try_acquire_lock(key, ttl_sec=settings.PAY_USER_LOCK_SECONDS)
    if token is None:
        logger.warning("user pay lock busy: user_id=%s", user_id)
        yield False
        return
    try:
        yield True
    finally:
        redis_client.release_lock(key, token)
