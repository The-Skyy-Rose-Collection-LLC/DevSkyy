/**
 * LOVE_HURTS Collection Layout - SEO Metadata
 *
 * Provides metadata for LOVE_HURTS collection page.
 * Includes title, description, Open Graph, Twitter Card, and canonical URL.
 */

import { Metadata } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://skyyrose.com';

export const metadata: Metadata = {
  title: 'LOVE HURTS Collection - Gothic Romance Fashion | SkyyRose',
  description: 'Discover the LOVE HURTS collection by SkyyRose - a captivating blend of gothic romance and luxury fashion. Dark elegance meets modern sophistication in this enchanting collection.',

  metadataBase: new URL(SITE_URL),

  alternates: {
    canonical: '/collections/love-hurts',
  },

  openGraph: {
    title: 'LOVE HURTS Collection - Gothic Romance Fashion | SkyyRose',
    description: 'Discover the LOVE HURTS collection by SkyyRose - a captivating blend of gothic romance and luxury fashion.',
    url: `${SITE_URL}/collections/love-hurts`,
    siteName: 'SkyyRose',
    locale: 'en_US',
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/images/collections/love-hurts-og.jpg`,
        width: 1200,
        height: 630,
        alt: 'SkyyRose LOVE HURTS Collection - Gothic Romance Fashion',
      },
    ],
  },

  twitter: {
    card: 'summary_large_image',
    title: 'LOVE HURTS Collection - Gothic Romance Fashion | SkyyRose',
    description: 'Discover the LOVE HURTS collection by SkyyRose - a captivating blend of gothic romance and luxury fashion.',
    images: [`${SITE_URL}/images/collections/love-hurts-og.jpg`],
    creator: '@skyyrose',
    site: '@skyyrose',
  },

  keywords: [
    'gothic fashion',
    'romantic style',
    'love hurts collection',
    'skyyrose',
    'designer clothing',
    'dark elegance',
    'luxury gothic',
    'premium apparel',
    'romantic fashion',
    'contemporary gothic',
    'edgy luxury',
  ],

  authors: [{ name: 'SkyyRose' }],

  robots: {
    index: true,
    follow: true,
    'max-image-preview': 'large',
    'max-snippet': -1,
    'max-video-preview': -1,
  },

  other: {
    'og:brand': 'SkyyRose',
    'product:brand': 'SkyyRose',
    'product:availability': 'in stock',
    'product:condition': 'new',
  },
};

export default function LoveHurtsCollectionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
