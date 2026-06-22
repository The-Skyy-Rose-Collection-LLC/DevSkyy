import { HoloCard } from '@skyyrose/storefront-ds'

// Real product renders from skyyrose.co WooCommerce media library (all verified 200)
const BR_IMG = 'https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/black-rose-crewneck-front-model.webp?fit=1024%2C1024&ssl=1'
const LH_IMG = 'https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/love-hurts-joggers-front-model.webp?fit=1024%2C1024&ssl=1'
const SG_IMG = 'https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/bridge-stay-golden-shorts-front-model.webp?fit=1024%2C1024&ssl=1'
const KC_IMG = 'https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/kids-red-set-front-model.webp?fit=896%2C1200&ssl=1'

export const BlackRose = () => (
  <HoloCard
    collection="black-rose"
    title="BLACK Rose Crewneck"
    price="$35"
    sku="br-001"
    frontImage={BR_IMG}
  />
)

export const LoveHurts = () => (
  <HoloCard
    collection="love-hurts"
    title="Love Hurts Joggers (Black)"
    price="$95"
    sku="lh-002"
    frontImage={LH_IMG}
  />
)

export const Signature = () => (
  <HoloCard
    collection="signature"
    title="The Bridge Series 'Stay Golden' Shorts"
    price="$65"
    sku="sg-003"
    frontImage={SG_IMG}
  />
)

export const KidsCapsule = () => (
  <HoloCard
    collection="kids-capsule"
    title="Kids Colorblock Hoodie Set — Red/Black"
    price="$65"
    sku="kids-001"
    frontImage={KC_IMG}
  />
)
