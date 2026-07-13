#!/usr/bin/env node
// driver.mjs — Playwright-library headless driver for the DevSkyy Next.js
// dashboard. Lives next to SKILL.md so a future agent can run it without
// hunting for an entry point.
//
// Usage:
//   node driver.mjs smoke                       — visit a canonical route set,
//                                                 assert HTTP 200 + non-empty
//                                                 DOM, screenshot each.
//   node driver.mjs ss <url> <out.png>          — one-shot screenshot.
//   node driver.mjs eval <url> "<js>"           — print page.evaluate() result.
//
// Env:
//   BASE_URL   default http://127.0.0.1:3000
//   OUT_DIR    default ./screenshots (relative to this file)
//   TIMEOUT_MS default 60000  (Next dev first-compile is slow)

import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:3000'
const OUT_DIR = resolve(HERE, process.env.OUT_DIR || 'screenshots')
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS || 60_000)

const SMOKE_ROUTES = [
  { path: '/', name: 'home', fullPage: true },
  { path: '/admin', name: 'admin' },
]

function log(...a) { console.error('[driver]', ...a) }

async function withBrowser(fn) {
  let browser
  try {
    browser = await chromium.launch({ headless: true })
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
    const page = await ctx.newPage()
    page.setDefaultTimeout(TIMEOUT_MS)
    return await fn(page)
  } finally {
    if (browser) await browser.close()
  }
}

async function gotoOk(page, url) {
  const r = await page.goto(url, { waitUntil: 'domcontentloaded' })
  if (!r) throw new Error(`no response: ${url}`)
  const status = r.status()
  const body = (await page.content()).length
  return { status, body }
}

async function cmdSmoke() {
  await mkdir(OUT_DIR, { recursive: true })
  const results = []
  await withBrowser(async (page) => {
    for (const route of SMOKE_ROUTES) {
      const url = BASE_URL + route.path
      let status, body, err
      try {
        ({ status, body } = await gotoOk(page, url))
        const shot = join(OUT_DIR, `${route.name}.png`)
        await page.screenshot({ path: shot, fullPage: route.fullPage === true })
        log(`OK   ${url} status=${status} body=${body}b -> ${shot}`)
      } catch (e) {
        err = String(e?.message || e)
        log(`FAIL ${url} err=${err}`)
      }
      results.push({ url, status, body, err })
    }
  })
  const failures = results.filter((r) => r.err || (r.status && r.status >= 400))
  console.log(JSON.stringify({ baseUrl: BASE_URL, outDir: OUT_DIR, results }, null, 2))
  process.exit(failures.length === 0 ? 0 : 2)
}

async function cmdScreenshot(url, out) {
  if (!url || !out) {
    log('usage: node driver.mjs ss <url> <out.png>')
    process.exit(64)
  }
  const absOut = resolve(out)
  await mkdir(dirname(absOut), { recursive: true })
  await withBrowser(async (page) => {
    const r = await gotoOk(page, url)
    await page.screenshot({ path: absOut, fullPage: false })
    log(`OK ${url} status=${r.status} body=${r.body}b -> ${absOut}`)
  })
}

async function cmdEval(url, js) {
  if (!url || !js) {
    log('usage: node driver.mjs eval <url> "<js>"')
    process.exit(64)
  }
  await withBrowser(async (page) => {
    await gotoOk(page, url)
    const result = await page.evaluate(js)
    console.log(JSON.stringify(result, null, 2))
  })
}

const [cmd, ...rest] = process.argv.slice(2)
const dispatch = {
  smoke: () => cmdSmoke(),
  ss: () => cmdScreenshot(rest[0], rest[1]),
  eval: () => cmdEval(rest[0], rest[1]),
}
const fn = dispatch[cmd || 'smoke']
if (!fn) {
  log(`unknown command: ${cmd}`)
  log('commands: smoke | ss <url> <out.png> | eval <url> "<js>"')
  process.exit(64)
}
fn().catch((e) => {
  log('fatal:', e?.stack || e)
  process.exit(1)
})
