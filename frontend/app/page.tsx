/**
 * Dashboard Home Page
 * ===================
 * Server component that fetches initial data and streams to client.
 */

import { Suspense } from 'react';
import DashboardClient from '@/components/DashboardClient';
import { DashboardSkeleton } from '@/components/skeletons';

// Force dynamic rendering (don't pre-render at build time)
export const dynamic = 'force-dynamic';

// Get API URL from environment
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getInitialMetrics() {
  try {
    const res = await fetch(`${API_URL}/api/v1/metrics`, {
      next: { revalidate: 60 }, // ISR: revalidate every 60s
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) return null;
    return res.json();
  } catch (error) {
    console.error('Failed to fetch initial metrics:', error);
    return null;
  }
}

async function getInitialAgents() {
  try {
    const res = await fetch(`${API_URL}/api/v1/agents`, {
      next: { revalidate: 300 }, // Cache for 5 minutes
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) return [];
    return res.json();
  } catch (error) {
    console.error('Failed to fetch initial agents:', error);
    return [];
  }
}

export default async function DashboardPage() {
  // Fetch initial data in parallel on server
  const [initialMetrics, initialAgents] = await Promise.all([
    getInitialMetrics(),
    getInitialAgents(),
  ]);

  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardClient
        initialMetrics={initialMetrics}
        initialAgents={initialAgents}
      />
    </Suspense>
  );
}
