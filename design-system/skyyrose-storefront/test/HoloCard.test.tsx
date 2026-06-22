import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HoloCard } from '../src/components/HoloCard'

const base = {
  title: 'Oakland Jersey',
  price: '$95',
  sku: 'br-012',
  collection: 'black-rose' as const,
  frontImage: 'https://example.test/front.webp',
  backImage: 'https://example.test/back.webp',
}

describe('HoloCard', () => {
  it('renders title, price, and sets the collection theming attributes', () => {
    const { container } = render(<HoloCard {...base} />)
    expect(screen.getByText('Oakland Jersey')).toBeInTheDocument()
    expect(screen.getByText('$95')).toBeInTheDocument()
    expect(container.querySelector('[data-collection="black-rose"]')).not.toBeNull()
    expect(container.querySelector('.holo--black-rose')).not.toBeNull()
    expect(container.querySelector('.holo')?.getAttribute('data-sku')).toBe('br-012')
  })

  it('renders front and back (techflat) images', () => {
    const { container } = render(<HoloCard {...base} />)
    expect(container.querySelector('.holo__img--front')).not.toBeNull()
    expect(container.querySelector('.holo__img--back')).not.toBeNull()
  })

  it('selects a size pill and calls onAddToCart with that size', async () => {
    const onAddToCart = vi.fn()
    render(<HoloCard {...base} onAddToCart={onAddToCart} />)
    await userEvent.click(screen.getByRole('radio', { name: 'M' }))
    expect(screen.getByRole('radio', { name: 'M' })).toHaveAttribute('aria-checked', 'true')
    await userEvent.click(screen.getByRole('button', { name: /add .* to cart/i }))
    expect(onAddToCart).toHaveBeenCalledWith({ sku: 'br-012', size: 'M' })
  })

  it('toggles wishlist and reports active state', async () => {
    const onWishlistToggle = vi.fn()
    render(<HoloCard {...base} onWishlistToggle={onWishlistToggle} />)
    await userEvent.click(screen.getByRole('button', { name: /wishlist/i }))
    expect(onWishlistToggle).toHaveBeenCalledWith({ sku: 'br-012', active: true })
  })

  it('renders a preorder badge when badge="preorder"', () => {
    const { container } = render(<HoloCard {...base} badge="preorder" />)
    expect(container.querySelector('.holo__badge--preorder')).not.toBeNull()
  })
})
