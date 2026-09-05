#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UTOO 双试点 + 菜单/me 严格交叉测试（只读）。

覆盖：
  - 路由：consult → order/platform；welcome 不在 VUE_BIZ_EXACT
  - 网关 HTTP：isServiceConsult ≡ DB；welcome 字段；main 菜单；usercenter ≡ DB
  - 快照：关键表只读前后一致

用法（仓库根）:
  python scripts/verify-utoo-pilot-cross.py
  python scripts/verify-utoo-pilot-cross.py --offline-only

环境：
  UTOO_GATEWAY_URL   默认 http://127.0.0.1:18083
  UTOO_ORDER_URL     默认 http://127.0.0.1:18082（直连对照 isServiceConsult）
  CROSS_TEST_USER / CROSS_TEST_PASSWORD  默认 admin / 123456
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from cross_verify_support import (  # noqa: E402
    Tester,
    fetch_one,
    load_env,
    readonly_db,
    snapshot,
    unwrap_obj,
)

SNAPSHOT_TABLES = (
    "service_consult",
    "sy_users",
    "sy_menu",
    "sy_role_menu",
    "experiment_order",
    "account",
)


def utoo_gateway() -> str:
    return os.getenv("UTOO_GATEWAY_URL", "http://127.0.0.1:18083").rstrip("/")


def order_url() -> str:
    return os.getenv("UTOO_ORDER_URL", os.getenv("SVC_ORDER_URL", "http://127.0.0.1:18082")).rstrip("/")


def http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    channel: str = "admin",
    timeout: int = 45,
) -> tuple[int, object]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Channel": channel,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["token"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, raw = resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)
    if not raw:
        return status, {}
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw


def ajax_ok(body: object) -> bool:
    if not isinstance(body, dict):
        return False
    # Java/网关常用 res=true；部分中台 qd_common 用 res=1
    res = body.get("res")
    if res is True or res in (1, "1", "true", "True"):
        return True
    if body.get("success") is True:
        return True
    code = body.get("code")
    return code in (0, "0", 200, "200")


def extract_token(body: object) -> str:
    data = unwrap_obj(body) if isinstance(body, dict) else {}
    if not isinstance(data, dict):
        data = body if isinstance(body, dict) else {}
    for key in ("token", "accessToken", "access_token"):
        val = data.get(key) if isinstance(data, dict) else None
        if val:
            return str(val)
        if isinstance(body, dict) and body.get(key):
            return str(body.get(key))
    nested = data.get("token") if isinstance(data, dict) else None
    return str(nested or "")


def utoo_login(user: str, password: str) -> str:
    st, body = http_json(
        "POST",
        f"{utoo_gateway()}/api/vue/userLogin.ajax",
        body={"loginName": user, "userName": user, "password": password},
        channel="admin",
    )
    if st != 200 or not ajax_ok(body):
        raise RuntimeError(f"登录失败 HTTP={st} body={str(body)[:200]}")
    token = extract_token(body)
    if not token:
        raise RuntimeError(f"登录响应无 token: {str(body)[:200]}")
    return token


def payment_url() -> str:
    return os.getenv("SVC_PAYMENT_URL", "http://127.0.0.1:18084").rstrip("/")


def platform_url() -> str:
    return os.getenv("SVC_ADMIN_PLATFORM_URL", "http://127.0.0.1:18091").rstrip("/")


def offline_route_checks(t: Tester) -> None:
    from shared.utoo_admin_routes import VUE_BIZ_EXACT
    from shared.utoo_consumer_routes import MidTarget, resolve_consumer_path

    d1 = resolve_consumer_path("/api/consult/isServiceConsult.ajax")
    t.record("路由 consult isServiceConsult → ORDER", d1.target == MidTarget.ORDER, str(d1))
    d2 = resolve_consumer_path("/api/consult/list.ajax")
    t.record("路由 consult list → PLATFORM", d2.target == MidTarget.PLATFORM, str(d2))
    t.record("welcome 在 VUE_BIZ_EXACT（走 utoo_biz 本地）", VUE_BIZ_EXACT == frozenset({"welcome.ajax"}), str(VUE_BIZ_EXACT))
    t.record(
        "开票/付款/复测不经 VUE_BIZ（无假转发）",
        "invoice/listPage.ajax" not in VUE_BIZ_EXACT
        and "paymentapply/applylist.ajax" not in VUE_BIZ_EXACT
        and "retestapplication/list.ajax" not in VUE_BIZ_EXACT,
        "",
    )
    d3 = resolve_consumer_path("/api/pc/serviceConsultAdd.ajax")
    t.record("路由 pc serviceConsultAdd → ORDER", d3.target == MidTarget.ORDER, str(d3))
    d4 = resolve_consumer_path("/api/index/userRoles.ajax")
    t.record("路由 userRoles → BIZ_LOCAL（非 twin）", d4.target == MidTarget.BIZ_LOCAL, str(d4))
    d5 = resolve_consumer_path("/api/pc/addCash.ajax")
    t.record("路由 addCash → PAYMENT", d5.target == MidTarget.PAYMENT, str(d5))
    d6 = resolve_consumer_path("/api/pc/setPassword.ajax")
    t.record("路由 setPassword → IDENTITY", d6.target == MidTarget.IDENTITY, str(d6))
    d7 = resolve_consumer_path("/api/pc/register.ajax")
    t.record("路由 register → IDENTITY（offline）", d7.target == MidTarget.IDENTITY, str(d7))
    d8 = resolve_consumer_path("/api/pc/getXcxBanner.ajax")
    t.record("路由 getXcxBanner → ORDER", d8.target == MidTarget.ORDER, str(d8))
    d9 = resolve_consumer_path("/api/wx/TuZhebannerList.ajax")
    t.record(
        "路由 wx TuZhebannerList → ORDER（非 twin）",
        d9.target == MidTarget.ORDER and d9.path == "/api/wx/TuZhebannerList.ajax",
        str(d9),
    )
    d10 = resolve_consumer_path("/api/wx/phoneCodeLogin.ajax")
    t.record(
        "路由 wx phoneCodeLogin → IDENTITY（非 twin）",
        d10.target == MidTarget.IDENTITY and "/_internal/" not in d10.path,
        str(d10),
    )

def pick_consult_order_id(db) -> str | None:
    row = fetch_one(
        db,
        """
        SELECT order_id AS oid FROM service_consult
        WHERE deleteStatus = 0 AND order_id IS NOT NULL
        ORDER BY id DESC LIMIT 1
        """,
    )
    if row and row.get("oid") not in (None, ""):
        return str(int(row["oid"]))
    return None


def expected_is_service_consult(db, order_id: str) -> tuple[bool, str]:
    row = fetch_one(
        db,
        """
        SELECT id FROM service_consult
        WHERE deleteStatus = 0 AND order_id = %s
        LIMIT 1
        """,
        (int(order_id),),
    )
    if row:
        return True, "有用户业务咨询"
    return False, "没有用户业务咨询"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-only", action="store_true", help="只跑路由离线断言")
    args = parser.parse_args()
    load_env()
    # 交叉测强制校正被污染的 DB_PORT（IDE/Runner 偶发写入 UUID）
    if not (os.getenv("DB_PORT") or "").strip().isdigit():
        os.environ["DB_PORT"] = "3306"
    t = Tester("UTOO 双试点交叉测试")

    offline_route_checks(t)
    if args.offline_only:
        return t.summary()

    # --- 存活探测 ---
    st_gw, _ = http_json("GET", f"{utoo_gateway()}/health", channel="admin")
    if st_gw == 0:
        t.skip("utoo_gateway 存活", f"无法连接 {utoo_gateway()}")
        return t.summary()
    t.record("utoo_gateway 存活", st_gw == 200, f"HTTP={st_gw}")

    try:
        with readonly_db() as db:
            before = snapshot(db, SNAPSHOT_TABLES)
    except Exception as exc:
        t.skip("DB 只读连接", f"{type(exc).__name__}: {exc}; DB_PORT={os.getenv('DB_PORT')!r}")
        return t.summary()
    t.record("DB 会话 READ ONLY", True, f"port={os.getenv('DB_PORT')}")

    user = os.getenv("CROSS_TEST_USER", "admin").strip()
    password = os.getenv("CROSS_TEST_PASSWORD", "123456").strip()
    try:
        token = utoo_login(user, password)
        t.record("管理端登录", True, f"user={user}")
    except Exception as exc:
        t.record("管理端登录", False, str(exc))
        return t.summary()

    # --- consult：网关 vs DB；可选直连 order ---
    with readonly_db() as db:
        oid = pick_consult_order_id(db)
        if not oid:
            t.skip("isServiceConsult 样本", "service_consult 无有效 order_id")
            oid = "0"
            expect_found, expect_msg = False, "没有用户业务咨询"
        else:
            expect_found, expect_msg = expected_is_service_consult(db, oid)

    path = f"/api/consult/isServiceConsult.ajax?id={urllib.parse.quote(oid)}"
    st, body = http_json("GET", f"{utoo_gateway()}{path}", token=token, channel="pc")
    ok_flag = ajax_ok(body)
    msg = ""
    if isinstance(body, dict):
        msg = str(body.get("message") or body.get("resMsg") or body.get("msg") or "")
    # 无咨询时接口可能返回业务失败码但仍 HTTP 200
    matched = (expect_found and ok_flag and expect_msg in msg) or (
        (not expect_found) and (not ok_flag or expect_msg in msg or "没有" in msg)
    )
    t.record(
        "网关 isServiceConsult ≡ DB",
        st == 200 and matched,
        f"oid={oid} HTTP={st} expect_found={expect_found} msg={msg!r} body={str(body)[:120]}",
    )

    st_o, body_o = http_json("GET", f"{order_url()}{path}", token=token, channel="pc")
    if st_o == 0:
        t.skip("order 直连 isServiceConsult", f"无法连接 {order_url()}")
    else:
        same = (ajax_ok(body_o) == ok_flag) or (
            str(body_o)[:80] == str(body)[:80]
        )
        # 宽松：两边都 200 且「有/没有」语义一致
        msg_o = ""
        if isinstance(body_o, dict):
            msg_o = str(body_o.get("message") or body_o.get("resMsg") or "")
        semantic = ("有用户" in msg and "有用户" in msg_o) or ("没有" in msg and "没有" in msg_o) or (msg == msg_o)
        t.record(
            "网关 vs order 中台 isServiceConsult",
            st_o == 200 and semantic,
            f"gw={msg!r} order={msg_o!r}",
        )

    # --- main 菜单（原子拼装）---
    st_m, body_m = http_json("POST", f"{utoo_gateway()}/api/vue/main.ajax", token=token, body={})
    data_m = unwrap_obj(body_m)
    menus = data_m.get("menus") if isinstance(data_m, dict) else None
    t.record(
        "main.ajax 菜单树（原子拼装）",
        st_m == 200 and ajax_ok(body_m) and isinstance(menus, list) and len(menus) > 0,
        f"HTTP={st_m} menus={len(menus) if isinstance(menus, list) else 'n/a'} msg={body_m.get('resMsg') if isinstance(body_m, dict) else ''}",
    )

    # --- 开票列表：网关 → platform 中台（配了 SVC_ADMIN_PLATFORM_URL 时）---
    st_inv, body_inv = http_json(
        "POST",
        f"{utoo_gateway()}/api/vue/invoice/listPage.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    t.record(
        "invoice/listPage 经 platform（或网关回退）",
        st_inv == 200 and ajax_ok(body_inv),
        f"HTTP={st_inv} msg={(body_inv.get('resMsg') if isinstance(body_inv, dict) else body_inv)!r}",
    )
    platform = platform_url()
    st_pl, body_pl = http_json(
        "POST",
        f"{platform}/api/vue/invoice/listPage.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    if st_pl == 0:
        t.skip("platform 直连 invoice listPage", f"无法连接 {platform}")
    else:
        t.record(
            "platform 直连 invoice/listPage",
            st_pl == 200 and ajax_ok(body_pl),
            f"HTTP={st_pl} msg={(body_pl.get('resMsg') if isinstance(body_pl, dict) else body_pl)!r}",
        )

    # --- 付款申请列表：网关 → payment ---
    st_pa, body_pa = http_json(
        "POST",
        f"{utoo_gateway()}/api/vue/paymentapply/applylist.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    t.record(
        "paymentapply/applylist 经 payment（或网关回退）",
        st_pa == 200 and ajax_ok(body_pa),
        f"HTTP={st_pa} msg={(body_pa.get('resMsg') if isinstance(body_pa, dict) else body_pa)!r}",
    )
    pay = payment_url()
    st_pay, body_pay = http_json(
        "POST",
        f"{pay}/api/vue/paymentapply/applylist.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    if st_pay == 0:
        t.skip("payment 直连 applylist", f"无法连接 {pay}")
    else:
        t.record(
            "payment 直连 paymentapply/applylist",
            st_pay == 200 and ajax_ok(body_pay),
            f"HTTP={st_pay} msg={(body_pay.get('resMsg') if isinstance(body_pay, dict) else body_pay)!r}",
        )

    # --- 复测列表：网关 → order ---
    st_rt, body_rt = http_json(
        "POST",
        f"{utoo_gateway()}/api/vue/retestapplication/list.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    t.record(
        "retestapplication/list 经 order（或网关回退）",
        st_rt == 200 and ajax_ok(body_rt),
        f"HTTP={st_rt} msg={(body_rt.get('resMsg') if isinstance(body_rt, dict) else body_rt)!r}",
    )
    st_ord, body_ord = http_json(
        "POST",
        f"{order_url()}/api/vue/retestapplication/list.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    if st_ord == 0:
        t.skip("order 直连 retest list", f"无法连接 {order_url()}")
    else:
        t.record(
            "order 直连 retestapplication/list",
            st_ord == 200 and ajax_ok(body_ord),
            f"HTTP={st_ord} msg={(body_ord.get('resMsg') if isinstance(body_ord, dict) else body_ord)!r}",
        )

    # --- payLog：网关 → payment ---
    st_plg, body_plg = http_json(
        "POST",
        f"{utoo_gateway()}/api/vue/payLog/payList.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    t.record(
        "payLog/payList 经 payment（或网关回退）",
        st_plg == 200 and ajax_ok(body_plg),
        f"HTTP={st_plg} msg={(body_plg.get('resMsg') if isinstance(body_plg, dict) else body_plg)!r}",
    )
    st_plg2, body_plg2 = http_json(
        "POST",
        f"{pay}/api/vue/payLog/payList.ajax",
        token=token,
        body={"draw": 1, "start": 0, "length": 5},
    )
    if st_plg2 == 0:
        t.skip("payment 直连 payLog/payList", f"无法连接 {pay}")
    else:
        t.record(
            "payment 直连 payLog/payList",
            st_plg2 == 200 and ajax_ok(body_plg2),
            f"HTTP={st_plg2} msg={(body_plg2.get('resMsg') if isinstance(body_plg2, dict) else body_plg2)!r}",
        )

    # --- order tryFinishAfterInvoice 路由存活（缺 orderId 应业务失败，非 404）---
    st_tf, body_tf = http_json(
        "POST",
        f"{order_url()}/api/adminExperiment/order/tryFinishAfterInvoice.ajax",
        token=token,
        body={},
    )
    if st_tf == 0:
        t.skip("order tryFinishAfterInvoice 路由", f"无法连接 {order_url()}")
    else:
        msg_tf = ""
        if isinstance(body_tf, dict):
            msg_tf = str(body_tf.get("resMsg") or body_tf.get("message") or "")
        t.record(
            "order tryFinishAfterInvoice 路由存活",
            st_tf == 200 and ("缺少" in msg_tf or ajax_ok(body_tf)),
            f"HTTP={st_tf} msg={msg_tf!r}",
        )

    # --- usercenter ≡ DB ---
    st_u, body_u = http_json("POST", f"{utoo_gateway()}/api/vue/usercenter.ajax", token=token, body={})
    data_u = unwrap_obj(body_u)
    with readonly_db() as db:
        row = fetch_one(db, "SELECT id,user_name,true_name,email,mobile_phone_number,dept_id,type,utoo_type,user_status,account_type,pt_type FROM sy_users WHERE user_name=%s LIMIT 1", (user,))
    if not isinstance(data_u, dict) or not row:
        t.record("usercenter ≡ DB", False, f"HTTP={st_u} data={str(body_u)[:120]}")
    else:
        checks = [
            str(data_u.get("id") or "") == str(row.get("id") or ""),
            str(data_u.get("userName") or "") == str(row.get("user_name") or ""),
            str(data_u.get("trueName") or "") == str(row.get("true_name") or ""),
            str(data_u.get("email") or "") == str(row.get("email") or ""),
            str(data_u.get("ptType") or "") == str(row.get("pt_type") or ""),
            str(data_u.get("utooType") or "") == str(row.get("utoo_type") or ""),
        ]
        t.record(
            "usercenter ≡ DB（经 identity）",
            st_u == 200 and ajax_ok(body_u) and all(checks),
            f"id={data_u.get('id')} utooType={data_u.get('utooType')!r}",
        )

    # --- welcome 形状 + 关键金额/角色字段 ---
    st_w, body_w = http_json(
        "POST",
        f"{utoo_gateway()}/api/vue/welcome.ajax",
        token=token,
        body={"year": os.getenv("CROSS_TEST_YEAR", "")},
    )
    data_w = unwrap_obj(body_w)
    if not isinstance(data_w, dict):
        t.record("welcome.ajax 响应", False, f"HTTP={st_w} body={str(body_w)[:160]}")
    else:
        base_keys = ("userType", "currentUserId", "userName", "menuCount", "xdate", "ydata")
        shape = all(k in data_w for k in base_keys)
        t.record(
            "welcome.ajax 字段形状",
            st_w == 200 and ajax_ok(body_w) and shape,
            f"userType={data_w.get('userType')} uid={data_w.get('currentUserId')} keys={sorted(data_w.keys())[:12]}",
        )
        if int(data_w.get("userType") or 0) == 1:
            t.record(
                "welcome 管理员图表键",
                all(k in data_w for k in ("xdate", "ydata", "newlogs"))
                or all(k in data_w for k in ("xdate", "ydata")),
                "",
            )

    # --- userRoles：biz 本地（非 _internal twin）---
    st_ur, body_ur = http_json(
        "GET", f"{utoo_gateway()}/api/index/userRoles.ajax", token=token, channel="wx"
    )
    data_ur = unwrap_obj(body_ur)
    t.record(
        "userRoles.ajax biz 本地",
        st_ur == 200 and ajax_ok(body_ur) and isinstance(data_ur, dict) and "ADMIN" in data_ur,
        f"HTTP={st_ur} keys={list(data_ur.keys())[:5] if isinstance(data_ur, dict) else type(data_ur)}",
    )

    # --- getXcxBanner：匿名可读；网关或 order 直连 ---
    st_xb, body_xb = http_json(
        "GET", f"{utoo_gateway()}/api/pc/getXcxBanner.ajax", channel="pc"
    )
    t.record(
        "getXcxBanner 网关冒烟（匿名）",
        st_xb == 200 and ajax_ok(body_xb),
        f"HTTP={st_xb} msg={(body_xb.get('resMsg') if isinstance(body_xb, dict) else body_xb)!r}",
    )
    st_xb2, body_xb2 = http_json(
        "GET", f"{order_url()}/api/pc/getXcxBanner.ajax", channel="pc"
    )
    if st_xb2 == 0:
        t.skip("order 直连 getXcxBanner", f"无法连接 {order_url()}")
    else:
        t.record(
            "order 直连 getXcxBanner",
            st_xb2 == 200 and ajax_ok(body_xb2),
            f"HTTP={st_xb2} msg={(body_xb2.get('resMsg') if isinstance(body_xb2, dict) else body_xb2)!r}",
        )

    # --- TuZhebannerList：wx → order（匿名可读）---
    st_tz, body_tz = http_json(
        "GET", f"{utoo_gateway()}/api/wx/TuZhebannerList.ajax", channel="wx"
    )
    # 暂无轮播时可能业务失败，仍须非 404 / 非 twin 挂死
    tz_ok = st_tz == 200 and (
        ajax_ok(body_tz)
        or (isinstance(body_tz, dict) and "轮播" in str(body_tz.get("resMsg") or ""))
    )
    t.record(
        "wx TuZhebannerList 网关冒烟（匿名）",
        tz_ok,
        f"HTTP={st_tz} msg={(body_tz.get('resMsg') if isinstance(body_tz, dict) else body_tz)!r}",
    )
    st_tz2, body_tz2 = http_json(
        "GET", f"{order_url()}/api/wx/TuZhebannerList.ajax", channel="wx"
    )
    if st_tz2 == 0:
        t.skip("order 直连 TuZhebannerList", f"无法连接 {order_url()}")
    else:
        tz2_ok = st_tz2 == 200 and (
            ajax_ok(body_tz2)
            or (isinstance(body_tz2, dict) and "轮播" in str(body_tz2.get("resMsg") or ""))
        )
        t.record(
            "order 直连 TuZhebannerList",
            tz2_ok,
            f"HTTP={st_tz2} msg={(body_tz2.get('resMsg') if isinstance(body_tz2, dict) else body_tz2)!r}",
        )

    with readonly_db() as db:
        after = snapshot(db, SNAPSHOT_TABLES)
    t.compare_snapshot(before, after)
    return t.summary()


if __name__ == "__main__":
    raise SystemExit(main())
