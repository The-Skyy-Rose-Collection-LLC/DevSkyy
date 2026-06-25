// test/parity.test.ts
import { describe, it, expect } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { createElement } from 'react'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { HoloCard } from '../src/components/HoloCard'

const THEME = resolve(__dirname, '../../../wordpress-theme/skyyrose-flagship')
const PHP = readFileSync(resolve(THEME, 'template-parts/product-card-holo.php'), 'utf8')

describe('WP markup parity (class contract)', () => {
  it('HoloCard emits every BEM class the PHP template defines', () => {
    const html = renderToStaticMarkup(
      createElement(HoloCard, {
        title: 'T', price: '$1', sku: 's', collection: 'black-rose',
        frontImage: 'f.webp', backImage: 'b.webp',
      }),
    )
    // Classes the PHP template renders that must exist on the React side too.
    const contract = [
      'holo', 'holo__body', 'holo__gallery', 'holo__img--front', 'holo__img--back',
      'holo__info', 'holo__collection', 'holo__name', 'holo__price',
      'holo__drawer', 'holo__sizes', 'holo__size-pill', 'holo__buy', 'holo__wishlist',
    ]
    for (const cls of contract) {
      expect(html, `React HoloCard missing .${cls}`).toContain(cls)
      expect(PHP, `PHP template no longer defines .${cls} — update the contract`).toContain(cls)
    }
  })
})
