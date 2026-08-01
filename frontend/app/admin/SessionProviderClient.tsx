'use client';

import { SessionProvider as NextAuthSessionProvider } from 'next-auth/react';

// Thin client-boundary wrapper so app/admin/layout.tsx can stay an async
// Server Component (needs to fetch order counts server-side) while still
// mounting NextAuth's context provider, which requires 'use client'.
export function SessionProvider({ children }: { children: React.ReactNode }) {
  return <NextAuthSessionProvider>{children}</NextAuthSessionProvider>;
}
