'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Sparkles,
  User,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Download,
  Eye,
  RefreshCw,
  Palette,
  Shirt,
  Crown,
  Baby,
  Heart,
  Flower2,
  Star,
  Image as ImageIcon,
  Layers,
  Zap,
  UserCircle2,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type MascotPose = 'standing' | 'walking' | 'presenting' | 'waving' | 'sitting' | 'confident';
type MascotCollection = 'black-rose' | 'love-hurts' | 'signature' | 'kids-capsule' | 'none';
type GenerationStatus = 'queued' | 'processing' | 'completed' | 'failed';

interface MascotJob {
  id: string;
  pose: MascotPose;
  collection: MascotCollection;
  product: string;
  prompt: string;
  status: GenerationStatus;
  imageUrl: string | null;
  createdAt: string;
  completedAt: string | null;
  error: string | null;
}

interface MascotStats {
  totalGenerated: number;
  processing: number;
  queued: number;
  failed: number;
  collectionsWithMascot: number;
  posesGenerated: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POSE_OPTIONS: { value: MascotPose; label: string; icon: string }[] = [
  { value: 'standing', label: 'Standing', icon: '🧍' },
  { value: 'walking', label: 'Walking', icon: '🚶' },
  { value: 'presenting', label: 'Presenting', icon: '💁' },
  { value: 'waving', label: 'Waving', icon: '👋' },
  { value: 'sitting', label: 'Sitting', icon: '🪑' },
  { value: 'confident', label: 'Arms Crossed', icon: '💪' },
];

const COLLECTION_OPTIONS: { value: MascotCollection; label: string; gradient: string; icon: typeof Crown }[] = [
  { value: 'none', label: 'Casual (No Collection)', gradient: 'from-gray-500 to-gray-600', icon: Star },
  { value: 'black-rose', label: 'Black Rose', gradient: 'from-rose-900 to-red-900', icon: Flower2 },
  { value: 'love-hurts', label: 'Love Hurts', gradient: 'from-red-600 to-rose-800', icon: Heart },
  { value: 'signature', label: 'Signature', gradient: 'from-[#B76E79] to-amber-600', icon: Crown },
  { value: 'kids-capsule', label: 'Kids Capsule', gradient: 'from-pink-400 to-purple-500', icon: Baby },
];

const PRODUCT_CATALOG: Record<string, string[]> = {
  'black-rose': [
    'Thorn Crewneck', 'Midnight Hoodie', 'Shadow Joggers', 'Iron Rose Jacket',
    'Dark Petal Tee', 'Obsidian Cap',
  ],
  'love-hurts': [
    'Bleeding Heart Tee', 'Crimson Hoodie', 'Heartbreak Joggers',
    'Velvet Thorns Jacket', 'Rose Wound Cap',
  ],
  'signature': [
    'Rose Gold Crewneck', 'Golden Hour Hoodie', 'Sunset Joggers',
    'Prestige Bomber', 'Crown Cap',
  ],
  'kids-capsule': [
    'Mini Rose Tee', 'Little Luxe Hoodie', 'Tiny Thorns Joggers',
    'Petal Play Dress', 'Junior Crown Cap',
  ],
};

const PLACEHOLDER_GRADIENTS = [
  'from-rose-900/60 to-purple-900/60',
  'from-amber-900/60 to-rose-900/60',
  'from-red-900/60 to-pink-900/60',
  'from-violet-900/60 to-fuchsia-900/60',
  'from-pink-900/60 to-rose-800/60',
  'from-orange-900/60 to-red-900/60',
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function MascotPage() {
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<MascotJob[]>([]);
  const [stats, setStats] = useState<MascotStats | null>(null);
  const [generating, setGenerating] = useState(false);

  // Form state
  const [selectedPose, setSelectedPose] = useState<MascotPose>('standing');
  const [selectedCollection, setSelectedCollection] = useState<MascotCollection>('none');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [customPrompt, setCustomPrompt] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/mascot');
      const data = await res.json();
      if (data.success) {
        setJobs(data.data.jobs);
        setStats(data.data.stats);
      }
    } catch {
      // Graceful fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  async function handleGenerate() {
    if (generating) return;

    setGenerating(true);
    try {
      const res = await fetch('/api/mascot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pose: selectedPose,
          collection: selectedCollection,
          product: selectedProduct,
          customPrompt: customPrompt || undefined,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setJobs((prev) => [data.data.job, ...prev]);
        setCustomPrompt('');
        setSelectedProduct('');
      }
    } catch {
      // Error handled by API
    } finally {
      setGenerating(false);
    }
  }

  const availableProducts = selectedCollection !== 'none' ? (PRODUCT_CATALOG[selectedCollection] || []) : [];

  if (loading) {
    return <MascotSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#B76E79]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-pink-500/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[#B76E79] to-pink-600 flex items-center justify-center">
                <UserCircle2 className="h-6 w-6 text-white" />
              </div>
              Brand Mascot
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Generate and manage the SkyyRose brand avatar across all touchpoints
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#B76E79] text-[#B76E79]">
              <div className="h-2 w-2 rounded-full mr-2 bg-[#B76E79] animate-pulse" />
              {stats?.collectionsWithMascot || 0}/4 Collections Covered
            </Badge>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <GradientStatCard
          title="Total Generated"
          value={stats?.totalGenerated ?? 0}
          icon={Layers}
          gradient="from-[#B76E79] to-rose-600"
        />
        <GradientStatCard
          title="Poses Created"
          value={`${stats?.posesGenerated ?? 0}/6`}
          icon={User}
          gradient="from-purple-500 to-pink-500"
        />
        <GradientStatCard
          title="Processing"
          value={stats?.processing ?? 0}
          icon={Zap}
          gradient="from-amber-500 to-orange-500"
        />
        <GradientStatCard
          title="Collections"
          value={`${stats?.collectionsWithMascot ?? 0}/4`}
          icon={Shirt}
          gradient="from-emerald-500 to-teal-500"
        />
      </div>

      {/* Reference Image + Generation Form */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Reference Image Card */}
        <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Eye className="h-5 w-5 text-[#B76E79]" />
              Reference Character
            </CardTitle>
            <CardDescription className="text-gray-400">
              All generated mascots must match this character exactly
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative rounded-xl overflow-hidden bg-gradient-to-br from-[#B76E79]/20 to-pink-900/20 border border-[#B76E79]/30">
              <div className="aspect-square flex items-center justify-center p-8">
                <div className="text-center space-y-4">
                  <div className="h-32 w-32 mx-auto rounded-full bg-gradient-to-br from-[#B76E79] to-pink-600 flex items-center justify-center">
                    <UserCircle2 className="h-20 w-20 text-white/80" />
                  </div>
                  <div>
                    <p className="text-white font-semibold text-lg">SkyyRose Mascot</p>
                    <p className="text-gray-400 text-sm">Pixar/Disney-quality 3D animated character</p>
                    <p className="text-gray-500 text-xs mt-1 font-mono">
                      assets/branding/mascot/skyyrose-mascot-reference.png
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <Badge className="bg-rose-500/10 text-rose-300 border-rose-500/30">Curly Afro Hair</Badge>
                    <Badge className="bg-amber-500/10 text-amber-300 border-amber-500/30">Brown Eyes</Badge>
                    <Badge className="bg-orange-500/10 text-orange-300 border-orange-500/30">Warm Brown Skin</Badge>
                    <Badge className="bg-pink-500/10 text-pink-300 border-pink-500/30">Confident Smile</Badge>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Generation Form */}
        <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[#B76E79]" />
              Generate Mascot Variant
            </CardTitle>
            <CardDescription className="text-gray-400">
              Create new mascot poses and outfits for product placements
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Pose Selection */}
            <div className="space-y-2">
              <Label className="text-gray-300">Pose</Label>
              <div className="grid grid-cols-3 gap-2">
                {POSE_OPTIONS.map((pose) => (
                  <button
                    key={pose.value}
                    onClick={() => setSelectedPose(pose.value)}
                    className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                      selectedPose === pose.value
                        ? 'border-[#B76E79] bg-[#B76E79]/10 text-[#B76E79]'
                        : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <span className="text-lg block mb-1">{pose.icon}</span>
                    {pose.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Collection Selection */}
            <div className="space-y-2">
              <Label className="text-gray-300">Collection Outfit</Label>
              <div className="space-y-2">
                {COLLECTION_OPTIONS.map((col) => {
                  const Icon = col.icon;
                  return (
                    <button
                      key={col.value}
                      onClick={() => {
                        setSelectedCollection(col.value);
                        setSelectedProduct('');
                      }}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg border text-sm transition-all ${
                        selectedCollection === col.value
                          ? 'border-[#B76E79] bg-[#B76E79]/10'
                          : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                      }`}
                    >
                      <div className={`h-8 w-8 rounded-lg bg-gradient-to-br ${col.gradient} flex items-center justify-center`}>
                        <Icon className="h-4 w-4 text-white" />
                      </div>
                      <span className={selectedCollection === col.value ? 'text-[#B76E79]' : 'text-gray-300'}>
                        {col.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Product Selector (conditional) */}
            {availableProducts.length > 0 && (
              <div className="space-y-2">
                <Label className="text-gray-300">Product Piece</Label>
                <select
                  value={selectedProduct}
                  onChange={(e) => setSelectedProduct(e.target.value)}
                  className="w-full h-10 rounded-md bg-gray-800 border border-gray-700 text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#B76E79]/50"
                >
                  <option value="">Any piece from collection</option>
                  {availableProducts.map((product) => (
                    <option key={product} value={product}>{product}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Custom Prompt Override */}
            <div className="space-y-2">
              <Label className="text-gray-300">Custom Prompt (optional)</Label>
              <Input
                placeholder="Override with a specific scene description..."
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>

            {/* Generate Button */}
            <Button
              onClick={handleGenerate}
              disabled={generating}
              className="w-full bg-gradient-to-r from-[#B76E79] via-rose-500 to-pink-600 hover:from-rose-600 hover:via-pink-500 hover:to-pink-700 h-12 text-lg font-semibold disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Generating Mascot...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-5 w-5" />
                  Generate Mascot
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Placement Guide */}
      <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Palette className="h-5 w-5 text-[#B76E79]" />
            Mascot Placement Guide
          </CardTitle>
          <CardDescription className="text-gray-400">
            Where the mascot is used across SkyyRose touchpoints
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: 'Kids Capsule Page', status: 'Primary mascot', color: 'text-pink-400', bg: 'bg-pink-500/10' },
              { label: 'Homepage Welcome', status: 'Greeting element', color: 'text-amber-400', bg: 'bg-amber-500/10' },
              { label: 'Pre-Order CTA', status: 'Animated prompt', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
              { label: '404 Error Page', status: 'Fun error state', color: 'text-red-400', bg: 'bg-red-500/10' },
              { label: 'Loading States', status: 'Animations', color: 'text-blue-400', bg: 'bg-blue-500/10' },
              { label: 'Social Media', status: 'Post content', color: 'text-purple-400', bg: 'bg-purple-500/10' },
              { label: 'Email Templates', status: 'Header/footer', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
              { label: 'WordPress Theme', status: 'Integration ready', color: 'text-[#B76E79]', bg: 'bg-[#B76E79]/10' },
            ].map((placement) => (
              <div
                key={placement.label}
                className={`p-4 rounded-lg ${placement.bg} border border-gray-800`}
              >
                <p className={`font-medium text-sm ${placement.color}`}>{placement.label}</p>
                <p className="text-gray-500 text-xs mt-1">{placement.status}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Generated Gallery */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <ImageIcon className="h-5 w-5 text-[#B76E79]" />
            Generated Mascots
          </h2>
          <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
            {jobs.length} variants
          </Badge>
        </div>

        {jobs.length === 0 ? (
          <Card className="bg-gray-900 border-gray-800 py-16">
            <CardContent className="text-center">
              <UserCircle2 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-500">No mascot variants generated yet</p>
              <p className="text-gray-600 text-sm mt-1">
                Use the form above to generate your first mascot variant
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {jobs.map((job, index) => (
              <MascotCard
                key={job.id}
                job={job}
                gradient={PLACEHOLDER_GRADIENTS[index % PLACEHOLDER_GRADIENTS.length]}
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
          <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${gradient} bg-opacity-10 flex items-center justify-center`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function MascotCard({ job, gradient }: { job: MascotJob; gradient: string }) {
  const statusConfig: Record<
    GenerationStatus,
    { icon: React.ComponentType<{ className?: string }>; iconClass: string; bg: string; label: string }
  > = {
    completed: { icon: CheckCircle2, iconClass: 'text-green-400', bg: 'bg-green-500/10', label: 'Completed' },
    processing: { icon: Loader2, iconClass: 'text-blue-400 animate-spin', bg: 'bg-blue-500/10', label: 'Processing' },
    queued: { icon: Clock, iconClass: 'text-gray-400', bg: 'bg-gray-500/10', label: 'Queued' },
    failed: { icon: XCircle, iconClass: 'text-red-400', bg: 'bg-red-500/10', label: 'Failed' },
  };

  const { icon: StatusIcon, iconClass, bg } = statusConfig[job.status];

  const collectionLabel = COLLECTION_OPTIONS.find((c) => c.value === job.collection)?.label || 'Unknown';
  const poseLabel = POSE_OPTIONS.find((p) => p.value === job.pose)?.label || 'Unknown';

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      {/* Thumbnail */}
      <div className={`relative h-48 bg-gradient-to-br ${gradient} flex items-center justify-center`}>
        {job.imageUrl ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <UserCircle2 className="h-16 w-16 text-white/40" />
          </div>
        ) : job.status === 'completed' ? (
          <div className="flex flex-col items-center gap-2">
            <UserCircle2 className="h-12 w-12 text-white/30" />
            <span className="text-xs text-white/30">Generated</span>
          </div>
        ) : job.status === 'processing' ? (
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 text-white/60 animate-spin" />
            <span className="text-xs text-white/60">Generating...</span>
          </div>
        ) : job.status === 'queued' ? (
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

        {/* Status badge */}
        <div className="absolute top-2 right-2">
          <div className={`h-8 w-8 rounded-lg ${bg} flex items-center justify-center`}>
            <StatusIcon className={`h-4 w-4 ${iconClass}`} />
          </div>
        </div>

        {/* Pose badge */}
        <div className="absolute top-2 left-2">
          <Badge variant="secondary" className="bg-black/50 text-white text-xs backdrop-blur-sm">
            {poseLabel}
          </Badge>
        </div>
      </div>

      <CardContent className="p-4">
        {/* Collection + Product */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
            {collectionLabel}
          </Badge>
          {job.product && (
            <span className="text-xs text-[#B76E79] font-medium truncate max-w-[120px]">
              {job.product}
            </span>
          )}
        </div>

        {/* Prompt preview */}
        <p className="text-xs text-gray-500 leading-relaxed line-clamp-2 mb-3">
          {job.prompt}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>{new Date(job.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          {job.completedAt && (
            <span className="text-green-500/70">
              {Math.round(
                (new Date(job.completedAt).getTime() - new Date(job.createdAt).getTime()) / 1000
              )}s
            </span>
          )}
        </div>

        {/* Actions */}
        {job.status === 'completed' && (
          <div className="flex gap-2 mt-3">
            <Button
              size="sm"
              variant="ghost"
              className="flex-1 text-[#B76E79] hover:text-rose-300 hover:bg-[#B76E79]/10 text-xs h-8"
            >
              <Download className="h-3 w-3 mr-1" />
              Save
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="flex-1 text-gray-400 hover:text-white hover:bg-gray-700 text-xs h-8"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Redo
            </Button>
          </div>
        )}

        {job.error && (
          <p className="text-xs text-red-400 mt-2 truncate">{job.error}</p>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function MascotSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-96 bg-gray-800" />
        <Skeleton className="h-96 bg-gray-800" />
      </div>
      <Skeleton className="h-40 bg-gray-800" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-72 bg-gray-800" />
        ))}
      </div>
    </div>
  );
}
