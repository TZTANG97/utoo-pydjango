"""小程序登录短信 — 对齐 Java userType=code_login。"""
from __future__ import annotations

from apps.auth_pc.services import verify_code as verify_svc


def send_login_code(telephone: str) -> tuple[bool, str]:
    return verify_svc.send_code_login_code(telephone)


def verify_login_code(telephone: str, code: str) -> bool:
    return verify_svc.verify_code_login_code(telephone, code)
