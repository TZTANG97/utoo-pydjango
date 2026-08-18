from datetime import timedelta

from django.test import override_settings
from django.utils import timezone

from apps.identity.services.login import _lock_message, _resolve_user_type


def test_resolve_user_type():
    assert _resolve_user_type({"account_type": 1}) == 3
    assert _resolve_user_type({}) == 0


@override_settings(LOGIN_MAX_FAILURES=5, LOGIN_LOCK_MINUTES=30)
def test_lock_message_within_window():
    msg = _lock_message(
        {
            "error_count": 5,
            "error_time": timezone.now() - timedelta(minutes=5),
        }
    )
    assert msg and "锁定" in msg


@override_settings(LOGIN_MAX_FAILURES=5, LOGIN_LOCK_MINUTES=30)
def test_lock_message_below_threshold():
    assert _lock_message({"error_count": 2, "error_time": timezone.now()}) is None
