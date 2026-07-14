import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@/utils/request'

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

async function getAjax(url: string, config?: RequestConfig) {
  return (await request.get(url, config)) as unknown as AjaxBody
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

async function fetchTree<T = Record<string, unknown>>(url: string, params?: Record<string, unknown>) {
  const res = await postAjax(url, params)
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    return res.obj as T[]
  }
  return []
}

async function fetchOptions<T = Record<string, unknown>>(url: string) {
  const res = await postAjax(url)
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    return res.obj as T[]
  }
  return []
}

// --- dept ---
export function fetchDeptTree() {
  return fetchTree('/sys/dept/loadAll.ajax')
}

export function fetchDeptOptions() {
  return fetchOptions('/sys/dept/options.ajax')
}

export function getDeptById(id: string | number) {
  return postAjax('/sys/dept/getById.ajax', { id })
}

export function addDept(data: Record<string, unknown>) {
  return postAjax('/sys/dept/add.ajax', data)
}

export function updateDept(data: Record<string, unknown>) {
  return postAjax('/sys/dept/update.ajax', data)
}

export function deleteDept(id: string | number) {
  return postAjax('/sys/dept/del.ajax', { id })
}

// --- user ---
export function fetchUserList(params: Record<string, unknown>) {
  return fetchDatatable('/sys/user/queryUsers.ajax', params)
}

export function getUserById(id: string | number) {
  return postAjax('/sys/user/getById.ajax', { id })
}

export function addUser(data: Record<string, unknown>) {
  return postAjax('/sys/user/add.ajax', data)
}

export function updateUser(data: Record<string, unknown>) {
  return postAjax('/sys/user/update.ajax', data)
}

export function deleteUser(id: string | number) {
  return postAjax('/sys/user/del.ajax', { id })
}

export function fetchUserRoleOptions() {
  return fetchOptions('/sys/user/roleOptions.ajax')
}

// --- role ---
export function fetchRoleList(params: Record<string, unknown>) {
  return fetchDatatable('/sys/role/query.ajax', params)
}

export function getRoleById(id: string | number) {
  return postAjax('/sys/role/getById.ajax', { id })
}

export function addRole(data: Record<string, unknown>) {
  return postAjax('/sys/role/add.ajax', data)
}

export function updateRole(data: Record<string, unknown>) {
  return postAjax('/sys/role/update.ajax', data)
}

export function deleteRole(id: string | number) {
  return postAjax('/sys/role/del.ajax', { id })
}

export async function fetchRolePower(roleId: string | number) {
  const res = await postAjax('/sys/role/power/query.ajax', { id: roleId })
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    return res.obj as (string | number)[]
  }
  return []
}

export function updateRolePower(roleId: string | number, menuIds: (string | number)[]) {
  return postAjax('/sys/role/power/update.ajax', { id: roleId, menuIds })
}

// --- menu ---
export function fetchMenuTree() {
  return fetchTree('/sys/menu/query.ajax')
}

export function getMenuById(id: string | number) {
  return postAjax('/sys/menu/getById.ajax', { id })
}

export function addMenu(data: Record<string, unknown>) {
  return postAjax('/sys/menu/add.ajax', data)
}

export function updateMenu(data: Record<string, unknown>) {
  return postAjax('/sys/menu/update.ajax', data)
}

export function deleteMenu(id: string | number) {
  return postAjax('/sys/menu/del.ajax', { id })
}

// --- district ---
export function fetchDistrictList(params: Record<string, unknown>) {
  return fetchDatatable('/sys/district/query.ajax', params)
}

export function fetchDistrictChildren(superId: string | number) {
  return postAjax('/sys/district/children.ajax', { superId })
}

export function addDistrict(data: Record<string, unknown>) {
  return postAjax('/sys/district/add.ajax', data)
}

export function updateDistrict(data: Record<string, unknown>) {
  return postAjax('/sys/district/update.ajax', data)
}

export function deleteDistrict(id: string | number) {
  return postAjax('/sys/district/del.ajax', { id })
}

// --- userType ---
export function fetchUserTypeList(params: Record<string, unknown>) {
  return fetchDatatable('/sys/userType/query.ajax', params)
}

export function getUserTypeById(id: string | number) {
  return postAjax('/sys/userType/getById.ajax', { id })
}

export function addUserType(data: Record<string, unknown>) {
  return postAjax('/sys/userType/add.ajax', data)
}

export function updateUserType(data: Record<string, unknown>) {
  return postAjax('/sys/userType/update.ajax', data)
}

export function deleteUserType(id: string | number) {
  return postAjax('/sys/userType/del.ajax', { id })
}

export function fetchTypeRoleOptions() {
  return fetchOptions('/sys/userType/typeRoleOptions.ajax')
}

// --- area ---
export function fetchAreaList(params: Record<string, unknown>) {
  return fetchDatatable('/district/getAreaList.ajax', params)
}

export function submitArea(data: { areaName: string }) {
  return postAjax('/district/submitArea.ajax', data)
}

export function updateArea(data: { id: string | number; areaName: string }) {
  return postAjax('/district/updateArea.ajax', data)
}

export function deleteArea(id: string | number) {
  return postAjax('/district/updateStatus.ajax', { id })
}

export function fetchAreaOptions() {
  return fetchOptions('/district/areaOptions.ajax')
}

// --- supplier (所属公司) ---
export function fetchSupplierList(params: Record<string, unknown>) {
  return fetchDatatable('/supplier/getSupplierList.ajax', params)
}

export function fetchSupplierAll() {
  return postAjax('/supplier/queryAll.ajax')
}

export function getSupplierById(id: string | number) {
  return postAjax('/supplier/getById.ajax', { id })
}

export function saveSupplier(data: Record<string, unknown>) {
  return postAjax('/supplier/saveSupplier.ajax', data)
}

export function deleteSupplier(id: string | number) {
  return postAjax('/supplier/deleteById.ajax', { id })
}

// --- userCompany (企业会员公司，备用) ---
export function fetchCompanyList(params: Record<string, unknown>) {
  return fetchDatatable('/userCompany/getUserCompanyList.ajax', params)
}

export function getCompanyById(id: string | number) {
  return postAjax('/userCompany/getById.ajax', { id })
}

export function saveCompany(data: Record<string, unknown>) {
  return postAjax('/userCompany/saveUserCompany.ajax', data)
}

export function updateCompany(data: Record<string, unknown>) {
  return postAjax('/userCompany/updateUserCompany.ajax', data)
}

export function deleteCompany(id: string | number) {
  return postAjax('/userCompany/deleteById.ajax', { id })
}

// --- appUser ---
export function fetchAppUserList(params: Record<string, unknown>) {
  return fetchDatatable('/appUser/list.ajax', params)
}

export function getAppUserById(id: string | number) {
  return postAjax('/appUser/getById.ajax', { id })
}

// --- testaddress ---
export function fetchTestAddressList(params: Record<string, unknown>) {
  return fetchDatatable('/testaddress/selectalladdress.ajax', params)
}

export function getTestAddressById(id: string | number) {
  return postAjax('/testaddress/getAddressById.ajax', { id })
}

export function createTestAddress(data: Record<string, unknown>) {
  return postAjax('/testaddress/addresscreate.ajax', data)
}

export function updateTestAddress(data: Record<string, unknown>) {
  return postAjax('/testaddress/updateStatus1.ajax', data)
}

export function deleteTestAddress(id: string | number) {
  return postAjax('/testaddress/updateStatus.ajax', { id })
}

// --- companyaccount ---
export function fetchCompanyAccountList(params: Record<string, unknown>) {
  return fetchDatatable('/companyaccount/selectallaccount.ajax', params)
}

export function getCompanyAccountById(id: string | number) {
  return postAjax('/companyaccount/getAddressById.ajax', { id })
}

export function createCompanyAccount(data: Record<string, unknown>) {
  return postAjax('/companyaccount/accountcreate.ajax', data)
}

export function updateCompanyAccount(data: Record<string, unknown>) {
  return postAjax('/companyaccount/updateStatus1.ajax', data)
}

export function deleteCompanyAccount(id: string | number) {
  return postAjax('/companyaccount/updateStatus.ajax', { id })
}

export async function fetchDefaultCompanyAccount() {
  const res = await postAjax('/companyaccount/defaultaddress.ajax')
  if (isAjaxOk(res) && res.obj && typeof res.obj === 'object') {
    return res.obj as Record<string, unknown>
  }
  return null
}

export function setDefaultCompanyAccount(id: string | number) {
  return postAjax('/companyaccount/updatedefault.ajax', { id })
}
