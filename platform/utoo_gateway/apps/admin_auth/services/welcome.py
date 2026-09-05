"""兼容入口：实现已迁至 shared.utoo_welcome（utoo_biz / gateway 共用）。"""
from shared.utoo_welcome.service import build_welcome_payload, list_sys_logs_page

__all__ = ["build_welcome_payload", "list_sys_logs_page"]
