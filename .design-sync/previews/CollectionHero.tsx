import { CollectionHero } from '@skyyrose/storefront-ds'

// Canonical brand-script lockup images from skyyrose.co theme assets (all verified 200)
const BR_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/hero-overlays/br-brand-script-logotype.webp'
const LH_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/hero-overlays/lh-logo-combined.png'
const SG_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/hero-overlays/sig-brand-skyy-rose-gold.webp'
const KC_LOCKUP = 'https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/images/logos/sr-monogram-rose-gold.webp'

export const BlackRose = () => (
  <CollectionHero
    collection="black-rose"
    title="Black Rose"
    subtitle="Armor for the ones who stood up."
    ctaLabel="Shop Black Rose"
    ctaHref="#"
    backgroundImage={BR_LOCKUP}
  />
)

export const LoveHurts = () => (
  <CollectionHero
    collection="love-hurts"
    title="Love Hurts"
    subtitle="Bloodline that raised me."
    ctaLabel="Shop Love Hurts"
    ctaHref="#"
    backgroundImage={LH_LOCKUP}
  />
)

export const Signature = () => (
  <CollectionHero
    collection="signature"
    title="Signature"
    subtitle="Gold standard. Nothing less."
    ctaLabel="Shop Signature"
    ctaHref="#"
    backgroundImage={SG_LOCKUP}
  />
)

export const KidsCapsule = () => (
  <CollectionHero
    collection="kids-capsule"
    title="Kids Capsule"
    subtitle="Little roses. Same concrete."
    ctaLabel="Shop Kids"
    ctaHref="#"
    backgroundImage={KC_LOCKUP}
  />
)
