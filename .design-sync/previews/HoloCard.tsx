import { HoloCard } from '@skyyrose/storefront-ds'

const img = 'https://placehold.co/600x750/0a0a0a/b76e79?text=SkyyRose'

export const BlackRose = () => (
  <HoloCard
    collection="black-rose"
    title="Oakland Bomber Jacket"
    price="$240"
    sku="br-001"
    frontImage={img}
  />
)

export const LoveHurts = () => (
  <HoloCard
    collection="love-hurts"
    title="Bloodline Hoodie"
    price="$160"
    sku="lh-002"
    frontImage={img}
    badge="preorder"
  />
)

export const Signature = () => (
  <HoloCard
    collection="signature"
    title="Gold Standard Tee"
    price="$85"
    sku="sg-003"
    frontImage={img}
  />
)

export const KidsCapsule = () => (
  <HoloCard
    collection="kids-capsule"
    title="Mini Rose Set"
    price="$60"
    sku="kc-001"
    frontImage={img}
  />
)
