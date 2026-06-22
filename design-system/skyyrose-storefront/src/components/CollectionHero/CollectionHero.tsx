// CollectionHero.tsx — lockup-image hero (no Three.js, no type-rendered title).
import type { Collection } from '../../types'
import { Button } from '../Button'
import './collection-hero.css'

export interface CollectionHeroProps {
  collection: Collection
  lockupImage: string
  tagline?: string
  backgroundImage?: string
  cta?: { label: string; href: string }
  align?: 'center' | 'left'
}

export function CollectionHero({
  collection,
  lockupImage,
  tagline,
  backgroundImage,
  cta,
  align = 'center',
}: CollectionHeroProps) {
  return (
    <section
      className={`sr-hero sr-hero--${align}`}
      data-collection={collection}
      style={backgroundImage ? { backgroundImage: `url(${backgroundImage})` } : undefined}
    >
      <img className="sr-hero__lockup" src={lockupImage} alt={`${collection.replace('-', ' ')} collection`} />
      {tagline && <p className="sr-hero__tagline">{tagline}</p>}
      {cta && (
        <Button as="a" href={cta.href} variant="solid" size="lg">
          {cta.label}
        </Button>
      )}
    </section>
  )
}
