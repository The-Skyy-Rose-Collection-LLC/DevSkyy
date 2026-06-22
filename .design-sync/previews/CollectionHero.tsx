import { CollectionHero } from '@skyyrose/storefront-ds'

const img = 'https://placehold.co/1200x800/0a0a0a/b76e79?text=SkyyRose'

export const BlackRose = () => (
  <CollectionHero
    collection="black-rose"
    title="Black Rose"
    subtitle="Armor for the ones who stood up."
    ctaLabel="Shop Black Rose"
    ctaHref="#"
    backgroundImage={img}
  />
)

export const LoveHurts = () => (
  <CollectionHero
    collection="love-hurts"
    title="Love Hurts"
    subtitle="Bloodline that raised me."
    ctaLabel="Shop Love Hurts"
    ctaHref="#"
    backgroundImage={img}
  />
)

export const Signature = () => (
  <CollectionHero
    collection="signature"
    title="Signature"
    subtitle="Gold standard. Nothing less."
    ctaLabel="Shop Signature"
    ctaHref="#"
    backgroundImage={img}
  />
)

export const KidsCapsule = () => (
  <CollectionHero
    collection="kids-capsule"
    title="Kids Capsule"
    subtitle="Little roses. Same concrete."
    ctaLabel="Shop Kids"
    ctaHref="#"
    backgroundImage={img}
  />
)
