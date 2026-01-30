'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Workflow,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  Layers,
  Activity,
  RefreshCcw,
} from 'lucide-react';
import { api, type Job3D, type PipelineStatus, type Provider3D, type BatchJob } from '@/lib/api';
import { use3DPipelineWS } from '@/hooks/useWebSocket';

// Extracted Components
import { QueueStatCard } from '@/components/admin/pipeline/QueueStatCard';
import { ProviderCard } from '@/components/admin/pipeline/ProviderCard';
import { BatchJobCard } from '@/components/admin/pipeline/BatchJobCard';
import { JobCard } from '@/components/admin/pipeline/JobCard';
import { JobDetailModal } from '@/components/admin/pipeline/JobDetailModal';

interface QueueStats {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
  avgProcessingTime: number;
}

export default function PipelinePage() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [providers, setProviders] = useState<Provider3D[]>([]);
  const [jobs, setJobs] = useState<Job3D[]>([]);
  const [batchJobs, setBatchJobs] = useState<BatchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<Job3D | null>(null);
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set());

  const { status: wsStatus, lastMessage, isConnected } = use3DPipelineWS();

  // Calculate queue stats
  const queueStats: QueueStats = {
    queued: jobs.filter((j) => j.status === 'queued').length,
    processing: jobs.filter((j) => j.status === 'processing').length,
    completed: jobs.filter((j) => j.status === 'completed').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
    avgProcessingTime: (() => {
      const completed = jobs.filter((j) => j.status === 'completed' && j.completed_at);
      if (completed.length === 0) return 0;
      const total = completed.reduce((sum, j) => {
        const start = new Date(j.created_at).getTime();
        const end = new Date(j.completed_at!).getTime();
        return sum + (end - start);
      }, 0);
      return Math.round(total / completed.length / 1000);
    })(),
  };

  // Fetch data
  useEffect(() => {
    async function fetchData() {
      try {
        const [statusData, providersData, jobsData, batchData] = await Promise.all([
          api.pipeline3d.getStatus(),
          api.pipeline3d.getProviders(),
          api.pipeline3d.getJobs(50),
          api.batch.list(),
        ]);
        setStatus(statusData);
        setProviders(providersData);
        setJobs(jobsData);
        setBatchJobs(batchData);
      } catch (err) {
        console.error('Failed to load pipeline data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage?.data) {
      const event = lastMessage.data;
      if (['job_queued', 'job_started', 'job_progress', 'job_completed', 'job_failed'].includes(event.event)) {
        // Refresh jobs list
        api.pipeline3d.getJobs(50).then(setJobs);
        api.pipeline3d.getStatus().then(setStatus);
      }
    }
  }, [lastMessage]);

  const toggleProvider = (id: string) => {
    setExpandedProviders((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const refreshData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusData, jobsData, batchData] = await Promise.all([
        api.pipeline3d.getStatus(),
        api.pipeline3d.getJobs(50),
        api.batch.list(),
      ]);
      setStatus(statusData);
      setJobs(jobsData);
      setBatchJobs(batchData);
    } finally {
      setLoading(false);
    }
  }, []);

  if (loading && jobs.length === 0) {
    return <PipelineSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-rose-600 flex items-center justify-center">
                <Workflow className="h-6 w-6 text-white" />
              </div>
              Generation Queue
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Real-time 3D model generation pipeline status
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              variant="outline"
              className={wsStatus === 'connected'
                ? 'border-green-500 text-green-400'
                : 'border-yellow-500 text-yellow-400'
              }
            >
              <div className={`h-2 w-2 rounded-full mr-2 ${wsStatus === 'connected' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
                }`} />
              {wsStatus === 'connected' ? 'Live' : 'Connecting...'}
            </Badge>
            <Button
              variant="outline"
              className="border-gray-700"
              onClick={refreshData}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCcw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Queue Stats */}
      <div className="grid gap-4 md:grid-cols-5">
        <QueueStatCard
          title="Queued"
          value={queueStats.queued}
          icon={Clock}
          color="gray"
        />
        <QueueStatCard
          title="Processing"
          value={queueStats.processing}
          icon={Loader2}
          color="blue"
          animate
        />
        <QueueStatCard
          title="Completed"
          value={queueStats.completed}
          icon={CheckCircle2}
          color="green"
        />
        <QueueStatCard
          title="Failed"
          value={queueStats.failed}
          icon={XCircle}
          color="red"
        />
        <QueueStatCard
          title="Avg Time"
          value={`${queueStats.avgProcessingTime}s`}
          icon={Activity}
          color="purple"
        />
      </div>

      {/* Provider Status Cards */}
      <Card className="bg-gray-900/80 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Cpu className="h-5 w-5 text-rose-400" />
            Provider Status
          </CardTitle>
          <CardDescription className="text-gray-400">
            Real-time status of 3D generation providers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {providers.map((provider) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                isExpanded={expandedProviders.has(provider.id)}
                onToggle={() => toggleProvider(provider.id)}
                activeJobs={jobs.filter(
                  (j) => j.provider === provider.id && j.status === 'processing'
                ).length}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Batch Jobs */}
      {batchJobs.length > 0 && (
        <Card className="bg-gray-900/80 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Layers className="h-5 w-5 text-amber-400" />
              Batch Jobs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {batchJobs.map((batch) => (
                <BatchJobCard key={batch.id} batch={batch} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Job Queue */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="all" className="data-[state=active]:bg-gray-700">
            All Jobs ({jobs.length})
          </TabsTrigger>
          <TabsTrigger value="processing" className="data-[state=active]:bg-gray-700">
            Processing ({queueStats.processing})
          </TabsTrigger>
          <TabsTrigger value="queued" className="data-[state=active]:bg-gray-700">
            Queued ({queueStats.queued})
          </TabsTrigger>
          <TabsTrigger value="completed" className="data-[state=active]:bg-gray-700">
            Completed ({queueStats.completed})
          </TabsTrigger>
          <TabsTrigger value="failed" className="data-[state=active]:bg-gray-700">
            Failed ({queueStats.failed})
          </TabsTrigger>
        </TabsList>

        {(['all', 'processing', 'queued', 'completed', 'failed'] as const).map((tab) => (
          <TabsContent key={tab} value={tab}>
            <div className="space-y-3">
              {jobs
                .filter((j) => tab === 'all' || j.status === tab)
                .map((job) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    isSelected={selectedJob?.id === job.id}
                    onSelect={() => setSelectedJob(job)}
                  />
                ))}
              {jobs.filter((j) => tab === 'all' || j.status === tab).length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No {tab === 'all' ? '' : tab} jobs
                </div>
              )}
            </div>
          </TabsContent>
        ))}
      </Tabs>

      {/* Job Detail Modal */}
      {selectedJob && (
        <JobDetailModal job={selectedJob} onClose={() => setSelectedJob(null)} />
      )}
    </div>
  );
}

// Skeleton loader
function PipelineSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-48 bg-gray-800" />
      <Skeleton className="h-64 bg-gray-800" />
    </div>
  );
}
