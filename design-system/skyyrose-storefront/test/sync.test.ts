import { describe, it, expect, beforeAll } from 'vitest'
import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

const PKG = resolve(__dirname, '..')
const THEME = resolve(PKG, '../../wordpress-theme/skyyrose-flagship')

describe('theme-asset sync', () => {
  beforeAll(() => execFileSync('node', ['scripts/sync-theme-assets.mjs'], { cwd: PKG }))

  it('copies design tokens verbatim', () => {
    const src = readFileSync(resolve(THEME, 'assets/css/design-tokens.css'), 'utf8')
    const dst = readFileSync(resolve(PKG, 'src/tokens/tokens.css'), 'utf8')
    expect(dst).toBe(src)
  })

  it('copies the holo card CSS verbatim', () => {
    const src = readFileSync(resolve(THEME, 'assets/css/product-card-holo.css'), 'utf8')
    const dst = readFileSync(resolve(PKG, 'src/components/HoloCard/holo-card.css'), 'utf8')
    expect(dst).toBe(src)
  })

  it('generates a fonts.css with at least one @font-face and copies a woff2', () => {
    const css = readFileSync(resolve(PKG, 'src/fonts/fonts.css'), 'utf8')
    expect(css).toMatch(/@font-face/)
    expect(existsSync(resolve(PKG, 'src/fonts'))).toBe(true)
  })

  it('--check passes when in sync and fails when a synced file is mutated', () => {
    expect(() => execFileSync('node', ['scripts/sync-theme-assets.mjs', '--check'], { cwd: PKG })).not.toThrow()

    const tokensPath = resolve(PKG, 'src/tokens/tokens.css')
    const original = readFileSync(tokensPath, 'utf8')
    writeFileSync(tokensPath, original + '\n/* drift-marker */')
    try {
      expect(() => execFileSync('node', ['scripts/sync-theme-assets.mjs', '--check'], { cwd: PKG })).toThrow()
    } finally {
      writeFileSync(tokensPath, original)
    }
  })
})
