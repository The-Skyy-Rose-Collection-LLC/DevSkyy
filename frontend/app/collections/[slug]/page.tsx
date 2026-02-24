import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import {
  getCollection,
  getAllCollectionSlugs,
  type CollectionSlug,
} from '@/lib/collections';
import CollectionExperience from './CollectionExperience';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  return getAllCollectionSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const collection = getCollection(slug);
  if (!collection) return {};

  const totalProducts = collection.scenes.reduce(
    (sum, s) => sum + s.products.length,
    0
  );

  return {
    title: `${collection.name} Collection`,
    description: collection.description,
    openGraph: {
      title: `${collection.name} | SkyyRose`,
      description: collection.description,
      images: [{ url: collection.heroImage, width: 1200, height: 630 }],
    },
    other: {
      'product:brand': 'SkyyRose',
      'product:availability': 'in stock',
      'product:item_group_id': collection.slug,
    },
  };
}

export default async function CollectionPage({ params }: PageProps) {
  const { slug } = await params;
  const collection = getCollection(slug);

  if (!collection) {
    notFound();
  }

  // JSON-LD structured data
  const totalProducts = collection.scenes.reduce(
    (sum, s) => sum + s.products.length,
    0
  );

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: `${collection.name} Collection`,
    description: collection.description,
    brand: {
      '@type': 'Brand',
      name: 'SkyyRose',
    },
    numberOfItems: totalProducts,
    breadcrumb: {
      '@type': 'BreadcrumbList',
      itemListElement: [
        {
          '@type': 'ListItem',
          position: 1,
          name: 'Collections',
          item: '/collections',
        },
        {
          '@type': 'ListItem',
          position: 2,
          name: collection.name,
          item: `/collections/${collection.slug}`,
        },
      ],
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <CollectionExperience collection={collection} />
    </>
  );
}
