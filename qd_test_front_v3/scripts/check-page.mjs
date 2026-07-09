import { chromium } from 'playwright'

const url = process.argv[2] || 'http://127.0.0.1:9530/#/home'
const withToken = process.argv.includes('--token')

const browser = await chromium.launch()
const context = await browser.newContext()
if (withToken) {
  await context.addCookies([
    {
      name: 'token',
      value: 'fake-stale-java-token',
      domain: '127.0.0.1',
      path: '/',
    },
  ])
}
const page = await context.newPage()
const logs = []
page.on('console', (msg) => logs.push(`[${msg.type()}] ${msg.text()}`))
page.on('pageerror', (err) => logs.push(`[pageerror] ${err.message}`))

const t0 = Date.now()
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 })
await page.waitForTimeout(8000)
const elapsed = Date.now() - t0

const appLen = await page.locator('#app').innerHTML().then((h) => h.length).catch(() => 0)
const headCount = await page.locator('.head').count()

console.log('URL:', url, withToken ? '(with stale token)' : '')
console.log('elapsed ms:', elapsed)
console.log('#app length:', appLen)
console.log('.head count:', headCount)
logs.filter((l) => /error|pageerror|permission|getInfo/i.test(l)).forEach((l) => console.log(l))

await browser.close()
