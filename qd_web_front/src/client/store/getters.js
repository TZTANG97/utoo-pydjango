import { defaultAvatarUrl } from '@client/utils/oss-image'

function resolveAvatarUrl(raw) {
  const url = (raw || '').trim()
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  return defaultAvatarUrl()
}

const getters = {
  sidebar: state => state.app.sidebar,
  device: state => state.app.device,
  token: state => state.user.token,
  avatar: state => resolveAvatarUrl(state.user.avatar),
  name: state => state.user.name,
  mobile: state => state.user.mobile,
  authInfo: state => state.user.authInfo,
  visitedViews: state => state.tagsView.visitedViews,
  cachedViews: state => state.user.cachedViews,
  cateList: state => state.cate.cateList,
  showCate: state => state.cate.showCate,
  loading: state => state.app.loading,
  IntegralConvertRatio: state => state.user.IntegralConvertRatio,
  totalIntegral: state => state.user.totalIntegral,
}
export default getters
