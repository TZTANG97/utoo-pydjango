/**
 * Created by PanJiaChen on 16/11/18.
 */

/**
 * @param {string} path
 * @returns {Boolean}
 */
export function isExternal(path) {
  return /^(https?:|mailto:|tel:)/.test(path)
}

/**
 * @param {string} str
 * @returns {Boolean}
 */
export function validUsername(str) {
  const valid_map = ['admin', 'editor']
  return valid_map.indexOf(str.trim()) >= 0
}


// 验证邮箱
export function validEmail(val) {
  const reg = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return reg.test(val)
}

// 验证手机号
export function validMobile(val) {
  const reg = /^1[3-9]\d{9}$/
  return reg.test(val)
}

// 验证税号
export function validTaxNum(val) {
  const reg = /^\d{15}$/
  return reg.test(val)
}

// 是否包含汉字
export function validHasChinese(val) {
  const reg = /[\u4e00-\u9fa5]/
  return reg.test(val)
}

// 验证银行账号
export function validBankAccount(val) {
  const reg = /^\d{12,22}$/
  return reg.test(val)
}

//过滤
export function validNone(val) {
  return val.replace(/\s/g, '')
}
