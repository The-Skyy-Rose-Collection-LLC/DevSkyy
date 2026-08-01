/**
 * Operator Console brand tokens — collection accents and status colors.
 * Collection accents follow root CLAUDE.md §6 (Gold/Silver/Crimson/Rose-gold),
 * NOT lib/collections.ts's `accentColor` field (that file has Signature as
 * rose-gold, a pre-existing divergence from brand canon out of scope here).
 */
import type { CollectionSlug } from '@/lib/collections';

export const COLLECTION_ACCENT: Record<CollectionSlug, string> = {
  signature: '#D4AF37',
  'black-rose': '#C0C0C0',
  'love-hurts': '#DC143C',
  'kids-capsule': '#B76E79',
};

export const STATUS_GREEN = '#5FBF7F';
export const STATUS_AMBER = '#E5A85C';
export const STATUS_GREY = '#8A8A92';
export const STATUS_GREY_DIM = '#6A6A72';

export function statusPillColors(kind: 'success' | 'warning' | 'idle' | 'danger' | 'accent', acc = '#B76E79') {
  switch (kind) {
    case 'success':
      return { bg: 'rgba(95,191,127,.12)', color: STATUS_GREEN };
    case 'warning':
      return { bg: 'rgba(229,168,92,.12)', color: STATUS_AMBER };
    case 'danger':
      return { bg: 'rgba(220,20,60,.12)', color: '#DC143C' };
    case 'accent':
      return { bg: 'rgba(183,110,121,.14)', color: acc };
    case 'idle':
    default:
      return { bg: 'rgba(255,255,255,.05)', color: STATUS_GREY };
  }
}
