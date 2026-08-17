from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from django.conf import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {**data}
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update(
        {
            "exp": expire,
            "type": "access",
            "iss": settings.JWT_ISSUER,
        }
    )
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = {**data}
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
            "iss": settings.JWT_ISSUER,
        }
    )
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """先试中台密钥，再试青岛 mall 密钥（切流后双端 token）。"""
    secrets = []
    for key in (settings.JWT_SECRET_KEY, getattr(settings, "MALL_JWT_SECRET", "")):
        if key and key not in secrets:
            secrets.append(key)
    for secret in secrets:
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM],
                options={"require": ["exp"]},
            )
        except jwt.PyJWTError:
            continue
    return None
