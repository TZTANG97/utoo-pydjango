from rest_framework.request import Request

from apps.auth_support.authentication import (
    ExpJWTAuthentication,
    TokenUser,
    decode_access_token,
    user_from_request_user,
)


def get_current_user_from_request(request: Request) -> dict | None:
    if hasattr(request, "user") and isinstance(request.user, TokenUser):
        return request.user._payload
    auth = ExpJWTAuthentication()
    result = auth.authenticate(request)
    if result:
        return user_from_request_user(result[0])
    token = (request.META.get("HTTP_TOKEN") or request.query_params.get("token") or "").strip()
    if not token:
        return None
    try:
        return decode_access_token(token)
    except Exception:
        return None


def is_exp_customer(user: dict | None) -> bool:
    if not user:
        return False
    if user.get("account_kind") == "exp_user":
        return True
    return str(user.get("user_type")) == "1" and user.get("account_kind") != "sy_user"
