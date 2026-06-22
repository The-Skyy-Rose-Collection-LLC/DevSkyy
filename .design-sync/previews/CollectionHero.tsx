import { CollectionHero } from '@skyyrose/storefront-ds'

// Canonical brand-script lockup images from skyyrose.co theme assets (all verified 200).
// These are the foreground collection lockups — the hero name IS the image (never type-rendered).
const BR_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/hero-overlays/br-brand-script-logotype.webp'
const LH_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/hero-overlays/lh-logo-combined.png'
const SG_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/hero-overlays/sig-brand-skyy-rose-gold.webp'
const KC_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/logos/sr-monogram-rose-gold.webp'

export const BlackRose = () => (
  <CollectionHero
    collection="black-rose"
    lockupImage={BR_LOCKUP}
    tagline="Armor for the ones who stood up."
    cta={{ label: 'Shop Black Rose', href: '#' }}
    align="center"
  />
)

export const LoveHurts = () => (
  <CollectionHero
    collection="love-hurts"
    lockupImage={LH_LOCKUP}
    tagline="Bloodline that raised me."
    cta={{ label: 'Shop Love Hurts', href: '#' }}
    align="center"
  />
)

export const Signature = () => (
  <CollectionHero
    collection="signature"
    lockupImage={SG_LOCKUP}
    tagline="Gold standard. Nothing less."
    cta={{ label: 'Shop Signature', href: '#' }}
    align="center"
  />
)

export const KidsCapsule = () => (
  <CollectionHero
    collection="kids-capsule"
    lockupImage={KC_LOCKUP}
    tagline="Little roses. Same concrete."
    cta={{ label: 'Shop Kids', href: '#' }}
    align="center"
  />
)
