export interface AdminMenuItem {
  id?: string | number
  menu_name?: string
  menu_url?: string
  menu_icon?: string
  menu_order?: number
  parent_id?: string | number | null
  children?: AdminMenuItem[]
}

export interface LoginResult {
  token: string
  refreshToken?: string
  userType?: number
  userName?: string
  loginName?: string
  uRoleName?: string
}

export interface WelcomeLogItem {
  id?: string | number
  addTime?: string
  content?: string
  userName?: string
  loginName?: string
  ip?: string
  title?: string
  type?: number
  userId?: string | number
}

export interface WelcomeData {
  userName?: string
  loginName?: string
  userType?: number
  /** 对齐 Java welcome.ajax userType2：1管理员交易 2销售额 3测试数量 0无 */
  userType2?: number
  roleName?: string
  deptName?: string
  email?: string
  mobilePhoneNumber?: string
  menuCount?: number
  xdate?: string[]
  ydata?: string[]
  chartKind?: 'none' | 'admin_trade' | 'user_sale' | 'user_test' | string
  chartTitle?: string
  chartUnit?: string
  showAssets?: boolean
  accountRMB?: string | number
  accountUS?: string | number
  pendingCounts?: {
    expOrder?: number
    subcontractOrder?: number
    subcontractSubOrder?: number
  }
  newlogs?: WelcomeLogItem[]
}
