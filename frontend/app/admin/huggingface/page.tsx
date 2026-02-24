'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Brain,
  Cpu,
  Layers,
  Download,
  Play,
  Pause,
  RefreshCw,
  Moon,
  ExternalLink,
  Loader2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Settings,
  Shield,
  TrendingUp,
  Activity,
  Zap,
  Globe,
  ArrowUpDown,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface HFSpace {
  id: string;
  name: string;
  status: 'running' | 'building' | 'sleeping' | 'stopped' | 'error';
  url: string;
  sdk: string;
  sdkVersion: string;
  hardware: string;
  createdAt: string;
  lastUpdated: string;
}

interface HFModel {
  id: string;
  name: string;
  taskType: string;
  downloads: number;
  likes: number;
  lastUpdated: string;
  tags: string[];
}

interface HFEndpoint {
  id: string;
  name: string;
  model: string;
  status: 'running' | 'scaling' | 'paused' | 'failed';
  requestsPerMin: number;
  avgLatencyMs: number;
  instanceType: string;
  replicas: number;
  maxReplicas: number;
}

interface HFStats {
  modelsDeployed: number;
  spacesActive: number;
  inferenceEndpoints: number;
  totalDownloads: number;
}

// ---------------------------------------------------------------------------
// Simulated Data
// ---------------------------------------------------------------------------

const SIMULATED_STATS: HFStats = {
  modelsDeployed: 12,
  spacesActive: 5,
  inferenceEndpoints: 3,
  totalDownloads: 284_500,
};

const SIMULATED_SPACES: HFSpace[] = [
  {
    id: 'space-001',
    name: 'skyyrose/product-image-gen',
    status: 'running',
    url: 'https://huggingface.co/spaces/skyyrose/product-image-gen',
    sdk: 'Gradio',
    sdkVersion: '4.44.0',
    hardware: 'A10G Small',
    createdAt: '2025-11-15T10:00:00Z',
    lastUpdated: '2026-02-20T14:30:00Z',
  },
  {
    id: 'space-002',
    name: 'skyyrose/fashion-classifier',
    status: 'running',
    url: 'https://huggingface.co/spaces/skyyrose/fashion-classifier',
    sdk: 'Gradio',
    sdkVersion: '4.44.0',
    hardware: 'T4 Medium',
    createdAt: '2025-12-01T08:00:00Z',
    lastUpdated: '2026-02-18T09:15:00Z',
  },
  {
    id: 'space-003',
    name: 'skyyrose/brand-voice-chat',
    status: 'building',
    url: 'https://huggingface.co/spaces/skyyrose/brand-voice-chat',
    sdk: 'Streamlit',
    sdkVersion: '1.40.0',
    hardware: 'CPU Basic',
    createdAt: '2026-02-10T12:00:00Z',
    lastUpdated: '2026-02-24T08:45:00Z',
  },
  {
    id: 'space-004',
    name: 'skyyrose/collection-recommender',
    status: 'sleeping',
    url: 'https://huggingface.co/spaces/skyyrose/collection-recommender',
    sdk: 'Gradio',
    sdkVersion: '4.42.0',
    hardware: 'CPU Basic',
    createdAt: '2025-10-20T16:00:00Z',
    lastUpdated: '2026-01-30T11:20:00Z',
  },
  {
    id: 'space-005',
    name: 'skyyrose/3d-texture-preview',
    status: 'stopped',
    url: 'https://huggingface.co/spaces/skyyrose/3d-texture-preview',
    sdk: 'Gradio',
    sdkVersion: '4.40.0',
    hardware: 'A10G Small',
    createdAt: '2025-09-05T09:00:00Z',
    lastUpdated: '2025-12-15T17:00:00Z',
  },
];

const SIMULATED_MODELS: HFModel[] = [
  {
    id: 'model-001',
    name: 'skyyrose/fashion-embeddings-v2',
    taskType: 'feature-extraction',
    downloads: 128_400,
    likes: 342,
    lastUpdated: '2026-02-19T10:30:00Z',
    tags: ['fashion', 'embeddings', 'luxury', 'pytorch'],
  },
  {
    id: 'model-002',
    name: 'skyyrose/product-caption-gen',
    taskType: 'text-generation',
    downloads: 67_200,
    likes: 189,
    lastUpdated: '2026-02-15T14:00:00Z',
    tags: ['captions', 'luxury-fashion', 'transformers'],
  },
  {
    id: 'model-003',
    name: 'skyyrose/rose-gold-lora',
    taskType: 'text-to-image',
    downloads: 45_800,
    likes: 521,
    lastUpdated: '2026-02-10T08:00:00Z',
    tags: ['lora', 'sdxl', 'rose-gold', 'fashion'],
  },
  {
    id: 'model-004',
    name: 'skyyrose/garment-segmentation',
    taskType: 'image-segmentation',
    downloads: 23_100,
    likes: 97,
    lastUpdated: '2026-01-28T16:45:00Z',
    tags: ['segmentation', 'fashion', 'onnx'],
  },
  {
    id: 'model-005',
    name: 'skyyrose/brand-sentiment',
    taskType: 'text-classification',
    downloads: 12_600,
    likes: 64,
    lastUpdated: '2026-01-15T12:00:00Z',
    tags: ['sentiment', 'brand-monitoring', 'bert'],
  },
  {
    id: 'model-006',
    name: 'skyyrose/color-palette-extractor',
    taskType: 'image-classification',
    downloads: 7_400,
    likes: 41,
    lastUpdated: '2025-12-20T09:30:00Z',
    tags: ['color', 'fashion', 'palette', 'vision'],
  },
];

const SIMULATED_ENDPOINTS: HFEndpoint[] = [
  {
    id: 'ep-001',
    name: 'fashion-embeddings-prod',
    model: 'skyyrose/fashion-embeddings-v2',
    status: 'running',
    requestsPerMin: 245,
    avgLatencyMs: 42,
    instanceType: 'GPU - Nvidia A10G',
    replicas: 2,
    maxReplicas: 4,
  },
  {
    id: 'ep-002',
    name: 'caption-gen-prod',
    model: 'skyyrose/product-caption-gen',
    status: 'running',
    requestsPerMin: 89,
    avgLatencyMs: 310,
    instanceType: 'GPU - Nvidia T4',
    replicas: 1,
    maxReplicas: 3,
  },
  {
    id: 'ep-003',
    name: 'segmentation-staging',
    model: 'skyyrose/garment-segmentation',
    status: 'paused',
    requestsPerMin: 0,
    avgLatencyMs: 0,
    instanceType: 'GPU - Nvidia T4',
    replicas: 0,
    maxReplicas: 2,
  },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function HuggingFacePage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<HFStats | null>(null);
  const [spaces, setSpaces] = useState<HFSpace[]>([]);
  const [models, setModels] = useState<HFModel[]>([]);
  const [endpoints, setEndpoints] = useState<HFEndpoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Settings state
  const [tokenStatus, setTokenStatus] = useState<'valid' | 'expired' | 'missing'>('valid');
  const [defaultOrg, setDefaultOrg] = useState('skyyrose');
  const [autoDeploy, setAutoDeploy] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      // Simulated data -- replace with real HuggingFace API calls once backend is live:
      //   const [statsData, spacesData, modelsData, endpointsData] = await Promise.all([
      //     api.huggingface.getStats(),
      //     api.huggingface.getSpaces(),
      //     api.huggingface.getModels(),
      //     api.huggingface.getEndpoints(),
      //   ]);
      setStats(SIMULATED_STATS);
      setSpaces(SIMULATED_SPACES);
      setModels(SIMULATED_MODELS);
      setEndpoints(SIMULATED_ENDPOINTS);
      setError(null);
    } catch (err) {
      setError('Failed to load HuggingFace data. Backend may be offline.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return <HuggingFaceSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#FF9D00]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#B76E79]/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[#FF9D00] to-[#B76E79] flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              HuggingFace Hub
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Deploy and manage AI models on HuggingFace Spaces
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#FF9D00] text-[#FF9D00]">
              <div className="h-2 w-2 rounded-full mr-2 bg-[#FF9D00] animate-pulse" />
              HuggingFace Connected
            </Badge>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto text-red-400 hover:text-red-300"
            onClick={() => setError(null)}
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <GradientStatCard
          title="Models Deployed"
          value={stats?.modelsDeployed ?? 0}
          icon={Layers}
          gradient="from-[#FF9D00] to-[#B76E79]"
        />
        <GradientStatCard
          title="Spaces Active"
          value={stats?.spacesActive ?? 0}
          icon={Globe}
          gradient="from-emerald-500 to-teal-500"
        />
        <GradientStatCard
          title="Inference Endpoints"
          value={stats?.inferenceEndpoints ?? 0}
          icon={Zap}
          gradient="from-blue-500 to-cyan-500"
        />
        <GradientStatCard
          title="Total Downloads"
          value={formatNumber(stats?.totalDownloads ?? 0)}
          icon={Download}
          gradient="from-purple-500 to-pink-500"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="spaces" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="spaces" className="data-[state=active]:bg-gray-700">
            <Globe className="mr-2 h-4 w-4" />
            Spaces
          </TabsTrigger>
          <TabsTrigger value="models" className="data-[state=active]:bg-gray-700">
            <Layers className="mr-2 h-4 w-4" />
            Models
          </TabsTrigger>
          <TabsTrigger value="inference" className="data-[state=active]:bg-gray-700">
            <Zap className="mr-2 h-4 w-4" />
            Inference
          </TabsTrigger>
          <TabsTrigger value="settings" className="data-[state=active]:bg-gray-700">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        {/* Spaces Tab */}
        <TabsContent value="spaces" className="space-y-4">
          {spaces.length === 0 ? (
            <Card className="bg-gray-900 border-gray-800 py-12">
              <CardContent className="text-center">
                <Globe className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500">No spaces deployed</p>
                <p className="text-gray-600 text-sm mt-1">
                  Deploy your first HuggingFace Space to get started
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {spaces.map((space) => (
                <SpaceCard key={space.id} space={space} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Models Tab */}
        <TabsContent value="models" className="space-y-4">
          {models.length === 0 ? (
            <Card className="bg-gray-900 border-gray-800 py-12">
              <CardContent className="text-center">
                <Layers className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500">No models pushed yet</p>
                <p className="text-gray-600 text-sm mt-1">
                  Push your first model to the HuggingFace Hub
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {models.map((model) => (
                <ModelCard key={model.id} model={model} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Inference Tab */}
        <TabsContent value="inference" className="space-y-4">
          {endpoints.length === 0 ? (
            <Card className="bg-gray-900 border-gray-800 py-12">
              <CardContent className="text-center">
                <Zap className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500">No inference endpoints</p>
                <p className="text-gray-600 text-sm mt-1">
                  Create an inference endpoint to serve your models
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {endpoints.map((endpoint) => (
                <EndpointCard key={endpoint.id} endpoint={endpoint} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="h-5 w-5 text-[#FF9D00]" />
                HuggingFace Account
              </CardTitle>
              <CardDescription className="text-gray-400">
                Manage your HuggingFace API connection and deployment preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* API Token Status */}
              <div className="space-y-2">
                <Label className="text-gray-300">API Token</Label>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-10 rounded-md bg-gray-800 border border-gray-700 px-3 flex items-center">
                    <span className="text-gray-400 font-mono text-sm">
                      hf_************************************KxMn
                    </span>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      tokenStatus === 'valid'
                        ? 'border-green-500 text-green-400'
                        : tokenStatus === 'expired'
                        ? 'border-yellow-500 text-yellow-400'
                        : 'border-red-500 text-red-400'
                    }
                  >
                    <div
                      className={`h-2 w-2 rounded-full mr-2 ${
                        tokenStatus === 'valid'
                          ? 'bg-green-500'
                          : tokenStatus === 'expired'
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                    />
                    {tokenStatus === 'valid'
                      ? 'Valid'
                      : tokenStatus === 'expired'
                      ? 'Expired'
                      : 'Missing'}
                  </Badge>
                </div>
                <p className="text-xs text-gray-500">
                  Token is stored securely in environment variables. Update via Vercel dashboard.
                </p>
              </div>

              {/* Default Organization */}
              <div className="space-y-2">
                <Label className="text-gray-300">Default Organization</Label>
                <Input
                  value={defaultOrg}
                  onChange={(e) => setDefaultOrg(e.target.value)}
                  placeholder="your-org-name"
                  className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                />
                <p className="text-xs text-gray-500">
                  Models and spaces will be pushed under this organization by default.
                </p>
              </div>

              {/* Auto-Deploy Toggle */}
              <div className="flex items-center justify-between rounded-lg border border-gray-700 bg-gray-800/50 p-4">
                <div>
                  <p className="text-sm font-medium text-white">Auto-Deploy on Push</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Automatically rebuild and redeploy spaces when model weights are updated
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setAutoDeploy(!autoDeploy)}
                  className={
                    autoDeploy
                      ? 'border-green-500 text-green-400 hover:bg-green-500/10'
                      : 'border-gray-600 text-gray-400 hover:bg-gray-700'
                  }
                >
                  {autoDeploy ? (
                    <>
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Enabled
                    </>
                  ) : (
                    <>
                      <Pause className="mr-1 h-3 w-3" />
                      Disabled
                    </>
                  )}
                </Button>
              </div>

              {/* Save Button */}
              <Button className="w-full bg-gradient-to-r from-[#FF9D00] to-[#B76E79] hover:from-[#e68e00] hover:to-[#a5606a] h-12 text-white">
                <Settings className="mr-2 h-5 w-5" />
                Save Settings
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

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
          <div
            className={`h-12 w-12 rounded-xl bg-gradient-to-br ${gradient} bg-opacity-10 flex items-center justify-center`}
          >
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SpaceCard({ space }: { space: HFSpace }) {
  const statusConfig: Record<
    HFSpace['status'],
    { color: string; bgColor: string; borderColor: string; label: string }
  > = {
    running: {
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500',
      label: 'Running',
    },
    building: {
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500',
      label: 'Building',
    },
    sleeping: {
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500',
      label: 'Sleeping',
    },
    stopped: {
      color: 'text-gray-400',
      bgColor: 'bg-gray-500/10',
      borderColor: 'border-gray-500',
      label: 'Stopped',
    },
    error: {
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500',
      label: 'Error',
    },
  };

  const config = statusConfig[space.status];

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <div
        className={`h-1 ${
          space.status === 'running'
            ? 'bg-gradient-to-r from-green-500 to-emerald-500'
            : space.status === 'building'
            ? 'bg-gradient-to-r from-amber-500 to-yellow-500'
            : space.status === 'sleeping'
            ? 'bg-gradient-to-r from-blue-500 to-cyan-500'
            : 'bg-gradient-to-r from-gray-500 to-gray-600'
        }`}
      />
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div
            className={`h-10 w-10 rounded-lg ${config.bgColor} flex items-center justify-center flex-shrink-0`}
          >
            <Globe className={`h-5 w-5 ${config.color}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-sm font-medium text-white truncate">{space.name}</span>
              <Badge variant="outline" className={`${config.borderColor} ${config.color}`}>
                {config.label}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-3 text-xs text-gray-500 mt-2">
              <span className="flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {space.hardware}
              </span>
              <span className="flex items-center gap-1">
                <Layers className="h-3 w-3" />
                {space.sdk} {space.sdkVersion}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Updated {new Date(space.lastUpdated).toLocaleDateString()}
              </span>
            </div>
          </div>
          <div className="flex gap-1 flex-shrink-0">
            {space.status === 'sleeping' || space.status === 'stopped' ? (
              <Button
                size="sm"
                variant="ghost"
                className="text-green-400 hover:text-green-300 hover:bg-green-500/10 h-8 w-8 p-0"
                title="Start"
              >
                <Play className="h-4 w-4" />
              </Button>
            ) : space.status === 'running' ? (
              <Button
                size="sm"
                variant="ghost"
                className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 h-8 w-8 p-0"
                title="Sleep"
              >
                <Moon className="h-4 w-4" />
              </Button>
            ) : null}
            <Button
              size="sm"
              variant="ghost"
              className="text-gray-400 hover:text-white h-8 w-8 p-0"
              title="Restart"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="text-[#FF9D00] hover:text-[#ffb740] h-8 w-8 p-0"
              title="Open on Hub"
              onClick={() => window.open(space.url, '_blank')}
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ModelCard({ model }: { model: HFModel }) {
  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <div className="h-1 bg-gradient-to-r from-[#FF9D00] to-[#B76E79]" />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white truncate">{model.name}</CardTitle>
          <Badge variant="secondary" className="bg-gray-800 text-gray-300 text-xs flex-shrink-0">
            {model.taskType}
          </Badge>
        </div>
        <CardDescription className="text-gray-500">
          Last updated {new Date(model.lastUpdated).toLocaleDateString()}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-3">
          <div className="flex items-center gap-1.5 text-sm">
            <Download className="h-4 w-4 text-gray-500" />
            <span className="text-white font-medium">{formatNumber(model.downloads)}</span>
            <span className="text-gray-500">downloads</span>
          </div>
          <div className="flex items-center gap-1.5 text-sm">
            <TrendingUp className="h-4 w-4 text-gray-500" />
            <span className="text-white font-medium">{model.likes}</span>
            <span className="text-gray-500">likes</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-1 mb-3">
          {model.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center text-xs text-[#FF9D00] bg-[#FF9D00]/10 px-2 py-0.5 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
        <Button
          size="sm"
          variant="ghost"
          className="w-full text-[#FF9D00] hover:text-[#ffb740] hover:bg-[#FF9D00]/10"
          onClick={() =>
            window.open(`https://huggingface.co/${model.name}`, '_blank')
          }
        >
          View on Hub <ExternalLink className="ml-2 h-3 w-3" />
        </Button>
      </CardContent>
    </Card>
  );
}

function EndpointCard({ endpoint }: { endpoint: HFEndpoint }) {
  const statusConfig: Record<
    HFEndpoint['status'],
    { color: string; bgColor: string; borderColor: string; label: string; animate?: boolean }
  > = {
    running: {
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500',
      label: 'Running',
      animate: true,
    },
    scaling: {
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500',
      label: 'Scaling',
      animate: true,
    },
    paused: {
      color: 'text-gray-400',
      bgColor: 'bg-gray-500/10',
      borderColor: 'border-gray-500',
      label: 'Paused',
    },
    failed: {
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500',
      label: 'Failed',
    },
  };

  const config = statusConfig[endpoint.status];

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <div
        className={`h-1 ${
          endpoint.status === 'running'
            ? 'bg-gradient-to-r from-green-500 to-emerald-500'
            : endpoint.status === 'scaling'
            ? 'bg-gradient-to-r from-amber-500 to-yellow-500'
            : 'bg-gradient-to-r from-gray-500 to-gray-600'
        }`}
      />
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div
            className={`h-10 w-10 rounded-lg ${config.bgColor} flex items-center justify-center flex-shrink-0`}
          >
            <Zap className={`h-5 w-5 ${config.color}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-sm font-medium text-white truncate">
                {endpoint.name}
              </span>
              <Badge variant="outline" className={`${config.borderColor} ${config.color}`}>
                {config.animate && (
                  <div className={`h-2 w-2 rounded-full mr-2 ${config.color.replace('text-', 'bg-')} animate-pulse`} />
                )}
                {config.label}
              </Badge>
            </div>
            <p className="text-xs text-gray-500 truncate">{endpoint.model}</p>
            <div className="grid grid-cols-3 gap-3 mt-3">
              <div className="rounded-lg bg-gray-800/50 px-3 py-2">
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Activity className="h-3 w-3" />
                  Req/min
                </p>
                <p className="text-sm font-medium text-white">{endpoint.requestsPerMin}</p>
              </div>
              <div className="rounded-lg bg-gray-800/50 px-3 py-2">
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Latency
                </p>
                <p className="text-sm font-medium text-white">
                  {endpoint.avgLatencyMs > 0 ? `${endpoint.avgLatencyMs}ms` : '--'}
                </p>
              </div>
              <div className="rounded-lg bg-gray-800/50 px-3 py-2">
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Cpu className="h-3 w-3" />
                  Replicas
                </p>
                <p className="text-sm font-medium text-white">
                  {endpoint.replicas}/{endpoint.maxReplicas}
                </p>
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-1 flex-shrink-0">
            {endpoint.status === 'paused' ? (
              <Button
                size="sm"
                variant="ghost"
                className="text-green-400 hover:text-green-300 hover:bg-green-500/10 h-8 w-8 p-0"
                title="Resume"
              >
                <Play className="h-4 w-4" />
              </Button>
            ) : endpoint.status === 'running' ? (
              <Button
                size="sm"
                variant="ghost"
                className="text-gray-400 hover:text-white h-8 w-8 p-0"
                title="Pause"
              >
                <Pause className="h-4 w-4" />
              </Button>
            ) : null}
            <Button
              size="sm"
              variant="ghost"
              className="text-[#FF9D00] hover:text-[#ffb740] h-8 w-8 p-0"
              title="Scale"
            >
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function HuggingFaceSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-10 w-80 bg-gray-800" />
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-28 bg-gray-800" />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}
