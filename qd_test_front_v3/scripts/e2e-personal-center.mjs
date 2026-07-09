/**
 * 首页「个人中心」：已登录应进入 #/b/order
 */
import { chromium } from 'playwright'

const BASE = 'http://127.0.0.1:9530'
const MOBILE = '18211984686'
const PASSWORD = '123456'

async function login(page) {
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  const accountBtn = page.locator('img.account-login')
  if (await accountBtn.isVisible().catch(() => false)) {
    await accountBtn.click()
    await page.waitForTimeout(400)
  }
  await page.getByPlaceholder('请输入手机号').fill(MOBILE)
  await page.locator('input[type="password"]').first().fill(PASSWORD)
  await page.locator('.slider').click()
  await page.getByRole('button', { name: /登\s*录/ }).click()
  await page.waitForTimeout(2500)
}

async function main() {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  await login(page)
  await page.goto(`${BASE}/#/home`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.waitForTimeout(800)
  await page.getByText('个人中心').click()
  await page.waitForTimeout(2000)
  const hash = await page.evaluate(() => window.location.hash)
  const hasSidebar = await page.locator('.sidebar-container').isVisible().catch(() => false)
  console.log('hash:', hash, 'sidebar:', hasSidebar)
  await browser.close()
  if (hash.includes('/b/') && hasSidebar) {
    console.log('OK personal center navigation')
    process.exit(0)
  }
  console.log('FAIL personal center')
  process.exit(1)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
