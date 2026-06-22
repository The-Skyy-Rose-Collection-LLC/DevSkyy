// scripts/sync-theme-assets.mjs
// One-way sync: WP theme assets -> package src. `--check` asserts no drift (exit 1 on diff).
import { readFileSync, writeFileSync, mkdirSync, readdirSync, copyFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const PKG = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const THEME = resolve(PKG, '../../wordpress-theme/skyyrose-flagship')
const CHECK = process.argv.includes('--check')

// [source theme file, dest package file] — verbatim CSS copies (single source of truth).
const CSS_MAP = [
  ['assets/css/design-tokens.css', 'src/tokens/tokens.css'],
  ['assets/css/commercial-polish.css', 'src/styles/commercial-polish.css'],
  ['assets/css/product-card-holo.css', 'src/components/HoloCard/holo-card.css'],
]

// Font directory: woff2 files live directly in assets/fonts/ (20 files verified 2026-06-22).
// The collections/ subdirectory contains only CLAUDE.local.md, no woff2 files.
const FONT_DIR = resolve(THEME, 'assets/fonts')
const FONT_DEST = resolve(PKG, 'src/fonts')

let drift = 0
function ensure(dir) { mkdirSync(dir, { recursive: true }) }

for (const [rel, dstRel] of CSS_MAP) {
  const src = readFileSync(resolve(THEME, rel), 'utf8')
  const dstPath = resolve(PKG, dstRel)
  ensure(dirname(dstPath))
  let cur = ''
  try { cur = readFileSync(dstPath, 'utf8') } catch { /* missing */ }
  if (CHECK) {
    if (cur !== src) { console.error(`DRIFT: ${dstRel} differs from theme ${rel}`); drift++ }
  } else {
    writeFileSync(dstPath, src)
    console.log(`synced ${dstRel}`)
  }
}

// Fonts: copy every woff2 and generate fonts.css with one @font-face per family file.
ensure(FONT_DEST)
const woff2 = readdirSync(FONT_DIR).filter((f) => f.endsWith('.woff2'))
const faces = woff2
  .map((f) => {
    // Family name = file stem with separators normalized; weight/style left normal (interim).
    const family = f.replace(/\.woff2$/, '').replace(/[-_]/g, ' ')
    return `@font-face{font-family:'${family}';src:url('./${f}') format('woff2');font-display:swap;}`
  })
  .join('\n') + '\n'
const fontsCssPath = resolve(FONT_DEST, 'fonts.css')
let curFonts = ''
try { curFonts = readFileSync(fontsCssPath, 'utf8') } catch { /* missing */ }
if (CHECK) {
  for (const f of woff2) {
    const dst = resolve(FONT_DEST, f)
    let same = false
    try { same = readFileSync(dst).equals(readFileSync(resolve(FONT_DIR, f))) } catch { same = false }
    if (!same) { console.error(`DRIFT: font ${f} missing/differs`); drift++ }
  }
  if (curFonts !== faces) { console.error('DRIFT: fonts.css out of date'); drift++ }
} else {
  for (const f of woff2) copyFileSync(resolve(FONT_DIR, f), resolve(FONT_DEST, f))
  writeFileSync(fontsCssPath, faces)
  console.log(`synced ${woff2.length} fonts + fonts.css`)
}

if (CHECK && drift > 0) { console.error(`sync:check FAILED — ${drift} drifted artifact(s); run \`npm run sync\``); process.exit(1) }
if (CHECK) console.log('sync:check OK')
