import r from '@/request/index.js'
import Vue from 'vue'

// 列表
export function list(data) {
	return r({
		url: `/consult/list.ajax`,
		method: 'post',
		data
	})
}

// 详情
export function consultDetail(data) {
	return r({
		url: `/consult/consultDetail.ajax`,
		method: 'post',
		data
	})
}

// 实验测试分类
export function queryAll3(data) {
	return r({
		url: `/experimentManage/queryAll.ajax?type=${data}`,
	})
}

// 实验测试地址
export function addressList() {
	return r({
		url: `/testaddress/addressList.ajax`,
	})
}

// 公司汇款账户
export function accountList() {
	return r({
		url: `/companyaccount/accountList.ajax`,
	})
}


// 获取我的认证信息
export function getPersonAuthInfoApi() {
	return r({
		url: `/wx/getIdentifyData.ajax`,
	})
}

// 保存
export function updateConsult(data) {
	return r({
		url: '/consult/updateConsult.ajax',
		method: 'post',
		cType: 'application/json',
		data
	})
}

// 生成订单
export function saveOrder(data) {
	return r({
		url: '/consult/saveOrder.ajax',
		method: 'post',
		cType: 'application/json',
		data
	})
}

// 取消咨询
export function cancelConsult(data) {
	return r({
		url: '/consult/cancelConsult.ajax?id='+data.id,
	})
}

// 新增产品
// export function submitExperimentGoods(data) {
// 	return r({
// 		url: '/experimentGoods/submitExperimentGoods.ajax',
// 		method: 'post',
// 		cType: 'application/json',
// 		data
// 	})
// }

export function submitExperimentGoods(data) {
	return r({
		url: '/experimentGoods/submitExperimentGoods.ajax?id='+data.id+'&goods_brand_id='+data.goods_brand_id+'&goods_model='+data.goods_model,
	})
}

// 新增产品名称
// export function addGoodsName(data) {
// 	return r({
// 		url: '/experimentGoods/addGoodsName.ajax',
// 		method: 'post',
// 		cType: 'application/json',
// 		data
// 	})
// }
export function addGoodsName(data) {
	return r({
		url: '/experimentGoods/addGoodsName.ajax?goods_name='+data.goods_name+'&goods_brand_id='+data.goods_brand_id,
	})
}

// 删除产品名称
export function delGoodsName(data) {
	return r({
		url: '/experimentGoods/delGoodsName.ajax?id='+data,
	})
}



// 所属品牌
export function queryBrand(data) {
	return r({
		url: '/goodsbrand/queryBrand.ajax?type=2',
	})
}

// 产品名称
export function loadGoodsNames(data) {
	return r({
		url: '/experimentGoods/loadGoodsNames.ajax?goods_brand_id='+data.goods_brand_id,
	})
}

// 产品型号
export function selGoodsModels(data) {
	return r({
		url: '/experimentGoods/selGoodsModels.ajax?id='+data,
	})
}

// 一级分类
export function queryAll(data) {
	return r({
		url: '/experimentManage/queryAll.ajax?type=1',
	})
}
// 二/三级分类
export function queryByParentId(data) {
	return r({
		url: '/experimentManage/queryByParentId.ajax?parent_id='+data,
	})
}

// 新增实验项目
export function submitExperimentProject(data) {
	return r({
		url: `/experimentProject/submitExperimentProject.ajax?first_id=${data.first_id}&sec_id=${data.sec_id}&class_id=${data.class_id}&country=${data.country}&test_price=${data.test_price}&project_name=${data.project_name}`,
	})
}
// 设备名称列表
export function sbList(data) {
	return r({
		url: '/experimentProject/list.ajax?project_name='+data.project_name+'&start='+data.start+'&length='+data.length+'&draw='+data.draw,
	})
}

// 样品列表
export function querySampleList(data) {
	return r({
		url: '/consult/querySampleList.ajax?consultId='+data.consultId
	})
}

