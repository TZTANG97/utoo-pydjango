/**

 * 浏览器 E2E：登录后「我的订单」页是否渲染表格行

 * 依赖：9530 前端 dev、18083 Python 后端

 */

import { chromium } from 'playwright'



const BASE = 'http://127.0.0.1:9530'

const MOBILE = '18211984686'

const PASSWORD = '123456'



async function main() {

  const browser = await chromium.launch({ headless: true })

  const context = await browser.newContext()

  const page = await context.newPage()



  const apiLogs = []

  page.on('response', async (res) => {

    const url = res.url()

    if (url.includes('myExperimentOrderList') || url.includes('/auth/login')) {

      let body = null

      try {

        body = await res.json()

      } catch {

        body = null

      }

      apiLogs.push({ status: res.status(), url, body })

    }

  })



  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })



  // 默认是扫码登录，先切换到账号密码登录

  const accountBtn = page.locator('img.account-login')

  if (await accountBtn.isVisible().catch(() => false)) {

    await accountBtn.click()

    await page.waitForTimeout(500)

  }



  await page.getByPlaceholder('请输入手机号').fill(MOBILE)

  await page.locator('input[type="password"]').first().fill(PASSWORD)

  await page.locator('.slider').click()

  await page.getByRole('button', { name: /登\s*录/ }).click()



  await page.waitForURL(/#\/(b|home)/, { timeout: 15000 }).catch(() => {})



  await page.goto(`${BASE}/#/b/order`, { waitUntil: 'networkidle', timeout: 30000 })

  await page.waitForTimeout(2500)



  const rows = await page.locator('.el-table__body-wrapper tbody tr').count()

  const emptyText = await page.locator('.el-table__empty-text').textContent().catch(() => '')

  const cookies = await context.cookies()

  const hasToken = cookies.some((c) => c.name === 'token' && c.value)



  const listLog = apiLogs.find((x) => x.url.includes('myExperimentOrderList'))

  const loginLog = apiLogs.find((x) => x.url.includes('/auth/login'))



  console.log('cookie has token:', hasToken)

  console.log('login api:', loginLog?.status, loginLog?.body?.code, loginLog?.body?.message)

  console.log('table rows:', rows)

  console.log('empty text:', emptyText || '(none)')

  if (listLog) {

    const b = listLog.body

    const payload = b?.data ?? b?.obj

    const inner = payload?.data ?? payload

    console.log('list api status:', listLog.status, 'code:', b?.code)

    console.log('list records:', payload?.recordsTotal)

    console.log('list rows:', Array.isArray(inner) ? inner.length : 'N/A')

  } else {

    console.log('list api: NOT CALLED')

    console.log('all api urls:', apiLogs.map((x) => x.url).join('\n  '))

  }



  await browser.close()



  if (rows > 0) {

    console.log('OK browser e2e passed')

    process.exit(0)

  }

  console.log('FAIL no table rows in browser')

  process.exit(1)

}



main().catch((e) => {

  console.error(e)

  process.exit(1)

})


