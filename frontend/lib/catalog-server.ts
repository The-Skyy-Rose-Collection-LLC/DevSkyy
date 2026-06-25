import 'server-only';
import { cache } from 'react';
import { getCatalog, type CatalogProduct } from './catalog';
import {
  getCollection,
  getAllCollectionSlugs,
  type CollectionConfig,
  type CollectionProduct,
  type CollectionSlug,
} from './collections';

function toCollectionProduct(p: CatalogProduct): CollectionProduct {
  return {
    id: p.sku,
    name: p.name,
    price: p.price,
    image: p.frontModelImage || p.image,
    sizes: p.sizes,
    description: p.description || undefined,
    category: p.badge || undefined,
  };
}

export const getEnrichedCollection = cache(function (
  slug: string
): CollectionConfig | undefined {
  const brand = getCollection(slug as CollectionSlug);
  if (!brand) return undefined;

  const sceneCount = brand.scenes.length;
  if (sceneCount === 0) return brand;

  const products = getCatalog()
    .filter((p) => p.collection === slug && p.published)
    .map(toCollectionProduct);

  const perScene: CollectionProduct[][] = brand.scenes.map(() => []);
  products.forEach((p, i) => perScene[i % sceneCount].push(p));

  return {
    ...brand,
    scenes: brand.scenes.map((scene, i) => ({ ...scene, products: perScene[i] })),
  };
});

export function getAllEnrichedCollections(): CollectionConfig[] {
  return getAllCollectionSlugs()
    .map((slug) => getEnrichedCollection(slug))
    .filter((c): c is CollectionConfig => c !== undefined);
}
