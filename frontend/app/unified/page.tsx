/**
 * Unified Dashboard Page
 * ======================
 * Single view combining:
 * - Round Table competition results
 * - HuggingFace Spaces status
 * - WordPress media status
 * - Training progress
 * - Sync pipeline status
 */

'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui';
import {
  Trophy,
  Cloud,
  Globe,
  Zap,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  Award,
  Database,
  ArrowRight,
} from 'lucide-react';

// Interfaces
interface RoundTableResult {
  collection: string;
  winner: {
    provider: string;
    total_score: number;
    verdict: string;
  };
}

interface HFSpaceStatus {
  id: string;
  name: string;
  status: 'running' | 'building' | 'error' | 'unknown';
  category: string;
}

interface SyncStatus {
  status: string;
  systems: Array<{
    system: string;
    available: boolean;
    last_sync: string | null;
    items_count: number;
  }>;
  last_full_sync: string | null;
}

interface TrainingStatus {
  status: string;
  version: string;
  progress_percentage: number;
  current_epoch: number;
  total_epochs: number;
  loss: number;
  message: string;
}

export default function UnifiedDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [roundTableResults, setRoundTableResults] = useState<RoundTableResult[]>([]);
  const [hfSpaces, setHFSpaces] = useState<HFSpaceStatus[]>([]);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // Fetch all data
  const fetchAllData = async () => {
    setLoading(true);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
      // Fetch Round Table results
      try {
        const rtResponse = await fetch(`${apiUrl}/api/v1/round-table/results`);
        if (rtResponse.ok) {
          const rtData = await rtResponse.json();
          setRoundTableResults(rtData.collections || []);
        }
      } catch (e) {
        console.error('RT fetch failed:', e);
      }

      // Fetch HF Spaces status
      try {
        const hfResponse = await fetch(`${apiUrl}/api/v1/hf-spaces/status`);
        if (hfResponse.ok) {
          const hfData = await hfResponse.json();
          setHFSpaces(hfData.spaces || []);
        }
      } catch (e) {
        console.error('HF fetch failed:', e);
      }

      // Fetch Sync status
      try {
        const syncResponse = await fetch(`${apiUrl}/api/v1/sync/status`);
        if (syncResponse.ok) {
          const syncData = await syncResponse.json();
          setSyncStatus(syncData);
        }
      } catch (e) {
        console.error('Sync fetch failed:', e);
      }

      // Fetch Training status
      try {
        const trainingResponse = await fetch(`${apiUrl}/api/v1/training/status`);
        if (trainingResponse.ok) {
          const trainingData = await trainingResponse.json();
          setTrainingStatus(trainingData);
        }
      } catch (e) {
        console.error('Training fetch failed:', e);
      }

      setLastRefresh(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  // Trigger full sync
  const triggerSync = async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      await fetch(`${apiUrl}/api/v1/sync/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: 'full' }),
      });
      await fetchAllData();
    } catch (e) {
      console.error('Sync trigger failed:', e);
    }
  };

  // Get verdict color
  const getVerdictColor = (verdict: string) => {
    switch (verdict?.toUpperCase()) {
      case 'EXCELLENT':
        return 'text-green-600 bg-green-100';
      case 'GOOD':
        return 'text-blue-600 bg-blue-100';
      case 'ACCEPTABLE':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'building':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Zap className="h-8 w-8 text-brand-primary" />
            Unified Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            Round Table • HuggingFace • WordPress • Training
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            {lastRefresh && `Last updated: ${lastRefresh.toLocaleTimeString()}`}
          </span>
          <button
            onClick={fetchAllData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={triggerSync}
            className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg hover:bg-brand-primary/90"
          >
            <Zap className="h-4 w-4" />
            Full Sync
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Round Table Winners */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-500" />
              <CardTitle>Round Table Winners</CardTitle>
            </div>
            <CardDescription>
              Claude won all 3 collections with elite 3-pillar judging
            </CardDescription>
          </CardHeader>
          <CardContent>
            {roundTableResults.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Trophy className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No Round Table results available</p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-3">
                {roundTableResults.map((result) => (
                  <div
                    key={result.collection}
                    className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium uppercase tracking-wide text-gray-500">
                        {result.collection}
                      </span>
                      <Award className="h-4 w-4 text-yellow-500" />
                    </div>
                    <p className="font-bold text-lg mb-1">
                      {result.winner?.provider || 'Unknown'}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-2xl font-bold text-brand-primary">
                        {result.winner?.total_score?.toFixed(1) || '0.0'}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded ${getVerdictColor(result.winner?.verdict)}`}>
                        {result.winner?.verdict || 'N/A'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Training Status */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-500" />
              <CardTitle>Training Status</CardTitle>
            </div>
            <CardDescription>LoRA training progress</CardDescription>
          </CardHeader>
          <CardContent>
            {trainingStatus ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Status</span>
                  <span className={`px-2 py-1 text-xs rounded ${
                    trainingStatus.status === 'training'
                      ? 'bg-blue-100 text-blue-800'
                      : trainingStatus.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {trainingStatus.status}
                  </span>
                </div>
                {trainingStatus.version && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Version</span>
                    <span className="font-mono text-sm">{trainingStatus.version}</span>
                  </div>
                )}
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-500">Progress</span>
                    <span>{trainingStatus.progress_percentage?.toFixed(1) || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-brand-primary h-2 rounded-full transition-all"
                      style={{ width: `${trainingStatus.progress_percentage || 0}%` }}
                    />
                  </div>
                </div>
                {trainingStatus.loss > 0 && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Loss</span>
                    <span className="font-mono text-sm">{trainingStatus.loss.toFixed(4)}</span>
                  </div>
                )}
                {trainingStatus.message && (
                  <p className="text-xs text-gray-500 italic">{trainingStatus.message}</p>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No active training</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* HuggingFace Spaces */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cloud className="h-5 w-5 text-purple-500" />
              <CardTitle>HuggingFace Spaces</CardTitle>
            </div>
            <CardDescription>
              {hfSpaces.filter(s => s.status === 'running').length}/{hfSpaces.length} running
            </CardDescription>
          </CardHeader>
          <CardContent>
            {hfSpaces.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <Cloud className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No Spaces found</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {hfSpaces.map((space) => (
                  <div
                    key={space.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {getStatusIcon(space.status)}
                      <div>
                        <p className="font-medium text-sm">{space.name}</p>
                        <p className="text-xs text-gray-500">{space.category}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded ${
                      space.status === 'running'
                        ? 'bg-green-100 text-green-800'
                        : space.status === 'building'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {space.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sync Status */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-green-500" />
              <CardTitle>Sync Pipeline</CardTitle>
            </div>
            <CardDescription>
              {syncStatus?.status === 'healthy' ? 'All systems operational' : 'Some systems unavailable'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {syncStatus ? (
              <div className="space-y-3">
                {syncStatus.systems?.map((system) => (
                  <div
                    key={system.system}
                    className="flex items-center justify-between p-2 border rounded"
                  >
                    <div className="flex items-center gap-2">
                      {system.available ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                      <span className="text-sm capitalize">{system.system.replace('_', ' ')}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {system.items_count > 0 && `${system.items_count} items`}
                    </span>
                  </div>
                ))}
                {syncStatus.last_full_sync && (
                  <p className="text-xs text-gray-500 mt-2">
                    Last full sync: {new Date(syncStatus.last_full_sync).toLocaleString()}
                  </p>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Sync status unavailable</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks across all systems</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-4">
            <button className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 group">
              <div className="flex items-center gap-2">
                <Trophy className="h-4 w-4 text-yellow-500" />
                <span>View RT Results</span>
              </div>
              <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
            <button className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 group">
              <div className="flex items-center gap-2">
                <Cloud className="h-4 w-4 text-purple-500" />
                <span>Export to HF</span>
              </div>
              <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
            <button className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 group">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-blue-500" />
                <span>Sync to WordPress</span>
              </div>
              <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
            <button className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 group">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span>Start Training</span>
              </div>
              <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
