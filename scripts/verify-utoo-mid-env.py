#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UTOO 中台 URL 配齐 + 健康 + 缺配应 503 运维巡检。

验收（方案 B / P3）：
  - 关键 SVC_* 已配齐（缺则 FAIL）
  - biz mid：UTOO_*_MID 或回落 SVC_*（默认建议项；--strict-prod 强制显式 MID）
  - 各中台与 utoo_biz / utoo_gateway /health 可达
  - 可选 mid 路径抽测：无 token 可 401/403，但不得整段 404/连不上
  - 离线：网关 forward_*_first 缺配须走 mid_svc_unconfigured_response（503）
  - 生产建议：APP_ENV=production、BFF-only、公开 twin 关、Platform 永不 twin

用法（仓库根）:
  python scripts/verify-utoo-mid-env.py
  python scripts/verify-utoo-mid-env.py --env-only
  python scripts/verify-utoo-mid-env.py --strict-prod
  python scripts/verify-utoo-mid-env.py --skip-probe
  python scripts/verify-utoo-mid-env.py --skip-offline-503

环境：优先进程已设变量；否则从 scripts/dev.env、utoo_gateway/.env.local、
utoo_biz/.env.local 等 setdefault 补齐（不覆盖显式配置）。
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from cross_verify_support import Tester, load_env  # noqa: E402

# 网关侧显式 SVC（缺 → 中台归属路径 503）
GATEWAY_SVC_KEYS = (
    "SVC_IDENTITY_URL",
    "SVC_ORDER_URL",
    "SVC_PAYMENT_URL",
    "SVC_ADMIN_ASSET_URL",
    "SVC_ADMIN_PLATFORM_URL",
)

# utoo_biz 侧 mid（可用 SVC_* 回落；--strict-prod 要求显式 UTOO_*_MID）
BIZ_MID_KEYS = (
    "UTOO_IDENTITY_MID_SERVICE_URL",
    "UTOO_ORDER_MID_SERVICE_URL",
    "UTOO_PAYMENT_MID_SERVICE_URL",
    "UTOO_ASSET_MID_SERVICE_URL",
    "UTOO_PLATFORM_MID_SERVICE_URL",
)

BIZ_MID_FALLBACKS: dict[str, tuple[str, ...]] = {
    "UTOO_IDENTITY_MID_SERVICE_URL": ("SVC_IDENTITY_URL", "IDENTITY_MID_SERVICE_URL"),
    "UTOO_ORDER_MID_SERVICE_URL": ("SVC_ORDER_URL", "UTOO_ORDER_SERVICE_URL"),
    "UTOO_PAYMENT_MID_SERVICE_URL": ("SVC_PAYMENT_URL",),
    "UTOO_ASSET_MID_SERVICE_URL": ("SVC_ADMIN_ASSET_URL",),
    "UTOO_PLATFORM_MID_SERVICE_URL": ("SVC_ADMIN_PLATFORM_URL",),
}

# 进程入口 / twin stub
PROCESS_KEYS = (
    "UTOO_BIZ_SERVICE_URL",
    "UTOO_GATEWAY_INTERNAL_URL",
)

PROCESS_FALLBACKS: dict[str, tuple[str, ...]] = {
    "UTOO_BIZ_SERVICE_URL": (),
    "UTOO_GATEWAY_INTERNAL_URL": ("UTOO_GATEWAY_URL",),
}

# (label, env keys in priority order, default base for display only)
HEALTH_TARGETS = (
    ("identity", ("SVC_IDENTITY_URL", "UTOO_IDENTITY_MID_SERVICE_URL"), "http://127.0.0.1:18110"),
    ("order", ("SVC_ORDER_URL", "UTOO_ORDER_MID_SERVICE_URL"), "http://127.0.0.1:18082"),
    ("payment", ("SVC_PAYMENT_URL", "UTOO_PAYMENT_MID_SERVICE_URL"), "http://127.0.0.1:18084"),
    ("admin_asset", ("SVC_ADMIN_ASSET_URL", "UTOO_ASSET_MID_SERVICE_URL"), "http://127.0.0.1:18090"),
    ("admin_platform", ("SVC_ADMIN_PLATFORM_URL", "UTOO_PLATFORM_MID_SERVICE_URL"), "http://127.0.0.1:18091"),
    ("utoo_biz", ("UTOO_BIZ_SERVICE_URL",), "http://127.0.0.1:18103"),
    ("utoo_gateway", ("UTOO_GATEWAY_INTERNAL_URL", "UTOO_GATEWAY_URL"), "http://127.0.0.1:18083"),
)

# 无 token 抽测：200/401/403 可接受；404 / 连接失败 = FAIL
MID_PROBES = (
    ("identity", "SVC_IDENTITY_URL", "UTOO_IDENTITY_MID_SERVICE_URL", "GET", "/api/v1/identity/auth/me"),
    ("order", "SVC_ORDER_URL", "UTOO_ORDER_MID_SERVICE_URL", "GET", "/api/pc/getXcxBanner.ajax"),
    ("payment", "SVC_PAYMENT_URL", "UTOO_PAYMENT_MID_SERVICE_URL", "POST", "/api/vue/paymentapply/applylist.ajax"),
    ("platform", "SVC_ADMIN_PLATFORM_URL", "UTOO_PLATFORM_MID_SERVICE_URL", "POST", "/api/vue/invoice/listPage.ajax"),
    ("asset", "SVC_ADMIN_ASSET_URL", "UTOO_ASSET_MID_SERVICE_URL", "GET", "/health"),
    ("gateway→order", "UTOO_GATEWAY_INTERNAL_URL", "UTOO_GATEWAY_URL", "GET", "/api/pc/getXcxBanner.ajax"),
)

_FORWARD_MODULES = (
    "identity_forward.py",
    "order_forward.py",
    "payment_forward.py",
    "invoice_forward.py",
    "entry_forward.py",
    "wx_forward.py",
    "admin_asset_forward.py",
    "admin_platform_forward.py",
)

_TRUTHY = ("1", "true", "yes", "on")


def load_utoo_env() -> None:
    """在公共 load_env 之上补齐 UTOO 网关/biz 本地 env。"""
    load_env()
    extra = (
        REPO / "platform" / "utoo_gateway" / ".env",
        REPO / "platform" / "utoo_gateway" / ".env.local",
        REPO / "services" / "utoo_biz" / ".env",
        REPO / "services" / "utoo_biz" / ".env.local",
        REPO / "scripts" / "dev.env",
    )
    for path in extra:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), value)


def env_url(*keys: str, default: str = "") -> str:
    for key in keys:
        val = (os.getenv(key) or "").strip().rstrip("/")
        if val:
            return val
    return default.rstrip("/")


def _env_truthy(*keys: str) -> bool:
    for key in keys:
        raw = (os.getenv(key) or "").strip().lower()
        if raw in _TRUTHY:
            return True
    return False


def _is_prod_env() -> bool:
    return (os.getenv("APP_ENV") or "").strip().lower() in ("production", "prod")


def http_status(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    timeout: int = 8,
) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Channel": "admin",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return exc.code, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)
    except Exception as exc:  # noqa: BLE001 — 运维巡检要吞掉超时等
        return 0, f"{type(exc).__name__}: {exc}"


def check_required_env(t: Tester, *, strict_prod: bool) -> None:
    for key in GATEWAY_SVC_KEYS:
        val = (os.getenv(key) or "").strip()
        t.record(
            f"env {key}",
            bool(val),
            f"value={val[:64]!r}" if val else "未配置（方案 B：缺配应 503，运维须配齐）",
        )

    for key in BIZ_MID_KEYS:
        explicit = (os.getenv(key) or "").strip()
        fallbacks = BIZ_MID_FALLBACKS.get(key, ())
        via = env_url(key, *fallbacks)
        if strict_prod:
            t.record(
                f"env {key}（strict）",
                bool(explicit),
                f"value={explicit[:64]!r}"
                if explicit
                else f"生产建议显式配置（可回落 {'/'.join(fallbacks) or '无'}）",
            )
        else:
            t.record(
                f"env {key}",
                bool(via),
                (
                    f"value={explicit[:64]!r}"
                    if explicit
                    else (f"via fallback={via[:64]!r}" if via else "未配置")
                ),
            )

    for key in PROCESS_KEYS:
        explicit = (os.getenv(key) or "").strip()
        fallbacks = PROCESS_FALLBACKS.get(key, ())
        via = env_url(key, *fallbacks)
        # UTOO_BIZ：网关 settings 有默认 :18103；巡检未设时用建议默认仅作非 strict 提示
        if key == "UTOO_BIZ_SERVICE_URL" and not via and not strict_prod:
            via = "http://127.0.0.1:18103"
            note = "未设环境变量；网关 Django 默认 :18103（建议显式配置）"
            t.record(f"env {key}", True, note)
            continue
        if key == "UTOO_GATEWAY_INTERNAL_URL" and not via and not strict_prod:
            via = env_url("UTOO_GATEWAY_URL") or "http://127.0.0.1:18083"
            t.record(
                f"env {key}",
                True,
                f"via fallback/default={via[:64]!r}（建议显式；生产 --strict-prod）",
            )
            continue
        ok = bool(explicit) if strict_prod else bool(via)
        t.record(
            f"env {key}" + ("（strict）" if strict_prod else ""),
            ok,
            (
                f"value={explicit[:64]!r}"
                if explicit
                else (f"via={via[:64]!r}" if via else "未配置")
            ),
        )


def check_prod_recommendations(t: Tester, *, strict_prod: bool) -> None:
    """生产建议项：默认 WARN 记为 PASS+提示；--strict-prod 则缺项 FAIL。"""
    is_prod = _is_prod_env()
    bff = _env_truthy("UTOO_GATEWAY_BFF_ONLY", "GATEWAY_BFF_ONLY")
    wx = (os.getenv("SVC_WX_URL") or "").strip()

    checks = [
        (
            "prod APP_ENV=production|prod",
            is_prod,
            f"APP_ENV={(os.getenv('APP_ENV') or '')!r}",
        ),
        (
            "prod BFF-only（UTOO_GATEWAY_BFF_ONLY/GATEWAY_BFF_ONLY）",
            bff or is_prod,
            "已开 BFF-only 或生产态（生产默认关公开 twin）"
            if (bff or is_prod)
            else "建议生产设 APP_ENV=production 或 UTOO_GATEWAY_BFF_ONLY=true",
        ),
        (
            "prod SVC_WX_URL",
            bool(wx),
            f"value={wx[:64]!r}" if wx else "扫码/预约转发建议配齐（可与 payment 同址）",
        ),
    ]

    # 离线：Platform 永不 twin（无 twin 回落分支）
    urls_py = REPO / "platform" / "utoo_gateway" / "config" / "urls.py"
    if urls_py.is_file():
        text = urls_py.read_text(encoding="utf-8")
        platform_ok = (
            "def _admin_platform_patterns():" in text
            and "admin_settings.urls" not in text.split("def _admin_platform_patterns():", 1)[-1].split(
                "def _experiment_order_patterns():", 1
            )[0]
            and "Platform 路由组永不 twin" in text
        )
        invoice_ok = (
            "def _invoice_patterns():" in text
            and "_invoice_twin_patterns" not in text
        )
        entry_ok = (
            "def _entry_patterns():" in text
            and "_entry_twin_patterns" not in text
        )
        member_ok = '"memberAccount"' in text
        seller_album_ok = "seller/goods_img_album.ajax" in text
        checks.append(
            (
                "offline Platform 永不 twin（urls）",
                platform_ok and invoice_ok and entry_ok and member_ok and seller_album_ok,
                "proxy-only + memberAccount + seller/goods_img_album"
                if (platform_ok and invoice_ok and entry_ok and member_ok and seller_album_ok)
                else "仍可能 twin 或缺补丁路径",
            )
        )

    for label, ok, detail in checks:
        if strict_prod:
            t.record(label, ok, detail)
        else:
            # 非 strict：建议项不阻断 --env-only；记 PASS 并提示缺口
            t.record(
                label,
                True,
                detail if ok else f"建议：{detail}",
            )


def check_health(t: Tester) -> None:
    for label, keys, default in HEALTH_TARGETS:
        base = env_url(*keys)
        if not base:
            t.record(
                f"health {label}",
                False,
                f"无 URL（keys={'+'.join(keys)}；参考默认 {default}）",
            )
            continue
        st, detail = http_status("GET", f"{base}/health")
        t.record(f"health {label}", st == 200, f"{base}/health — {detail}")


def check_mid_probes(t: Tester) -> None:
    for label, key_a, key_b, method, path in MID_PROBES:
        base = env_url(key_a, key_b)
        if not base:
            t.skip(f"probe {label} {path}", f"跳过：{key_a}/{key_b} 未配")
            continue
        body = {"draw": 1, "start": 0, "length": 1} if method == "POST" else None
        st, detail = http_status(method, f"{base}{path}", body=body)
        # 存活即可：鉴权失败可接受；整段挂掉（404）/连不上（0）/5xx 为 FAIL
        ok = st in (200, 401, 403)
        t.record(
            f"probe {label} {path}",
            ok,
            f"{method} {base}{path} — {detail}（期望 200/401/403，禁 404）",
        )


def _forward_first_fn(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def check_offline_missing_503(t: Tester) -> None:
    """静态：forward_*_first 未配不得 silent twin，须 mid_svc_unconfigured_response。"""
    core = REPO / "platform" / "utoo_gateway" / "apps" / "core"
    if not core.is_dir():
        t.record("offline 缺配→503 源码门禁", False, f"目录不存在: {core}")
        return
    bad: list[str] = []
    for mod in _FORWARD_MODULES:
        path = core / mod
        if not path.is_file():
            bad.append(f"{mod}: missing file")
            continue
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        fn_name = None
        for line in src.splitlines():
            if line.startswith("def forward_") and line.endswith("_first(view_func):"):
                fn_name = line[len("def ") :].split("(", 1)[0]
                break
        if not fn_name:
            bad.append(f"{mod}: no forward_*_first")
            continue
        fn = _forward_first_fn(tree, fn_name)
        if fn is None:
            bad.append(f"{mod}: cannot parse {fn_name}")
            continue
        text = ast.unparse(fn)
        if "view_func(" in text:
            bad.append(f"{mod}: still calls view_func (silent twin)")
        if "mid_svc_unconfigured_response" not in text and "503" not in text:
            bad.append(f"{mod}: no 503 / mid_svc_unconfigured_response")
    t.record(
        "offline 网关 forward_*_first 缺配→503",
        not bad,
        "OK" if not bad else "; ".join(bad),
    )

    # 启动门禁：生产/BFF-only 校验存在
    svc_proxy = core / "svc_proxy.py"
    if svc_proxy.is_file():
        text = svc_proxy.read_text(encoding="utf-8")
        gate_ok = (
            "gateway_production_env" in text
            and "gateway_enforce_mid_config" in text
            and "gateway_twin_public_enabled" in text
        )
        twin_prod_off = "gateway_enforce_mid_config()" in text.split(
            "def gateway_twin_public_enabled", 1
        )[-1][:800]
        t.record(
            "offline 启动门禁（production/BFF-only）",
            gate_ok and twin_prod_off,
            "生产默认关 twin + 缺 SVC 拒启" if (gate_ok and twin_prod_off) else "门禁函数缺失",
        )

    # utoo_biz：asset mid 未配返回空串（proxy 503），禁止默认回落网关
    registry = (
        REPO
        / "services"
        / "utoo_biz"
        / "apps"
        / "utoo_admin"
        / "clients"
        / "mid_registry.py"
    )
    if registry.is_file():
        text = registry.read_text(encoding="utf-8")
        asset_block_ok = True
        if "if target == AdminMidTarget.ASSET:" in text:
            after = text.split("if target == AdminMidTarget.ASSET:", 1)[1]
            block = after.split("if target ==", 1)[0]
            if "default=" in block:
                asset_block_ok = False
        t.record(
            "offline utoo_biz asset mid 缺配→空串/503",
            asset_block_ok and ("503" in text or "空串" in text or "禁止默认" in text),
            "ASSET 无 default 回落" if asset_block_ok else "ASSET 仍带 default（可能 silent twin）",
        )
    else:
        t.skip("offline utoo_biz asset mid 缺配→503", f"无文件 {registry}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-only", action="store_true", help="只检查环境变量是否配齐")
    parser.add_argument(
        "--strict-prod",
        action="store_true",
        help="生产严格：要求显式 UTOO_*_MID / PROCESS；生产建议项缺则 FAIL",
    )
    parser.add_argument("--skip-health", action="store_true", help="跳过 /health")
    parser.add_argument("--skip-probe", action="store_true", help="跳过 mid 路径抽测")
    parser.add_argument("--skip-offline-503", action="store_true", help="跳过缺配→503 源码门禁")
    args = parser.parse_args()

    load_utoo_env()
    t = Tester("UTOO 中台 URL / 健康 / 缺配503 巡检")

    check_required_env(t, strict_prod=args.strict_prod)
    check_prod_recommendations(t, strict_prod=args.strict_prod)
    if args.env_only:
        return t.summary()

    if not args.skip_offline_503:
        check_offline_missing_503(t)
    if not args.skip_health:
        check_health(t)
    if not args.skip_probe:
        check_mid_probes(t)

    return t.summary()


if __name__ == "__main__":
    raise SystemExit(main())
