import { Suspense } from 'react';
import { SessionProvider } from './SessionProviderClient';
import { ConsoleShell } from '@/components/console/ConsoleShell';
import './console.css';

// Deliberately synchronous — no server-side data fetching here. An async
// layout that awaits WC/session data before rendering breaks Next.js 16's
// Cache Components prerendering for EVERY /admin/* route (children render
// inside whatever Suspense boundary wraps the layout's own async work), which
// took down unrelated pages like /admin/jobs. ConsoleShell fetches its own
// nav-badge and identity data client-side (useSession/useQuery) instead.
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <Suspense fallback={null}>
        <ConsoleShell>{children}</ConsoleShell>
      </Suspense>
    </SessionProvider>
  );
}
