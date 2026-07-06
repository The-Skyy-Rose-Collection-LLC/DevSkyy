import type { Metadata } from 'next';
import SiteNav from '@/components/navigation/SiteNav';
import IncentivePopup from '@/components/marketing/IncentivePopup';
import PreOrderPage from './PreOrderPage';
import { getAllEnrichedCollections } from '@/lib/catalog-server';

export const metadata: Metadata = {
  title: 'Pre-Order | SkyyRose',
  description:
    'Secure your exclusive SkyyRose pieces. All three collections available for pre-order with exclusive early-adopter perks.',
  openGraph: {
    title: 'Pre-Order SkyyRose Collections',
    description:
      'Be first to own. Exclusive packaging, signed certificates, lifetime Inner Circle membership.',
  },
};

export default function PreOrder() {
  const collections = getAllEnrichedCollections();
  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      <SiteNav />
      <PreOrderPage collections={collections} />
      <IncentivePopup />
    </div>
  );
}
