#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
咨询「生成订单」自动化脚本（本地运行，默认不真正建单）。

能力：
1. 登录管理端，拉取咨询详情 / 样品列表
2. 按业务规则校验：有样品时「每个样品须被至少一条产品选中」；额外产品可不选样品
3. 对「应失败」场景会真实调用 saveOrder.ajax（校验失败不会建单）
4. 「应成功」场景默认只做本地校验；加 --submit 才会真正生成订单（咨询会变为已生成）

示例：
  python scripts/automate_consult_save_order.py --consult-id 1419
  python scripts/automate_consult_save_order.py --consult-id 1419 --base-url https://uat.utoodev.laide.tech/api
  python scripts/automate_consult_save_order.py --consult-id 1419 --submit

环境变量（可替代参数）：
  UTOO_API_BASE / UTOO_ADMIN_USER / UTOO_ADMIN_PASSWORD / UTOO_CONSULT_ID
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE = os.environ.get("UTOO_API_BASE", "https://uat.utoodev.laide.tech/api")
SAMPLE_MSG = "请将所有样品关联到产品后再生成订单"


@dataclass
class CaseResult:
    name: str
    ok: bool
    detail: str


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = ""

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def request(
        self,
        method: str,
        path: str,
        *,
        data: Any = None,
        form: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "X-Channel": "admin",
        }
        if self.token:
            headers["token"] = self.token
            headers["Authorization"] = f"Bearer {self.token}"

        body: bytes | None = None
        if form is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"
            body = urllib.parse.urlencode(
                {k: "" if v is None else str(v) for k, v in form.items()}
            ).encode("utf-8")
        elif data is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            self._url(path), data=body, headers=headers, method=method.upper()
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except Exception as parse_exc:
                raise RuntimeError(f"HTTP {exc.code}: {raw[:300]}") from parse_exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"请求失败 {self._url(path)}: {exc}") from exc

        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"非 JSON 响应: {raw[:300]}") from exc

    def login(self, username: str, password: str) -> None:
        # 兼容两套登录入口
        for path in ("/admin/userLogin.ajax", "/vue/userLogin.ajax"):
            res = self.request(
                "POST",
                path,
                form={"loginName": username, "userName": username, "password": password},
            )
            if int(res.get("res") or 0) == 1:
                obj = res.get("obj") or {}
                token = obj.get("token") or obj.get("accessToken") or ""
                if not token and isinstance(obj, dict):
                    token = (obj.get("data") or {}).get("token") if isinstance(obj.get("data"), dict) else ""
                if not token:
                    raise RuntimeError(f"登录成功但未返回 token: {res}")
                self.token = str(token)
                return
        raise RuntimeError(f"登录失败: {res.get('resMsg') or res}")

    def consult_detail(self, consult_id: int) -> dict[str, Any]:
        res = self.request("POST", "/consult/consultDetail.ajax", form={"id": consult_id})
        if int(res.get("res") or 0) != 1:
            raise RuntimeError(f"拉取咨询详情失败: {res.get('resMsg') or res}")
        obj = res.get("obj") or {}
        if not isinstance(obj, dict):
            raise RuntimeError("咨询详情 obj 格式异常")
        return obj

    def save_order(self, payload: list[Any]) -> dict[str, Any]:
        return self.request("POST", "/consult/saveOrder.ajax", data=payload)


def _as_int(val: Any) -> int | None:
    if val in (None, "", 0, "0"):
        return None
    try:
        n = int(val)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def sample_ids_from_detail(detail: dict[str, Any]) -> list[int]:
    ids: list[int] = []
    for src in (detail.get("sampleList") or [], detail.get("childsyp") or []):
        if not isinstance(src, list):
            continue
        for row in src:
            if not isinstance(row, dict):
                continue
            sid = _as_int(row.get("value") if row.get("value") is not None else row.get("id"))
            if sid is not None and sid not in ids:
                ids.append(sid)
    return ids


def check_samples_covered(sample_ids: list[int], children: list[dict[str, Any]]) -> str:
    """对齐后端：样品必须都被选中；产品可不选样品。"""
    if not sample_ids:
        return ""
    selected: set[int] = set()
    for ch in children:
        sid = _as_int(ch.get("sample_id") or ch.get("sampleId"))
        if sid is not None:
            selected.add(sid)
    missing = [sid for sid in sample_ids if sid not in selected]
    if missing:
        return SAMPLE_MSG
    return ""


def build_head(detail: dict[str, Any]) -> dict[str, Any]:
    c = detail.get("consult") or {}
    if not isinstance(c, dict):
        c = {}

    def pick(*keys: str, default: Any = "") -> Any:
        for k in keys:
            if c.get(k) not in (None, ""):
                return c.get(k)
            if detail.get(k) not in (None, ""):
                return detail.get(k)
        return default

    return {
        "id": pick("id"),
        "class_id": pick("class_id", "classId"),
        "userName": pick("userName", "user_name"),
        "mobile": pick("mobile"),
        "company_name": pick("company_name", "companyName"),
        "content": pick("content"),
        "remark": pick("remark"),
        "syUserName": pick("syUserName"),
        "supplier_name": pick("supplier_name"),
        "sale_manager": pick("sale_manager"),
        "delivery_time_str": pick("delivery_time_str"),
        "collection_time_str": pick("collection_time_str"),
        "order_type": pick("order_type", default=2),
        "send_address": pick("send_address"),
        "reverso_context": pick("reverso_context", default="OFF"),
        "addressee_name": pick("addressee_name"),
        "addressee_mobile": pick("addressee_mobile"),
        "test_address_id": pick("test_address_id"),
        "company_account_id": pick("company_account_id"),
        "invoiceType": pick("invoiceType", default="OFF"),
        "is_video": pick("is_video", default=0),
        "is_arrive": pick("is_arrive", default=0),
        "is_on": pick("is_on", default=0),
        "totalPrice": pick("totalPrice", "total_price", default=0),
        "goods_amount": pick("goods_amount", default=0),
    }


def normalize_child(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "goods_id": raw.get("goods_id") or raw.get("goodsId"),
        "goods_name": raw.get("goods_name") or raw.get("goodsName") or "",
        "goods_spec": raw.get("goods_spec") or raw.get("goodsSpec") or "",
        "goods_brand_name": raw.get("goods_brand_name") or raw.get("goodsBrandName") or "",
        "goods_nums": raw.get("goods_nums") or raw.get("goodsNums") or 1,
        "goods_price": raw.get("goods_price") or raw.get("goodsPrice") or 0,
        "reference_price": raw.get("reference_price") or raw.get("referencePrice") or 0,
        "experiment_project_id": raw.get("experiment_project_id") or raw.get("experimentProjectId") or "",
        "experiment_project_name": raw.get("experiment_project_name")
        or raw.get("experimentProjectName")
        or "",
        "experiment_class_id": raw.get("experiment_class_id") or raw.get("experimentClassId") or "",
        "experiment_class_name": raw.get("experiment_class_name")
        or raw.get("experimentClassName")
        or "",
        "sample_id": raw.get("sample_id") if raw.get("sample_id") not in (None,) else raw.get("sampleId") or "",
    }


def children_from_detail(detail: dict[str, Any]) -> list[dict[str, Any]]:
    rows = detail.get("childs") or []
    out: list[dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        ch = normalize_child(r)
        if ch.get("goods_id") in (None, "", 0, "0"):
            continue
        out.append(ch)
    return out


def ensure_extra_child(children: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """复制第一条产品作为无样品额外行，用于覆盖「样品选完后可加无样品产品」。"""
    if not children:
        return children
    extra = deepcopy(children[0])
    extra["sample_id"] = ""
    extra["goods_name"] = (extra.get("goods_name") or "产品") + "-无样品附加"
    return children + [extra]


def assign_samples_cover_all(
    children: list[dict[str, Any]], sample_ids: list[int]
) -> list[dict[str, Any]]:
    rows = deepcopy(children)
    if not rows:
        raise RuntimeError("咨询没有产品行，无法构造用例")
    # 先清空
    for r in rows:
        r["sample_id"] = ""
    # 每个样品至少一个产品；产品不够则复用/追加
    while len(rows) < len(sample_ids):
        rows.append(deepcopy(rows[0]))
    for i, sid in enumerate(sample_ids):
        rows[i]["sample_id"] = sid
    return rows


def clear_all_samples(children: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = deepcopy(children)
    for r in rows:
        r["sample_id"] = ""
    return rows


def partial_samples(children: list[dict[str, Any]], sample_ids: list[int]) -> list[dict[str, Any]]:
    rows = deepcopy(children)
    for r in rows:
        r["sample_id"] = ""
    if not sample_ids or not rows:
        return rows
    # 只选中第一个样品，留其余未覆盖
    rows[0]["sample_id"] = sample_ids[0]
    return rows


def print_case(result: CaseResult) -> None:
    mark = "PASS" if result.ok else "FAIL"
    print(f"[{mark}] {result.name}: {result.detail}")


def run_local_case(
    name: str, sample_ids: list[int], children: list[dict[str, Any]], expect_msg: str
) -> CaseResult:
    msg = check_samples_covered(sample_ids, children)
    if expect_msg:
        ok = msg == expect_msg
        detail = f"期望「{expect_msg}」，实际「{msg or '通过'}」"
    else:
        ok = msg == ""
        detail = f"期望通过，实际「{msg or '通过'}」"
    return CaseResult(name=name, ok=ok, detail=detail)


def run_api_expect_fail(
    client: ApiClient,
    name: str,
    head: dict[str, Any],
    children: list[dict[str, Any]],
    expect_substr: str,
) -> CaseResult:
    payload = [head, *children]
    res = client.save_order(payload)
    res_code = int(res.get("res") or 0)
    res_msg = str(res.get("resMsg") or "")
    ok = res_code == 0 and expect_substr in res_msg
    detail = f"res={res_code}, resMsg={res_msg!r}"
    if res_code == 1:
        detail += "（警告：接口返回成功，可能已建单）"
    return CaseResult(name=name, ok=ok, detail=detail)


def run_api_submit(
    client: ApiClient, name: str, head: dict[str, Any], children: list[dict[str, Any]]
) -> CaseResult:
    payload = [head, *children]
    res = client.save_order(payload)
    res_code = int(res.get("res") or 0)
    res_msg = str(res.get("resMsg") or "")
    order_pk = res.get("obj")
    ok = res_code == 1
    detail = f"res={res_code}, resMsg={res_msg!r}, order={order_pk}"
    return CaseResult(name=name, ok=ok, detail=detail)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="咨询生成订单自动化（样品覆盖规则）")
    p.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help=f"网关 API 前缀，默认 {DEFAULT_BASE}",
    )
    p.add_argument(
        "--user",
        default=os.environ.get("UTOO_ADMIN_USER", ""),
        help="管理端账号（或环境变量 UTOO_ADMIN_USER）",
    )
    p.add_argument(
        "--password",
        default=os.environ.get("UTOO_ADMIN_PASSWORD", ""),
        help="管理端密码（或环境变量 UTOO_ADMIN_PASSWORD）",
    )
    p.add_argument(
        "--consult-id",
        type=int,
        default=int(os.environ.get("UTOO_CONSULT_ID") or "0"),
        help="咨询 ID（或环境变量 UTOO_CONSULT_ID）",
    )
    p.add_argument(
        "--submit",
        action="store_true",
        help="对「应成功」场景真实调用 saveOrder（会生成订单，慎用）",
    )
    p.add_argument(
        "--skip-api-fail",
        action="store_true",
        help="跳过对失败用例的真实 API 探测，仅本地规则校验",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.consult_id:
        print("请提供 --consult-id", file=sys.stderr)
        return 2
    if not args.user or not args.password:
        print("请提供 --user / --password（或环境变量）", file=sys.stderr)
        return 2

    client = ApiClient(args.base_url)
    print(f"API: {args.base_url}")
    print(f"登录: {args.user}")
    client.login(args.user, args.password)
    print("登录成功")

    detail = client.consult_detail(args.consult_id)
    consult = detail.get("consult") or {}
    status = consult.get("status") if isinstance(consult, dict) else None
    try:
        status_i = int(status) if status is not None else -1
    except (TypeError, ValueError):
        status_i = -1

    sample_ids = sample_ids_from_detail(detail)
    children = children_from_detail(detail)
    head = build_head(detail)

    print(f"咨询 ID={args.consult_id}, status={status_i}, 样品数={len(sample_ids)}, 产品数={len(children)}")
    if sample_ids:
        print(f"样品 IDs: {sample_ids}")
    if status_i == 2:
        print("提示: 该咨询已生成订单(status=2)，成功提交用例会失败；失败探测仍可跑。")
    if status_i == 3:
        print("提示: 该咨询已取消(status=3)。")

    if not children:
        print("咨询无有效产品行，无法继续", file=sys.stderr)
        return 2

    results: list[CaseResult] = []

    # ---- 本地规则 ----
    if sample_ids:
        results.append(
            run_local_case(
                "本地-全部未选样品应失败",
                sample_ids,
                clear_all_samples(children),
                SAMPLE_MSG,
            )
        )
        if len(sample_ids) > 1:
            results.append(
                run_local_case(
                    "本地-样品未选完应失败",
                    sample_ids,
                    partial_samples(children, sample_ids),
                    SAMPLE_MSG,
                )
            )
        else:
            results.append(
                run_local_case(
                    "本地-仅1样品且已选中应通过",
                    sample_ids,
                    partial_samples(children, sample_ids),
                    "",
                )
            )

        covered = assign_samples_cover_all(children, sample_ids)
        results.append(
            run_local_case("本地-样品全覆盖应通过", sample_ids, covered, "")
        )
        results.append(
            run_local_case(
                "本地-样品全覆盖+无样品附加产品应通过",
                sample_ids,
                ensure_extra_child(covered),
                "",
            )
        )
    else:
        results.append(
            CaseResult("本地-无样品跳过覆盖校验", True, "咨询无样品，规则不拦截")
        )

    # ---- API 失败探测（不会建单）----
    if sample_ids and not args.skip_api_fail and status_i not in (2, 3):
        results.append(
            run_api_expect_fail(
                client,
                "API-全部未选样品应失败",
                head,
                clear_all_samples(children),
                SAMPLE_MSG,
            )
        )
        if len(sample_ids) > 1:
            results.append(
                run_api_expect_fail(
                    client,
                    "API-样品未选完应失败",
                    head,
                    partial_samples(children, sample_ids),
                    SAMPLE_MSG,
                )
            )
    elif sample_ids and status_i in (2, 3):
        results.append(
            CaseResult(
                "API-失败探测跳过",
                True,
                f"咨询 status={status_i}，跳过 saveOrder 失败探测",
            )
        )

    # ---- 真正提交 ----
    if args.submit:
        if status_i in (2, 3):
            results.append(
                CaseResult(
                    "API-提交建单",
                    False,
                    f"咨询 status={status_i}，无法再次生成订单",
                )
            )
        else:
            if sample_ids:
                rows = ensure_extra_child(assign_samples_cover_all(children, sample_ids))
            else:
                rows = children
            results.append(
                run_api_submit(client, "API-提交建单(样品全覆盖+附加无样品行)", head, rows)
            )
    else:
        print("未加 --submit：跳过真实建单（仅校验/失败探测）")

    print("-" * 60)
    for r in results:
        print_case(r)

    failed = [r for r in results if not r.ok]
    print("-" * 60)
    print(f"合计 {len(results)}，通过 {len(results) - len(failed)}，失败 {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
