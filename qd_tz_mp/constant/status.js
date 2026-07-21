// 支持查看的图像文件类型
export const IMAGE_FILE_LIST = ['png', 'jpg', 'jpeg', 'gif']

// 支持查看的其他文件类型
export const OTHER_FILE_LIST = ['doc', 'xls', 'ppt', 'pdf', 'docx', 'xlsx', 'pptx', 'txt']


// 静态资源地址
// 为极少部分没有返回oss地址的接口提供帮助
export const STATIC_URL = 'https://qgongye.oss-cn-shanghai.aliyuncs.com'

// 销售订单状态
// 实验分包订单状态列表
export const TEST_SUBPACKAGE_STATUS_LIST = [{
		id: 0,
		label: '已取消'
	},
	{
		id: 5,
		label: '采购成本未确认'
	},
	{
		id: 10,
		label: '已驳回'
	},
	{
		id: 20,
		label: '待审核'
	},
	{
		id: 30,
		label: '已审核'
	},
	{
		id: 40,
		label: '已确认'
	},
	{
		id: 49,
		label: '所有成本未结清'
	},
	{
		id: 50,
		label: '已完成'
	},
	{
		id: 35,
		label: '已下单'
	},
	{
		id: 45,
		label: '已发货'
	},
	{
		id: 46,
		label: '已入库'
	},
	{
		id: 66,
		label: '待平台确认'
	},
	{
		id: 67,
		label: '已和客户沟通确认'
	},
	{
		id: 1,
		label: '待支付'
	},
	{
		id: 2,
		label: '待实验'
	},
	{
		id: 3,
		label: '实验中'
	},
	{
		id: 4,
		label: '已完成'
	},
]


// 实验订单和实验分包订单状态列表
export const ORDER_STATUS = {
	0: "已取消",
	5: "订单未发起审核",
	10: "已驳回",
	20: "待审核",
	30: "已审核",
	40: "已确认",
	48: "已支付",
	49: "所有成本未结清",
	50: "已完成",
	32: "付款申请待审核",
	33: "付款申请已驳回",
	34: "付款申请已审核",
	36: "已付款",
	38: "已发货",
	35: "已下单",
	45: "已发货",
	46: "已入库",
	66: "待平台确认",
	67: "待客户确认",
	41: "已付款",
	42: "已开票"
}



// 实验分付款状态列表
export const TEST_SUBPACKAGE_PAY_STATUS_LIST = [{
		id: 0,
		label: '未申请'
	},
	{
		id: 32,
		label: '付款申请待审核'
	},
	{
		id: 33,
		label: '付款申请已驳回'
	},
	{
		id: 34,
		label: '付款申请已审核'
	},
	{
		id: 36,
		label: '已付款'
	},
	{
		id: 38,
		label: '已完成'
	}
]

// 实验订单状态
// 调租订单状态
// 采购订单状态
export const TEST_STATUS_LIST = [{
		id: 0,
		label: '已取消'
	},
	{
		id: 5,
		label: '采购成本未确认'
	},
	{
		id: 10,
		label: '已驳回'
	},
	{
		id: 20,
		label: '待审核'
	},
	{
		id: 30,
		label: '已审核'
	},
	{
		id: 40,
		label: '已确认'
	},
	{
		id: 49,
		label: '所有成本未结清'
	},
	{
		id: 50,
		label: '已完成'
	},
	{
		id: 35,
		label: '已下单'
	},
	{
		id: 45,
		label: '已发货'
	},
	{
		id: 46,
		label: '已入库'
	},
	{
		id: 66,
		label: '待平台确认'
	},
	{
		id: 67,
		label: '待客户确认'
	}
]

// 租赁订单列表
export const RNET_ORDER_STATUS_LIST = [{
		id: 0,
		label: '已取消'
	},
	{
		id: 6,
		label: '已提交'
	},
	{
		id: 5,
		label: '待提交审核'
	},
	{
		id: 10,
		label: '已驳回'
	},
	{
		id: 20,
		label: '待审核'
	},
	{
		id: 30,
		label: '已审核'
	},
	{
		id: 35,
		label: '已下单'
	},
	{
		id: 50,
		label: '已完成'
	},
]

// 采购订单支付状态
export const PURCHASE_ORDER_PAY_STATUS_LIST = [{
		id: 0,
		label: '未申请'
	},
	{
		id: 32,
		label: '待审核'
	},
	{
		id: 33,
		label: '已驳回'
	},
	{
		id: 34,
		label: '已审核'
	},
	{
		id: 36,
		label: '已付款'
	},
	{
		id: 38,
		label: '已完成'
	}
]

// 出库单状态
export const OUT_ORDER_STATUS = [{
		id: 1,
		label: '待入库'
	},
	{
		id: 2,
		label: '已入库'
	},
	{
		id: 3,
		label: '已废弃'
	},
]