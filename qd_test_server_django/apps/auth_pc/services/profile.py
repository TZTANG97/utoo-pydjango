import logging
from typing import Any

from apps.auth_pc.repositories import profile as profile_repo
from qd_common.oss_url import build_oss_object_url, default_avatar_url

logger = logging.getLogger(__name__)


class UserProfileService:
    @staticmethod
    def _oss_kwargs():
        from django.conf import settings

        return {
            "public_base_url": getattr(settings, "OSS_PUBLIC_BASE_URL", ""),
            "bucket": getattr(settings, "OSS_BUCKET", "qgongye"),
            "endpoint": getattr(settings, "OSS_ENDPOINT", ""),
        }

    @staticmethod
    def avatar_url(photo_id) -> str:
        if not photo_id:
            return default_avatar_url(**UserProfileService._oss_kwargs())
        try:
            row = profile_repo.get_accessory_photo(int(photo_id))
            if row and row.get("path") and row.get("name"):
                return build_oss_object_url(
                    row["path"], row["name"], **UserProfileService._oss_kwargs()
                )
        except Exception as exc:
            logger.warning("load avatar failed: %s", exc)
        return default_avatar_url(**UserProfileService._oss_kwargs())

    @staticmethod
    def _area_id_chain(area_id: str) -> str:
        raw = (area_id or "").strip()
        if not raw or "," in raw:
            return raw
        try:
            county = profile_repo.get_district_parent(raw)
            if not county or not county.get("super_id"):
                return raw
            city = profile_repo.get_district_parent(str(county["super_id"]))
            if not city or not city.get("super_id"):
                return raw
            prov = profile_repo.get_district_parent(str(city["super_id"]))
            if not prov:
                return raw
            return f"{prov['id']},{city['id']},{county['id']}"
        except Exception as exc:
            logger.warning("area chain failed: %s", exc)
            return raw

    @staticmethod
    def get_basic_info(user_id: int) -> dict:
        data = profile_repo.get_exp_user(user_id)
        if not data:
            return {}
        true_name = data.get("userName") or data.get("trueName") or ""
        return {
            "trueName": true_name,
            "mobile": data.get("mobile") or "",
            "email": data.get("email") or "",
            "identity": data.get("identity"),
            "area_id": UserProfileService._area_id_chain(str(data.get("area_id") or "")),
            "avatar": UserProfileService.avatar_url(data.get("photo_id")),
            "is_accept_message": data.get("is_accept_message"),
        }

    @staticmethod
    def update_basic_info(
        user_id: int,
        *,
        user_name: str = "",
        mobile: str = "",
        email: str = "",
        identity: str = "",
        area_id: str = "",
        image_id: str = "",
        is_accept_message: str = "",
    ) -> tuple[bool, str]:
        if not profile_repo.get_exp_user(user_id):
            return False, "用户不存在"

        area_store = ""
        if area_id and "," in area_id:
            parts = area_id.split(",")
            area_store = parts[2].strip() if len(parts) >= 3 else parts[-1].strip()
        elif area_id:
            area_store = area_id.strip()

        sets: list[str] = []
        params: dict[str, Any] = {}
        if user_name:
            sets.append("userName = %(user_name)s")
            params["user_name"] = user_name
        if mobile:
            sets.append("mobile = %(mobile)s")
            params["mobile"] = mobile
        if email:
            sets.append("email = %(email)s")
            params["email"] = email
        if identity != "":
            sets.append("identity = %(identity)s")
            params["identity"] = (
                int(identity) if str(identity).isdigit() else identity
            )
        if area_id:
            sets.append("area_id = %(area_id)s")
            params["area_id"] = area_store
        if image_id:
            sets.append("photo_id = %(photo_id)s")
            params["photo_id"] = int(image_id)
        if is_accept_message != "":
            sets.append("is_accept_message = %(iam)s")
            params["iam"] = int(is_accept_message)

        if not sets:
            return True, "修改用户基本信息成功!"

        try:
            profile_repo.update_exp_user_fields(user_id, sets, params)
            return True, "修改用户基本信息成功!"
        except Exception as exc:
            logger.exception("update_basic_info failed: %s", exc)
            return False, f"修改失败：{exc}"
