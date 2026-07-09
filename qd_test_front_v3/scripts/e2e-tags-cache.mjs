/**

 * E2E：顶部标签切换不应重复请求订单详情接口

 */

import { chromium } from 'playwright'



const BASE = 'http://127.0.0.1:9530'



async function login(page) {

  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })

  await page.locator('img.account-login').click().catch(() => {})

  await page.getByPlaceholder('请输入手机号').fill('18211984686')

  await page.locator('input[type="password"]').first().fill('123456')

  await page.locator('.slider').click()

  await page.getByRole('button', { name: /登\s*录/ }).click()

  await page.waitForTimeout(2500)

}



async function main() {

  const browser = await chromium.launch({ headless: true })

  const page = await browser.newPage()

  let detailApiCount = 0



  page.on('response', (res) => {

    if (res.url().includes('orderdetail.ajax')) detailApiCount += 1

  })



  await login(page)

  await page.goto(`${BASE}/#/b/order`, { waitUntil: 'domcontentloaded' })

  await page.waitForTimeout(2000)



  await page.locator('a[href*="/b/order_detail/"]').first().click()

  await page.waitForTimeout(2000)

  const firstCount = detailApiCount



  await page.getByRole('menuitem', { name: '我的订单' }).click()

  await page.waitForTimeout(1500)



  await page.locator('.tags-view-item').filter({ hasText: '订单详情' }).first().click()

  await page.waitForTimeout(1500)

  const afterSwitch = detailApiCount



  const detailVisible = await page.getByText('订单详情').count()



  console.log('detail api first open', firstCount)

  console.log('detail api after tab switch', afterSwitch)

  console.log('extra calls on switch', afterSwitch - firstCount)

  console.log('detail still visible', detailVisible > 0)



  await browser.close()



  if (afterSwitch === firstCount && detailVisible > 0) {

    console.log('OK tags cache: no extra detail api')

    process.exit(0)

  }

  console.log('FAIL tags cache: detail re-fetched on switch')

  process.exit(1)

}



main().catch((e) => {

  console.error(e)

  process.exit(1)

})


