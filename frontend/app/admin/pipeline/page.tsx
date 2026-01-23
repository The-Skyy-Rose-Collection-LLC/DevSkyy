'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Workflow,
  Play,
  Pause,
  RotateCcw,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  Cpu,
  Layers,
  AlertCircle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Eye,
  RefreshCcw,
  Activity,
  TrendingUp,
  Box,
} from 'lucide-react';
import { api, type Job3D, type PipelineStatus, type Provider3D, type BatchJob } from '@/lib/api';
import { use3DPipelineWS } from '@/hooks/useWebSocket';
import { ThreeViewer, ModelViewerFallback } from '@/components/three-viewer';

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
              <div className={`h-2 w-2 rounded-full mr-2 ${
                wsStatus === 'connected' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
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

// Queue Stat Card
function QueueStatCard({
  title,
  value,
  icon: Icon,
  color,
  animate = false,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'gray' | 'blue' | 'green' | 'red' | 'purple';
  animate?: boolean;
}) {
  const colorMap = {
    gray: 'from-gray-500 to-gray-600',
    blue: 'from-blue-500 to-cyan-500',
    green: 'from-green-500 to-emerald-500',
    red: 'from-red-500 to-rose-500',
    purple: 'from-purple-500 to-pink-500',
  };

  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden">
      <div className={`h-1 bg-gradient-to-r ${colorMap[color]}`} />
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">{title}</p>
            <p className="text-2xl font-bold text-white mt-1">{value}</p>
          </div>
          <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${colorMap[color]} flex items-center justify-center`}>
            <Icon className={`h-5 w-5 text-white ${animate ? 'animate-spin' : ''}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Provider Card
function ProviderCard({
  provider,
  isExpanded,
  onToggle,
  activeJobs,
}: {
  provider: Provider3D;
  isExpanded: boolean;
  onToggle: () => void;
  activeJobs: number;
}) {
  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-red-500',
    busy: 'bg-yellow-500',
  };

  return (
    <Card
      className={`bg-gray-800 border-gray-700 cursor-pointer transition-all ${
        isExpanded ? 'ring-1 ring-rose-500' : ''
      }`}
      onClick={onToggle}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`h-2.5 w-2.5 rounded-full ${statusColors[provider.status]}`} />
            <span className="text-white font-medium">{provider.name}</span>
          </div>
          {activeJobs > 0 && (
            <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
              {activeJobs} active
            </Badge>
          )}
        </div>

        <div className="text-sm text-gray-400 space-y-1">
          <div className="flex justify-between">
            <span>Type:</span>
            <span className="text-white capitalize">{provider.type}</span>
          </div>
          <div className="flex justify-between">
            <span>Avg Time:</span>
            <span className="text-white">{provider.avg_generation_time_s}s</span>
          </div>
        </div>

        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-500 mb-2">Capabilities</p>
            <div className="flex flex-wrap gap-1">
              {provider.capabilities.map((cap) => (
                <Badge key={cap} variant="secondary" className="bg-gray-700 text-gray-300 text-xs">
                  {cap}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-center mt-3">
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-gray-500" />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Batch Job Card
function BatchJobCard({ batch }: { batch: BatchJob }) {
  const statusColors = {
    pending: 'text-gray-400 bg-gray-500/10',
    processing: 'text-blue-400 bg-blue-500/10',
    completed: 'text-green-400 bg-green-500/10',
    failed: 'text-red-400 bg-red-500/10',
    paused: 'text-yellow-400 bg-yellow-500/10',
  };

  return (
    <div className="flex items-center gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      <div className="flex-shrink-0">
        {batch.status === 'processing' ? (
          <Loader2 className="h-8 w-8 text-blue-400 animate-spin" />
        ) : batch.status === 'completed' ? (
          <CheckCircle2 className="h-8 w-8 text-green-400" />
        ) : batch.status === 'failed' ? (
          <XCircle className="h-8 w-8 text-red-400" />
        ) : (
          <Clock className="h-8 w-8 text-gray-400" />
        )}
      </div>

      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-white font-medium">Batch #{batch.id.slice(0, 8)}</span>
          <Badge className={statusColors[batch.status]} variant="secondary">
            {batch.status}
          </Badge>
        </div>
        <p className="text-gray-400 text-sm mt-1">
          {batch.processed_assets} / {batch.total_assets} assets
          {batch.failed_assets > 0 && (
            <span className="text-red-400 ml-2">({batch.failed_assets} failed)</span>
          )}
        </p>
      </div>

      <div className="flex-shrink-0 w-32">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-500">Progress</span>
          <span className="text-white">{batch.progress_percentage.toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-rose-500 to-purple-600 transition-all duration-300"
            style={{ width: `${batch.progress_percentage}%` }}
          />
        </div>
      </div>

      {batch.status === 'processing' && (
        <Button size="sm" variant="outline" className="border-gray-700">
          <Pause className="h-4 w-4" />
        </Button>
      )}
      {batch.status === 'paused' && (
        <Button size="sm" variant="outline" className="border-gray-700">
          <Play className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

// Job Card
function JobCard({
  job,
  isSelected,
  onSelect,
}: {
  job: Job3D;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const statusConfig = {
    queued: { icon: Clock, bg: 'bg-gray-500/10', text: 'text-gray-400', label: 'Queued' },
    processing: { icon: Loader2, bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'Processing' },
    completed: { icon: CheckCircle2, bg: 'bg-green-500/10', text: 'text-green-400', label: 'Completed' },
    failed: { icon: XCircle, bg: 'bg-red-500/10', text: 'text-red-400', label: 'Failed' },
  };

  const config = statusConfig[job.status];
  const StatusIcon = config.icon;

  return (
    <div
      className={`flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all ${
        isSelected
          ? 'bg-gray-800 border-rose-500'
          : 'bg-gray-900/80 border-gray-700 hover:border-gray-600'
      }`}
      onClick={onSelect}
    >
      <div className={`h-10 w-10 rounded-lg ${config.bg} flex items-center justify-center`}>
        <StatusIcon className={`h-5 w-5 ${config.text} ${job.status === 'processing' ? 'animate-spin' : ''}`} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-white font-medium truncate">{job.provider}</span>
          <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
            {job.input_type}
          </Badge>
        </div>
        <p className="text-gray-500 text-sm truncate mt-0.5">{job.input}</p>
      </div>

      <Badge className={`${config.bg} ${config.text} border-0`}>
        {config.label}
      </Badge>

      <div className="text-right text-sm">
        <p className="text-gray-400">
          {new Date(job.created_at).toLocaleTimeString()}
        </p>
        {job.completed_at && (
          <p className="text-gray-500 text-xs">
            {Math.round(
              (new Date(job.completed_at).getTime() - new Date(job.created_at).getTime()) / 1000
            )}s
          </p>
        )}
      </div>

      <ArrowRight className="h-4 w-4 text-gray-500" />
    </div>
  );
}

// Job Detail Modal
function JobDetailModal({
  job,
  onClose,
}: {
  job: Job3D;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-gray-900/95 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl bg-gray-900 border-gray-700 max-h-[90vh] overflow-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white">Job Details</CardTitle>
            <CardDescription className="text-gray-400">
              {job.id}
            </CardDescription>
          </div>
          <Button variant="ghost" onClick={onClose}>
            <XCircle className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Model Preview */}
          {job.status === 'completed' && job.output_url && (
            <div className="aspect-video rounded-lg overflow-hidden">
              <ModelViewerFallback
                modelUrl={job.output_url}
                height="100%"
                arEnabled
              />
            </div>
          )}

          {/* Job Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-gray-500 text-sm">Provider</p>
              <p className="text-white">{job.provider}</p>
            </div>
            <div className="space-y-1">
              <p className="text-gray-500 text-sm">Input Type</p>
              <p className="text-white capitalize">{job.input_type}</p>
            </div>
            <div className="space-y-1">
              <p className="text-gray-500 text-sm">Status</p>
              <Badge
                className={
                  job.status === 'completed'
                    ? 'bg-green-500/10 text-green-400'
                    : job.status === 'failed'
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-blue-500/10 text-blue-400'
                }
              >
                {job.status}
              </Badge>
            </div>
            <div className="space-y-1">
              <p className="text-gray-500 text-sm">Created</p>
              <p className="text-white">{new Date(job.created_at).toLocaleString()}</p>
            </div>
          </div>

          {/* Input */}
          <div className="space-y-1">
            <p className="text-gray-500 text-sm">Input</p>
            <p className="text-white bg-gray-800 rounded-lg p-3 text-sm break-all">
              {job.input}
            </p>
          </div>

          {/* Error */}
          {job.error && (
            <div className="space-y-1">
              <p className="text-red-400 text-sm flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Error
              </p>
              <p className="text-red-300 bg-red-500/10 rounded-lg p-3 text-sm">
                {job.error}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            {job.status === 'completed' && job.output_url && (
              <Button
                className="bg-rose-500 hover:bg-rose-600"
                onClick={() => window.open(job.output_url, '_blank')}
              >
                <Box className="mr-2 h-4 w-4" />
                View 3D Model
              </Button>
            )}
            {job.status === 'failed' && (
              <Button className="bg-amber-500 hover:bg-amber-600">
                <RotateCcw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            )}
            <Button variant="outline" className="border-gray-700" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
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
