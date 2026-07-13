'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
  FolderOpen,
  Search,
  Grid3X3,
  List,
  CheckCircle2,
  XCircle,
  Trash2,
  Zap,
  ChevronRight,
  ImageIcon,
  Box,
  Film,
  Layers,
  Loader2,
  HardDrive,
  Database,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  GraduationCap,
  AlertTriangle,
  ShieldCheck,
} from 'lucide-react';
import {
  useAssets,
  useBatchJob,
  useDebounce,
  type Collection,
  type AssetType,
} from '@/hooks';
import { api, type Asset } from '@/lib/api';
import type { SkuImageCounts, HfDatasetsResponse, TrainingReadinessResponse, BrandAsset } from '@/lib/api/types';

// Extracted Components
import { AssetCard } from '@/components/admin/assets/AssetCard';
import { AssetRow } from '@/components/admin/assets/AssetRow';
import { AssetPreviewModal } from '@/components/admin/assets/AssetPreviewModal';
import { AssetEditModal } from '@/components/admin/assets/AssetEditModal';
import { BatchGenerationModal } from '@/components/admin/assets/BatchGenerationModal';
import { UploadZone } from '@/components/admin/assets/UploadZone';

const COLLECTIONS: { id: Collection; label: string; color: string }[] = [
  { id: 'black_rose', label: 'Black Rose', color: 'bg-gray-800' },
  { id: 'signature', label: 'Signature', color: 'bg-amber-800' },
  { id: 'love_hurts', label: 'Love Hurts', color: 'bg-red-800' },
  { id: 'showroom', label: 'Showroom', color: 'bg-blue-800' },
  { id: 'runway', label: 'Runway', color: 'bg-purple-800' },
];

const ASSET_TYPES: { id: AssetType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'image', label: 'Images', icon: ImageIcon },
  { id: '3d_model', label: '3D Models', icon: Box },
  { id: 'video', label: 'Videos', icon: Film },
  { id: 'texture', label: 'Textures', icon: Layers },
];

export default function AssetsPage() {
  const {
    assets,
    total,
    loading,
    error,
    hasMore,
    selectedIds,
    viewMode,
    filters,
    collectionStats,
    refresh,
    loadMore,
    toggleAsset,
    selectAll,
    clearSelection,
    setCollection,
    setType,
    setSearch,
    setViewMode,
    uploadAsset,
    updateAsset,
    deleteAsset,
    deleteSelected,
    startBatchGeneration,
  } = useAssets();

  const [previewAsset, setPreviewAsset] = useState<Asset | null>(null);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);
  const [batchJobId, setBatchJobId] = useState<string | null>(null);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  const [perSkuCounts, setPerSkuCounts] = useState<SkuImageCounts | null>(null);
  const [hfDatasets, setHfDatasets] = useState<HfDatasetsResponse | null>(null);
  const [skuBreakdownOpen, setSkuBreakdownOpen] = useState(false);
  const [trainingReadiness, setTrainingReadiness] = useState<TrainingReadinessResponse | null>(null);
  const [trainingReadinessError, setTrainingReadinessError] = useState<string | null>(null);
  const [trainingReadinessLoading, setTrainingReadinessLoading] = useState(true);
  const [pendingBrandAssets, setPendingBrandAssets] = useState<BrandAsset[]>([]);
  const [pendingBrandAssetsError, setPendingBrandAssetsError] = useState<string | null>(null);
  const [pendingBrandAssetsLoading, setPendingBrandAssetsLoading] = useState(true);
  const [brandAssetActionId, setBrandAssetActionId] = useState<string | null>(null);

  // Debounce search query
  const debouncedSearch = useDebounce(searchQuery, 300);

  // Update filter when debounced value changes
  useEffect(() => {
    setSearch(debouncedSearch);
  }, [debouncedSearch, setSearch]);

  // Fetch per-SKU image counts and HF datasets on mount
  useEffect(() => {
    api.assets.perSku().then(setPerSkuCounts).catch(() => null);
    api.assets.datasets().then(setHfDatasets).catch(() => null);
  }, []);

  const loadTrainingReadiness = () => {
    setTrainingReadinessLoading(true);
    setTrainingReadinessError(null);
    api.brandAssets.trainingReadiness()
      .then(setTrainingReadiness)
      .catch((err) => setTrainingReadinessError(err instanceof Error ? err.message : 'Failed to load training readiness'))
      .finally(() => setTrainingReadinessLoading(false));
  };

  useEffect(() => {
    loadTrainingReadiness();
  }, []);

  const loadPendingBrandAssets = () => {
    setPendingBrandAssetsLoading(true);
    setPendingBrandAssetsError(null);
    api.brandAssets.list({ approvalStatus: 'pending', pageSize: 12 })
      .then((res) => setPendingBrandAssets(res.assets))
      .catch((err) => setPendingBrandAssetsError(err instanceof Error ? err.message : 'Failed to load pending assets'))
      .finally(() => setPendingBrandAssetsLoading(false));
  };

  useEffect(() => {
    loadPendingBrandAssets();
  }, []);

  const handleApproveBrandAsset = async (assetId: string) => {
    setBrandAssetActionId(assetId);
    try {
      await api.brandAssets.approve(assetId);
      setPendingBrandAssets((prev) => prev.filter((a) => a.id !== assetId));
      loadTrainingReadiness();
    } catch (err) {
      setPendingBrandAssetsError(err instanceof Error ? err.message : 'Failed to approve asset');
    } finally {
      setBrandAssetActionId(null);
    }
  };

  const handleRejectBrandAsset = async (assetId: string) => {
    setBrandAssetActionId(assetId);
    try {
      await api.brandAssets.reject(assetId);
      setPendingBrandAssets((prev) => prev.filter((a) => a.id !== assetId));
      loadTrainingReadiness();
    } catch (err) {
      setPendingBrandAssetsError(err instanceof Error ? err.message : 'Failed to reject asset');
    } finally {
      setBrandAssetActionId(null);
    }
  };

  const { job: batchJob } = useBatchJob(batchJobId);

  // File upload handler
  const handleUpload = async (files: File[]) => {
    for (const file of files) {
      await uploadAsset(file, filters.collection || 'black_rose');
    }
    refresh();
  };

  // Start batch 3D generation
  const handleStartBatch = async (quality: 'draft' | 'standard' | 'high') => {
    const job = await startBatchGeneration('tripo', quality);
    if (job) {
      setBatchJobId(job.id);
      setShowBatchModal(false);
    }
  };

  if (loading && assets.length === 0) {
    return <AssetsSkeleton />;
  }

  return (
    <div className="space-y-6 relative min-h-screen">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <FolderOpen className="h-6 w-6 text-white" />
              </div>
              Asset Library
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Manage product images and 3D models for SkyyRose collections
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-gray-600 text-gray-300">
              {total} Assets
            </Badge>
            <UploadZone
              collection={filters.collection || 'black_rose'}
              onUpload={handleUpload}
            />
          </div>
        </div>
      </div>

      {/* Collection Stats + Disk Images */}
      <div className="grid gap-4 md:grid-cols-6">
        {COLLECTIONS.map((col) => {
          const count = collectionStats[col.id] || 0;
          const isActive = filters.collection === col.id;
          return (
            <Card
              key={col.id}
              className={`cursor-pointer transition-all ${isActive
                  ? 'bg-gray-800 border-rose-500 ring-1 ring-rose-500'
                  : 'bg-gray-900/80 border-gray-700 hover:border-gray-600'
                }`}
              onClick={() => setCollection(isActive ? undefined : col.id)}
            >
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`h-3 w-3 rounded-full ${col.color}`} />
                    <span className="text-sm font-medium text-white">{col.label}</span>
                  </div>
                  <span className="text-lg font-bold text-white">{count}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {/* Disk images tile */}
        <Card
          className="cursor-pointer transition-all bg-gray-900/80 border-gray-700 hover:border-emerald-600"
          onClick={() => setSkuBreakdownOpen((o) => !o)}
        >
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HardDrive className="h-3 w-3 text-emerald-400" />
                <span className="text-sm font-medium text-white">Disk</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-lg font-bold text-white">
                  {perSkuCounts ? perSkuCounts.total : '—'}
                </span>
                {skuBreakdownOpen
                  ? <ChevronUp className="h-3 w-3 text-gray-400" />
                  : <ChevronDown className="h-3 w-3 text-gray-400" />
                }
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Per-SKU breakdown panel */}
      {skuBreakdownOpen && perSkuCounts && (
        <Card className="bg-gray-900/80 border-gray-700">
          <CardContent className="py-4">
            <p className="text-xs text-gray-500 mb-3">
              Disk images per product slug · scanned {new Date(perSkuCounts.scanned_at).toLocaleTimeString()}
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {Object.entries(perSkuCounts.counts).map(([slug, count]) => (
                <div
                  key={slug}
                  className="flex items-center justify-between bg-gray-800 rounded px-2 py-1"
                >
                  <span className="text-xs text-gray-300 truncate mr-2">{slug}</span>
                  <Badge variant="secondary" className="bg-emerald-900/40 text-emerald-300 shrink-0">
                    {count}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4 bg-gray-900/80 rounded-lg p-4 border border-gray-700">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            ref={searchInputRef}
            placeholder="Search assets..."
            className="pl-10 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Type filters */}
        <div className="flex gap-2">
          {ASSET_TYPES.map((type) => {
            const Icon = type.icon;
            const isActive = filters.type === type.id;
            return (
              <Button
                key={type.id}
                size="sm"
                variant={isActive ? 'default' : 'outline'}
                className={isActive
                  ? 'bg-rose-500 hover:bg-rose-600'
                  : 'border-gray-700 text-gray-400 hover:text-white'
                }
                onClick={() => setType(isActive ? undefined : type.id)}
              >
                <Icon className="mr-1 h-4 w-4" />
                {type.label}
              </Button>
            );
          })}
        </div>

        {/* View mode toggle */}
        <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
          <Button
            size="icon"
            variant="ghost"
            className={`h-8 w-8 ${viewMode === 'grid' ? 'bg-gray-700 text-white' : 'text-gray-400'}`}
            onClick={() => setViewMode('grid')}
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className={`h-8 w-8 ${viewMode === 'list' ? 'bg-gray-700 text-white' : 'text-gray-400'}`}
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>

        {/* Selection actions */}
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 ml-auto">
            <Badge variant="secondary" className="bg-gray-800">
              {selectedIds.size} selected
            </Badge>
            <Button
              size="sm"
              variant="outline"
              className="border-gray-700 text-gray-400"
              onClick={clearSelection}
            >
              Clear
            </Button>
            <Button
              size="sm"
              className="bg-gradient-to-r from-rose-500 to-purple-600"
              onClick={() => setShowBatchModal(true)}
            >
              <Zap className="mr-1 h-4 w-4" />
              Generate 3D
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={deleteSelected}
            >
              <Trash2 className="mr-1 h-4 w-4" />
              Delete
            </Button>
          </div>
        )}
      </div>

      {/* Batch job status */}
      {batchJob && (
        <Card className="bg-gray-900/80 border-gray-700">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Loader2 className="h-5 w-5 animate-spin text-rose-400" />
                <div>
                  <p className="text-white font-medium">Batch 3D Generation</p>
                  <p className="text-gray-400 text-sm">
                    {batchJob.processed_assets} / {batchJob.total_assets} assets processed
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-48 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-rose-500 to-purple-600 transition-all"
                    style={{ width: `${batchJob.progress_percentage}%` }}
                  />
                </div>
                <span className="text-white font-medium">
                  {batchJob.progress_percentage.toFixed(0)}%
                </span>
                {batchJob.status === 'completed' && (
                  <CheckCircle2 className="h-5 w-5 text-green-400" />
                )}
                {batchJob.status === 'failed' && (
                  <XCircle className="h-5 w-5 text-red-400" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Asset grid/list */}
      {viewMode === 'grid' ? (
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
          {assets.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              isSelected={selectedIds.has(asset.id)}
              onToggle={() => toggleAsset(asset.id)}
              onPreview={() => setPreviewAsset(asset)}
              onEdit={() => setEditingAsset(asset)}
            />
          ))}
        </div>
      ) : (
        <div className="bg-gray-900/80 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr>
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.size === assets.length && assets.length > 0}
                    onChange={() => selectedIds.size === assets.length ? clearSelection() : selectAll()}
                    className="rounded"
                  />
                </th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">Asset</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">Collection</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">Type</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">SKU</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">Date</th>
                <th className="w-24 px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {assets.map((asset) => (
                <AssetRow
                  key={asset.id}
                  asset={asset}
                  isSelected={selectedIds.has(asset.id)}
                  onToggle={() => toggleAsset(asset.id)}
                  onPreview={() => setPreviewAsset(asset)}
                  onEdit={() => setEditingAsset(asset)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Load more */}
      {hasMore && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            className="border-gray-700 text-gray-400"
            onClick={loadMore}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <ChevronRight className="mr-2 h-4 w-4" />
            )}
            Load More
          </Button>
        </div>
      )}

      {/* Empty state */}
      {!loading && assets.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="h-20 w-20 rounded-full bg-gray-800 flex items-center justify-center mb-4">
            <FolderOpen className="h-10 w-10 text-gray-600" />
          </div>
          <h3 className="text-xl font-medium text-white mb-2">No assets found</h3>
          <p className="text-gray-400 mb-4">
            {filters.collection || filters.type || filters.search
              ? 'Try adjusting your filters'
              : 'Upload your first product images to get started'}
          </p>
        </div>
      )}

      {/* HuggingFace Datasets */}
      {hfDatasets && (
        <Card className="bg-gray-900/80 border-gray-700">
          <CardContent className="py-5">
            <div className="flex items-center gap-2 mb-4">
              <Database className="h-4 w-4 text-orange-400" />
              <h3 className="text-white font-semibold">HuggingFace Datasets</h3>
              <Badge variant="outline" className="border-gray-600 text-gray-300 ml-auto">
                {hfDatasets.count} dataset{hfDatasets.count !== 1 ? 's' : ''}
              </Badge>
              <span className="text-xs text-gray-500">{hfDatasets.author}</span>
            </div>
            {hfDatasets.datasets.length === 0 ? (
              <p className="text-gray-500 text-sm">No datasets found for author &quot;{hfDatasets.author}&quot;.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-2 px-3 text-gray-400 font-medium">ID</th>
                      <th className="text-right py-2 px-3 text-gray-400 font-medium">Downloads</th>
                      <th className="text-right py-2 px-3 text-gray-400 font-medium">Likes</th>
                      <th className="text-left py-2 px-3 text-gray-400 font-medium">Last Modified</th>
                      <th className="text-left py-2 px-3 text-gray-400 font-medium">Tags</th>
                      <th className="py-2 px-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {hfDatasets.datasets.map((ds) => (
                      <tr key={ds.id} className="hover:bg-gray-800/50 transition-colors">
                        <td className="py-2 px-3 text-white font-mono text-xs">{ds.id}</td>
                        <td className="py-2 px-3 text-right text-gray-300">{ds.downloads.toLocaleString()}</td>
                        <td className="py-2 px-3 text-right text-gray-300">{ds.likes}</td>
                        <td className="py-2 px-3 text-gray-400 text-xs">
                          {ds.last_modified ? new Date(ds.last_modified).toLocaleDateString() : '—'}
                        </td>
                        <td className="py-2 px-3">
                          <div className="flex flex-wrap gap-1">
                            {ds.tags.slice(0, 3).map((tag) => (
                              <Badge key={tag} variant="secondary" className="bg-gray-800 text-gray-400 text-xs px-1 py-0">
                                {tag}
                              </Badge>
                            ))}
                            {ds.tags.length > 3 && (
                              <span className="text-xs text-gray-500">+{ds.tags.length - 3}</span>
                            )}
                          </div>
                        </td>
                        <td className="py-2 px-3">
                          {ds.private ? (
                            <Badge variant="outline" className="border-gray-700 text-gray-500 text-xs">private</Badge>
                          ) : (
                            <a
                              href={`https://huggingface.co/datasets/${ds.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-orange-400 hover:text-orange-300 transition-colors"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Pending Brand Assets */}
      <Card className="bg-gray-900/80 border-gray-700">
        <CardContent className="py-5">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="h-4 w-4 text-rose-400" />
            <h3 className="text-white font-semibold">Pending Brand Assets</h3>
            <Badge variant="outline" className="border-gray-600 text-gray-300 ml-auto">
              {pendingBrandAssets.length} pending
            </Badge>
            <Button
              size="sm"
              variant="outline"
              className="border-gray-700 text-gray-400 hover:text-white"
              onClick={loadPendingBrandAssets}
              disabled={pendingBrandAssetsLoading}
            >
              {pendingBrandAssetsLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Refresh'
              )}
            </Button>
          </div>

          {pendingBrandAssetsError && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-3">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {pendingBrandAssetsError}
            </div>
          )}

          {pendingBrandAssetsLoading && pendingBrandAssets.length === 0 && !pendingBrandAssetsError && (
            <Skeleton className="h-24 bg-gray-800" />
          )}

          {!pendingBrandAssetsLoading && pendingBrandAssets.length === 0 && !pendingBrandAssetsError && (
            <p className="text-gray-500 text-sm">No brand assets awaiting review.</p>
          )}

          {pendingBrandAssets.length > 0 && (
            <div className="space-y-2">
              {pendingBrandAssets.map((asset) => (
                <div
                  key={asset.id}
                  className="flex items-center gap-3 bg-gray-800/50 rounded-lg p-3"
                >
                  <img
                    src={asset.url}
                    alt={asset.metadata.campaign || asset.category}
                    className="h-12 w-12 rounded object-cover shrink-0 bg-gray-800"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">
                      {asset.metadata.campaign || asset.category.replace('_', ' ')}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {asset.category.replace('_', ' ')} &middot; {new Date(asset.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      aria-label="Approve asset"
                      className="border-emerald-700 text-emerald-400 hover:text-emerald-300"
                      onClick={() => handleApproveBrandAsset(asset.id)}
                      disabled={brandAssetActionId === asset.id}
                    >
                      {brandAssetActionId === asset.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      aria-label="Reject asset"
                      className="border-red-700 text-red-400 hover:text-red-300"
                      onClick={() => handleRejectBrandAsset(asset.id)}
                      disabled={brandAssetActionId === asset.id}
                    >
                      {brandAssetActionId === asset.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <XCircle className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Training Readiness */}
      <Card className="bg-gray-900/80 border-gray-700">
        <CardContent className="py-5">
          <div className="flex items-center gap-2 mb-4">
            <GraduationCap className="h-4 w-4 text-rose-400" />
            <h3 className="text-white font-semibold">Training Readiness</h3>
            {trainingReadiness && (
              <Badge
                variant="outline"
                className={
                  trainingReadiness.status === 'ready'
                    ? 'border-emerald-600 text-emerald-400 ml-auto'
                    : trainingReadiness.status === 'needs_review'
                      ? 'border-amber-600 text-amber-400 ml-auto'
                      : 'border-gray-600 text-gray-400 ml-auto'
                }
              >
                {trainingReadiness.status.replace('_', ' ')}
              </Badge>
            )}
            <Button
              size="sm"
              variant="outline"
              className="border-gray-700 text-gray-400 hover:text-white"
              onClick={loadTrainingReadiness}
              disabled={trainingReadinessLoading}
            >
              {trainingReadinessLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Refresh'
              )}
            </Button>
          </div>

          {trainingReadinessError && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {trainingReadinessError}
            </div>
          )}

          {trainingReadinessLoading && !trainingReadiness && !trainingReadinessError && (
            <Skeleton className="h-24 bg-gray-800" />
          )}

          {!trainingReadinessLoading && !trainingReadinessError && trainingReadiness && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-gray-800/50 rounded-lg text-center">
                  <p className="text-xs text-gray-400">Approved</p>
                  <p className="font-semibold text-lg text-white">{trainingReadiness.approved_assets}</p>
                </div>
                <div className="p-3 bg-gray-800/50 rounded-lg text-center">
                  <p className="text-xs text-gray-400">Total Ingested</p>
                  <p className="font-semibold text-lg text-white">{trainingReadiness.total_assets}</p>
                </div>
                <div className="p-3 bg-gray-800/50 rounded-lg text-center">
                  <p className="text-xs text-gray-400">Minimum Required</p>
                  <p className="font-semibold text-lg text-white">{trainingReadiness.minimum_required}</p>
                </div>
              </div>

              <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-rose-500 to-purple-600 transition-all"
                  style={{
                    width: `${Math.min(100, (trainingReadiness.approved_assets / Math.max(1, trainingReadiness.minimum_required)) * 100)}%`,
                  }}
                />
              </div>

              {trainingReadiness.estimated_training_time && (
                <p className="text-xs text-gray-500">
                  Estimated training time: {trainingReadiness.estimated_training_time}
                </p>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
                {trainingReadiness.categories
                  .filter((cat) => cat.total > 0)
                  .map((cat) => (
                    <div key={cat.category} className="bg-gray-800 rounded px-2 py-1.5">
                      <p className="text-xs text-gray-300 truncate">{cat.category.replace('_', ' ')}</p>
                      <p className="text-xs text-gray-500">
                        <span className="text-emerald-400">{cat.approved}</span> / {cat.total}
                      </p>
                    </div>
                  ))}
              </div>

              {trainingReadiness.recommendations.length > 0 && (
                <ul className="space-y-1">
                  {trainingReadiness.recommendations.map((rec, i) => (
                    <li key={i} className="text-xs text-gray-400 flex items-start gap-2">
                      <span className="text-gray-600 mt-0.5">&bull;</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preview Modal */}
      {previewAsset && (
        <AssetPreviewModal
          asset={previewAsset}
          onClose={() => setPreviewAsset(null)}
        />
      )}

      {/* Edit Modal */}
      {editingAsset && (
        <AssetEditModal
          asset={editingAsset}
          onClose={() => setEditingAsset(null)}
          onSave={async (data) => {
            await updateAsset(editingAsset.id, { metadata: data });
            setEditingAsset(null);
          }}
        />
      )}

      {/* Batch Generation Modal */}
      {showBatchModal && (
        <BatchGenerationModal
          selectedCount={selectedIds.size}
          onClose={() => setShowBatchModal(false)}
          onStart={handleStartBatch}
        />
      )}
    </div>
  );
}

function AssetsSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-48 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-20 bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-6">
        {[...Array(12)].map((_, i) => (
          <Skeleton key={i} className="h-64 bg-gray-800" />
        ))}
      </div>
    </div>
  );
}
