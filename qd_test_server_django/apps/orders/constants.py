STATUS_STR = {30: "已审核", 50: "已完成", 51: "已评价", 55: "已评价"}

CHILD_ORDERSTATUS_STR = {
    0: "已取消",
    1: "待处理",
    2: "已审核",
    10: "生产中",
    20: "运输中",
    30: "已签收",
    38: "测试中",
    39: "测试完成",
    40: "已验收",
    50: "已完成",
}


PURCHASE_ORDERSTATUS_STR = {
    0: "已取消",
    5: "待提交审核",
    10: "已驳回",
    20: "待审核",
    30: "已审核",
    35: "已下单",
    36: "样品到货",
    37: "样品领用",
    38: "测试中",
    39: "测试完成",
    40: "已确认",
    41: "样品归还",
    42: "客户确认完成",
    43: "样品寄回",
    44: "样品留存",
    45: "已发货",
    46: "已入库",
    49: "所有成本未结清",
    50: "实验完成",
    55: "已评价",
    66: "待平台确认",
    67: "已和客户沟通确认",
}


def child_order_status_str(status: int) -> str:
    return CHILD_ORDERSTATUS_STR.get(status, "处理中")


def purchase_order_status_str(status: int) -> str:
    return PURCHASE_ORDERSTATUS_STR.get(status, "处理中")
