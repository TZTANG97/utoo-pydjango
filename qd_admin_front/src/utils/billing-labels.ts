export const INVOICE_STATUS: Record<number, string> = {
  1: '开票中',
  3: '已作废',
  4: '已开票',
  5: '已驳回',
}

export const INVOICE_TYPE: Record<number, string> = {
  1: '增值税专用发票',
  2: '增值税普通发票',
}

export const PAY_TYPE: Record<number, string> = {
  1: '充值',
  2: '还款',
  3: '支付',
  4: '提现',
}

export const PAY_WAY: Record<number, string> = {
  1: '支付宝',
  2: '微信',
  3: '线下',
  4: '余额',
}

export const PAYMENT_ORDER_TYPE: Record<string, string> = {
  '1': '账号充值',
  '2': '订单缴费',
  '3': '订单缴费',
  '4': '提现',
}

export const PAYMENT_APPLY_STATUS: Record<string, string> = {
  '1': '待审核',
  '2': '已审核',
  '3': '已拒绝',
}

export const RETEST_STATUS: Record<number, string> = {
  0: '待审核',
  1: '已同意',
  2: '已拒绝',
}

export function formatDate(value: unknown) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 19)
}

export function formatMoney(value: unknown) {
  const num = Number(value || 0)
  return Number.isFinite(num) ? num.toFixed(2) : '0.00'
}
