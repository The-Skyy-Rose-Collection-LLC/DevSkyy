'use client';

import { useCallback, useState, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  FolderOpen,
  Upload,
  Search,
  Grid3X3,
  List,
  CheckCircle2,
  XCircle,
  Image as ImageIcon,
  Box,
  Film,
  Layers,
  Trash2,
  Edit3,
  Zap,
  ChevronRight,
  Filter,
  Eye,
  Tag,
  Download,
  X,
  Loader2,
} from 'lucide-react';
import {
  useAssets,
  useBatchJob,
  type Collection,
  type AssetType,
  type ViewMode,
} from '@/hooks/useAssets';
import { type Asset } from '@/lib/api';
import { ThreeViewer, ModelViewerFallback } from '@/components/three-viewer';

const COLLECTIONS: { id: Collection; label: string; color: string }[] = [
  { id: 'black_rose', label: 'Black Rose', color: 'bg-gray-800' },
  { id: 'signature', label: 'Signature', color: 'bg-amber-800' },
  { id: 'love_hurts', label: 'Love Hurts', color: 'bg-red-800' },
  { id: 'showroom', label: 'Showroom', color: 'bg-blue-800' },
  { id: 'runway', label: 'Runway', color: 'bg-purple-800' },
];

const ASSET_TYPES: { id: AssetType; label: string; icon: React.ElementType }[] = [
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
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<Collection>('black_rose');
  const [batchJobId, setBatchJobId] = useState<string | null>(null);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { job: batchJob } = useBatchJob(batchJobId);

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploadingFiles(acceptedFiles);

    for (const file of acceptedFiles) {
      await uploadAsset(file, selectedCollection);
    }

    setUploadingFiles([]);
    refresh();
  }, [selectedCollection, uploadAsset, refresh]);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
      'model/gltf-binary': ['.glb'],
      'model/gltf+json': ['.gltf'],
      'video/*': ['.mp4', '.webm'],
    },
    noClick: true,
    noKeyboard: true,
  });

  // Start batch 3D generation
  const handleStartBatch = async (quality: 'draft' | 'standard' | 'high') => {
    const job = await startBatchGeneration('tripo', quality);
    if (job) {
      setBatchJobId(job.id);
      setShowBatchModal(false);
    }
  };

  // Handle search with debounce
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Simple debounce
    const timeoutId = setTimeout(() => {
      setSearch(value);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [setSearch]);

  if (loading && assets.length === 0) {
    return <AssetsSkeleton />;
  }

  return (
    <div {...getRootProps()} className="space-y-6 relative min-h-screen">
      <input {...getInputProps()} />

      {/* Drag overlay */}
      {isDragActive && (
        <div className="fixed inset-0 z-50 bg-gray-900/90 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="h-24 w-24 rounded-full bg-rose-500/20 flex items-center justify-center">
              <Upload className="h-12 w-12 text-rose-400" />
            </div>
            <h3 className="text-2xl font-bold text-white">Drop files to upload</h3>
            <p className="text-gray-400">
              Images, 3D models, and videos are supported
            </p>
          </div>
        </div>
      )}

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
            <Button
              onClick={open}
              className="bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700"
            >
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Button>
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
              className={`cursor-pointer transition-all ${
                isActive
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
            onChange={handleSearchChange}
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
          <Button onClick={open}>
            <Upload className="mr-2 h-4 w-4" />
            Upload Assets
          </Button>
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

// Asset Card Component
function AssetCard({
  asset,
  isSelected,
  onToggle,
  onPreview,
  onEdit,
}: {
  asset: Asset;
  isSelected: boolean;
  onToggle: () => void;
  onPreview: () => void;
  onEdit: () => void;
}) {
  const TypeIcon = {
    image: ImageIcon,
    '3d_model': Box,
    video: Film,
    texture: Layers,
  }[asset.type];

  return (
    <Card
      className={`group relative overflow-hidden cursor-pointer transition-all ${
        isSelected
          ? 'ring-2 ring-rose-500 bg-gray-800'
          : 'bg-gray-900 hover:bg-gray-800'
      } border-gray-700`}
    >
      {/* Selection checkbox */}
      <div className="absolute top-2 left-2 z-10">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className={`h-6 w-6 rounded-full flex items-center justify-center transition-all ${
            isSelected
              ? 'bg-rose-500 text-white'
              : 'bg-gray-800/80 text-gray-400 hover:bg-gray-700'
          }`}
        >
          {isSelected && <CheckCircle2 className="h-4 w-4" />}
        </button>
      </div>

      {/* Thumbnail */}
      <div
        className="aspect-square bg-gray-800 flex items-center justify-center overflow-hidden"
        onClick={onPreview}
      >
        {asset.thumbnail_url ? (
          <img
            src={asset.thumbnail_url}
            alt={asset.filename}
            className="w-full h-full object-cover"
          />
        ) : (
          <TypeIcon className="h-12 w-12 text-gray-600" />
        )}
      </div>

      {/* Info */}
      <CardContent className="p-3">
        <p className="text-sm font-medium text-white truncate">
          {asset.metadata?.product_name || asset.filename}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <Badge
            variant="secondary"
            className="bg-gray-800 text-gray-400 text-xs capitalize"
          >
            {asset.collection.replace('_', ' ')}
          </Badge>
          {asset.metadata?.sku && (
            <span className="text-xs text-gray-500">{asset.metadata.sku}</span>
          )}
        </div>
      </CardContent>

      {/* Hover actions */}
      <div className="absolute inset-0 bg-gray-900/80 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
        <Button size="icon" variant="ghost" className="h-10 w-10 text-white" onClick={onPreview}>
          <Eye className="h-5 w-5" />
        </Button>
        <Button size="icon" variant="ghost" className="h-10 w-10 text-white" onClick={onEdit}>
          <Edit3 className="h-5 w-5" />
        </Button>
      </div>
    </Card>
  );
}

// Asset Row Component (for list view)
function AssetRow({
  asset,
  isSelected,
  onToggle,
  onPreview,
  onEdit,
}: {
  asset: Asset;
  isSelected: boolean;
  onToggle: () => void;
  onPreview: () => void;
  onEdit: () => void;
}) {
  return (
    <tr className={`${isSelected ? 'bg-gray-800/50' : ''} hover:bg-gray-800/30`}>
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggle}
          className="rounded"
        />
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded bg-gray-800 overflow-hidden flex-shrink-0">
            {asset.thumbnail_url ? (
              <img
                src={asset.thumbnail_url}
                alt=""
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <ImageIcon className="h-5 w-5 text-gray-600" />
              </div>
            )}
          </div>
          <div>
            <p className="text-white text-sm font-medium">
              {asset.metadata?.product_name || asset.filename}
            </p>
            <p className="text-gray-500 text-xs">{asset.filename}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <Badge variant="secondary" className="bg-gray-800 text-gray-400 capitalize">
          {asset.collection.replace('_', ' ')}
        </Badge>
      </td>
      <td className="px-4 py-3 text-gray-400 text-sm capitalize">
        {asset.type.replace('_', ' ')}
      </td>
      <td className="px-4 py-3 text-gray-400 text-sm">
        {asset.metadata?.sku || '-'}
      </td>
      <td className="px-4 py-3 text-gray-500 text-sm">
        {new Date(asset.created_at).toLocaleDateString()}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <Button size="icon" variant="ghost" className="h-8 w-8 text-gray-400" onClick={onPreview}>
            <Eye className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" className="h-8 w-8 text-gray-400" onClick={onEdit}>
            <Edit3 className="h-4 w-4" />
          </Button>
        </div>
      </td>
    </tr>
  );
}

// Preview Modal
function AssetPreviewModal({
  asset,
  onClose,
}: {
  asset: Asset;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-gray-900/95 flex items-center justify-center p-4">
      <div className="relative w-full max-w-4xl bg-gray-900 rounded-2xl overflow-hidden border border-gray-700">
        <Button
          size="icon"
          variant="ghost"
          className="absolute top-4 right-4 z-10 text-white"
          onClick={onClose}
        >
          <X className="h-5 w-5" />
        </Button>

        <div className="aspect-video bg-gray-800">
          {asset.type === '3d_model' ? (
            <ModelViewerFallback
              modelUrl={asset.path}
              collection={asset.collection}
              height="100%"
              arEnabled
            />
          ) : (
            <img
              src={asset.thumbnail_url || asset.path}
              alt={asset.filename}
              className="w-full h-full object-contain"
            />
          )}
        </div>

        <div className="p-6">
          <h3 className="text-xl font-bold text-white mb-2">
            {asset.metadata?.product_name || asset.filename}
          </h3>
          <div className="flex flex-wrap gap-2 mb-4">
            <Badge variant="secondary" className="bg-gray-800 capitalize">
              {asset.collection.replace('_', ' ')}
            </Badge>
            <Badge variant="secondary" className="bg-gray-800 capitalize">
              {asset.type.replace('_', ' ')}
            </Badge>
            {asset.metadata?.sku && (
              <Badge variant="outline" className="border-gray-700">
                SKU: {asset.metadata.sku}
              </Badge>
            )}
          </div>
          {asset.metadata?.tags && asset.metadata.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {asset.metadata.tags.map((tag) => (
                <Badge key={tag} variant="outline" className="border-gray-700 text-gray-400">
                  <Tag className="h-3 w-3 mr-1" />
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Edit Modal
function AssetEditModal({
  asset,
  onClose,
  onSave,
}: {
  asset: Asset;
  onClose: () => void;
  onSave: (data: { sku?: string; product_name?: string; tags?: string[] }) => Promise<void>;
}) {
  const [sku, setSku] = useState(asset.metadata?.sku || '');
  const [productName, setProductName] = useState(asset.metadata?.product_name || '');
  const [tags, setTags] = useState((asset.metadata?.tags || []).join(', '));
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave({
      sku: sku || undefined,
      product_name: productName || undefined,
      tags: tags ? tags.split(',').map((t) => t.trim()).filter(Boolean) : undefined,
    });
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 z-50 bg-gray-900/95 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900 border-gray-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white">Edit Asset</CardTitle>
            <Button size="icon" variant="ghost" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label className="text-gray-300">Product Name</Label>
            <Input
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="Black Rose Tee"
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-gray-300">SKU</Label>
            <Input
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              placeholder="BR-TEE-001"
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-gray-300">Tags (comma-separated)</Label>
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="summer, bestseller, limited"
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
          <div className="flex gap-3 pt-4">
            <Button variant="outline" className="flex-1 border-gray-700" onClick={onClose}>
              Cancel
            </Button>
            <Button
              className="flex-1 bg-rose-500 hover:bg-rose-600"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Batch Generation Modal
function BatchGenerationModal({
  selectedCount,
  onClose,
  onStart,
}: {
  selectedCount: number;
  onClose: () => void;
  onStart: (quality: 'draft' | 'standard' | 'high') => void;
}) {
  const [quality, setQuality] = useState<'draft' | 'standard' | 'high'>('standard');

  return (
    <div className="fixed inset-0 z-50 bg-gray-900/95 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900 border-gray-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="h-5 w-5 text-rose-400" />
              Generate 3D Models
            </CardTitle>
            <Button size="icon" variant="ghost" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-400">
            Generate 3D models for <span className="text-white font-medium">{selectedCount}</span> selected assets
            using Tripo3D with 98%+ fidelity target.
          </p>

          <div className="space-y-2">
            <Label className="text-gray-300">Quality Level</Label>
            <div className="grid grid-cols-3 gap-2">
              {(['draft', 'standard', 'high'] as const).map((q) => (
                <Button
                  key={q}
                  variant={quality === q ? 'default' : 'outline'}
                  className={quality === q
                    ? 'bg-rose-500 hover:bg-rose-600'
                    : 'border-gray-700 text-gray-400'
                  }
                  onClick={() => setQuality(q)}
                >
                  {q.charAt(0).toUpperCase() + q.slice(1)}
                </Button>
              ))}
            </div>
            <p className="text-xs text-gray-500">
              {quality === 'draft' && 'Fast preview, ~10s per model, lower detail'}
              {quality === 'standard' && 'Balanced quality, ~30s per model, good for most uses'}
              {quality === 'high' && 'Maximum fidelity, ~60s per model, production-ready'}
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button variant="outline" className="flex-1 border-gray-700" onClick={onClose}>
              Cancel
            </Button>
            <Button
              className="flex-1 bg-gradient-to-r from-rose-500 to-purple-600"
              onClick={() => onStart(quality)}
            >
              Start Generation
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Skeleton loader
function AssetsSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-14 bg-gray-800" />
      <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
        {[...Array(12)].map((_, i) => (
          <Skeleton key={i} className="aspect-square bg-gray-800" />
        ))}
      </div>
    </div>
  );
}
