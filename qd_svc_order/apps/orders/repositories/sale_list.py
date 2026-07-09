"""主订单列表 Tab 筛选所需的 JOIN / WHERE 片段（SQL 只在此文件）。"""

RECEIVE_PLAN_PC_JOINS = """
    LEFT JOIN (
        SELECT qb.exp_of_id, COUNT(qb.id) AS num
        FROM qd_bill qb WHERE qb.type = 2 GROUP BY qb.exp_of_id
    ) qdtab ON t.id = qdtab.exp_of_id
    LEFT JOIN (
        SELECT qb.exp_of_id, COUNT(qb.id) AS num
        FROM exp_online_qd_bill qb WHERE qb.type = 2 GROUP BY qb.exp_of_id
    ) qdtab2 ON t.id = qdtab2.exp_of_id
"""

RECEIVE_PLAN_PC_EXTRA = """
    AND IFNULL(qdtab.num, 0) < (
        LENGTH(IFNULL(t.collection_time, '')) -
        LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', '')) + 1
    )
    AND IFNULL(qdtab2.num, 0) < 1
"""

BILLABLE_EXTRA = """
    AND t.order_status IN (30, 40, 50)
    AND t.invoiceType = 1 AND t.is_apply = 0
"""

AFTER_SALE_EXTRA = """
    AND t.is_online = 1
    AND EXISTS (
        SELECT 1 FROM experiment_order_child eoc
        WHERE eoc.order_form_id = t.id
          AND eoc.delete_status = 2
          AND IFNULL(eoc.fcsq, 0) = 0
          AND eoc.is_sure IS NULL
          AND eoc.order_status IN (39, 41)
    )
"""
