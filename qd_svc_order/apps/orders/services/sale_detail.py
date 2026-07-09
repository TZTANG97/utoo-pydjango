from typing import Any

from apps.orders.repositories import accessory_list as acc_repo
from apps.orders.repositories import orders as repo
from apps.orders.repositories import qd_bill as qd_bill_repo
from apps.orders.services import detail_flags
from apps.orders.services import jdshow as jdshow_svc
from apps.orders.services import sale_detail_enrich as enrich
from apps.core.services.sysconfig import get_config_row, image_web_server
from qd_common.serialize import to_jsonable


def order_detail(*, user_id: int, order_id: int) -> dict[str, Any]:
    """对齐 ExperimentOrderController.orderDetailAjax（C 端）"""
    _, mobile = repo.user_context(user_id)
    empty: dict[str, Any] = {
        "of": None,
        "logs": [],
        "collectionTimes": [],
        "openBills": [],
        "testFiles": [],
        "files": [],
        "hzdFiles": [],
        "jdshow": 0,
        "ispjqx": False,
        "bhyy": "",
        "yydUrl": "",
        "yspAndDhList": [],
        "viewReciveBtn": False,
        "viewKpBtn": False,
        "hzdpath": "",
    }
    if order_id <= 0:
        return empty

    of = repo.get_sale_order_for_user(
        order_id=order_id, user_id=user_id, mobile=mobile
    )
    if not of:
        return empty

    oid = int(of["id"])
    config = get_config_row()
    image_base = image_web_server(config) or ""

    open_bills = [enrich.enrich_bill_row(dict(b)) for b in repo.load_bills(oid, 1)]
    receive_bills = [enrich.enrich_bill_row(dict(b)) for b in repo.load_bills(oid, 2)]
    skje = sum(float(b.get("money") or 0) for b in receive_bills)
    has_online = qd_bill_repo.has_online_receive_bill(oid)

    enrich.enrich_sale_order(
        of,
        skje,
        kaip_bills=open_bills,
        receive_bills=receive_bills,
        has_online_receive=has_online,
    )
    of["order_statusstr"] = enrich.compute_sale_order_statusstr(of, oid)
    isfk = of.get("isfk", "0")
    jdshow = jdshow_svc.compute_jdshow(oid, str(isfk))
    ispjqx = bool(of.pop("ispjqx", False))

    yyd_url, hzdpath, ysp_and_dh = enrich.enrich_pc_order_detail(of, order_id=oid)

    files = enrich.enrich_accessory_rows(
        acc_repo.load_accessories(exp_of_id=oid, exclude_types=(5, 7)),
        image_base,
    )
    hzd_files = enrich.enrich_accessory_rows(
        acc_repo.load_accessories(child_of_id=oid, file_type=7),
        image_base,
    )
    test_files = enrich.enrich_accessory_rows(
        acc_repo.load_all_test_files(oid),
        image_base,
    )

    view_receive = detail_flags.compute_view_receive_btn(
        order_id=oid, of=of, receive_bills=receive_bills
    )
    view_kp = detail_flags.compute_view_kp_btn(
        order_id=oid, of=of, open_bills=open_bills
    )

    return {
        **empty,
        "of": to_jsonable(of),
        "logs": repo.load_logs(oid),
        "collectionTimes": enrich.build_collection_times(of, receive_bills),
        "openBills": [to_jsonable(b) for b in open_bills],
        "testFiles": test_files,
        "files": files,
        "hzdFiles": hzd_files,
        "jdshow": jdshow,
        "ispjqx": ispjqx,
        "viewReciveBtn": view_receive,
        "viewKpBtn": view_kp,
        "yydUrl": yyd_url,
        "hzdpath": hzdpath,
        "yspAndDhList": ysp_and_dh,
        "bhyy": of.get("bhyy") or "",
    }
