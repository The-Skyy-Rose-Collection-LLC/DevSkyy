// scripts/sync-theme-assets.mjs
// One-way sync: WP theme assets -> package src. `--check` asserts no drift (exit 1 on diff).
import { readFileSync, writeFileSync, mkdirSync, readdirSync, copyFileSync } from 'node:fs'
import { dirname, resolve, basename } from 'node:path'
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

// ---------------------------------------------------------------------------
// Font sync: parse theme.json fontFamilies to get AUTHORITATIVE family names,
// weights, and styles. Woff2 files outside fontFamilies (Yellowtail, Pinyon
// Script, Kaushan Script) use a curated name map — these are the collection
// script fonts referenced by tokens.css CSS variables.
// ---------------------------------------------------------------------------

function buildFontsCss(fontDir) {
  const themeJsonPath = resolve(THEME, 'theme.json')
  const themeData = JSON.parse(readFileSync(themeJsonPath, 'utf8'))
  const fontFamilies = themeData?.settings?.typography?.fontFamilies ?? []

  // Build woff2 -> { family, weight, style } from theme.json
  const woff2Map = new Map()
  for (const fam of fontFamilies) {
    // family name may be a comma-separated stack like "'Inter', -apple-system, ..."
    const familyName = fam.fontFamily.split(',')[0].trim().replace(/^['"]|['"]$/g, '')
    for (const face of (fam.fontFace ?? [])) {
      for (const src of (face.src ?? [])) {
        // src format: "file:./assets/fonts/<filename>.woff2"
        const m = src.match(/file:\.\/assets\/fonts\/(.+\.woff2)/)
        if (m) {
          woff2Map.set(m[1], {
            family: familyName,
            weight: face.fontWeight ?? '400',
            style: face.fontStyle ?? 'normal',
          })
        }
      }
    }
  }

  // Curated names for collection script fonts not in theme.json fontFamilies.
  // These names match the CSS variable values in tokens.css:
  //   --skyyrose-font-script: 'Yellowtail' | 'Pinyon Script' | 'Kaushan Script'
  const CURATED = new Map([
    ['yellowtail-latin.woff2',    { family: 'Yellowtail',    weight: '400', style: 'normal' }],
    ['pinyon-script-latin.woff2', { family: 'Pinyon Script', weight: '400', style: 'normal' }],
    ['kaushan-script-latin.woff2',{ family: 'Kaushan Script',weight: '400', style: 'normal' }],
  ])

  const woff2Files = readdirSync(fontDir).filter((f) => f.endsWith('.woff2')).sort()
  const lines = []
  for (const f of woff2Files) {
    const meta = woff2Map.get(f) ?? CURATED.get(f)
    if (!meta) {
      // Fallback: should never happen unless new font files are added — warn and derive.
      console.warn(`sync: no family mapping for ${f}, deriving from filename (check theme.json)`)
      const family = basename(f, '.woff2').replace(/[-_]/g, ' ')
      lines.push(`@font-face{font-family:'${family}';src:url('./${f}') format('woff2');font-display:swap;}`)
      continue
    }
    lines.push(
      `@font-face{font-family:'${meta.family}';src:url('./${f}') format('woff2');` +
      `font-weight:${meta.weight};font-style:${meta.style};font-display:swap;}`
    )
  }
  return lines.join('\n') + '\n'
}

ensure(FONT_DEST)
const woff2 = readdirSync(FONT_DIR).filter((f) => f.endsWith('.woff2'))
const generatedFontsCss = buildFontsCss(FONT_DIR)
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
  if (curFonts !== generatedFontsCss) { console.error('DRIFT: fonts.css out of date'); drift++ }
} else {
  for (const f of woff2) copyFileSync(resolve(FONT_DIR, f), resolve(FONT_DEST, f))
  writeFileSync(fontsCssPath, generatedFontsCss)
  console.log(`synced ${woff2.length} fonts + fonts.css (family names from theme.json)`)
}

if (CHECK && drift > 0) { console.error(`sync:check FAILED — ${drift} drifted artifact(s); run \`npm run sync\``); process.exit(1) }
if (CHECK) console.log('sync:check OK')
