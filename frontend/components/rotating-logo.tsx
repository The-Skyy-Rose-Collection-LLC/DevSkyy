'use client';

import Image from 'next/image';
import { cn } from '@/lib/utils';

export type CollectionType = 'black-rose' | 'love-hurts' | 'signature' | 'sr-monogram' | 'love-hurts-text';
export type AnimationType = 'rotate3D' | 'rotate3DContinuous' | 'spinGlow' | 'pulse' | 'heartbeat' | 'gentleFloat';
export type SizeType = 'small' | 'medium' | 'large' | 'hero';

interface RotatingLogoProps {
  collection: CollectionType;
  size?: SizeType;
  animation?: AnimationType;
  className?: string;
  withSparkle?: boolean;
}

const logoMap: Record<CollectionType, string> = {
  'black-rose': '/assets/logos/black-rose-trophy-cosmic.png',
  'love-hurts': '/assets/logos/love-hurts-trophy-red.png',
  'signature': '/assets/logos/signature-rose-rosegold.png',
  'sr-monogram': '/assets/logos/sr-monogram-rosegold.png',
  'love-hurts-text': '/assets/logos/love-hurts-text-logo.png',
};

const sizeMap: Record<SizeType, number> = {
  small: 80,
  medium: 200,
  large: 400,
  hero: 600,
};

const collectionNames: Record<CollectionType, string> = {
  'black-rose': 'BLACK ROSE Collection',
  'love-hurts': 'LOVE HURTS Collection',
  'signature': 'SIGNATURE Collection',
  'sr-monogram': 'SkyyRose Monogram',
  'love-hurts-text': 'LOVE HURTS',
};

export function RotatingLogo({
  collection,
  size = 'medium',
  animation = 'rotate3D',
  className,
  withSparkle = false,
}: RotatingLogoProps) {
  const logoSrc = logoMap[collection];
  const logoSize = sizeMap[size];
  const logoAlt = collectionNames[collection];

  // Combine animation classes
  const animationClass = cn(
    `animate-${animation}`,
    withSparkle && 'animate-sparkle',
    // Hardware acceleration
    'will-change-transform',
    // Accessibility - respect reduced motion preference
    'motion-reduce:animate-none'
  );

  return (
    <div
      className={cn(
        'relative inline-block',
        animationClass,
        className
      )}
      style={{
        width: logoSize,
        height: logoSize,
      }}
    >
      <Image
        src={logoSrc}
        alt={logoAlt}
        width={logoSize}
        height={logoSize}
        className="w-full h-full object-contain"
        priority={size === 'hero'}
        quality={95}
      />
    </div>
  );
}

// Helper components for specific use cases

export function HeaderLogo({ className }: { className?: string }) {
  return (
    <RotatingLogo
      collection="sr-monogram"
      size="small"
      animation="rotate3DContinuous"
      className={className}
    />
  );
}

export function CollectionHero({
  collection,
  className
}: {
  collection: Exclude<CollectionType, 'sr-monogram' | 'love-hurts-text'>;
  className?: string;
}) {
  return (
    <RotatingLogo
      collection={collection}
      size="hero"
      animation="rotate3D"
      withSparkle
      className={className}
    />
  );
}

export function ProductBadge({
  collection,
  className
}: {
  collection: Exclude<CollectionType, 'sr-monogram' | 'love-hurts-text'>;
  className?: string;
}) {
  return (
    <RotatingLogo
      collection={collection}
      size="small"
      animation="rotate3D"
      className={className}
    />
  );
}
