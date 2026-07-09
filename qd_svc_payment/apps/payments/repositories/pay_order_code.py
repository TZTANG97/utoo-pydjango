from datetime import datetime

from apps.core.db_utils import fetch_one


def gen_code(seq: int) -> str:
    if seq < 100000:
        return str(seq).zfill(5)
    return str(seq)


def order_num_generate(order_type: int) -> str:
    prefix_map = {1: "ZF", 2: "CZ", 3: "HK"}
    prefix = prefix_map.get(order_type, "ZF")
    orderstr = prefix + datetime.now().strftime("%Y%m%d")
    row = fetch_one(
        """
        SELECT order_num FROM exp_pay_order_num
        WHERE order_num LIKE %(like)s
        ORDER BY order_num DESC
        LIMIT 1
        """,
        {"like": f"{orderstr}%"},
    )
    if row and row.get("order_num"):
        n = int(str(row["order_num"])[-5:]) + 1
        return orderstr + gen_code(n)
    return orderstr + gen_code(1)


def payment_pa_num_generate(pay_type: str) -> str:
    prefix_map = {"1": "CZ", "2": "HK", "3": "ZF", "4": "TX"}
    prefix = prefix_map.get(pay_type, "ZF")
    orderstr = prefix + datetime.now().strftime("%Y%m")
    row = fetch_one(
        """
        SELECT pa_num FROM pay_info_log
        WHERE pa_num LIKE %(like)s
        ORDER BY pa_num DESC
        LIMIT 1
        """,
        {"like": f"{orderstr}%"},
    )
    if row and row.get("pa_num"):
        n = int(str(row["pa_num"])[-5:]) + 1
        return orderstr + gen_code(n)
    return orderstr + gen_code(1)
