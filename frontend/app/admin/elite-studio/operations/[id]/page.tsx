// Server-component shell for the runtime-only operations detail route.
// Operation IDs are generated at runtime, so there are no static IDs to
// prerender. Returning [] from generateStaticParams tells Next.js to skip
// build-time prerender for this route entirely — required because
// `cacheComponents` is enabled in next.config.ts and forbids the
// `dynamic = 'force-dynamic'` route segment config.
// The actual UI lives in OperationDetailClient (client component).

import OperationDetailClient from './OperationDetailClient';

export function generateStaticParams() {
  return [];
}

interface Props {
  params: Promise<{ id: string }>;
}

export default function OperationDetailPage({ params }: Props) {
  return <OperationDetailClient params={params} />;
}
