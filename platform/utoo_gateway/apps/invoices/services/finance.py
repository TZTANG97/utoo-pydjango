import logging

from apps.core.db_utils import scalar

logger = logging.getLogger(__name__)


def us_exchange_rate() -> float:
    try:
        val = scalar("SELECT us_exchange_rate FROM account_setting LIMIT 1", {}, None)
        if val is not None:
            return float(val)
    except Exception as exc:
        logger.warning("account_setting read failed: %s", exc)
    return 1.0


def exp_receive_sum_pc(*, user_id: int, mobile: str, currency_type: int) -> float:
    """对齐 experimentOrderDao.expReceiveSumPc（待支付金额汇总）"""
    sql = """
        SELECT IFNULL(SUM(tab.money), 0) FROM (
            SELECT t.totalPrice - IFNULL(qdtab.zfje, 0) AS money
            FROM experiment_order t
            LEFT JOIN (
                SELECT qb.exp_of_id, COUNT(qb.id) AS num, SUM(qb.money) AS zfje
                FROM qd_bill qb WHERE qb.type = 2 GROUP BY qb.exp_of_id
            ) qdtab ON t.id = qdtab.exp_of_id
            LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
            WHERE t.order_type IN ('6', '8')
              AND t.order_status >= 30
              AND IFNULL(qdtab.num, 0) < (
                  LENGTH(IFNULL(t.collection_time, ''))
                  - LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', '')) + 1
              )
              AND (
                t.custom_user_id = %(user_id)s
                OR CAST(t.custom_user_id AS CHAR) = %(user_id_str)s
                OR quc.contract_phone = %(mobile)s
                OR t.mobile = %(mobile)s
              )
              AND t.currency_type = %(ctype)s
        ) tab
    """
    params = {
        "user_id": user_id,
        "user_id_str": str(user_id),
        "mobile": mobile,
        "ctype": currency_type,
    }
    return float(scalar(sql, params, 0) or 0)


def get_all_money_dkp(*, user_id: int, mobile: str, currency_type: int) -> float:
    sql = """
        SELECT IFNULL(SUM(tab.money), 0) FROM (
            SELECT t.totalPrice - IFNULL(qdtab.kpje, 0) AS money
            FROM experiment_order t
            LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
            LEFT JOIN (
                SELECT qb.exp_of_id, COUNT(qb.id) AS num, SUM(qb.money) AS kpje
                FROM qd_bill qb WHERE qb.type = 1 GROUP BY qb.exp_of_id
            ) qdtab ON t.id = qdtab.exp_of_id
            WHERE t.order_status IN (30, 40, 50)
              AND t.order_type IN ('6', '8')
              AND t.invoiceType = 1 AND t.is_online = 0 AND t.is_apply = 0
              AND IFNULL(qdtab.kpje, 0) < t.totalPrice
              AND IFNULL(qdtab.num, 0) < (
                  LENGTH(IFNULL(t.collection_time, ''))
                  - LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', '')) + 1
              )
              AND (
                t.custom_user_id = %(user_id)s
                OR CAST(t.custom_user_id AS CHAR) = %(user_id_str)s
                OR quc.contract_phone = %(mobile)s
                OR t.mobile = %(mobile)s
              )
              AND t.currency_type = %(ctype)s
            UNION ALL
            SELECT IFNULL(qdtab.kpje, 0) AS money
            FROM experiment_order t
            LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
            LEFT JOIN (
                SELECT qb.exp_of_id, SUM(qb.money) AS kpje
                FROM qd_bill qb
                WHERE qb.type = 2 AND qb.is_apply = 0
                GROUP BY qb.exp_of_id
            ) qdtab ON t.id = qdtab.exp_of_id
            WHERE t.invoiceType = 1 AND t.order_type IN ('6', '8')
              AND t.is_online = 1 AND IFNULL(qdtab.kpje, 0) > 0
              AND (
                t.custom_user_id = %(user_id)s
                OR CAST(t.custom_user_id AS CHAR) = %(user_id_str)s
                OR quc.contract_phone = %(mobile)s
                OR t.mobile = %(mobile)s
              )
              AND t.currency_type = %(ctype)s
        ) tab
    """
    params = {
        "user_id": user_id,
        "user_id_str": str(user_id),
        "mobile": mobile,
        "ctype": currency_type,
    }
    return float(scalar(sql, params, 0) or 0)
