from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.auth_domain.jwt_tokens import decode_token


class TokenUser:
    def __init__(self, payload: dict):
        self._payload = payload

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


def payload_to_user(payload: dict) -> dict:
    user_type = str(payload.get("user_type", "0"))
    account_kind = payload.get("account_kind")
    if not account_kind:
        account_kind = "exp_user" if user_type == "1" else "sy_user"
    return {
        "user_id": payload.get("user_id"),
        "user_name": payload.get("user_name"),
        "true_name": payload.get("true_name"),
        "user_type": user_type,
        "dept_id": payload.get("dept_id", ""),
        "dept_name": payload.get("dept_name", ""),
        "role_ids": payload.get("role_ids", []),
        "account_kind": account_kind,
    }


def decode_access_token(raw: str) -> dict:
    payload = decode_token(raw)
    if not payload or payload.get("type") != "access":
        raise AuthenticationFailed("认证令牌无效或已过期")
    if not payload.get("user_id"):
        raise AuthenticationFailed("令牌缺少用户信息")
    return payload_to_user(payload)


class ExpJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = None
        auth = request.META.get("HTTP_AUTHORIZATION") or ""
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
        if not token:
            token = (request.META.get("HTTP_TOKEN") or "").strip()
        if not token:
            token = (request.query_params.get("access_token") or "").strip()
        if not token:
            return None
        return (TokenUser(decode_access_token(token)), token)
