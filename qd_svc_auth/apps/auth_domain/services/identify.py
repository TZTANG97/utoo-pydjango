import logging
from typing import Any

from django.db import transaction

from apps.auth_domain.models import ExpUser
from apps.auth_domain.repositories import company as company_repo
from apps.auth_domain.services.customer import CustomerUserService
from qd_common.password_java import encrypt_password_for_storage

logger = logging.getLogger(__name__)


def _ensure_company(*, name: str, contract_phone: str = "") -> int | None:
    if not name:
        return None
    row = company_repo.find_company_by_name(name)
    if row:
        return int(row["id"])
    return company_repo.insert_company(name=name, contract_phone=contract_phone)


@transaction.atomic
def update_personal_profile(
    user_id: int,
    *,
    true_name: str = "",
    mobile: str = "",
    email: str = "",
    idcard: str = "",
    company_name: str = "",
    area_id: str = "",
    address: str = "",
    password: str = "",
) -> tuple[bool, str]:
    user = CustomerUserService.get_by_id(user_id)
    if not user:
        return False, "用户不存在"

    updates: dict[str, Any] = {"is_identify": 1, "userType": 1}
    if true_name:
        updates["trueName"] = true_name
    if mobile:
        updates["mobile"] = mobile
    if email:
        updates["email"] = email
    if idcard:
        updates["idcard"] = idcard
    if company_name:
        updates["company_name"] = company_name
    if area_id:
        updates["area_id"] = area_id
    if address:
        updates["address_info"] = address
    if password:
        updates["password"] = encrypt_password_for_storage(password)

    if company_name:
        parent_id = _ensure_company(
            name=company_name,
            contract_phone=mobile or user.mobile or "",
        )
        if parent_id:
            updates["parent_id"] = parent_id

    try:
        ExpUser.objects.filter(pk=user.pk).update(**updates)
        return True, "个人会员认证成功!"
    except Exception as exc:
        logger.exception("update_personal_profile failed: %s", exc)
        return False, f"认证失败：{exc}"


@transaction.atomic
def update_company_profile(
    user_id: int,
    *,
    company_id: str = "",
    name: str = "",
    country: str = "",
    area_id: str = "",
    address: str = "",
    tax_num: str = "",
    bank: str = "",
    bank_card_num: str = "",
    contract_phone: str = "",
) -> tuple[bool, str]:
    user = CustomerUserService.get_by_id(user_id)
    if not user:
        return False, "用户不存在"

    cid: int | None = None
    if company_id and str(company_id).isdigit():
        cid = int(company_id)
        company_repo.update_company(
            company_id=cid,
            name=name,
            country=country,
            area_id=area_id,
            address=address,
            tax_num=tax_num,
            bank=bank,
            bank_card_num=bank_card_num,
            contract_phone=contract_phone,
        )
    elif name:
        cid = _ensure_company(
            name=name,
            contract_phone=contract_phone or user.mobile or "",
        )
        if cid:
            company_repo.update_company(
                company_id=cid,
                country=country,
                area_id=area_id,
                address=address,
                tax_num=tax_num,
                bank=bank,
                bank_card_num=bank_card_num,
                contract_phone=contract_phone,
            )

    updates: dict[str, Any] = {"is_identify": 1, "userType": 2}
    if cid:
        updates["parent_id"] = cid
    try:
        ExpUser.objects.filter(pk=user.pk).update(**updates)
        return True, "企业会员认证成功!"
    except Exception as exc:
        logger.exception("update_company_profile failed: %s", exc)
        return False, f"认证失败：{exc}"
