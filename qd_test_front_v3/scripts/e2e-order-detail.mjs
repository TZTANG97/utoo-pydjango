/**

 * E2E：订单列表点击进入详情，侧栏可跳转

 */

import { chromium } from 'playwright'



const BASE = 'http://127.0.0.1:9530'

const MOBILE = '18211984686'

const PASSWORD = '123456'



async function login(page) {

  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })

  await page.locator('img.account-login').click().catch(() => {})

  await page.getByPlaceholder('请输入手机号').fill(MOBILE)

  await page.locator('input[type="password"]').first().fill(PASSWORD)

  await page.locator('.slider').click()

  await page.getByRole('button', { name: /登\s*录/ }).click()

  await page.waitForTimeout(2500)

}



async function main() {

  const browser = await chromium.launch({ headless: true })

  const page = await browser.newPage()

  let routeErrors = 0

  page.on('pageerror', () => {

    routeErrors += 1

  })



  await login(page)

  await page.goto(`${BASE}/#/b/order`, { waitUntil: 'domcontentloaded' })

  await page.waitForTimeout(2000)



  const link = page.locator('a[href*="/b/order_detail/"]').first()

  await link.click()

  await page.waitForTimeout(2500)



  const url = page.url()

  const hasDetail = await page.locator('.box-card').filter({ hasText: '订单详情' }).count()

  const orderNo = await page.getByText('HYYPTFBLHWQMICAPQ20260600002').count().catch(() => 0)



  await page.getByRole('menuitem', { name: '我的订单' }).click().catch(() => {})

  await page.waitForTimeout(1500)

  const backOrder = page.url().includes('/b/order')



  console.log('url after click', url)

  console.log('detail card', hasDetail)

  console.log('order no visible', orderNo)

  console.log('sidebar back to order', backOrder)

  console.log('page errors', routeErrors)



  await browser.close()



  if (url.includes('order_detail') && hasDetail > 0 && backOrder) {

    console.log('OK order detail e2e')

    process.exit(0)

  }

  console.log('FAIL order detail e2e')

  process.exit(1)

}



main().catch((e) => {

  console.error(e)

  process.exit(1)

})


