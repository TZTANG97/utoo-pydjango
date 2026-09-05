"""
pytest 配置。

联调测试（打真实业务库）请用 live_client，不要用 @pytest.mark.django_db。
django_db 会触发 setup_databases → 对 TEST 库执行 CREATE/DROP，误配 NAME 会删业务库。
"""

import pytest


@pytest.fixture
def live_client(django_db_blocker):
    """只读/联调：复用 settings 中的业务库，不创建、不销毁测试库。"""
    django_db_blocker.unblock()
    from django.test import Client

    yield Client()
