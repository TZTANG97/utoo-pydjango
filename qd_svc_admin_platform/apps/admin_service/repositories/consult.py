from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from apps.admin_service.helpers import normalize_rows, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar
from django.db import transaction
from qd_common.serialize import to_jsonable


def list_consults(
    *,
    user_name: str = "",
    mobile: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.deleteStatus = 0 AND t.type = 2"
    params: dict[str, Any] = {}
    if user_name:
        where += " AND t.userName LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if mobile:
        where += " AND t.mobile LIKE %(mobile)s"
        params["mobile"] = f"%{mobile}%"
    total = int(
        scalar(
            f"SELECT COUNT(*) FROM service_consult t {where}",
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.*,
            em.name AS className,
            COALESCE(su.user_name, su.true_name, su2.user_name, su2.true_name, '') AS syUserName
        FROM service_consult t
        LEFT JOIN experiment_manage em ON t.class_id = em.id
        LEFT JOIN experiment_manage em2 ON em.parent_id = em2.id
        LEFT JOIN sy_users su ON em2.syuser_id = su.id
        LEFT JOIN sy_users su2 ON em.head_user_id = su2.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    out = normalize_rows(rows)
    for r in out:
        try:
            st = int(r.get("status")) if r.get("status") is not None else -1
        except (TypeError, ValueError):
            st = -1
        r["status"] = st
        r["statusLabel"] = {
            0: "待处理",
            1: "已处理",
            2: "已生成订单",
            3: "已取消",
        }.get(st, "未回复" if st < 0 else str(st))
        at = r.get("addTime")
        if at:
            r["addTime"] = str(at)[:19]
    return out, total


def _fmt_date(val: Any) -> str:
    if val is None or val == "":
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")
    text = str(val).strip()
    return text[:10] if text else ""


def _on_off_to_flag(val: Any, *, on_val: str = "1", off_val: str = "2") -> str:
    s = str(val or "").strip().upper()
    if s in ("ON", "1", "TRUE", "YES"):
        return on_val
    if s in ("OFF", "2", "0", "FALSE", "NO"):
        return off_val
    return str(val) if val not in (None, "") else off_val


def _to_int(val: Any, default: int | None = None) -> int | None:
    if val in (None, ""):
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _to_decimal(val: Any, default: Decimal = Decimal("0")) -> Decimal:
    if val in (None, ""):
        return default
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return default


def get_consult_detail(consult_id: int) -> dict[str, Any] | None:
    """对齐 Java ServiceConsultAction.consultDetail.ajax 的 obj 形状。"""
    row = fetch_one(
        """
        SELECT
            t.*,
            em.name AS className,
            em.head_user_id AS headUserId,
            em.parent_id AS parentClassId,
            em2.syuser_id AS parentSyUserId
        FROM service_consult t
        LEFT JOIN experiment_manage em ON t.class_id = em.id
        LEFT JOIN experiment_manage em2 ON em.parent_id = em2.id
        WHERE t.id = %(id)s AND IFNULL(t.deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": consult_id},
    )
    if not row:
        return None

    consult = dict(row)
    class_name = consult.pop("className", None) or ""
    head_user_id = consult.pop("headUserId", None)
    consult.pop("parentClassId", None)
    parent_sy_user_id = consult.pop("parentSyUserId", None)
    try:
        class_id = int(consult.get("class_id") or 0)
    except (TypeError, ValueError):
        class_id = 0

    consult["collection_time_str"] = _fmt_date(consult.get("collection_time"))
    consult["delivery_time_str"] = _fmt_date(consult.get("delivery_time"))
    try:
        consult["status"] = int(consult.get("status") if consult.get("status") is not None else -1)
    except (TypeError, ValueError):
        consult["status"] = -1

    sy_user_name = ""
    # 详情优先 head_user_id（与 Java Action 一致），再回落到父级 syuser_id（与列表一致）
    for uid in (head_user_id, parent_sy_user_id):
        if uid in (None, ""):
            continue
        su = fetch_one(
            """
            SELECT user_name, true_name
            FROM sy_users
            WHERE id = %(id)s
            LIMIT 1
            """,
            {"id": str(uid)},
        )
        if su:
            sy_user_name = str(su.get("user_name") or su.get("true_name") or "")
            if sy_user_name:
                break
    consult["syUserName"] = sy_user_name

    children = fetch_all(
        """
        SELECT *
        FROM service_consult_child
        WHERE consult_id = %(cid)s
          AND IFNULL(deleteStatus, 0) = 0
        ORDER BY id ASC
        """,
        {"cid": consult_id},
    )
    childs: list[dict[str, Any]] = []
    for ch in children:
        item = dict(ch)
        goods_id = item.get("goods_id")
        exp_goods = None
        if goods_id not in (None, ""):
            exp_goods = fetch_one(
                """
                SELECT
                    g.id,
                    g.goods_name,
                    g.goods_model,
                    g.goods_brand_id,
                    b.name AS brand_name
                FROM experiment_goods g
                LEFT JOIN goodsbrand b ON g.goods_brand_id = b.id
                WHERE g.id = %(id)s
                LIMIT 1
                """,
                {"id": goods_id},
            )
        item["expGoods"] = exp_goods
        if exp_goods and not item.get("goods_spec"):
            item["goods_spec"] = exp_goods.get("goods_model") or ""
        if exp_goods and not item.get("goods_brand_name"):
            item["goods_brand_name"] = exp_goods.get("brand_name") or ""
        if exp_goods and not item.get("goods_brand_id"):
            item["goods_brand_id"] = exp_goods.get("goods_brand_id")
        childs.append(item)

    files = fetch_all(
        """
        SELECT id, info, name, path, ext, size, addTime, type
        FROM accessory
        WHERE IFNULL(deleteStatus, 0) = 0 AND sc_id = %(sid)s
        ORDER BY id ASC
        """,
        {"sid": consult_id},
    )

    childsyp: list[dict[str, Any]] = []
    try:
        childsyp = fetch_all(
            """
            SELECT *
            FROM order_sample_information
            WHERE consult_id = %(cid)s
              AND IFNULL(deleteStatus, 0) = 0
            ORDER BY id ASC
            """,
            {"cid": consult_id},
        )
    except Exception:
        try:
            childsyp = fetch_all(
                """
                SELECT *
                FROM order_sample_information
                WHERE consult_id = %(cid)s
                ORDER BY id ASC
                """,
                {"cid": consult_id},
            )
        except Exception:
            childsyp = []

    # 对齐 Java：解析 attribute_id → sampleAttributeManageList（二级列名 + 三级取值）
    enriched_yp: list[dict[str, Any]] = []
    for yr in childsyp or []:
        item = dict(yr)
        item["sampleAttributeManageList"] = _sample_attributes(
            str(item.get("attribute_id") or item.get("attributeId") or "")
        )
        enriched_yp.append(item)
    childsyp = enriched_yp

    sample_list = list_sample_options(consult_id)

    zc_mobile = ""
    isxg = True
    user_id = consult.get("user_id")
    if user_id not in (None, ""):
        user = fetch_one(
            """
            SELECT mobile
            FROM `user`
            WHERE id = %(id)s
            LIMIT 1
            """,
            {"id": user_id},
        )
        if not user:
            user = fetch_one(
                """
                SELECT mobile
                FROM exp_user
                WHERE id = %(id)s
                LIMIT 1
                """,
                {"id": user_id},
            )
        if user:
            zc_mobile = str(user.get("mobile") or "")
            if zc_mobile and zc_mobile != str(consult.get("mobile") or ""):
                isxg = False

    return {
        "consult": to_jsonable(consult),
        "className": class_name,
        "classId": class_id,
        "childs": to_jsonable(childs),
        "childsyp": to_jsonable(childsyp),
        "files": to_jsonable(files),
        "sampleList": to_jsonable(sample_list),
        "zcMobile": zc_mobile,
        "isxg": isxg,
    }


def _get_sample_attribute(attr_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, sttribute_name, parent_id
        FROM sample_attribute_manage
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": attr_id},
    )


def _sample_attributes(attribute_id: str) -> list[dict[str, Any]]:
    """对齐 Java/小程序：attribute_id 形如「二级id:三级id:三级id;二级id:…」。"""
    raw = (attribute_id or "").strip()
    if not raw:
        return []
    erji_list: list[dict[str, Any]] = []
    sanji_list: list[dict[str, Any]] = []
    for group in raw.split(";"):
        parts = [p.strip() for p in group.split(":") if p.strip()]
        if not parts:
            continue
        if parts[0].isdigit():
            parent = _get_sample_attribute(int(parts[0]))
            if parent:
                erji_list.append(dict(parent))
        for cid in parts[1:]:
            if cid.isdigit():
                crow = _get_sample_attribute(int(cid))
                if crow:
                    sanji_list.append(dict(crow))
    for erji in erji_list:
        erji_id = erji.get("id")
        erji["attributeListsanji"] = [s for s in sanji_list if s.get("parent_id") == erji_id]
    return [to_jsonable(e) for e in erji_list]


def list_sample_options(consult_id: int) -> list[dict[str, Any]]:
    """对齐 Java querySampleList.ajax。"""
    try:
        rows = fetch_all(
            """
            SELECT id, sample_num AS sampleNum, sample_name AS sampleName,
                   main_component AS mainComponent
            FROM order_sample_information
            WHERE consult_id = %(cid)s
              AND IFNULL(deleteStatus, 0) = 0
            ORDER BY id ASC
            """,
            {"cid": consult_id},
        )
    except Exception:
        rows = fetch_all(
            """
            SELECT id, sample_num AS sampleNum, sample_name AS sampleName,
                   main_component AS mainComponent
            FROM order_sample_information
            WHERE consult_id = %(cid)s
            ORDER BY id ASC
            """,
            {"cid": consult_id},
        )
    for r in rows:
        name = str(r.get("sampleName") or r.get("sample_name") or "")
        num = str(r.get("sampleNum") or r.get("sample_num") or "")
        r["label"] = f"{num} {name}".strip() or str(r.get("id") or "")
        r["value"] = r.get("id")
    return rows


def cancel_consult(consult_id: int) -> None:
    execute(
        "UPDATE service_consult SET status = 3 WHERE id = %(id)s",
        {"id": consult_id},
    )


def _normalize_consult_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """将前端/Java 提交字段归一化。"""
    inv = _on_off_to_flag(raw.get("invoiceType"), on_val="1", off_val="2")
    rev = _on_off_to_flag(
        raw.get("reverso_context") or raw.get("reversoContext"), on_val="1", off_val="2"
    )
    delivery = str(raw.get("delivery_time_str") or raw.get("deliveryTime") or "").strip()[:10]
    collection = str(raw.get("collection_time_str") or raw.get("collectionTime") or "").strip()[:10]
    content = str(raw.get("content") or raw.get("zxcontent") or "").strip()
    zxcontent = str(raw.get("zxcontent") or raw.get("content") or "").strip()
    return {
        "id": _to_int(raw.get("id")),
        "class_id": _to_int(raw.get("class_id") or raw.get("classId")),
        "userName": str(raw.get("userName") or "").strip(),
        "mobile": str(raw.get("mobile") or "").strip(),
        "company_name": str(raw.get("company_name") or raw.get("companyName") or "").strip(),
        "content": content,
        "zxcontent": zxcontent,
        "remark": str(raw.get("remark") or "").strip(),
        "supplier_name": str(raw.get("supplier_name") or raw.get("supplierName") or "").strip(),
        "sale_manager": str(raw.get("sale_manager") or raw.get("saleManager") or "").strip(),
        "sale_user": str(raw.get("sale_user") or raw.get("saleUser") or "").strip(),
        "delivery_time": delivery,
        "collection_time": collection,
        "order_type": _to_int(raw.get("order_type") or raw.get("orderType"), 2),
        "send_address": str(raw.get("send_address") or raw.get("sendAddress") or "").strip(),
        "reverso_context": rev,
        "addressee_name": str(raw.get("addressee_name") or raw.get("addresseeName") or "").strip(),
        "addressee_mobile": str(
            raw.get("addressee_mobile") or raw.get("addresseeMobile") or ""
        ).strip(),
        "test_address_id": _to_int(raw.get("test_address_id") or raw.get("testAddressId")),
        "company_account_id": _to_int(
            raw.get("company_account_id") or raw.get("companyAccountId")
        ),
        "out_bill_type_id": _to_int(
            raw.get("out_bill_type_id") or raw.get("outBillTypeId")
        ),
        "invoiceType": inv,
        "is_video": 1
        if str(raw.get("is_video") or raw.get("isVideo") or "0") in ("1", "true", "ON", "on")
        else 0,
        "is_arrive": 1
        if str(raw.get("is_arrive") or raw.get("isArrive") or "0") in ("1", "true", "ON", "on")
        else 0,
        "is_on": 1
        if str(raw.get("is_on") or raw.get("isOn") or "0") in ("1", "true", "ON", "on")
        else 0,
        "currency_type": _to_int(raw.get("currency_type") or raw.get("currencyType"), 1) or 1,
        "totalPrice": _to_decimal(raw.get("totalPrice") or raw.get("total_price")),
        "goods_amount": _to_decimal(raw.get("goods_amount") or raw.get("goodsAmount")),
    }


def _normalize_child_payload(
    raw: dict[str, Any], *, consult_id: int, currency_type: int
) -> dict[str, Any] | None:
    goods_id = _to_int(raw.get("goods_id") or raw.get("goodsId"))
    if not goods_id:
        return None
    goods = fetch_one(
        """
        SELECT id, goods_name, goods_model, goods_brand_id
        FROM experiment_goods WHERE id = %(id)s LIMIT 1
        """,
        {"id": goods_id},
    )
    goods_name = str(raw.get("goods_name") or (goods or {}).get("goods_name") or "")
    goods_spec = str(raw.get("goods_spec") or (goods or {}).get("goods_model") or "")
    brand_id = _to_int(raw.get("goods_brand_id") or (goods or {}).get("goods_brand_id"))
    brand_name = str(raw.get("goods_brand_name") or "")
    if brand_id and not brand_name:
        br = fetch_one(
            "SELECT name FROM goodsbrand WHERE id = %(id)s LIMIT 1",
            {"id": brand_id},
        )
        if not br:
            br = fetch_one(
                "SELECT name FROM goods_brand WHERE id = %(id)s LIMIT 1",
                {"id": brand_id},
            )
        if not br:
            br = fetch_one(
                "SELECT name FROM experiment_brand WHERE id = %(id)s LIMIT 1",
                {"id": brand_id},
            )
        brand_name = str((br or {}).get("name") or "")
    return {
        "consult_id": consult_id,
        "goods_id": goods_id,
        "goods_name": goods_name[:200],
        "goods_spec": goods_spec[:200],
        "goods_brand_id": brand_id,
        "goods_brand_name": brand_name[:100],
        "goods_price": float(_to_decimal(raw.get("goods_price") or raw.get("goodsPrice"))),
        "goods_nums": float(
            _to_decimal(raw.get("goods_nums") or raw.get("goodsNums"), Decimal("1"))
        ),
        "reference_price": float(
            _to_decimal(raw.get("reference_price") or raw.get("referencePrice"))
        ),
        "experiment_project_id": _to_int(
            raw.get("experiment_project_id") or raw.get("experimentProjectId")
        ),
        "experiment_project_name": str(
            raw.get("experiment_project_name") or raw.get("experimentProjectName") or ""
        )[:200],
        "experiment_class_id": _to_int(
            raw.get("experiment_class_id") or raw.get("experimentClassId")
        ),
        "experiment_class_name": str(
            raw.get("experiment_class_name") or raw.get("experimentClassName") or ""
        )[:200],
        "sample_id": _to_int(raw.get("sample_id") or raw.get("sampleId")),
        "currency_type": currency_type,
    }


def _replace_consult_children(
    consult_id: int, children: list[dict[str, Any]], currency_type: int
) -> tuple[bool, str]:
    try:
        execute(
            """
            UPDATE service_consult_child
            SET deleteStatus = 1
            WHERE consult_id = %(cid)s AND IFNULL(deleteStatus, 0) = 0
            """,
            {"cid": consult_id},
        )
        execute(
            "DELETE FROM service_consult_child WHERE consult_id = %(cid)s AND IFNULL(deleteStatus, 0) = 1",
            {"cid": consult_id},
        )
    except Exception:
        execute("DELETE FROM service_consult_child WHERE consult_id = %(cid)s", {"cid": consult_id})

    saved = 0
    for raw in children:
        item = _normalize_child_payload(raw, consult_id=consult_id, currency_type=currency_type)
        if not item:
            continue
        execute_insert(
            """
            INSERT INTO service_consult_child
                (addTime, deleteStatus, consult_id, goods_id, goods_name, goods_spec,
                 goods_brand_id, goods_brand_name, goods_price, goods_nums, reference_price,
                 experiment_project_id, experiment_project_name,
                 experiment_class_id, experiment_class_name, sample_id, currency_type)
            VALUES
                (NOW(), 0, %(consult_id)s, %(goods_id)s, %(goods_name)s, %(goods_spec)s,
                 %(goods_brand_id)s, %(goods_brand_name)s, %(goods_price)s, %(goods_nums)s,
                 %(reference_price)s,
                 %(experiment_project_id)s, %(experiment_project_name)s,
                 %(experiment_class_id)s, %(experiment_class_name)s, %(sample_id)s, %(currency_type)s)
            """,
            item,
        )
        saved += 1
    return True, f"saved {saved}"


def _update_consult_row(c: dict[str, Any], *, status: int | None = None) -> None:
    params = {
        **c,
        "status": status if status is not None else None,
        "totalPrice": float(c["totalPrice"]),
        "goods_amount": float(c["goods_amount"]),
    }
    execute(
        """
        UPDATE service_consult SET
            class_id = %(class_id)s,
            content = %(content)s,
            remark = %(remark)s,
            supplier_name = %(supplier_name)s,
            sale_manager = %(sale_manager)s,
            sale_user = COALESCE(NULLIF(%(sale_user)s, ''), sale_user),
            delivery_time = NULLIF(%(delivery_time)s, ''),
            collection_time = NULLIF(%(collection_time)s, ''),
            order_type = %(order_type)s,
            send_address = %(send_address)s,
            reverso_context = %(reverso_context)s,
            addressee_name = %(addressee_name)s,
            addressee_mobile = %(addressee_mobile)s,
            test_address_id = %(test_address_id)s,
            company_account_id = %(company_account_id)s,
            invoiceType = %(invoiceType)s,
            is_video = %(is_video)s,
            is_arrive = %(is_arrive)s,
            is_on = %(is_on)s,
            currency_type = %(currency_type)s,
            totalPrice = %(totalPrice)s,
            goods_amount = %(goods_amount)s,
            mobile = COALESCE(NULLIF(%(mobile)s, ''), mobile),
            status = COALESCE(%(status)s, status)
        WHERE id = %(id)s
        """,
        params,
    )
    try:
        execute(
            "UPDATE service_consult SET zxcontent = %(zx)s WHERE id = %(id)s",
            {"zx": c.get("zxcontent") or c.get("content") or "", "id": c["id"]},
        )
    except Exception:
        pass


def update_consult(payload_list: list[Any]) -> tuple[bool, str]:
    """对齐 Java updateConsult.ajax：payload = [consult, ...children]。"""
    if not payload_list:
        return False, "保存失败，数据为空"
    raw_consult = payload_list[0] if isinstance(payload_list[0], dict) else {}
    c = _normalize_consult_payload(raw_consult)
    if not c.get("id"):
        return False, "咨询 ID 为空"
    existing = fetch_one(
        "SELECT id, status FROM service_consult WHERE id = %(id)s LIMIT 1",
        {"id": c["id"]},
    )
    if not existing:
        return False, "咨询不存在"
    try:
        st = int(existing.get("status") if existing.get("status") is not None else -1)
    except (TypeError, ValueError):
        st = -1
    if st in (2, 3):
        return False, "当前状态不可编辑"

    if c.get("supplier_name") and not c.get("sale_user"):
        try:
            u = fetch_one(
                "SELECT syuser_id FROM `user` WHERE id = %(id)s LIMIT 1",
                {"id": int(c["supplier_name"])},
            )
            if u and u.get("syuser_id"):
                c["sale_user"] = str(u["syuser_id"])
        except Exception:
            pass

    children = [x for x in payload_list[1:] if isinstance(x, dict)]
    _update_consult_row(c)
    _replace_consult_children(int(c["id"]), children, int(c["currency_type"] or 1))
    return True, "保存成功"


def check_save_order_params(c: dict[str, Any]) -> str:
    if not c.get("class_id"):
        return "请选择实验测试分类"
    if not c.get("supplier_name"):
        return "请选择所属公司"
    if not c.get("sale_manager"):
        return "请选择销售主管"
    if not c.get("delivery_time"):
        return "请选择预计收货时间"
    if not c.get("collection_time"):
        return "请选择预计收款时间"
    if not c.get("test_address_id"):
        return "请选择实验测试地址"
    if not c.get("company_account_id"):
        return "请选择公司汇款账号"
    return ""


def _list_consult_sample_ids(consult_id: int) -> list[int]:
    """咨询下未删除的样品 ID 列表。"""
    try:
        rows = fetch_all(
            """
            SELECT id
            FROM order_sample_information
            WHERE consult_id = %(cid)s
              AND IFNULL(deleteStatus, 0) = 0
            ORDER BY id ASC
            """,
            {"cid": int(consult_id)},
        )
    except Exception:
        try:
            rows = fetch_all(
                """
                SELECT id
                FROM order_sample_information
                WHERE consult_id = %(cid)s
                ORDER BY id ASC
                """,
                {"cid": int(consult_id)},
            )
        except Exception:
            return []
    ids: list[int] = []
    for r in rows or []:
        try:
            sid = int(r.get("id"))
        except (TypeError, ValueError):
            continue
        if sid > 0:
            ids.append(sid)
    return ids


def _check_children_sample_required(
    consult_id: int, children: list[dict[str, Any]]
) -> str:
    """有样品时：每个样品都必须被至少一条产品选中；产品可不选样品。"""
    sample_ids = _list_consult_sample_ids(consult_id)
    if not sample_ids:
        return ""
    selected: set[int] = set()
    for ch in children:
        sid = ch.get("sample_id")
        if sid in (None, "", 0, "0"):
            continue
        try:
            selected.add(int(sid))
        except (TypeError, ValueError):
            continue
    missing = [sid for sid in sample_ids if sid not in selected]
    if missing:
        return "请将所有样品关联到产品后再生成订单"
    return ""


def _gen_order_seq_code(n: int) -> str:
    """对齐 Java OrderFormUtils.genCode：不足 5 位左补 0。"""
    if n < 100000:
        return f"{n:05d}"
    return str(n)


def _manage_ennames(class_id: Any) -> tuple[str, str, str]:
    """按三级类目向上取 enname，用于订单号。"""
    en1 = en2 = en3 = ""
    try:
        cid = int(class_id) if class_id not in (None, "") else 0
    except (TypeError, ValueError):
        cid = 0
    if not cid:
        return en1, en2, en3
    row = fetch_one(
        "SELECT id, parent_id, enname FROM experiment_manage WHERE id = %(id)s LIMIT 1",
        {"id": cid},
    )
    if not row:
        return en1, en2, en3
    en3 = str(row.get("enname") or "")
    pid = row.get("parent_id")
    if pid:
        sec = fetch_one(
            "SELECT id, parent_id, enname FROM experiment_manage WHERE id = %(id)s LIMIT 1",
            {"id": pid},
        )
        if sec:
            en2 = str(sec.get("enname") or "")
            pid2 = sec.get("parent_id")
            if pid2:
                first = fetch_one(
                    "SELECT enname FROM experiment_manage WHERE id = %(id)s LIMIT 1",
                    {"id": pid2},
                )
                if first:
                    en1 = str(first.get("enname") or "")
    return en1, en2, en3


def _gen_order_no(
    *, class_id: int | None, currency_type: int, supplier_id: Any = None, order_time: str = ""
) -> str:
    """对齐 Java orderIdGeranateSale：{company_code}PT{en1}{en2}{en3}{yyyyMM}{5位序号}。"""
    del currency_type  # 咨询转单当前固定人民币；保留参数兼容调用方
    en1, en2, en3 = _manage_ennames(class_id)
    com_code = ""
    try:
        sid = int(supplier_id) if supplier_id not in (None, "") else 0
    except (TypeError, ValueError):
        sid = 0
    if sid:
        u = fetch_one(
            "SELECT company_code FROM `user` WHERE id = %(id)s LIMIT 1",
            {"id": sid},
        )
        if u:
            com_code = str(u.get("company_code") or "")
    dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(str(order_time).strip()[:19], fmt)
            break
        except (TypeError, ValueError):
            continue
    if dt is None:
        dt = datetime.now()
    datestr = dt.strftime("%Y%m")
    prefix = f"{com_code}PT{en1}{en2}{en3}{datestr}"
    latest = fetch_one(
        """
        SELECT order_id FROM experiment_order
        WHERE order_id LIKE %(pfx)s
        ORDER BY order_id DESC
        LIMIT 1
        """,
        {"pfx": f"{prefix}%"},
    )
    seq = 1
    if latest and latest.get("order_id"):
        oid = str(latest["order_id"])
        try:
            seq = int(oid[-5:]) + 1
        except (TypeError, ValueError):
            seq = 1
    return prefix + _gen_order_seq_code(seq)


def _ensure_customer_company(company_name: str) -> int | None:
    name = (company_name or "").strip()
    if not name:
        return None
    row = fetch_one(
        """
        SELECT id FROM qd_user_company
        WHERE IFNULL(deleteStatus, 0) = 0 AND name = %(name)s
        LIMIT 1
        """,
        {"name": name},
    )
    if row:
        return int(row["id"])
    try:
        return execute_insert(
            """
            INSERT INTO qd_user_company (addTime, deleteStatus, name, type)
            VALUES (NOW(), 0, %(name)s, 1)
            """,
            {"name": name},
        )
    except Exception:
        return None


def _exp_user_by_id(uid: Any) -> dict[str, Any] | None:
    if uid in (None, ""):
        return None
    try:
        return fetch_one(
            """
            SELECT id, mobile, parent_id
            FROM exp_user
            WHERE id = %(id)s
              AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"id": uid},
        )
    except Exception:
        return None


def _exp_user_by_mobile(mobile: str) -> dict[str, Any] | None:
    m = (mobile or "").strip()
    if not m:
        return None
    try:
        return fetch_one(
            """
            SELECT id, mobile, parent_id
            FROM exp_user
            WHERE mobile = %(m)s
              AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"m": m},
        )
    except Exception:
        return None


def _resolve_order_customer(
    *,
    company_name: str,
    mobile: str,
    consult_user_id: Any,
) -> tuple[int | None, int | None]:
    """解析订单客户企业 + 客户账号。

    对齐 Java 咨询/预约转订单：不自动写入 customer_name（客户名称常为空）；
    编辑页账号下拉来自 exp_user，因此只解析 custom_user_id。
    company_name 参数保留兼容调用方，不再用于建企业或回填 customer_name。
    """
    del company_name  # 对齐 Java：咨询公司名不写入订单客户名称
    customer_id: int | None = None
    custom_user_id: int | None = None

    def _apply_exp(eu: dict[str, Any] | None) -> None:
        nonlocal custom_user_id
        if not eu or eu.get("id") in (None, ""):
            return
        try:
            custom_user_id = int(eu["id"])
        except (TypeError, ValueError):
            return

    # 1) 咨询绑定的 user_id：优先当 exp_user
    _apply_exp(_exp_user_by_id(consult_user_id))
    if custom_user_id is None and consult_user_id not in (None, ""):
        urow = fetch_one(
            "SELECT id, mobile FROM `user` WHERE id = %(id)s LIMIT 1",
            {"id": consult_user_id},
        )
        if urow:
            _apply_exp(_exp_user_by_mobile(str(urow.get("mobile") or mobile or "")))
            if custom_user_id is None:
                try:
                    custom_user_id = int(urow["id"])
                except (TypeError, ValueError):
                    pass

    # 2) 手机号：优先 exp_user（与下拉一致）
    if custom_user_id is None:
        _apply_exp(_exp_user_by_mobile(mobile))
    if custom_user_id is None and (mobile or "").strip():
        urow = fetch_one(
            "SELECT id FROM `user` WHERE mobile = %(m)s LIMIT 1",
            {"m": (mobile or "").strip()},
        )
        if urow:
            try:
                custom_user_id = int(urow["id"])
            except (TypeError, ValueError):
                pass

    return customer_id, custom_user_id


def _default_out_bill_type_id() -> int | None:
    """开票时默认出项开票类型（bill_type.type=1 首条可用）。"""
    try:
        row = fetch_one(
            """
            SELECT id
            FROM bill_type
            WHERE type = 1
              AND IFNULL(delete_status, 0) = 0
            ORDER BY id ASC
            LIMIT 1
            """
        )
    except Exception:
        return None
    if not row or row.get("id") in (None, ""):
        return None
    try:
        return int(row["id"])
    except (TypeError, ValueError):
        return None


def _resolve_out_bill_type_id(raw: Any, *, invoice_type: int) -> int | None:
    """显式传入优先；开票时回落默认出项类型。"""
    if invoice_type != 1:
        return None
    if raw not in (None, "", 0, "0"):
        try:
            return int(raw)
        except (TypeError, ValueError):
            pass
    return _default_out_bill_type_id()


def save_order_from_consult(
    payload_list: list[Any], *, staff_user_id: str = ""
) -> tuple[bool, str, int | None]:
    """对齐 Java saveOrder.ajax：保存咨询并生成实验/分包订单。"""
    with transaction.atomic():
        ok, msg, order_pk = _save_order_from_consult_impl(
            payload_list, staff_user_id=staff_user_id
        )
        if not ok:
            # 业务失败也回滚，避免主单已写、子行失败留下空单
            transaction.set_rollback(True)
        return ok, msg, order_pk


def _save_order_from_consult_impl(
    payload_list: list[Any], *, staff_user_id: str = ""
) -> tuple[bool, str, int | None]:
    """对齐 Java saveOrder.ajax：保存咨询并生成实验/分包订单。"""
    if not payload_list:
        return False, "保存失败，数据为空", None
    raw_consult = payload_list[0] if isinstance(payload_list[0], dict) else {}
    c = _normalize_consult_payload(raw_consult)
    if not c.get("id"):
        return False, "咨询 ID 为空", None
    msg = check_save_order_params(c)
    if msg:
        return False, msg, None

    existing = fetch_one(
        """
        SELECT id, status, order_id, order_num, company_name, user_id, mobile, userName
        FROM service_consult WHERE id = %(id)s LIMIT 1
        """,
        {"id": c["id"]},
    )
    if not existing:
        return False, "咨询不存在", None
    try:
        st = int(existing.get("status") if existing.get("status") is not None else -1)
    except (TypeError, ValueError):
        st = -1
    if st == 2:
        return False, "已生成订单，请勿重复操作", None
    if st == 3:
        return False, "咨询已取消", None

    children_raw = [x for x in payload_list[1:] if isinstance(x, dict)]
    children: list[dict[str, Any]] = []
    for raw in children_raw:
        item = _normalize_child_payload(
            raw, consult_id=int(c["id"]), currency_type=int(c["currency_type"] or 1)
        )
        if item:
            children.append(item)
    if not children:
        return False, "请至少选择一条产品信息", None
    sample_msg = _check_children_sample_required(int(c["id"]), children)
    if sample_msg:
        return False, sample_msg, None

    if c.get("supplier_name"):
        try:
            u = fetch_one(
                "SELECT syuser_id FROM `user` WHERE id = %(id)s LIMIT 1",
                {"id": int(c["supplier_name"])},
            )
            if u and u.get("syuser_id"):
                c["sale_user"] = str(u["syuser_id"])
        except Exception:
            pass

    c["currency_type"] = 1
    _replace_consult_children(int(c["id"]), children_raw, int(c["currency_type"] or 1))

    order_type = "6" if int(c.get("order_type") or 2) == 2 else "8"
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_no = _gen_order_no(
        class_id=c.get("class_id"),
        currency_type=int(c["currency_type"] or 1),
        supplier_id=c.get("supplier_name"),
        order_time=order_time,
    )
    # 前端 payload 可能缺 company/mobile/user_id，回落咨询表原值
    if not c.get("company_name"):
        c["company_name"] = str(existing.get("company_name") or "")
    if not c.get("mobile"):
        c["mobile"] = str(existing.get("mobile") or "")
    customer_id, custom_user_id = _resolve_order_customer(
        company_name=str(c.get("company_name") or ""),
        mobile=str(c.get("mobile") or ""),
        consult_user_id=existing.get("user_id"),
    )

    invoice_type = 1 if str(c.get("invoiceType")) == "1" else 2
    # 实验订单「是否开票」详情按 1=是 展示；库内非 1 视为否
    order_invoice_type = 1 if invoice_type == 1 else 0
    out_bill_type_id = _resolve_out_bill_type_id(
        c.get("out_bill_type_id"), invoice_type=order_invoice_type
    )
    reverso = 1 if str(c.get("reverso_context")) == "1" else 2
    msg_text = (c.get("zxcontent") or c.get("content") or "")[:1000]

    order_pk = None
    insert_err = ""
    # 空日期用 None，避免 MySQL 把 '' 当成非法 datetime
    coll_val = c.get("collection_time") or None
    delv_val = c.get("delivery_time") or None
    try:
        order_pk = execute_insert(
            """
            INSERT INTO experiment_order
                (addTime, deleteStatus, order_id, order_type, order_status,
                 mobile, reverso_context, send_address, addressee_name, addressee_mobile,
                 in_status, relation_type, invoiceType, is_online, msg, consultid,
                 order_time, sale_manager, sale_user, custom_user_id, customer_name,
                 supplier_name, currency_type, pay_way, goods_amount, collection_time,
                 delivery_time, taxes, totalPrice, class_id, test_address_id,
                 company_account_id, out_bill_type_id, is_video, is_arrive, is_on,
                 add_user_id, exp_type_id)
            VALUES
                (NOW(), 0, %(ono)s, %(ot)s, 5,
                 %(mobile)s, %(rev)s, %(addr)s, %(an)s, %(am)s,
                 0, 0, %(inv)s, 1, %(msg)s, %(cid)s,
                 NOW(), %(sm)s, %(su)s, %(cuid)s, %(cust)s,
                 %(sup)s, %(ct)s, 1, %(ga)s, %(coll)s,
                 %(delv)s, 0.06, %(tp)s, %(class_id)s, %(taddr)s,
                 %(acc)s, %(obt)s, %(iv)s, %(ia)s, %(io)s,
                 %(add_uid)s, %(class_id)s)
            """,
            {
                "ono": order_no,
                "ot": order_type,
                "mobile": c.get("mobile") or "",
                "rev": reverso,
                "addr": c.get("send_address") or "",
                "an": c.get("addressee_name") or "",
                "am": c.get("addressee_mobile") or "",
                "inv": order_invoice_type,
                "msg": msg_text,
                "cid": c["id"],
                "sm": c.get("sale_manager") or None,
                "su": c.get("sale_user") or None,
                "cuid": custom_user_id,
                "cust": customer_id,
                "sup": c.get("supplier_name") or None,
                "ct": c.get("currency_type") or 1,
                "ga": float(c.get("goods_amount") or 0),
                "coll": coll_val,
                "delv": delv_val,
                "tp": float(c.get("totalPrice") or 0),
                "class_id": c.get("class_id"),
                "taddr": c.get("test_address_id") or None,
                "acc": c.get("company_account_id") or None,
                "obt": out_bill_type_id,
                "iv": c.get("is_video") or 0,
                "ia": c.get("is_arrive") or 0,
                "io": c.get("is_on") or 0,
                "add_uid": staff_user_id or None,
            },
        )
    except Exception as exc:
        insert_err = str(exc)
        order_pk = None

    if not order_pk:
        try:
            order_pk = execute_insert(
                """
                INSERT INTO experiment_order
                    (addTime, deleteStatus, order_id, order_type, order_status,
                     totalPrice, sale_manager, sale_user, customer_name, custom_user_id,
                     supplier_name, currency_type, invoiceType, consultid, mobile, class_id,
                     collection_time, delivery_time, goods_amount, reverso_context,
                     send_address, addressee_name, addressee_mobile)
                VALUES
                    (NOW(), 0, %(ono)s, %(ot)s, 5,
                     %(tp)s, %(sm)s, %(su)s, %(cust)s, %(cuid)s,
                     %(sup)s, %(ct)s, %(inv)s, %(cid)s, %(mobile)s, %(class_id)s,
                     %(coll)s, %(delv)s, %(ga)s, %(rev)s,
                     %(addr)s, %(an)s, %(am)s)
                """,
                {
                    "ono": order_no,
                    "ot": order_type,
                    "tp": float(c.get("totalPrice") or 0),
                    "sm": c.get("sale_manager") or None,
                    "su": c.get("sale_user") or None,
                    "cust": customer_id,
                    "cuid": custom_user_id,
                    "sup": c.get("supplier_name") or None,
                    "ct": c.get("currency_type") or 1,
                    "inv": order_invoice_type,
                    "cid": c["id"],
                    "mobile": c.get("mobile") or "",
                    "class_id": c.get("class_id"),
                    "coll": coll_val,
                    "delv": delv_val,
                    "ga": float(c.get("goods_amount") or 0),
                    "rev": reverso,
                    "addr": c.get("send_address") or "",
                    "an": c.get("addressee_name") or "",
                    "am": c.get("addressee_mobile") or "",
                },
            )
        except Exception as exc:
            return False, f"创建订单失败：{exc or insert_err}", None
    if not order_pk:
        return False, f"创建订单失败：{insert_err or '未知错误'}", None

    for idx, ch in enumerate(children, 1):
        child_no = f"{order_no}-{idx:02d}"
        # experiment_order_child 为 snake_case（add_time/delete_status）；
        # delete_status：1=删除 2=正常（对齐 Java / admin_experiment 建单）
        child_params = {
            "oid": order_pk,
            "cno": child_no,
            "gid": ch.get("goods_id") or None,
            "gn": ch.get("goods_name") or "",
            "gs": ch.get("goods_spec") or "",
            "gb": ch.get("goods_brand_name") or "",
            "nums": ch.get("goods_nums") or 1,
            "price": ch.get("goods_price") or 0,
            "ref": ch.get("reference_price") or 0,
            "epid": ch.get("experiment_project_id") or None,
            "epn": ch.get("experiment_project_name") or "",
            "ecid": ch.get("experiment_class_id") or None,
            "ecn": ch.get("experiment_class_name") or "",
            "sid": ch.get("sample_id") or None,
            "ct": ch.get("currency_type") or 1,
        }
        child_pk = None
        try:
            child_pk = execute_insert(
                """
                INSERT INTO experiment_order_child
                    (add_time, delete_status, order_form_id, order_id,
                     goods_id, goods_name, goods_spec, goods_brand_name, goods_nums,
                     goods_price, reference_price, experiment_project_id, experiment_project_name,
                     experiment_class_id, experiment_class_name, sample_id,
                     order_status, op_status, currency_type)
                VALUES
                    (NOW(), 2, %(oid)s, %(cno)s,
                     %(gid)s, %(gn)s, %(gs)s, %(gb)s, %(nums)s,
                     %(price)s, %(ref)s, %(epid)s, %(epn)s,
                     %(ecid)s, %(ecn)s, %(sid)s,
                     1, 1, %(ct)s)
                """,
                child_params,
            )
        except Exception as exc:
            try:
                child_pk = execute_insert(
                    """
                    INSERT INTO experiment_order_child
                        (add_time, delete_status, order_form_id, order_id,
                         goods_name, goods_nums, goods_price, order_status, op_status)
                    VALUES
                        (NOW(), 2, %(oid)s, %(cno)s,
                         %(gn)s, %(nums)s, %(price)s, 1, 1)
                    """,
                    {
                        "oid": order_pk,
                        "cno": child_no,
                        "gn": ch.get("goods_name") or "",
                        "nums": ch.get("goods_nums") or 1,
                        "price": ch.get("goods_price") or 0,
                    },
                )
            except Exception as exc2:
                return False, f"创建订单子行失败：{exc2 or exc}", None
        # 对齐 Java saveExpOrders：子行日志「创建子订单」
        if child_pk:
            try:
                execute(
                    """
                    INSERT INTO experiment_order_child_log
                        (addTime, deleteStatus, of_id, log_info, log_user_id)
                    VALUES (NOW(), 0, %(oid)s, %(info)s, %(uid)s)
                    """,
                    {
                        "oid": child_pk,
                        "info": "创建子订单",
                        "uid": staff_user_id or None,
                    },
                )
            except Exception:
                try:
                    execute(
                        """
                        INSERT INTO experiment_order_child_log
                            (addTime, deleteStatus, of_id, log_info)
                        VALUES (NOW(), 0, %(oid)s, %(info)s)
                        """,
                        {"oid": child_pk, "info": "创建子订单"},
                    )
                except Exception:
                    pass

    execute(
        """
        UPDATE service_consult
        SET status = 2, order_id = %(oid)s,
            invoiceType = %(inv)s, reverso_context = %(rev)s,
            totalPrice = %(tp)s, goods_amount = %(ga)s,
            supplier_name = %(sup)s, sale_manager = %(sm)s,
            class_id = %(class_id)s
        WHERE id = %(id)s
        """,
        {
            "oid": order_pk,
            "inv": c.get("invoiceType"),
            "rev": c.get("reverso_context"),
            "tp": float(c.get("totalPrice") or 0),
            "ga": float(c.get("goods_amount") or 0),
            "sup": c.get("supplier_name"),
            "sm": c.get("sale_manager"),
            "class_id": c.get("class_id"),
            "id": c["id"],
        },
    )
    _update_consult_row(c, status=2)
    # 对齐 Java：咨询转订单写「创建订单」操作日志
    try:
        execute(
            """
            INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info, log_user_id)
            VALUES (NOW(), 0, %(oid)s, %(info)s, %(uid)s)
            """,
            {
                "oid": int(order_pk),
                "info": "创建订单",
                "uid": staff_user_id or None,
            },
        )
    except Exception:
        try:
            execute(
                """
                INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info)
                VALUES (NOW(), 0, %(oid)s, %(info)s)
                """,
                {"oid": int(order_pk), "info": "创建订单"},
            )
        except Exception:
            pass
    return True, str(order_pk), order_pk


def get_consult_settings() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT gzh_userId_ut, gzh_issend_ut, service_mail_ut, mail_issend_ut
        FROM sysconfig WHERE id = 1 LIMIT 1
        """
    )
    if not row:
        return {}
    return {
        "gzh_userId_ut": row.get("gzh_userId_ut"),
        "gzh_issend_ut": row.get("gzh_issend_ut"),
        "service_mail_ut": row.get("service_mail_ut"),
        "mail_issend_ut": row.get("mail_issend_ut"),
    }


def save_consult_settings(
    *,
    gzh_user_id: str,
    gzh_issend: int,
    service_mail: str,
    mail_issend: int,
) -> None:
    execute(
        """
        UPDATE sysconfig
        SET gzh_userId_ut = %(gzh_user_id)s,
            gzh_issend_ut = %(gzh_issend)s,
            service_mail_ut = %(service_mail)s,
            mail_issend_ut = %(mail_issend)s
        WHERE id = 1
        """,
        {
            "gzh_user_id": gzh_user_id,
            "gzh_issend": gzh_issend,
            "service_mail": service_mail,
            "mail_issend": mail_issend,
        },
    )


def get_is_show() -> dict[str, Any]:
    row = fetch_one("SELECT is_show FROM sysconfig WHERE id = 1 LIMIT 1")
    return {"is_show": row.get("is_show") if row else 0}


def save_is_show(is_show: int) -> None:
    execute(
        "UPDATE sysconfig SET is_show = %(is_show)s WHERE id = 1",
        {"is_show": is_show},
    )
