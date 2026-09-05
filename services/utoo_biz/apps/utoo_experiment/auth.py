from __future__ import annotations

import jwt
from django.conf import settings
from rest_framework.request import Request


def _decode_token(token: str) -> dict | None:
    if not token:
        return None
    secrets: list[str] = []
    for key in (
        getattr(settings, "UTOO_JWT_SECRET_KEY", ""),
        getattr(settings, "JWT_SECRET", ""),
        settings.SECRET_KEY,
        getattr(settings, "MALL_JWT_SECRET", ""),
    ):
        if key and key not in secrets:
            secrets.append(key)
    for secret in secrets:
        try:
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"require": ["exp"]},
            )
            if claims.get("type") == "access" or claims.get("user_id") or claims.get("sub"):
                return claims
        except jwt.PyJWTError:
            continue
    return None


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        return token.strip()
    return authorization.strip()


def get_staff_user(request: Request) -> dict | None:
    token = _extract_bearer(request.headers.get("Authorization")) or (
        request.headers.get("token") or ""
    ).strip()
    if not token and hasattr(request, "query_params"):
        token = (request.query_params.get("token") or "").strip()
    claims = _decode_token(token)
    if not claims:
        return None
    user_id = str(claims.get("user_id") or claims.get("sub") or "").strip()
    if not user_id:
        return None
    if claims.get("account_kind") == "exp_user":
        return None
    return {
        "user_id": user_id,
        "id": user_id,
        "user_name": claims.get("user_name") or "",
        "true_name": claims.get("true_name") or "",
        "utoo_type": claims.get("utoo_type") or "",
        "dept_id": claims.get("dept_id") or "",
        "account_kind": claims.get("account_kind") or "sy_user",
    }


def is_sy_staff(user: dict | None) -> bool:
    if not user:
        return False
    if user.get("account_kind") == "exp_user":
        return False
    return bool(str(user.get("user_id") or user.get("id") or "").strip())
