/**
 * 讨论区路由：新标签页须为 /#/discussion，不能是 /discussion（Vite 会 404）
 */
import { chromium } from 'playwright'

const BASE = process.env.E2E_BASE || 'http://127.0.0.1:9530'
const API = process.env.E2E_API || 'http://127.0.0.1:18083'

async function main() {
  const bad = await fetch(`${BASE}/discussion`, { redirect: 'manual' })
  console.log('GET /discussion (no hash) status:', bad.status)

  const ok = await fetch(`${BASE}/`)
  console.log('GET / status:', ok.status)

  const api = await fetch(`${API}/api/entry/commenttreebulder.ajax`)
  console.log('API commenttreebulder status:', api.status)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()

  await page.goto(`${BASE}/#/home`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  const discussionLink = page.getByText('讨论', { exact: true }).first()
  await discussionLink.waitFor({ state: 'visible', timeout: 15000 })

  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    discussionLink.click(),
  ])
  await popup.waitForLoadState('domcontentloaded', { timeout: 30000 })
  const popupUrl = popup.url()
  console.log('popup url:', popupUrl)

  const hasHashRoute = popupUrl.includes('#/discussion')
  const on404 = await popup
    .locator('.wscn-http404-container')
    .isVisible()
    .catch(() => false)
  const hasDiscussionUi = await popup
    .locator('.infinite-scroll-container, .discussion')
    .first()
    .isVisible()
    .catch(() => false)

  let apiOk = false
  if (hasHashRoute && !on404) {
    const loginPage = await browser.newPage()
    await loginPage.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })
    const accountBtn = loginPage.locator('img.account-login')
    if (await accountBtn.isVisible().catch(() => false)) await accountBtn.click()
    await loginPage.getByPlaceholder('请输入手机号').fill('18211984686')
    await loginPage.locator('input[type="password"]').first().fill('123456')
    await loginPage.locator('.slider').click()
    await loginPage.getByRole('button', { name: /登\s*录/ }).click()
    await loginPage.waitForTimeout(2500)
    await loginPage.goto(`${BASE}/#/discussion`, { waitUntil: 'networkidle', timeout: 60000 })
    await loginPage.waitForTimeout(2000)
    apiOk = !(await loginPage.locator('.wscn-http404-container').isVisible().catch(() => false))
    await loginPage.close()
  }

  await popup.close()
  await browser.close()

  if (!hasHashRoute || on404) {
    console.error('FAIL: discussion popup should be hash route without 404 page')
    process.exit(1)
  }
  console.log('OK discussion route; logged-in page ok:', apiOk)
  process.exit(0)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
