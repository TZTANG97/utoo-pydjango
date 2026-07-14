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

export interface WelcomeData {
  userName?: string
  loginName?: string
  userType?: number
  roleName?: string
  deptName?: string
  email?: string
  mobilePhoneNumber?: string
  menuCount?: number
}
