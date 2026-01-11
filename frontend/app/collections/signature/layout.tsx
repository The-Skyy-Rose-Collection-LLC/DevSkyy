/**
 * SIGNATURE Collection Layout - SEO Metadata
 *
 * Provides metadata for SIGNATURE collection page.
 * Includes title, description, Open Graph, Twitter Card, and canonical URL.
 */

import { Metadata } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://skyyrose.com';

export const metadata: Metadata = {
  title: 'SIGNATURE Collection - Luxury Fashion | SkyyRose',
  description: 'Explore the SIGNATURE collection by SkyyRose - elegant luxury fashion pieces inspired by Oakland & San Francisco. Sophisticated designs that blend urban elegance with timeless style.',

  metadataBase: new URL(SITE_URL),

  alternates: {
    canonical: '/collections/signature',
  },

  openGraph: {
    title: 'SIGNATURE Collection - Luxury Fashion | SkyyRose',
    description: 'Explore the SIGNATURE collection by SkyyRose - elegant luxury fashion pieces inspired by Oakland & San Francisco.',
    url: `${SITE_URL}/collections/signature`,
    siteName: 'SkyyRose',
    locale: 'en_US',
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/images/collections/signature-og.jpg`,
        width: 1200,
        height: 630,
        alt: 'SkyyRose SIGNATURE Collection - Luxury Fashion',
      },
    ],
  },

  twitter: {
    card: 'summary_large_image',
    title: 'SIGNATURE Collection - Luxury Fashion | SkyyRose',
    description: 'Explore the SIGNATURE collection by SkyyRose - elegant luxury fashion pieces inspired by Oakland & San Francisco.',
    images: [`${SITE_URL}/images/collections/signature-og.jpg`],
    creator: '@skyyrose',
    site: '@skyyrose',
  },

  keywords: [
    'luxury fashion',
    'signature collection',
    'skyyrose',
    'designer clothing',
    'oakland fashion',
    'san francisco style',
    'premium apparel',
    'elegant fashion',
    'urban luxury',
    'contemporary fashion',
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

export default function SignatureCollectionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
