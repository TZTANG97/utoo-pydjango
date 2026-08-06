import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@admin/utils/request'

export type { AjaxBody }
export { isAjaxOk }

export interface DataTableResult<T = Record<string, unknown>> {
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
  data?: T[]
}

async function postAjax(
  url: string,
  data?: Record<string, unknown>,
  config?: RequestConfig
) {
  return (await request.post(url, data, config)) as unknown as AjaxBody
}

async function fetchDatatable<T>(
  url: string,
  params: Record<string, unknown>
): Promise<DataTableResult<T>> {
  const res = await postAjax(url, params)
  const payload = (res.data ? res : (res.obj as DataTableResult<T> | undefined) || res) as DataTableResult<T>
  return {
    draw: payload.draw || 1,
    recordsTotal: payload.recordsTotal || 0,
    recordsFiltered: payload.recordsFiltered || 0,
    data: Array.isArray(payload.data) ? payload.data : [],
  }
}

// Banner
export function fetchBannerList(params: Record<string, unknown>) {
  return fetchDatatable('/banner/photolist.ajax', params)
}

export function fetchXcxfmBannerList(params: Record<string, unknown>) {
  return fetchDatatable('/banner/xcxfmlist.ajax', params)
}

export function getBannerDetail(bid: string | number) {
  return postAjax('/banner/detail.ajax', { bid })
}

export function createBanner(data: Record<string, unknown>) {
  return postAjax('/banner/slidecreate.ajax', data)
}

export function updateBanner(data: Record<string, unknown>) {
  return postAjax('/banner/slideupdate.ajax', data)
}

export function createXcxfmBanner(data: Record<string, unknown>) {
  return postAjax('/banner/xcxfmslidecreate.ajax', data)
}

export function updateXcxfmBanner(data: Record<string, unknown>) {
  return postAjax('/banner/xcxfmslideupdate.ajax', data)
}

export function deleteBanner(id: string | number) {
  return postAjax('/banner/delBanner.ajax', { id })
}

export function toggleBannerShow(id: string | number) {
  return postAjax('/banner/updateisshow.ajax', { id })
}

/** 对齐 Java seller/swf_upload.ajax，返回 accessory id + url */
export async function uploadSellerImage(file: File) {
  const fd = new FormData()
  fd.append('imgFile', file)
  return (await request.post('/seller/swf_upload.ajax', fd, {
    timeout: 60000,
  })) as unknown as AjaxBody
}

// Advert
export function fetchAdvertList(params: Record<string, unknown>) {
  return fetchDatatable('/admin/advert_list.ajax', params)
}

export function getAdvertDetail(id: string | number) {
  return postAjax('/admin/advert_detail.ajax', { id })
}

export function saveAdvert(data: Record<string, unknown>) {
  return postAjax('/admin/advert_save.ajax', data)
}

export function deleteAdvert(id: string | number) {
  return postAjax('/admin/advert_del.ajax', { id })
}

export function fetchAdvPosList(params: Record<string, unknown>) {
  return fetchDatatable('/admin/adv_pos_list.ajax', params)
}

export function getAdvPosDetail(id: string | number) {
  return postAjax('/admin/adv_pos_detail.ajax', { id })
}

export function saveAdvPos(data: Record<string, unknown>) {
  return postAjax('/admin/adv_pos_save.ajax', data)
}

export function deleteAdvPos(id: string | number) {
  return postAjax('/admin/adv_pos_del.ajax', { id })
}

export function fetchAdvPosOptions() {
  return postAjax('/admin/adv_pos_options.ajax')
}

// QdSetting
export function getOpsSetting(settingType: string) {
  return postAjax('/edit/set_get.ajax', { settingType })
}

export function saveOpsSetting(settingType: string, imgsrc: string) {
  return postAjax('/edit/set_update.ajax', { settingType, imgsrc })
}

// Redeem
export function fetchRedeemLogList(params: Record<string, unknown>) {
  return fetchDatatable('/redeem/redeemloglist.ajax', params)
}

export function getRedeemLogDetail(id: string | number) {
  return postAjax('/redeem/redeemGoodsLogDetail.ajax', { id })
}

export function shipRedeemLog(data: Record<string, unknown>) {
  return postAjax('/redeem/shipment.ajax', data)
}

// Entry / Comment
export function fetchEntryList(params: Record<string, unknown>) {
  return fetchDatatable('/entry/entryList.ajax', params)
}

export function getEntryDetail(id: string | number) {
  return postAjax('/entry/entryDetail.ajax', { id })
}

export function auditEntry(id: string | number) {
  return postAjax('/entry/auditEntry.ajax', { id })
}

export function fetchCommentList(params: Record<string, unknown>) {
  return fetchDatatable('/entry/commentList.ajax', params)
}

export function getCommentDetail(id: string | number) {
  return postAjax('/entry/commentDetail.ajax', { id })
}

export function auditComment(id: string | number) {
  return postAjax('/entry/auditComment.ajax', { id })
}

export function deleteComment(id: string | number) {
  return postAjax('/entry/deletecomment.ajax', { id })
}

// Whitelist
export function fetchWhitelist(params: Record<string, unknown>) {
  return fetchDatatable('/whitelist/whitelist.ajax', params)
}

export function getWhitelistDetail(id: string | number) {
  return postAjax('/whitelist/detail.ajax', { id })
}

export function addWhitelist(data: Record<string, unknown>) {
  return postAjax('/whitelist/addwhitelist.ajax', data)
}

export function updateWhitelist(data: Record<string, unknown>) {
  return postAjax('/whitelist/updatewhitelist.ajax', data)
}

export function deleteWhitelist(id: string | number) {
  return postAjax('/whitelist/delete.ajax', { id })
}

export function fetchSyUserOptions(keyword = '') {
  return postAjax('/whitelist/syUsers.ajax', { keyword })
}

// Goods
export function fetchGoodsList(params: Record<string, unknown>) {
  return fetchDatatable('/goods/goods_list.ajax', params)
}

export function fetchGoodsBrandOptions() {
  return postAjax('/goods/brand_options.ajax')
}

export function fetchGoodsClassOptions() {
  return postAjax('/goods/class_options.ajax')
}

export function toggleGoodsRecommend(id: string | number) {
  return postAjax('/goods/updateRecommend.ajax', { id })
}

export function toggleGoodsSale(id: string | number) {
  return postAjax('/goods/goods_sale.ajax', { id })
}

// Product catalog
export function fetchSpecList(params: Record<string, unknown>) {
  return fetchDatatable('/goodspec/list.ajax', params)
}
export function getSpecDetail(id: string | number) {
  return postAjax('/goodspec/detail.ajax', { id })
}
export function saveSpec(data: Record<string, unknown>) {
  return postAjax('/goodspec/save.ajax', data)
}
export function deleteSpec(id: string | number) {
  return postAjax('/goodspec/del.ajax', { id })
}

export function fetchBrandList(params: Record<string, unknown>) {
  return fetchDatatable('/goodsbrand/list.ajax', params)
}
export function getBrandDetail(id: string | number) {
  return postAjax('/goodsbrand/detail.ajax', { id })
}
export function saveBrand(data: Record<string, unknown>) {
  return postAjax('/goodsbrand/save.ajax', data)
}
export function deleteBrand(id: string | number) {
  return postAjax('/goodsbrand/del.ajax', { id })
}

export function fetchGoodsTypeList(params: Record<string, unknown>) {
  return fetchDatatable('/goodstype/list.ajax', params)
}
export function getGoodsTypeDetail(id: string | number) {
  return postAjax('/goodstype/detail.ajax', { id })
}
export function saveGoodsType(data: Record<string, unknown>) {
  return postAjax('/goodstype/save.ajax', data)
}
export function deleteGoodsType(id: string | number) {
  return postAjax('/goodstype/del.ajax', { id })
}
export function fetchGoodsTypeOptions() {
  return postAjax('/goodstype/options.ajax')
}

export function fetchGoodsClassList(parentId?: string | number | null) {
  return postAjax('/goodsclass/list.ajax', { parent_id: parentId ?? '' })
}
export function getGoodsClassDetail(id: string | number) {
  return postAjax('/goodsclass/detail.ajax', { id })
}
export function saveGoodsClass(data: Record<string, unknown>) {
  return postAjax('/goodsclass/save.ajax', data)
}
export function deleteGoodsClass(id: string | number) {
  return postAjax('/goodsclass/del.ajax', { id })
}

export function fetchAlbumList(params: Record<string, unknown>) {
  return fetchDatatable('/album/list.ajax', params)
}
export function getAlbumDetail(id: string | number) {
  return postAjax('/album/detail.ajax', { id })
}
export function saveAlbum(data: Record<string, unknown>) {
  return postAjax('/album/save.ajax', data)
}
export function deleteAlbum(id: string | number) {
  return postAjax('/album/del.ajax', { id })
}
export function fetchAlbumImages(params: Record<string, unknown>) {
  return fetchDatatable('/album/images.ajax', params)
}
/** 对齐 Java seller/goods_img_album：轮播等「从相册选择」列表（path=goods） */
export function fetchGoodsAlbumImages(params: Record<string, unknown>) {
  return fetchDatatable('/album/goods_images.ajax', params)
}
export function deleteAlbumImage(id: string | number) {
  return postAjax('/album/image_del.ajax', { id })
}
export function setAlbumCover(albumId: string | number, imageId: string | number) {
  return postAjax('/album/cover.ajax', { album_id: albumId, image_id: imageId })
}

export function fetchGoodsEvaluateList(params: Record<string, unknown>) {
  return fetchDatatable('/evaluate/list.ajax', params)
}
export function getGoodsEvaluateDetail(id: string | number) {
  return postAjax('/evaluate/detail.ajax', { id })
}
export function checkGoodsEvaluate(id: string | number, type?: string | number) {
  return postAjax('/evaluate/check.ajax', { id, type })
}

export function getConsultConfig() {
  return postAjax('/consult/consultConfigGet.ajax')
}
export function saveConsultConfig(data: Record<string, unknown>) {
  return postAjax('/consult/consultConfigSave.ajax', data)
}
