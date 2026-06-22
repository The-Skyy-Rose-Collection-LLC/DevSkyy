import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CollectionHero } from '../src/components/CollectionHero'

describe('CollectionHero', () => {
  const base = {
    collection: 'signature' as const,
    lockupImage: 'https://example.test/signature-lockup.png',
    tagline: 'Elevated, confident, refined',
  }

  it('renders the lockup as an IMAGE (brand rule: never type-rendered)', () => {
    const { container } = render(<CollectionHero {...base} />)
    const img = container.querySelector('.sr-hero__lockup') as HTMLImageElement
    expect(img).not.toBeNull()
    expect(img.getAttribute('src')).toBe(base.lockupImage)
    // No heading element renders the collection name as text.
    expect(container.querySelector('h1')).toBeNull()
  })

  it('sets data-collection for palette theming and renders the tagline', () => {
    const { container } = render(<CollectionHero {...base} />)
    expect(container.querySelector('[data-collection="signature"]')).not.toBeNull()
    expect(screen.getByText('Elevated, confident, refined')).toBeInTheDocument()
  })

  it('renders a CTA link when cta is provided', () => {
    render(<CollectionHero {...base} cta={{ label: 'Shop Signature', href: '/signature' }} />)
    const link = screen.getByRole('link', { name: 'Shop Signature' })
    expect(link).toHaveAttribute('href', '/signature')
  })
})
