import pymysql

pymysql.install_as_MySQLdb()

import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def live_client(django_db_blocker):
    django_db_blocker.unblock()
    return Client()
