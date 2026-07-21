import r from '@/request/index.js'
import Vue from 'vue'

// 列表
export function List_dpt(data) {
	return r({
		url: `/redeem/xcx_List_dpt.ajax?draw=${data.draw}&start=${data.start}&length=${data.length}`,
		method: 'get',
	})
}
// 详情
export function redeemGoodsDetail(data) {
	return r({
		url: `/redeem/redeemGoodsDetail.ajax?id=${data}`,
		method: 'get',
	})
}

// 收货地址
export function getdeliveryaddress(data) {
	return r({
		url: `/pc/getdeliveryaddress.ajax`,
		method: 'get',
	})
}

// 兑换接口
export function duihuan(data) {
	return r({
		url: `/redeem/duihuan.ajax?id=${data.id}&userName=${data.userName}&mobile=${data.mobile}&address=${data.address}&nums=${data.nums}&prioritize=${data.prioritize}`,
		method: 'get',
	})
}

// 兑换记录
export function userredeemloglist(data) {
	return r({
		url: `/redeem/userredeemloglist.ajax?draw=${data.draw}&start=${data.start}&length=${data.length}`,
		method: 'get',
	})
}

// 积分刷新
export function getIntegral(data) {
	return r({
		url: `/pc/getIntegral.ajax`,
		method: 'get',
	})
}

// 积分记录
export function getIntegralList(data) {
	return r({
		url: `/wx/center/getIntegralList.ajax?draw=${data.draw}&start=${data.start}&length=${data.length}&type=${data.type}`,
		method: 'get',
	})
}

// 新增收货地址
export function insertdeliveryaddress(data) {
	return r({
		url: `/pc/insertdeliveryaddress.ajax?delivery_name=${data.name}&delivery_phone=${data.mobile}&delivery_address=${data.province}&detail_address=${data.address}`,
		method: 'get',
	})
}

// 修改收货地址
export function updatedeliveryaddress(data) {
	return r({
		url: `/pc/updatedeliveryaddress.ajax?id=${data.id}&delivery_name=${data.name}&delivery_phone=${data.mobile}&delivery_address=${data.province}&detail_address=${data.address}`,
		method: 'get',
	})
}
