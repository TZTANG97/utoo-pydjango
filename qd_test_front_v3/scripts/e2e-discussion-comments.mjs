/**
 * 首次展开评论应显示评论列表（非空帖）
 * 需：9530 前端、18083 Python API
 */
import { chromium } from 'playwright'

const BASE = process.env.E2E_BASE || 'http://127.0.0.1:9530'

async function main() {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()

  await page.goto(`${BASE}/#/discussion`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.waitForSelector('.post-card', { timeout: 60000 })

  const commentBtn = page
    .locator('.post-card')
    .first()
    .locator('.action-chip')
    .filter({ hasText: /评论\(\d+\)/ })
    .first()

  const hasBtn = (await commentBtn.count()) > 0
  if (!hasBtn) {
    const any = page.locator('.post-card .action-chip').filter({ hasText: '评论' }).first()
    if ((await any.count()) === 0) {
      console.error('FAIL: no comment button found')
      process.exit(1)
    }
    await any.click()
  } else {
    await commentBtn.click()
  }

  const commentsReq = page.waitForResponse(
    (res) => res.url().includes('commentsByEntry') && res.status() === 200,
    { timeout: 30000 }
  )
  await commentsReq

  const list = page.locator('.post-card').first().locator('.comments-list .comment-item')
  await list.first().waitFor({ state: 'visible', timeout: 15000 })
  const count = await list.count()
  console.log('First expand comment-item count:', count)

  await browser.close()

  if (count < 1) {
    console.error('FAIL: comments should appear on first click')
    process.exit(1)
  }
  console.log('PASS: comments load on first click')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
