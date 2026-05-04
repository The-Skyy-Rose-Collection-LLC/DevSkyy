// Server-component shell for the runtime-only operations detail route.
// Operation IDs are generated at runtime, so the route can't be statically
// prerendered — `dynamic = 'force-dynamic'` opts out of Next.js 16's PPR
// attempt that surfaces "Uncached data was accessed outside of" at build time.
// The actual UI lives in OperationDetailClient (client component).

import OperationDetailClient from './OperationDetailClient';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ id: string }>;
}

export default function OperationDetailPage({ params }: Props) {
  return <OperationDetailClient params={params} />;
}
