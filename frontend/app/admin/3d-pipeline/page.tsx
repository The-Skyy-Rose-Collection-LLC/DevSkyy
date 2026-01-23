'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Box,
  Upload,
  Type,
  Image as ImageIcon,
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Layers,
  Cpu,
  Zap,
  ExternalLink,
} from 'lucide-react';
import { api, type Provider3D, type Job3D, type PipelineStatus } from '@/lib/api';
import { use3DPipelineWS } from '@/hooks/useWebSocket';

export default function Pipeline3DPage() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [providers, setProviders] = useState<Provider3D[]>([]);
  const [jobs, setJobs] = useState<Job3D[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [inputType, setInputType] = useState<'text' | 'image'>('text');
  const [textPrompt, setTextPrompt] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('');

  const { status: wsStatus, lastMessage } = use3DPipelineWS();

  useEffect(() => {
    async function fetchData() {
      try {
        const [statusData, providersData, jobsData] = await Promise.all([
          api.pipeline3d.getStatus(),
          api.pipeline3d.getProviders(),
          api.pipeline3d.getJobs(20),
        ]);
        setStatus(statusData);
        setProviders(providersData);
        setJobs(jobsData);
      } catch (err) {
        console.error('Failed to load 3D Pipeline data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  useEffect(() => {
    if (lastMessage?.data) {
      const event = lastMessage.data;
      if (event.event === 'job_completed' || event.event === 'job_failed') {
        api.pipeline3d.getJobs(20).then(setJobs);
        api.pipeline3d.getStatus().then(setStatus);
      }
    }
  }, [lastMessage]);

  async function handleGenerate() {
    if (inputType === 'text' && !textPrompt.trim()) return;
    if (inputType === 'image' && !imageUrl.trim()) return;

    setGenerating(true);
    try {
      const job = inputType === 'text'
        ? await api.pipeline3d.generateFromText({
            prompt: textPrompt.trim(),
            provider: selectedProvider || undefined,
          })
        : await api.pipeline3d.generateFromImage({
            image_url: imageUrl.trim(),
            provider: selectedProvider || undefined,
          });
      setJobs((prev) => [job, ...prev]);
      setTextPrompt('');
      setImageUrl('');
    } catch (err) {
      console.error('Generation failed:', err);
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return <Pipeline3DSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header with Glassmorphism */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-rose-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-rose-500 to-purple-600 flex items-center justify-center">
                <Box className="h-6 w-6 text-white" />
              </div>
              3D Generation Pipeline
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Transform text and images into AR-ready 3D models
            </p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={status?.status || 'down'} />
            <Badge
              variant="outline"
              className={wsStatus === 'connected' ? 'border-green-500 text-green-400' : 'border-yellow-500 text-yellow-400'}
            >
              {wsStatus === 'connected' ? 'Live Updates' : 'Connecting...'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Stats with Gradient Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <GradientStatCard
          title="Providers Online"
          value={`${status?.providers_online || 0}/${status?.providers_total || 0}`}
          icon={Cpu}
          gradient="from-blue-500 to-cyan-500"
        />
        <GradientStatCard
          title="Active Jobs"
          value={status?.active_jobs || 0}
          icon={Zap}
          gradient="from-rose-500 to-pink-500"
        />
        <GradientStatCard
          title="Queued"
          value={status?.queued_jobs || 0}
          icon={Clock}
          gradient="from-amber-500 to-orange-500"
        />
        <GradientStatCard
          title="Models Generated"
          value={jobs.filter((j) => j.status === 'completed').length}
          icon={Layers}
          gradient="from-emerald-500 to-teal-500"
        />
      </div>

      {/* Generation Interface */}
      <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-rose-400" />
            Generate 3D Model
          </CardTitle>
          <CardDescription className="text-gray-400">
            Create AR-ready 3D models from text descriptions or images
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Input Type Toggle */}
          <div className="flex gap-2">
            <Button
              variant={inputType === 'text' ? 'default' : 'outline'}
              onClick={() => setInputType('text')}
              className={inputType === 'text'
                ? 'bg-gradient-to-r from-rose-500 to-rose-600'
                : 'border-gray-700 text-gray-400'}
            >
              <Type className="mr-2 h-4 w-4" />
              Text to 3D
            </Button>
            <Button
              variant={inputType === 'image' ? 'default' : 'outline'}
              onClick={() => setInputType('image')}
              className={inputType === 'image'
                ? 'bg-gradient-to-r from-rose-500 to-rose-600'
                : 'border-gray-700 text-gray-400'}
            >
              <ImageIcon className="mr-2 h-4 w-4" />
              Image to 3D
            </Button>
          </div>

          {/* Input Fields */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-gray-300">
                {inputType === 'text' ? 'Prompt' : 'Image URL'}
              </Label>
              {inputType === 'text' ? (
                <Input
                  placeholder="A luxury rose-gold handbag with leather texture..."
                  value={textPrompt}
                  onChange={(e) => setTextPrompt(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                />
              ) : (
                <Input
                  placeholder="https://example.com/product-image.jpg"
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                />
              )}
            </div>
            <div className="space-y-2">
              <Label className="text-gray-300">Provider (Optional)</Label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="w-full h-10 rounded-md bg-gray-800 border border-gray-700 text-white px-3"
              >
                <option value="">Round Table (All Compete)</option>
                {providers.map((p) => (
                  <option key={p.id} value={p.id} disabled={p.status !== 'online'}>
                    {p.name} {p.status !== 'online' ? `(${p.status})` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={generating || (inputType === 'text' ? !textPrompt.trim() : !imageUrl.trim())}
            className="w-full bg-gradient-to-r from-rose-500 via-rose-600 to-purple-600 hover:from-rose-600 hover:via-rose-700 hover:to-purple-700 h-12 text-lg"
          >
            {generating ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Play className="mr-2 h-5 w-5" />
                Generate 3D Model
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="jobs" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="jobs" className="data-[state=active]:bg-gray-700">
            Recent Jobs
          </TabsTrigger>
          <TabsTrigger value="providers" className="data-[state=active]:bg-gray-700">
            Providers
          </TabsTrigger>
        </TabsList>

        <TabsContent value="jobs">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
            {jobs.length === 0 && (
              <Card className="col-span-full bg-gray-900 border-gray-800 py-12">
                <CardContent className="text-center">
                  <Box className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-500">No generation jobs yet</p>
                  <p className="text-gray-600 text-sm mt-1">
                    Create your first 3D model above
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="providers">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {providers.map((provider) => (
              <Card key={provider.id} className="bg-gray-900 border-gray-800 overflow-hidden">
                <div className={`h-1 ${
                  provider.status === 'online'
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                    : provider.status === 'busy'
                    ? 'bg-gradient-to-r from-yellow-500 to-amber-500'
                    : 'bg-gradient-to-r from-red-500 to-rose-500'
                }`} />
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg text-white">{provider.name}</CardTitle>
                    <Badge
                      variant="outline"
                      className={
                        provider.status === 'online'
                          ? 'border-green-500 text-green-400'
                          : provider.status === 'busy'
                          ? 'border-yellow-500 text-yellow-400'
                          : 'border-red-500 text-red-400'
                      }
                    >
                      {provider.status}
                    </Badge>
                  </div>
                  <CardDescription className="text-gray-500 capitalize">
                    {provider.type} provider
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Avg Generation:</span>
                      <span className="text-white">{provider.avg_generation_time_s}s</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-3">
                      {provider.capabilities.map((cap) => (
                        <Badge key={cap} variant="secondary" className="bg-gray-800 text-gray-300 text-xs">
                          {cap}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    healthy: { class: 'border-green-500 text-green-400', label: 'Healthy' },
    degraded: { class: 'border-yellow-500 text-yellow-400', label: 'Degraded' },
    down: { class: 'border-red-500 text-red-400', label: 'Down' },
  };
  const { class: className, label } = config[status as keyof typeof config] || config.down;

  return (
    <Badge variant="outline" className={className}>
      <div className={`h-2 w-2 rounded-full mr-2 ${
        status === 'healthy' ? 'bg-green-500 animate-pulse' :
        status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
      }`} />
      {label}
    </Badge>
  );
}

function GradientStatCard({
  title,
  value,
  icon: Icon,
  gradient,
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  gradient: string;
}) {
  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
      <div className={`h-1 bg-gradient-to-r ${gradient}`} />
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">{title}</p>
            <p className="text-2xl font-bold text-white mt-1">{value}</p>
          </div>
          <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${gradient} bg-opacity-10 flex items-center justify-center`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function JobCard({ job }: { job: Job3D }) {
  const statusConfig = {
    queued: { icon: Clock, class: 'text-gray-400', bg: 'bg-gray-500/10' },
    processing: { icon: Loader2, class: 'text-blue-400 animate-spin', bg: 'bg-blue-500/10' },
    completed: { icon: CheckCircle2, class: 'text-green-400', bg: 'bg-green-500/10' },
    failed: { icon: XCircle, class: 'text-red-400', bg: 'bg-red-500/10' },
  };
  const { icon: StatusIcon, class: iconClass, bg } = statusConfig[job.status];

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={`h-10 w-10 rounded-lg ${bg} flex items-center justify-center flex-shrink-0`}>
            <StatusIcon className={`h-5 w-5 ${iconClass}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-white truncate">
                {job.provider}
              </span>
              <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
                {job.input_type}
              </Badge>
            </div>
            <p className="text-xs text-gray-500 truncate mt-1">{job.input}</p>
            <p className="text-xs text-gray-600 mt-2">
              {new Date(job.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        {job.status === 'completed' && job.output_url && (
          <Button
            size="sm"
            variant="ghost"
            className="w-full mt-3 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
            onClick={() => window.open(job.output_url, '_blank')}
          >
            View Model <ExternalLink className="ml-2 h-3 w-3" />
          </Button>
        )}
        {job.status === 'failed' && job.error && (
          <p className="text-xs text-red-400 mt-3 truncate">{job.error}</p>
        )}
      </CardContent>
    </Card>
  );
}

function Pipeline3DSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-64 bg-gray-800" />
    </div>
  );
}
