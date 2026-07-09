from django.db.models import Q

from apps.auth_support.models import ExpUser
from qd_common.oss_url import default_avatar_url
from qd_common.password_java import (
    encrypt_password_for_storage,
    should_rehash_to_java,
    verify_password,
)


class CustomerUserService:
    @staticmethod
    def find_by_login_name(login_name: str) -> ExpUser | None:
        if not login_name:
            return None
        return (
            ExpUser.objects.filter(deleteStatus=0)
            .filter(Q(userName=login_name) | Q(mobile=login_name))
            .first()
        )

    @staticmethod
    def get_by_id(user_id: int) -> ExpUser | None:
        try:
            return ExpUser.objects.filter(id=user_id, deleteStatus=0).first()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def display_name(user: ExpUser) -> str:
        if user.is_identify == 0:
            return user.mobile or user.userName or ""
        if user.trueName:
            return user.trueName
        return user.mobile or user.userName or ""

    @staticmethod
    def default_avatar() -> str:
        from django.conf import settings

        return default_avatar_url(
            public_base_url=getattr(settings, "OSS_PUBLIC_BASE_URL", ""),
            bucket=getattr(settings, "OSS_BUCKET", "qgongye"),
            endpoint=getattr(settings, "OSS_ENDPOINT", ""),
        )

    @staticmethod
    def rehash_password_if_legacy(user: ExpUser, plain: str) -> None:
        stored = user.password or ""
        if not should_rehash_to_java(stored):
            return
        ExpUser.objects.filter(pk=user.pk).update(
            password=encrypt_password_for_storage(plain)
        )
        user.password = encrypt_password_for_storage(plain)

    @staticmethod
    def validate_password(plain: str, stored: str) -> bool:
        ok, _ = verify_password(plain, stored or "")
        return ok

    @staticmethod
    def build_login_payload(
        user: ExpUser, token: str, refresh_token: str, *, avatar: str | None = None
    ) -> dict:
        return {
            "token": token,
            "refresh_token": refresh_token,
            "nickName": CustomerUserService.display_name(user),
            "phone": user.mobile or "",
            "avatar": avatar or CustomerUserService.default_avatar(),
        }

    @staticmethod
    def build_identify_payload(user: ExpUser, *, avatar: str | None = None) -> dict:
        show_name = CustomerUserService.display_name(user)
        data = {
            "userType": user.userType or 1,
            "show_name": show_name,
            "mobile": user.mobile or "",
            "avatar": avatar or CustomerUserService.default_avatar(),
        }
        if user.is_identify and user.is_identify != 0:
            data.update(
                {
                    "trueName": user.trueName or "",
                    "email": user.email or "",
                    "idcard": user.idcard or "",
                    "company_name": user.company_name or "",
                    "nickname": user.wx_nickname or "",
                    "area_id": user.area_id or "",
                    "address": user.address_info or "",
                    "company_id": str(user.parent_id) if user.parent_id else "",
                }
            )
        return data

    @staticmethod
    def exp_user_token_data(user: ExpUser) -> dict:
        return {
            "user_id": str(user.id),
            "user_name": user.mobile or user.userName or str(user.id),
            "true_name": CustomerUserService.display_name(user),
            "user_type": "1",
            "dept_id": "",
            "dept_name": "",
            "role_ids": [],
            "account_kind": "exp_user",
        }
