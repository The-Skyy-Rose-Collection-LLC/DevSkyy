import type { Metadata } from 'next';
import CollectionsLanding from './CollectionsLanding';

export const metadata: Metadata = {
  title: 'Collections | SkyyRose',
  description:
    'Discover the SkyyRose luxury fashion collections. Three immersive worlds: Black Rose, Love Hurts, and Signature.',
  openGraph: {
    title: 'SkyyRose Collections',
    description: 'Luxury Grows from Concrete.. Three immersive worlds await.',
  },
};

export default function CollectionsPage() {
  return <CollectionsLanding />;
}
