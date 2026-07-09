"""C 端密码 — 对齐 Java Md5Utils.MD5"""
from __future__ import annotations

import hashlib
from typing import Literal, Tuple

_JAVA_MD5_DIGITS = "A1B3C5D7E9F0G2H4"
PasswordScheme = Literal["java_md5", "std_hex_md5", "plaintext", ""]


def java_md5_encrypt(plain: str) -> str:
    if not plain:
        return ""
    digest = hashlib.md5(plain.encode("utf-8")).digest()
    chars: list[str] = []
    for b in digest:
        chars.append(_JAVA_MD5_DIGITS[(b >> 4) & 0x0F])
        chars.append(_JAVA_MD5_DIGITS[b & 0x0F])
    return "".join(chars)


def java_md5_verify(plain: str, stored: str) -> bool:
    if not stored:
        return False
    return java_md5_encrypt(plain) == stored


def std_hex_md5_encrypt(plain: str) -> str:
    return hashlib.md5(plain.encode("utf-8")).hexdigest()


def std_hex_md5_verify(plain: str, stored: str) -> bool:
    if not stored:
        return False
    return std_hex_md5_encrypt(plain).lower() == stored.lower()


def verify_password(plain: str, stored: str) -> Tuple[bool, PasswordScheme]:
    if java_md5_verify(plain, stored):
        return True, "java_md5"
    if std_hex_md5_verify(plain, stored):
        return True, "std_hex_md5"
    if stored and plain == stored:
        return True, "plaintext"
    return False, ""


def encrypt_password_for_storage(plain: str) -> str:
    return java_md5_encrypt(plain)


def detect_password_scheme(stored: str) -> PasswordScheme:
    if not stored:
        return ""
    if len(stored) == 32 and all(c in "0123456789abcdefABCDEF" for c in stored):
        return "std_hex_md5"
    if any(c in _JAVA_MD5_DIGITS for c in stored):
        return "java_md5"
    return ""


def should_rehash_to_java(stored: str) -> bool:
    scheme = detect_password_scheme(stored)
    return scheme in ("std_hex_md5", "plaintext")
