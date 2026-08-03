from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_fund.repositories import account as account_repo
from apps.admin_fund.repositories import digital as digital_repo
from apps.admin_fund.repositories import pay_detail as pay_repo
from apps.admin_fund.repositories import settings as settings_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_uid(data: dict, user) -> str:
    uid = str(data.get("userId") or data.get("user_id") or "").strip()
    if uid:
        return uid
    if isinstance(user, dict):
        return str(user.get("user_id") or user.get("id") or "").strip()
    if user is not None:
        return str(
            getattr(user, "user_id", None) or getattr(user, "id", None) or ""
        ).strip()
    return ""


# ---- settings ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def setting_get(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=settings_repo.get_setting() or {}))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def setting_save_rates(request: Request, user=None):
    del user
    data = merge_payload(request)
    rmb = _to_int(data.get("rmbRate") or data.get("rmb_rate"))
    us = _to_int(data.get("usRate") or data.get("us_rate"))
    if rmb is None or us is None:
        return Response(ajax_fail("请填写年化利率"))
    settings_repo.save_rates(rmb_rate=rmb, us_rate=us)
    return Response(ajax_ok(msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def setting_save_exchange(request: Request, user=None):
    del user
    data = merge_payload(request)
    rate = data.get("usExchangeRate") or data.get("us_exchange_rate")
    if rate in (None, ""):
        return Response(ajax_fail("请填写美金汇率"))
    settings_repo.save_exchange_rate(rate)
    return Response(ajax_ok(msg="保存成功"))


# ---- account overview / asset / logs ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = account_repo.list_account_overview(
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_user_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    uid = str(data.get("id") or data.get("userId") or data.get("user_id") or "").strip()
    if not uid:
        return Response(ajax_fail("参数错误"))
    return Response(ajax_ok(obj={"accounts": account_repo.get_user_accounts(uid)}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_user_balance(request: Request, user=None):
    """小程序可用余额：对齐 /funds/account_userId.htm，响应体为数字。"""
    data = merge_payload(request)
    uid = _resolve_uid(data, user)
    account_type = _to_int(data.get("type") or data.get("accountType") or data.get("account_type"), 1) or 1
    return Response(account_repo.available_balance_for_user(uid, account_type))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_user_list_mp(request: Request, user=None):
    """小程序转账用户列表：对齐 /account_User.ajax DataTables。"""
    del user
    data = merge_payload(request)
    draw, _page, _page_size = parse_datatable_params(request)
    account_type = _to_int(data.get("accountType") or data.get("account_type") or data.get("type"))
    rows = account_repo.list_account_users_for_mp(account_type)
    return Response(datatable_payload(draw=draw, total=len(rows), rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def asset_overview(request: Request, user=None):
    data = merge_payload(request)
    uid = _resolve_uid(data, user)
    return Response(ajax_ok(obj=account_repo.asset_summary(uid or None)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def asset_account_xcx(request: Request, user=None):
    """小程序账户统计汇总（totala/totalf/rmbi/usi + 利率）。"""
    data = merge_payload(request)
    uid = _resolve_uid(data, user)
    setting = settings_repo.get_setting() or {}
    try:
        fx = float(setting.get("usExchangeRate") or 1)
    except (TypeError, ValueError):
        fx = 1.0
    return Response(
        ajax_ok(
            obj=account_repo.asset_account_xcx(
                uid or None,
                us_exchange_rate=fx,
                rmb_rate=setting.get("rmbRate") or 0,
                us_rate=setting.get("usRate") or 0,
            )
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def yesterday_income_xcx(request: Request, user=None):
    """小程序昨日收益 rmbzrsy / uszrsy。"""
    data = merge_payload(request)
    uid = _resolve_uid(data, user)
    return Response(ajax_ok(obj=account_repo.yesterday_income(uid or None)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_log_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    exclude_zero = str(data.get("excludeZero") or data.get("exclude_zero") or "").lower() in (
        "1",
        "true",
        "yes",
    )
    rows, total = account_repo.list_account_logs(
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        user_id=str(data.get("userId") or data.get("user_id") or "").strip(),
        acc_type=str(data.get("accType") if data.get("accType") is not None else data.get("acc_type") or ""),
        account_type=str(data.get("accountType") or data.get("account_type") or ""),
        log_status=str(data.get("logStatus") or data.get("log_status") or ""),
        order_id=(data.get("order_id") or data.get("orderId") or data.get("czNum") or "").strip(),
        add_time=(data.get("addTime") or data.get("add_time") or "").strip(),
        exclude_zero=exclude_zero,
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def exp_sum_by_year(request: Request, user=None):
    data = merge_payload(request)
    year = str(data.get("statistics_time") or data.get("year") or "").strip()
    if year.endswith("年"):
        year = year[:-1]
    uid = str(data.get("uid") or data.get("userId") or data.get("user_id") or "").strip()
    if not uid and user:
        # 非管理员可传入自身；管理员空即全量
        utoo_type = str(getattr(user, "utoo_type", "") or getattr(user, "utooType", "") or "")
        if utoo_type.upper() not in ("ADMIN", "1") and "管理员" not in str(
            getattr(user, "type", "") or ""
        ):
            uid = str(getattr(user, "id", "") or "")
    return Response(ajax_ok(obj=account_repo.exp_sum_by_year(year=year, user_id=uid or None)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def fund_years(request: Request, user=None):
    del request, user
    return Response(ajax_ok(obj=account_repo.list_stat_years()))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_log_add(request: Request, user=None):
    data = merge_payload(request)
    acc_type = _to_int(data.get("accType") or data.get("acc_type"))
    account_type = _to_int(data.get("accountType") or data.get("account_type"), 1) or 1
    amount_raw = data.get("logAmount") or data.get("log_amount")
    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        return Response(ajax_fail("当前金额输入错误"))
    if amount <= 0:
        return Response(ajax_fail("当前金额输入错误"))
    user_id = str(data.get("userId") or data.get("user_id") or "").strip()
    if not user_id and user:
        user_id = str(getattr(user, "id", "") or "")
    if not user_id:
        return Response(ajax_fail("缺少用户"))
    if acc_type not in (1, 2):
        return Response(ajax_fail("类型错误"))
    log_id, err = account_repo.create_recharge_or_withdraw(
        user_id=user_id,
        account_type=account_type,
        acc_type=acc_type,
        log_amount=amount,
        pd_log_info=(data.get("pdLogInfo") or data.get("pd_log_info") or "").strip(),
        bank_name=str(data.get("bankName") or data.get("bank_name") or "").strip(),
        card_num=str(data.get("branKCard") or data.get("cardNum") or data.get("card_num") or "").strip(),
    )
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(obj={"id": log_id}, res_msg="提交成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_transfer_add(request: Request, user=None):
    data = merge_payload(request)
    return _apply_transfer_loan(request, user, data, acc_type=11)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_loan_add(request: Request, user=None):
    data = merge_payload(request)
    return _apply_transfer_loan(request, user, data, acc_type=12)


def _apply_transfer_loan(request: Request, user, data: dict, *, acc_type: int):
    del request
    account_type = _to_int(data.get("accountType") or data.get("account_type"), 1) or 1
    try:
        amount = float(data.get("logAmount") or data.get("log_amount"))
    except (TypeError, ValueError):
        return Response(ajax_fail("当前金额输入错误"))
    if amount <= 0:
        return Response(ajax_fail("当前金额输入错误"))
    user_id = str(data.get("userId") or data.get("user_id") or "").strip()
    if not user_id and user:
        user_id = str(getattr(user, "id", "") or "")
    if not user_id:
        return Response(ajax_fail("缺少用户"))
    log_id, err = account_repo.create_transfer_or_loan(
        user_id=user_id,
        account_type=account_type,
        acc_type=acc_type,
        log_amount=amount,
        pd_log_info=(data.get("pdLogInfo") or data.get("pd_log_info") or "").strip(),
        in_user_id=str(data.get("inUserId") or data.get("in_user_id") or "").strip(),
    )
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(obj={"id": log_id}, res_msg="提交成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_log_pass(request: Request, user=None):
    del user
    data = merge_payload(request)
    log_id = _to_int(data.get("id"))
    if not log_id:
        return Response(ajax_fail("缺少ID"))
    status = _to_int(data.get("status") or data.get("data-value") or data.get("value"), -2)
    if status is None:
        status = -2
    err = account_repo.update_log_status(log_id, status)
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(res_msg="操作成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def chargeback_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("userId") or data.get("user_id") or "").strip()
    if not user_id:
        return Response(ajax_fail("请选择用户"))
    try:
        amount = float(data.get("logAmount") or data.get("log_amount"))
    except (TypeError, ValueError):
        return Response(ajax_fail("当前金额输入错误"))
    if amount <= 0:
        return Response(ajax_fail("当前金额输入错误"))
    log_status = _to_int(data.get("logStatus") or data.get("log_status"), 5)
    log_id, err = account_repo.create_chargeback(
        user_id=user_id,
        account_type=_to_int(data.get("accountType") or data.get("account_type"), 1) or 1,
        log_amount=amount,
        pd_log_info=(data.get("pdLogInfo") or data.get("pd_log_info") or "").strip(),
        auto_pass=log_status == 1,
    )
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(obj={"id": log_id}, res_msg="提交成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def loan_clear_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("userId") or data.get("user_id") or "").strip()
    if not user_id:
        return Response(ajax_fail("请选择用户"))
    try:
        amount = float(data.get("logAmount") or data.get("log_amount"))
    except (TypeError, ValueError):
        return Response(ajax_fail("当前金额输入错误"))
    if amount <= 0:
        return Response(ajax_fail("当前金额输入错误"))
    log_status = _to_int(data.get("logStatus") or data.get("log_status"), 2)
    log_id, err = account_repo.create_loan_clear(
        user_id=user_id,
        account_type=_to_int(data.get("accountType") or data.get("account_type"), 1) or 1,
        log_amount=amount,
        pd_log_info=(data.get("pdLogInfo") or data.get("pd_log_info") or "").strip(),
        auto_pass=log_status == 1,
    )
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(obj={"id": log_id}, res_msg="提交成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def fund_user_options(request: Request, user=None):
    del user
    data = merge_payload(request)
    keyword = (data.get("keyword") or data.get("userName") or "").strip()
    return Response(ajax_ok(obj=account_repo.list_fund_users(keyword)))


# ---- options ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_options(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=pay_repo.list_companies()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_pay_options(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=pay_repo.list_pay_users()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_options(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=pay_repo.list_labs()))


# ---- pay details ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_pay_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    company_id = str(data.get("companyId") or data.get("company_id") or "")
    year = str(data.get("year") or "")
    account_type = _to_int(data.get("accountType") or data.get("account_type"), 1) or 1
    if not year:
        return Response(ajax_fail("请选择年份"))
    rows = pay_repo.list_company_pay(company_id, year, account_type)
    return Response(ajax_ok(obj=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_pay_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    items = data.get("list") or data.get("items") or []
    if isinstance(data, list):
        items = data
    if not isinstance(items, list) or not items:
        # also accept raw body list via request.data
        raw = request.data
        if isinstance(raw, list):
            items = raw
    if not items:
        return Response(ajax_fail("没有数据"))
    company_id = items[0].get("companyId") or items[0].get("company_id")
    year = items[0].get("year")
    account_type = items[0].get("accountType") or items[0].get("account_type") or 1
    for it in items:
        it.setdefault("companyId", company_id)
        it.setdefault("year", year)
        it.setdefault("accountType", account_type)
    pay_repo.upsert_company_pay(items)
    return Response(ajax_ok(msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_pay_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("userId") or data.get("user_id") or "")
    year = str(data.get("year") or "")
    account_type = _to_int(data.get("accountType") or data.get("account_type"), 1) or 1
    if not user_id or not year:
        return Response(ajax_fail("请选择用户和年份"))
    rows = pay_repo.list_user_pay(user_id, year, account_type)
    return Response(ajax_ok(obj=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_pay_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    items = data.get("list") or data.get("items") or []
    raw = request.data
    if isinstance(raw, list):
        items = raw
    if not items:
        return Response(ajax_fail("没有数据"))
    user_id = items[0].get("userId") or items[0].get("user_id")
    year = items[0].get("year")
    account_type = items[0].get("accountType") or items[0].get("account_type") or 1
    for it in items:
        it.setdefault("userId", user_id)
        it.setdefault("year", year)
        it.setdefault("accountType", account_type)
    pay_repo.upsert_user_pay(items)
    return Response(ajax_ok(msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_loan_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    company_id = str(data.get("companyId") or data.get("company_id") or "")
    year = str(data.get("year") or "")
    account_type = _to_int(data.get("accountType") or data.get("account_type"), 1) or 1
    if not year:
        return Response(ajax_fail("请选择年份"))
    rows = pay_repo.list_company_loan(company_id, year, account_type)
    return Response(ajax_ok(obj=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_loan_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    items = data.get("list") or data.get("items") or []
    raw = request.data
    if isinstance(raw, list):
        items = raw
    if not items:
        return Response(ajax_fail("没有数据"))
    company_id = items[0].get("companyId") or items[0].get("company_id")
    year = items[0].get("year")
    account_type = items[0].get("accountType") or items[0].get("account_type") or 1
    for it in items:
        it.setdefault("companyId", company_id)
        it.setdefault("year", year)
        it.setdefault("accountType", account_type)
    pay_repo.upsert_company_loan(items)
    return Response(ajax_ok(msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def project_pay_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    lab_id = str(data.get("labId") or data.get("lab_id") or "")
    year = str(data.get("year") or "")
    account_type = _to_int(data.get("accountType") or data.get("account_type"), 1) or 1
    if not lab_id or not year:
        return Response(ajax_fail("请选择实验室和年份"))
    rows = pay_repo.list_project_pay(lab_id, year, account_type)
    return Response(ajax_ok(obj=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def project_pay_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    items = data.get("list") or data.get("items") or []
    raw = request.data
    if isinstance(raw, list):
        items = raw
    if not items:
        return Response(ajax_fail("没有数据"))
    lab_id = items[0].get("labId") or items[0].get("lab_id")
    year = items[0].get("year")
    account_type = items[0].get("accountType") or items[0].get("account_type") or 1
    for it in items:
        it.setdefault("labId", lab_id)
        it.setdefault("year", year)
        it.setdefault("accountType", account_type)
    pay_repo.upsert_project_pay(items)
    return Response(ajax_ok(msg="保存成功"))


# ---- digital center ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def digital_overview(request: Request, user=None):
    del user
    data = merge_payload(request)
    year = str(data.get("year") or "")
    if not year:
        from datetime import datetime

        year = str(datetime.now().year)
    return Response(ajax_ok(obj=digital_repo.overview(year)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def digital_company_sale_by_year(request: Request, user=None):
    """公司列表实验金额：/digitalManage/selCompanySaleByYear.ajax"""
    del user
    data = merge_payload(request)
    year = str(data.get("year") or "").strip()
    type_code = str(data.get("type") or "1").strip() or "1"
    return Response(
        ajax_ok(obj=digital_repo.sel_company_sale_by_year(year=year, type_code=type_code))
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def digital_exp_sale_by_year(request: Request, user=None):
    """实验/分包月度金额柱图：/digitalManage/selExpSaleByYear.ajax"""
    del user
    data = merge_payload(request)
    year = str(data.get("year") or "").strip()
    test_type = str(data.get("test_type") or data.get("testType") or "").strip()
    order_type = data.get("order_type") or data.get("orderType") or 6
    return Response(
        ajax_ok(
            obj=digital_repo.sel_exp_sale_by_year(
                year=year, test_type=test_type, order_type=order_type
            )
        )
    )
