# -*- coding: utf-8 -*-
"""welcome 汇率 / 公司账户改调 asset mid。"""
from decimal import Decimal
from unittest.mock import patch

from shared.utoo_welcome import service as welcome_svc


def test_us_exchange_rate_from_mid():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_us_exchange_rate",
        return_value="7.2",
    ):
        assert welcome_svc._us_exchange_rate(token="t") == Decimal("7.2")


def test_us_exchange_rate_mid_miss_defaults_one():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_us_exchange_rate",
        return_value=None,
    ):
        assert welcome_svc._us_exchange_rate(token="t") == Decimal("1")


def test_us_exchange_rate_no_token_defaults_one():
    assert welcome_svc._us_exchange_rate(token=None) == Decimal("1")


def test_company_supplier_ids_from_mid():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_company_user_ids",
        return_value=["c1", "c2"],
    ):
        assert welcome_svc._company_supplier_ids("u1", token="t") == ["c1", "c2"]
        assert welcome_svc._user_has_company_account("u1", token="t") is True


def test_company_supplier_ids_mid_miss_empty():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_company_user_ids",
        return_value=None,
    ):
        assert welcome_svc._company_supplier_ids("u1", token="t") == []
        assert welcome_svc._user_has_company_account("u1", token="t") is False


def test_subcontract_gross_profit_uses_company_scope():
    with (
        patch(
            "shared.utoo_welcome.service.welcome_mid.fetch_us_exchange_rate",
            return_value="7",
        ),
        patch(
            "shared.utoo_welcome.service.welcome_mid.fetch_company_user_ids",
            return_value=["sup1"],
        ),
        patch(
            "shared.utoo_welcome.service.welcome_mid.fetch_subcontract_sum_by_currency",
            return_value={
                "parent": [{"currencyType": 1, "amount": "100"}],
                "child": [{"currencyType": 1, "amount": "40"}],
            },
        ) as mid_sum,
    ):
        profit, rate = welcome_svc._subcontract_gross_profit(
            user_id="u1", year=2026, token="tok"
        )
    assert profit == "60.00"
    assert rate == "60.00"
    kwargs = mid_sum.call_args.kwargs
    assert kwargs["scope"] == "supplier"
    assert kwargs["user_ids"] == ["sup1"]
    assert kwargs["exchange_rate"] == Decimal("7")


# --- 方案 B：禁 SQL 过渡回退（mid-only） ---


def test_enrich_welcome_user_from_mid():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_identity_user",
        return_value={
            "id": "u1",
            "true_name": "张三",
            "utoo_type": "销售人员",
            "dept_name": "销售部",
            "email": "a@b.c",
        },
    ):
        out = welcome_svc._enrich_welcome_user(
            {"user_id": "u1", "user_name": "zhang"}, token="tok"
        )
    assert out["true_name"] == "张三"
    assert out["utoo_type"] == "销售人员"
    assert out["dept_name"] == "销售部"


def test_enrich_welcome_user_mid_miss_keeps_jwt_fields():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_identity_user",
        return_value=None,
    ):
        out = welcome_svc._enrich_welcome_user(
            {
                "user_id": "u1",
                "user_name": "zhang",
                "true_name": "JWT名",
                "utoo_type": "销售人员",
                "dept_name": "JWT部门",
            },
            token="tok",
        )
    assert out["true_name"] == "JWT名"
    assert out["utoo_type"] == "销售人员"
    assert out["dept_name"] == "JWT部门"


def test_user_available_balances_from_mid():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_asset_accounts",
        return_value=[
            {"accountType": 1, "availableBalance": "12.5"},
            {"accountType": 2, "availableBalance": "3"},
        ],
    ):
        rmb, usd = welcome_svc._user_available_balances("u1", token="tok")
    assert rmb == "12.50"
    assert usd == "3.00"


def test_user_available_balances_mid_miss_zeros():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.fetch_asset_accounts",
        return_value=None,
    ):
        assert welcome_svc._user_available_balances("u1", token="tok") == ("0.00", "0.00")


def test_user_available_balances_no_token_zeros():
    assert welcome_svc._user_available_balances("u1", token=None) == ("0.00", "0.00")


def test_menu_count_from_mid():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.collect_role_menu_ids",
        return_value={"m1", "m2", "m3"},
    ):
        assert (
            welcome_svc._menu_count_for_user(
                {"user_id": "u1", "role_ids": ["r1"]}, token="tok"
            )
            == 3
        )


def test_menu_count_mid_empty_or_no_roles_is_zero():
    with patch(
        "shared.utoo_welcome.service.welcome_mid.collect_role_menu_ids",
        return_value=set(),
    ):
        assert (
            welcome_svc._menu_count_for_user(
                {"user_id": "u1", "role_ids": ["r1"]}, token="tok"
            )
            == 0
        )
    assert welcome_svc._menu_count_for_user({"user_id": "u1"}, token="tok") == 0
    assert welcome_svc._menu_count_for_user({"user_id": "u1", "role_ids": ["r1"]}, token=None) == 0


def test_user_sale_by_year_uses_passed_utoo_type_not_sql():
    """无 utoo_type 时不得查 sy_users；销售主管分流依赖入参 role。"""
    with (
        patch(
            "shared.utoo_welcome.service.welcome_mid.fetch_user_sale_by_month",
            return_value=[],
        ) as sale_mid,
        patch(
            "shared.utoo_welcome.service._subcontract_gross_profit",
            return_value=("0.00", "0.00"),
        ),
        patch(
            "shared.utoo_welcome.service._resolve_helper_user_ids",
            return_value=["u1"],
        ) as helpers,
    ):
        welcome_svc._user_sale_by_year(
            user_id="u1", year=2026, token="tok", utoo_type="销售主管"
        )
    assert sale_mid.call_args.kwargs["source"] == "sm"
    helpers.assert_not_called()

    with (
        patch(
            "shared.utoo_welcome.service.welcome_mid.fetch_user_sale_by_month",
            return_value=[],
        ) as sale_mid2,
        patch(
            "shared.utoo_welcome.service._subcontract_gross_profit",
            return_value=("0.00", "0.00"),
        ),
        patch(
            "shared.utoo_welcome.service._resolve_helper_user_ids",
            return_value=["u1", "h1"],
        ) as helpers2,
    ):
        # 空 utoo_type：不当销售主管，走 helper；不得 SQL
        welcome_svc._user_sale_by_year(
            user_id="u1", year=2026, token="tok", utoo_type=""
        )
    assert sale_mid2.call_args.kwargs["source"] == "exp"
    helpers2.assert_called_once()
