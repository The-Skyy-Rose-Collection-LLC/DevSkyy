import './styles/commercial-polish.css'
import './tokens/tokens.css'
// fonts/fonts.css is intentionally NOT imported here — if it were, Vite would
// base64-inline all 20 woff2 files (~580 KB) into dist/skyyrose-ds.css. Fonts
// ship via design-sync cfg.extraFonts (which copies @font-face + woff2 into
// the ds-bundle fonts/ directory) so they resolve correctly in claude.ai/design.

export type { Collection } from './types'
export { Button } from './components/Button'
export type { ButtonProps } from './components/Button'
export { HoloCard } from './components/HoloCard'
export type { HoloCardProps } from './components/HoloCard'
export { CollectionHero } from './components/CollectionHero'
export type { CollectionHeroProps } from './components/CollectionHero'
