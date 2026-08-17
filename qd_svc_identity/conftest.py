import pymysql

pymysql.install_as_MySQLdb()

import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()
