/**
 * Admin Dashboard Page
 * ====================
 * Main admin dashboard with stats, product overview, and sync status.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  Package,
  Box,
  ShoppingCart,
  DollarSign,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui';

// Types
interface DashboardStats {
  total_products: number;
  products_with_3d: number;
  products_synced: number;
  pending_sync: number;
  total_orders_today: number;
  revenue_today: number;
  total_orders_month: number;
  revenue_month: number;
}

interface SyncJob {
  id: string;
  product_sku: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  errors: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [syncJobs, setSyncJobs] = useState<SyncJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [statsRes, jobsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/admin/stats`),
        fetch(`${API_BASE}/api/v1/admin/sync-jobs`),
      ]);

      if (!statsRes.ok || !jobsRes.ok) {
        throw new Error('Failed to load dashboard data');
      }

      const statsData = await statsRes.json();
      const jobsData = await jobsRes.json();

      setStats(statsData);
      setSyncJobs(jobsData);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      // Set default stats on error
      setStats({
        total_products: 0,
        products_with_3d: 0,
        products_synced: 0,
        pending_sync: 0,
        total_orders_today: 0,
        revenue_today: 0,
        total_orders_month: 0,
        revenue_month: 0,
      });
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const triggerSync = useCallback(async () => {
    setSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/sync-all`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Sync failed');
      await loadDashboard();
    } catch (err) {
      console.error('Sync failed:', err);
    }
    setSyncing(false);
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">SkyyRose Admin Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Manage products, sync with WordPress, and monitor 3D assets
          </p>
        </div>
        <button
          onClick={triggerSync}
          disabled={syncing}
          className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
          Sync All Products
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <Package className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_products || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.products_with_3d || 0} with 3D models
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Synced to WordPress</CardTitle>
            <Box className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.products_synced || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.pending_sync || 0} pending sync
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Orders Today</CardTitle>
            <ShoppingCart className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_orders_today || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.total_orders_month || 0} this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Revenue Today</CardTitle>
            <DollarSign className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(stats?.revenue_today || 0).toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              ${(stats?.revenue_month || 0).toFixed(2)} this month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Link href="/admin/products">
          <Card className="hover:border-primary cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <Package className="w-10 h-10 text-primary" />
                <div>
                  <h3 className="font-semibold">Manage Products</h3>
                  <p className="text-sm text-muted-foreground">
                    View and edit product catalog
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/3d-pipeline">
          <Card className="hover:border-primary cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <Box className="w-10 h-10 text-primary" />
                <div>
                  <h3 className="font-semibold">3D Pipeline</h3>
                  <p className="text-sm text-muted-foreground">
                    Generate 3D models from images
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/agents">
          <Card className="hover:border-primary cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <RefreshCw className="w-10 h-10 text-primary" />
                <div>
                  <h3 className="font-semibold">AI Agents</h3>
                  <p className="text-sm text-muted-foreground">
                    Monitor and control agents
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Recent Sync Jobs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Sync Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {syncJobs.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No sync jobs yet. Click &quot;Sync All Products&quot; to start.
            </p>
          ) : (
            <div className="space-y-4">
              {syncJobs.slice(0, 10).map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    {job.status === 'completed' ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : job.status === 'failed' ? (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    ) : (
                      <Clock className="w-5 h-5 text-blue-500 animate-pulse" />
                    )}
                    <div>
                      <p className="font-medium">{job.product_sku}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(job.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        job.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : job.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {job.status}
                    </span>
                    {job.errors.length > 0 && (
                      <span className="text-xs text-red-500">
                        {job.errors.length} error(s)
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
