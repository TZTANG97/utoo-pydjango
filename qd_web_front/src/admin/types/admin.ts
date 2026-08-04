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

export interface WelcomePendingCounts {
  expOrder?: number
  selfChildOrder?: number
  subcontractOrder?: number
  subcontractSubOrder?: number
  materialSubOrder?: number
}

export interface WelcomeOpsCounts {
  notStarted?: number
  inProgress?: number
  timeout?: number
}

export interface WelcomeData {
  userName?: string
  loginName?: string
  currentUser?: string
  userType?: number
  /** 对齐 Java：1管理员交易 2销售额 3测试数量 0无 */
  userType2?: number
  roleName?: string
  deptName?: string
  email?: string
  mobilePhoneNumber?: string
  menuCount?: number
  /** 管理员近 6 月 */
  xdate?: string[]
  ydata?: string[]
  /** 个人销售额（双币种） */
  saleYear?: string
  xmonths?: string[]
  userSaleAryrmb?: Array<string | number>
  userSaleAryus?: Array<string | number>
  qnxsrmb?: string | number
  qnxsus?: string | number
  ddslrmb?: number
  ddslus?: number
  grmlzhbigdecimal?: string | number
  grmlllbigdecimal?: string | number
  /** 测试数量 */
  expmonth?: string[]
  expTestAry?: Array<string | number>
  showAssets?: boolean
  accountRMB?: string | number
  accountUS?: string | number
  pendingCounts?: WelcomePendingCounts
  opsCounts?: WelcomeOpsCounts
  showOpsCounts?: boolean
  newlogs?: WelcomeLogItem[]
}
