// Button.tsx
import type { MouseEvent, ReactNode } from 'react'
import './button.css'

export interface ButtonProps {
  children: ReactNode
  variant?: 'solid' | 'accent' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  as?: 'button' | 'a'
  href?: string
  loading?: boolean
  disabled?: boolean
  onClick?: (e: MouseEvent) => void
}

const VARIANT_CLASS: Record<NonNullable<ButtonProps['variant']>, string> = {
  solid: 'btn-cta',
  accent: 'btn-cta',
  ghost: 'btn-ghost',
}

export function Button({
  children,
  variant = 'solid',
  size = 'md',
  as = 'button',
  href,
  loading = false,
  disabled = false,
  onClick,
}: ButtonProps) {
  const className = ['sr-btn', `sr-btn--${size}`, VARIANT_CLASS[variant]].join(' ')
  const isDisabled = disabled || loading

  if (as === 'a') {
    return (
      <a
        className={className}
        href={isDisabled ? undefined : href}
        aria-disabled={isDisabled || undefined}
        aria-busy={loading || undefined}
        onClick={(e) => {
          if (isDisabled) { e.preventDefault(); return }
          onClick?.(e)
        }}
      >
        {children}
      </a>
    )
  }

  return (
    <button
      type="button"
      className={className}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      onClick={(e) => { if (!isDisabled) onClick?.(e) }}
    >
      {children}
    </button>
  )
}
