/** 仅验证登录后 hash 是否进入 /b */
import { chromium } from 'playwright'

const BASE = 'http://127.0.0.1:9530'
const MOBILE = '18211984686'
const PASSWORD = '123456'

async function main() {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })

  const accountBtn = page.locator('img.account-login')
  if (await accountBtn.isVisible().catch(() => false)) {
    await accountBtn.click()
    await page.waitForTimeout(500)
  }

  await page.getByPlaceholder('请输入手机号').fill(MOBILE)
  await page.locator('input[type="password"]').first().fill(PASSWORD)
  await page.locator('.slider').click()
  await page.getByRole('button', { name: /登\s*录/ }).click()

  await page.waitForTimeout(3000)
  const hash = await page.evaluate(() => window.location.hash)
  console.log('hash after login:', hash)
  await browser.close()
  if (hash.includes('/b')) {
    console.log('OK redirect to /b')
    process.exit(0)
  }
  console.log('FAIL still not on /b')
  process.exit(1)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
