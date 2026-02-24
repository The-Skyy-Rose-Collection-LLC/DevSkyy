'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Image as ImageIcon,
  Sparkles,
  Palette,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Download,
  Layers,
  Cpu,
  Zap,
  Eye,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ProviderStatus = 'connected' | 'disconnected' | 'checking';
type GenerationStatus = 'completed' | 'processing' | 'failed' | 'queued';
type StyleOption = 'product-photo' | 'lifestyle' | 'editorial' | 'flat-lay';
type AspectRatio = '1:1' | '4:3' | '16:9' | '9:16';
type Provider = 'gemini' | 'imagen' | 'huggingface-flux';

interface ImageProvider {
  id: Provider;
  name: string;
  description: string;
  model: string;
  status: ProviderStatus;
  avgLatencyMs: number;
  generationsToday: number;
  gradient: string;
  accentColor: string;
}

interface GeneratedImage {
  id: string;
  prompt: string;
  provider: Provider;
  style: StyleOption;
  aspectRatio: AspectRatio;
  status: GenerationStatus;
  thumbnailUrl: string | null;
  createdAt: string;
  durationMs: number | null;
  error: string | null;
}

interface PipelineStats {
  totalGenerations: number;
  successRate: number;
  avgDurationMs: number;
  providersOnline: number;
}

// ---------------------------------------------------------------------------
// Simulated Data
// ---------------------------------------------------------------------------

const SIMULATED_PROVIDERS: ImageProvider[] = [
  {
    id: 'gemini',
    name: 'Gemini',
    description: 'Google DeepMind multimodal image generation',
    model: 'gemini-2.0-flash-preview-image-generation',
    status: 'connected',
    avgLatencyMs: 3_200,
    generationsToday: 142,
    gradient: 'from-blue-500 to-cyan-500',
    accentColor: 'text-blue-400',
  },
  {
    id: 'imagen',
    name: 'Imagen',
    description: 'Google Imagen 3 for photorealistic output',
    model: 'imagen-3.0-generate-002',
    status: 'connected',
    avgLatencyMs: 5_800,
    generationsToday: 87,
    gradient: 'from-emerald-500 to-teal-500',
    accentColor: 'text-emerald-400',
  },
  {
    id: 'huggingface-flux',
    name: 'HuggingFace Flux',
    description: 'FLUX.1 schnell via HuggingFace Inference',
    model: 'black-forest-labs/FLUX.1-schnell',
    status: 'connected',
    avgLatencyMs: 8_400,
    generationsToday: 219,
    gradient: 'from-[#FF9D00] to-[#B76E79]',
    accentColor: 'text-[#FF9D00]',
  },
];

const SIMULATED_STATS: PipelineStats = {
  totalGenerations: 448,
  successRate: 97.3,
  avgDurationMs: 5_800,
  providersOnline: 3,
};

// Simulate placeholder thumbnails using gradient backgrounds as stand-ins
const PLACEHOLDER_GRADIENTS = [
  'from-rose-900/60 to-purple-900/60',
  'from-blue-900/60 to-cyan-900/60',
  'from-amber-900/60 to-orange-900/60',
  'from-emerald-900/60 to-teal-900/60',
  'from-pink-900/60 to-rose-900/60',
  'from-violet-900/60 to-indigo-900/60',
];

const SIMULATED_GALLERY: GeneratedImage[] = [
  {
    id: 'gen-001',
    prompt: 'Luxury rose gold handbag with embossed floral pattern, studio lighting, white background',
    provider: 'gemini',
    style: 'product-photo',
    aspectRatio: '1:1',
    status: 'completed',
    thumbnailUrl: null,
    createdAt: '2026-02-24T07:45:00Z',
    durationMs: 3_100,
    error: null,
  },
  {
    id: 'gen-002',
    prompt: 'Black Rose collection evening gown, editorial fashion photography, dramatic lighting',
    provider: 'imagen',
    style: 'editorial',
    aspectRatio: '9:16',
    status: 'completed',
    thumbnailUrl: null,
    createdAt: '2026-02-24T07:30:00Z',
    durationMs: 5_600,
    error: null,
  },
  {
    id: 'gen-003',
    prompt: 'Love Hurts collection accessories flat lay, marble surface, rose petals',
    provider: 'huggingface-flux',
    style: 'flat-lay',
    aspectRatio: '4:3',
    status: 'completed',
    thumbnailUrl: null,
    createdAt: '2026-02-24T07:15:00Z',
    durationMs: 8_200,
    error: null,
  },
  {
    id: 'gen-004',
    prompt: 'Signature collection lifestyle shoot, rooftop setting, golden hour',
    provider: 'gemini',
    style: 'lifestyle',
    aspectRatio: '16:9',
    status: 'completed',
    thumbnailUrl: null,
    createdAt: '2026-02-24T06:55:00Z',
    durationMs: 3_400,
    error: null,
  },
  {
    id: 'gen-005',
    prompt: 'Rose gold silk scarf, product photography, soft diffused light',
    provider: 'imagen',
    style: 'product-photo',
    aspectRatio: '1:1',
    status: 'processing',
    thumbnailUrl: null,
    createdAt: '2026-02-24T08:00:00Z',
    durationMs: null,
    error: null,
  },
  {
    id: 'gen-006',
    prompt: 'Kids Capsule collection playful scene, bright colors, studio backdrop',
    provider: 'huggingface-flux',
    style: 'lifestyle',
    aspectRatio: '4:3',
    status: 'failed',
    thumbnailUrl: null,
    createdAt: '2026-02-24T06:40:00Z',
    durationMs: null,
    error: 'Rate limit exceeded. Retry after 60s.',
  },
];

const STYLE_OPTIONS: { value: StyleOption; label: string }[] = [
  { value: 'product-photo', label: 'Product Photo' },
  { value: 'lifestyle', label: 'Lifestyle' },
  { value: 'editorial', label: 'Editorial' },
  { value: 'flat-lay', label: 'Flat Lay' },
];

const ASPECT_RATIO_OPTIONS: { value: AspectRatio; label: string }[] = [
  { value: '1:1', label: '1:1 Square' },
  { value: '4:3', label: '4:3 Landscape' },
  { value: '16:9', label: '16:9 Wide' },
  { value: '9:16', label: '9:16 Portrait' },
];

const PROVIDER_OPTIONS: { value: Provider | ''; label: string }[] = [
  { value: '', label: 'Auto-select (Best Available)' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'imagen', label: 'Imagen 3' },
  { value: 'huggingface-flux', label: 'HuggingFace Flux' },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function ImageryPipelinePage() {
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState<ImageProvider[]>([]);
  const [gallery, setGallery] = useState<GeneratedImage[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [generating, setGenerating] = useState(false);

  // Form state
  const [prompt, setPrompt] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<Provider | ''>('');
  const [selectedStyle, setSelectedStyle] = useState<StyleOption>('product-photo');
  const [selectedAspectRatio, setSelectedAspectRatio] = useState<AspectRatio>('1:1');

  useEffect(() => {
    // Simulate API fetch with a small delay
    const timer = setTimeout(() => {
      setProviders(SIMULATED_PROVIDERS);
      setGallery(SIMULATED_GALLERY);
      setStats(SIMULATED_STATS);
      setLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  async function handleGenerate() {
    if (!prompt.trim()) return;

    setGenerating(true);

    // Optimistically add a queued item to the gallery
    const newEntry: GeneratedImage = {
      id: `gen-${Date.now()}`,
      prompt: prompt.trim(),
      provider: selectedProvider || 'gemini',
      style: selectedStyle,
      aspectRatio: selectedAspectRatio,
      status: 'queued',
      thumbnailUrl: null,
      createdAt: new Date().toISOString(),
      durationMs: null,
      error: null,
    };

    setGallery((prev) => [newEntry, ...prev]);

    // Simulate async generation (2.5s)
    await new Promise((resolve) => setTimeout(resolve, 2_500));

    // Move to "processing" then "completed"
    setGallery((prev) =>
      prev.map((item) =>
        item.id === newEntry.id ? { ...item, status: 'processing' } : item
      )
    );

    await new Promise((resolve) => setTimeout(resolve, 3_000));

    setGallery((prev) =>
      prev.map((item) =>
        item.id === newEntry.id
          ? { ...item, status: 'completed', durationMs: 3_200 }
          : item
      )
    );

    setStats((prev) =>
      prev
        ? { ...prev, totalGenerations: prev.totalGenerations + 1 }
        : prev
    );

    setPrompt('');
    setGenerating(false);
  }

  if (loading) {
    return <ImageryPipelineSkeleton />;
  }

  const onlineCount = providers.filter((p) => p.status === 'connected').length;

  return (
    <div className="space-y-6">
      {/* Gradient Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#B76E79]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[#B76E79] to-rose-600 flex items-center justify-center">
                <ImageIcon className="h-6 w-6 text-white" />
              </div>
              Imagery Pipeline
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              AI-powered image generation for product photography
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#B76E79] text-[#B76E79]">
              <div className="h-2 w-2 rounded-full mr-2 bg-[#B76E79] animate-pulse" />
              {onlineCount}/{providers.length} Providers Online
            </Badge>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <GradientStatCard
          title="Total Generations"
          value={stats?.totalGenerations ?? 0}
          icon={Layers}
          gradient="from-[#B76E79] to-rose-600"
        />
        <GradientStatCard
          title="Success Rate"
          value={`${stats?.successRate ?? 0}%`}
          icon={CheckCircle2}
          gradient="from-emerald-500 to-teal-500"
        />
        <GradientStatCard
          title="Avg Generation"
          value={`${((stats?.avgDurationMs ?? 0) / 1000).toFixed(1)}s`}
          icon={Zap}
          gradient="from-amber-500 to-orange-500"
        />
        <GradientStatCard
          title="Providers Online"
          value={`${stats?.providersOnline ?? 0}/3`}
          icon={Cpu}
          gradient="from-blue-500 to-cyan-500"
        />
      </div>

      {/* Provider Status Cards */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[#B76E79]" />
          Provider Status
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          {providers.map((provider) => (
            <ProviderCard key={provider.id} provider={provider} />
          ))}
        </div>
      </div>

      {/* Generation Form */}
      <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Palette className="h-5 w-5 text-[#B76E79]" />
            Generate Image
          </CardTitle>
          <CardDescription className="text-gray-400">
            Create AI-generated product imagery using your preferred provider and style
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Prompt */}
          <div className="space-y-2">
            <Label className="text-gray-300">Prompt</Label>
            <Input
              placeholder="Luxury rose gold handbag with embossed floral pattern, studio lighting, white background..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 h-12"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && prompt.trim() && !generating) {
                  handleGenerate();
                }
              }}
            />
          </div>

          {/* Controls Grid */}
          <div className="grid gap-4 md:grid-cols-3">
            {/* Provider Selector */}
            <div className="space-y-2">
              <Label className="text-gray-300">Provider</Label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value as Provider | '')}
                className="w-full h-10 rounded-md bg-gray-800 border border-gray-700 text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#B76E79]/50"
              >
                {PROVIDER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Style Selector */}
            <div className="space-y-2">
              <Label className="text-gray-300">Style</Label>
              <select
                value={selectedStyle}
                onChange={(e) => setSelectedStyle(e.target.value as StyleOption)}
                className="w-full h-10 rounded-md bg-gray-800 border border-gray-700 text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#B76E79]/50"
              >
                {STYLE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Aspect Ratio Selector */}
            <div className="space-y-2">
              <Label className="text-gray-300">Aspect Ratio</Label>
              <select
                value={selectedAspectRatio}
                onChange={(e) => setSelectedAspectRatio(e.target.value as AspectRatio)}
                className="w-full h-10 rounded-md bg-gray-800 border border-gray-700 text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#B76E79]/50"
              >
                {ASPECT_RATIO_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={generating || !prompt.trim()}
            className="w-full bg-gradient-to-r from-[#B76E79] via-rose-500 to-rose-600 hover:from-rose-600 hover:via-rose-600 hover:to-rose-700 h-12 text-lg font-semibold disabled:opacity-50"
          >
            {generating ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                Generate Image
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Gallery */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Eye className="h-5 w-5 text-[#B76E79]" />
            Recent Generations
          </h2>
          <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
            {gallery.length} images
          </Badge>
        </div>

        {gallery.length === 0 ? (
          <Card className="bg-gray-900 border-gray-800 py-16">
            <CardContent className="text-center">
              <ImageIcon className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-500">No images generated yet</p>
              <p className="text-gray-600 text-sm mt-1">
                Use the form above to generate your first product image
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {gallery.map((image, index) => (
              <GalleryCard
                key={image.id}
                image={image}
                placeholderGradient={PLACEHOLDER_GRADIENTS[index % PLACEHOLDER_GRADIENTS.length]}
                providers={providers}
              />
            ))}
          </div>
        )}
      </div>
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

function ProviderCard({ provider }: { provider: ImageProvider }) {
  const isConnected = provider.status === 'connected';

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <div className={`h-1 bg-gradient-to-r ${provider.gradient}`} />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`h-9 w-9 rounded-lg bg-gradient-to-br ${provider.gradient} flex items-center justify-center`}
            >
              <Cpu className="h-4 w-4 text-white" />
            </div>
            <CardTitle className="text-base text-white">{provider.name}</CardTitle>
          </div>
          <Badge
            variant="outline"
            className={
              isConnected
                ? 'border-green-500 text-green-400'
                : 'border-red-500 text-red-400'
            }
          >
            {isConnected ? (
              <>
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse mr-2" />
                Connected
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Offline
              </>
            )}
          </Badge>
        </div>
        <CardDescription className="text-gray-500 text-xs mt-1">
          {provider.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Model</span>
            <span className="text-gray-300 text-xs font-mono truncate max-w-[160px]">
              {provider.model}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Avg Latency</span>
            <span className="text-white">{(provider.avgLatencyMs / 1000).toFixed(1)}s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Today</span>
            <span className={provider.accentColor}>{provider.generationsToday} images</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GalleryCard({
  image,
  placeholderGradient,
  providers,
}: {
  image: GeneratedImage;
  placeholderGradient: string;
  providers: ImageProvider[];
}) {
  const statusConfig: Record<
    GenerationStatus,
    { icon: React.ComponentType<{ className?: string }>; iconClass: string; bg: string; label: string }
  > = {
    completed: { icon: CheckCircle2, iconClass: 'text-green-400', bg: 'bg-green-500/10', label: 'Completed' },
    processing: { icon: Loader2, iconClass: 'text-blue-400 animate-spin', bg: 'bg-blue-500/10', label: 'Processing' },
    queued: { icon: Clock, iconClass: 'text-gray-400', bg: 'bg-gray-500/10', label: 'Queued' },
    failed: { icon: AlertCircle, iconClass: 'text-red-400', bg: 'bg-red-500/10', label: 'Failed' },
  };

  const { icon: StatusIcon, iconClass, bg, label } = statusConfig[image.status];
  const provider = providers.find((p) => p.id === image.provider);

  const styleLabels: Record<StyleOption, string> = {
    'product-photo': 'Product Photo',
    lifestyle: 'Lifestyle',
    editorial: 'Editorial',
    'flat-lay': 'Flat Lay',
  };

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      {/* Image Thumbnail Area */}
      <div
        className={`relative h-48 bg-gradient-to-br ${placeholderGradient} flex items-center justify-center`}
      >
        {image.status === 'completed' ? (
          <>
            <div className="absolute inset-0 flex items-center justify-center">
              <ImageIcon className="h-12 w-12 text-white/20" />
            </div>
            {/* Overlay controls on hover */}
            <div className="absolute inset-0 bg-black/0 hover:bg-black/40 transition-colors group flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
              <Button
                size="sm"
                variant="secondary"
                className="opacity-0 group-hover:opacity-100 bg-white/10 text-white hover:bg-white/20 backdrop-blur-sm transition-opacity"
                onClick={() => {}}
              >
                <Download className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="secondary"
                className="opacity-0 group-hover:opacity-100 bg-white/10 text-white hover:bg-white/20 backdrop-blur-sm transition-opacity"
                onClick={() => {}}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </>
        ) : image.status === 'processing' ? (
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 text-white/60 animate-spin" />
            <span className="text-xs text-white/60">Generating...</span>
          </div>
        ) : image.status === 'queued' ? (
          <div className="flex flex-col items-center gap-2">
            <Clock className="h-8 w-8 text-white/40" />
            <span className="text-xs text-white/40">In Queue</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <XCircle className="h-8 w-8 text-red-400/60" />
            <span className="text-xs text-red-400/60">Failed</span>
          </div>
        )}

        {/* Aspect ratio badge */}
        <div className="absolute top-2 left-2">
          <Badge variant="secondary" className="bg-black/50 text-white text-xs backdrop-blur-sm">
            {image.aspectRatio}
          </Badge>
        </div>

        {/* Status badge */}
        <div className="absolute top-2 right-2">
          <div className={`h-8 w-8 rounded-lg ${bg} flex items-center justify-center`}>
            <StatusIcon className={`h-4 w-4 ${iconClass}`} />
          </div>
        </div>
      </div>

      <CardContent className="p-4">
        {/* Prompt */}
        <p className="text-xs text-gray-300 leading-relaxed line-clamp-2 mb-3">
          {image.prompt}
        </p>

        {/* Meta */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
            {styleLabels[image.style]}
          </Badge>
          {provider && (
            <span className={`text-xs font-medium ${provider.accentColor}`}>
              {provider.name}
            </span>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-600 mt-2">
          <span>{new Date(image.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          {image.durationMs !== null && (
            <span>{(image.durationMs / 1000).toFixed(1)}s</span>
          )}
        </div>

        {/* Error */}
        {image.error && (
          <p className="text-xs text-red-400 mt-2 truncate">{image.error}</p>
        )}

        {/* Actions for completed */}
        {image.status === 'completed' && (
          <div className="flex gap-2 mt-3">
            <Button
              size="sm"
              variant="ghost"
              className="flex-1 text-[#B76E79] hover:text-rose-300 hover:bg-[#B76E79]/10 text-xs h-8"
            >
              <Download className="h-3 w-3 mr-1" />
              Download
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="flex-1 text-gray-400 hover:text-white hover:bg-gray-700 text-xs h-8"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Regenerate
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function ImageryPipelineSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-44 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-64 bg-gray-800" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-72 bg-gray-800" />
        ))}
      </div>
    </div>
  );
}
