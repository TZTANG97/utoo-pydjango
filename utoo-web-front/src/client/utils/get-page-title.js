import defaultSettings from '@client/settings'

const title = defaultSettings.title || '优兔测试平台'

export default function getPageTitle(pageTitle) {
  if (pageTitle) {
    return `${pageTitle} - ${title}`
  }
  return `${title}`
}
