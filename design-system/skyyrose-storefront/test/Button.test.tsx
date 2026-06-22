import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../src/components/Button'

describe('Button', () => {
  it('renders children and the solid variant class by default', () => {
    render(<Button>Shop</Button>)
    const btn = screen.getByRole('button', { name: 'Shop' })
    expect(btn).toHaveClass('sr-btn', 'btn-cta')
  })

  it('maps ghost variant to btn-ghost', () => {
    render(<Button variant="ghost">More</Button>)
    expect(screen.getByRole('button', { name: 'More' })).toHaveClass('btn-ghost')
  })

  it('renders as an anchor when as="a" with href', () => {
    render(<Button as="a" href="/shop">Go</Button>)
    const link = screen.getByRole('link', { name: 'Go' })
    expect(link).toHaveAttribute('href', '/shop')
  })

  it('is disabled and unclickable when disabled', async () => {
    const onClick = vi.fn()
    render(<Button disabled onClick={onClick}>X</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })

  it('sets aria-busy and disables while loading', () => {
    render(<Button loading>Save</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toHaveAttribute('aria-busy', 'true')
    expect(btn).toBeDisabled()
  })
})
