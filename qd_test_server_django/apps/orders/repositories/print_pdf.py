from typing import Any

from apps.core.db_utils import fetch_all, fetch_one


def fetch_print_pdf_rows(order_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            eo.id AS eid,
            eo.order_id AS ord_id,
            eo.addTime,
            eo.test_address_id,
            eo.reverso_context,
            eo.send_address,
            eo.addressee_name,
            eo.addressee_mobile,
            eo.is_video,
            eo.class_id,
            eo.is_arrive,
            eo.is_on,
            sc.userName,
            sc.mobile AS sc_mobile,
            sc.send_address AS sc_send_address,
            sc.reverso_context AS sc_reverso_context,
            eoc.id AS cid,
            eoc.experiment_class_name,
            eoc.order_id AS ordc_id,
            eoc.goods_name,
            eoc.goods_nums,
            eoc.experiment_project_name,
            eoc.sample_id,
            osi.main_component,
            osi.is_magnetic,
            osi.is_gold_spraying,
            osi.attribute_id,
            osi.gold_desc
        FROM experiment_order eo
        LEFT JOIN service_consult sc ON eo.id = sc.order_id
        LEFT JOIN experiment_order_child eoc ON eo.id = eoc.order_form_id
        LEFT JOIN order_sample_information osi ON eoc.sample_id = osi.id
        WHERE eo.id = %(oid)s
        """,
        {"oid": order_id},
    )


def get_test_address(test_address_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT address FROM test_address WHERE id = %(tid)s LIMIT 1",
        {"tid": test_address_id},
    )
