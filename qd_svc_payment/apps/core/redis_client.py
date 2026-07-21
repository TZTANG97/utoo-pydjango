"""同步 Redis 工具（支付锁、支付状态缓存）"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def set_string(key: str, value: str, *, ex: int | None = None) -> None:
    try:
        get_redis().set(key, value, ex=ex)
    except Exception as exc:
        logger.warning("redis set failed: %s", exc)


def delete_key(key: str) -> None:
    try:
        get_redis().delete(key)
    except Exception as exc:
        logger.warning("redis delete failed: %s", exc)


def get_string(key: str) -> str | None:
    try:
        return get_redis().get(key)
    except Exception as exc:
        logger.warning("redis get failed: %s", exc)
        return None


def try_acquire_lock(key: str, *, ttl_sec: int = 120) -> str | None:
    token = uuid.uuid4().hex
    try:
        if get_redis().set(key, token, nx=True, ex=ttl_sec):
            return token
    except Exception as exc:
        logger.warning("redis lock failed: %s", exc)
    return None


def release_lock(key: str, token: str) -> None:
    try:
        r = get_redis()
        if r.get(key) == token:
            r.delete(key)
    except Exception as exc:
        logger.warning("redis unlock failed: %s", exc)


def cache_json(key: str, payload: dict[str, Any], *, ex: int) -> None:
    set_string(key, json.dumps(payload, ensure_ascii=False), ex=ex)


def get_cached_json(key: str) -> dict[str, Any] | None:
    raw = get_string(key)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
