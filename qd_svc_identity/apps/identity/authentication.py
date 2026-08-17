from typing import Optional

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from apps.identity.jwt_tokens import decode_token


class TokenUser:
    is_authenticated = True

    def __init__(self, payload: dict):
        self._payload = payload
        self.pk = payload.get("user_id") or payload.get("sub")


class IdentityJWTAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> Optional[tuple[TokenUser, None]]:
        auth = request.META.get("HTTP_AUTHORIZATION") or ""
        token = ""
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
        if not token:
            token = (request.META.get("HTTP_TOKEN") or "").strip()
        if not token:
            return None
        payload = decode_token(token)
        if not payload:
            raise AuthenticationFailed("无效令牌")
        if payload.get("type") == "refresh":
            raise AuthenticationFailed("请使用 access token")
        return TokenUser(payload), None
