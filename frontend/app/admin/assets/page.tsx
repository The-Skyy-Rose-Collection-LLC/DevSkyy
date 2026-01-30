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
} from 'lucide-react';
import {
  useAssets,
  useBatchJob,
  useDebounce,
  type Collection,
  type AssetType,
} from '@/hooks';
import { type Asset } from '@/lib/api';

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

  // Debounce search query
  const debouncedSearch = useDebounce(searchQuery, 300);

  // Update filter when debounced value changes
  useEffect(() => {
    setSearch(debouncedSearch);
  }, [debouncedSearch, setSearch]);

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

      {/* Collection Stats */}
      <div className="grid gap-4 md:grid-cols-5">
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
      </div>

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
