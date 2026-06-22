// HoloCard.tsx — faithful React port of template-parts/product-card-holo.php
// + product-card-holo.js (size pills, wishlist, add-to-cart, magnetic tilt).
// Commerce is prop-ified: no WC/AJAX/localStorage here.
import { useRef, useState, type PointerEvent } from 'react'
import type { Collection } from '../../types'
import './holo-card.css'

export interface HoloCardProps {
  title: string
  price: string
  sku?: string
  collection: Collection
  frontImage: string
  backImage?: string
  permalink?: string
  sizes?: string[]
  badge?: 'soldout' | 'preorder' | null
  index?: number
  tilt?: boolean
  onAddToCart?: (p: { sku?: string; size: string | null }) => void
  onWishlistToggle?: (p: { sku?: string; active: boolean }) => void
}

const MAX_TILT = 8

export function HoloCard({
  title,
  price,
  sku,
  collection,
  frontImage,
  backImage,
  permalink = '#',
  sizes = ['S', 'M', 'L', 'XL'],
  badge = null,
  index = 0,
  tilt = true,
  onAddToCart,
  onWishlistToggle,
}: HoloCardProps) {
  const [size, setSize] = useState<string | null>(null)
  const [wished, setWished] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  const tiltEnabled =
    tilt &&
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    !window.matchMedia('(hover: none)').matches &&
    !window.matchMedia('(prefers-reduced-motion: reduce)').matches

  function onMove(e: PointerEvent<HTMLDivElement>) {
    if (!tiltEnabled || !bodyRef.current) return
    const r = bodyRef.current.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width
    const y = (e.clientY - r.top) / r.height
    const rx = (y - 0.5) * -2 * MAX_TILT
    const ry = (x - 0.5) * 2 * MAX_TILT
    bodyRef.current.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg)`
  }
  function onLeave() {
    if (bodyRef.current) bodyRef.current.style.transform = ''
  }

  return (
    <div data-collection={collection}>
      <div
        className={`holo holo--${collection}`}
        data-sku={sku ?? ''}
        style={{ ['--holo-delay' as string]: `${index * 80}ms` }}
      >
        <div className="holo__body" ref={bodyRef} onPointerMove={onMove} onPointerLeave={onLeave}>
          <div className="holo__gallery">
            {badge && <span className={`holo__badge holo__badge--${badge}`}>{badge === 'soldout' ? 'Sold Out' : 'Pre-Order'}</span>}
            <a href={permalink} className="holo__img-link" aria-label={`View ${title}`}>
              <img className="holo__img holo__img--front" src={frontImage} alt={title} width={600} height={750} loading="lazy" decoding="async" />
              <img className="holo__img holo__img--back" src={backImage ?? frontImage} alt={`${title} — technical blueprint view`} width={600} height={750} loading="lazy" decoding="async" />
            </a>
          </div>

          <div className="holo__info">
            <span className="holo__collection">{collection.replace(/-/g, ' ').toUpperCase()}</span>
            <h3 className="holo__name"><a href={permalink}>{title}</a></h3>
            <div className="holo__price-row"><span className="holo__price">{price}</span></div>
          </div>

          <div className="holo__drawer">
            <div className="holo__sizes" role="radiogroup" aria-label="Select size">
              {sizes.map((s) => (
                <button
                  key={s}
                  type="button"
                  className={`holo__size-pill${size === s ? ' holo__size-pill--active' : ''}`}
                  role="radio"
                  aria-checked={size === s}
                  data-size={s}
                  onClick={() => setSize(s)}
                >
                  {s}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="holo__buy"
              aria-label={`Add ${title} to cart`}
              onClick={() => onAddToCart?.({ sku, size })}
            >
              Add to Cart
            </button>
            <button
              type="button"
              className={`holo__wishlist${wished ? ' holo__wishlist--active' : ''}`}
              aria-pressed={wished}
              aria-label={`Add ${title} to wishlist`}
              onClick={() => {
                const active = !wished
                setWished(active)
                onWishlistToggle?.({ sku, active })
              }}
            >
              ♥
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
