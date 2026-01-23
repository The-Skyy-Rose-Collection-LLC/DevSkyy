'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  api,
  type Asset,
  type AssetFilters,
  type AssetUpdateRequest,
  type BatchJob,
  ApiError,
} from '@/lib/api';

export type Collection = 'black_rose' | 'signature' | 'love_hurts' | 'showroom' | 'runway';
export type AssetType = 'image' | '3d_model' | 'video' | 'texture';
export type ViewMode = 'grid' | 'list';

interface UseAssetsState {
  assets: Asset[];
  total: number;
  loading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;
  selectedIds: Set<string>;
  viewMode: ViewMode;
  filters: AssetFilters;
  collectionStats: Record<string, number>;
}

interface UseAssetsReturn extends UseAssetsState {
  // Fetching
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;

  // Selection
  selectAsset: (id: string) => void;
  deselectAsset: (id: string) => void;
  toggleAsset: (id: string) => void;
  selectAll: () => void;
  clearSelection: () => void;

  // Filtering
  setCollection: (collection: Collection | undefined) => void;
  setType: (type: AssetType | undefined) => void;
  setSearch: (search: string) => void;
  setViewMode: (mode: ViewMode) => void;

  // CRUD
  uploadAsset: (file: File, collection: Collection) => Promise<Asset | null>;
  updateAsset: (id: string, data: AssetUpdateRequest) => Promise<Asset | null>;
  deleteAsset: (id: string) => Promise<boolean>;
  deleteSelected: () => Promise<number>;

  // Batch operations
  startBatchGeneration: (
    provider?: string,
    quality?: 'draft' | 'standard' | 'high'
  ) => Promise<BatchJob | null>;
}

const ITEMS_PER_PAGE = 24;

export function useAssets(): UseAssetsReturn {
  const [state, setState] = useState<UseAssetsState>({
    assets: [],
    total: 0,
    loading: true,
    error: null,
    page: 1,
    hasMore: false,
    selectedIds: new Set(),
    viewMode: 'grid',
    filters: { limit: ITEMS_PER_PAGE },
    collectionStats: {},
  });

  // Fetch assets
  const fetchAssets = useCallback(async (page: number, append = false) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await api.assets.getList({
        ...state.filters,
        page,
        limit: ITEMS_PER_PAGE,
      });

      setState((prev) => ({
        ...prev,
        assets: append ? [...prev.assets, ...response.assets] : response.assets,
        total: response.total,
        page,
        hasMore: response.has_more,
        loading: false,
      }));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to fetch assets';
      setState((prev) => ({ ...prev, error: message, loading: false }));
    }
  }, [state.filters]);

  // Fetch collection stats
  const fetchStats = useCallback(async () => {
    try {
      const stats = await api.assets.getCollectionStats();
      setState((prev) => ({ ...prev, collectionStats: stats }));
    } catch {
      // Stats are optional, don't block on failure
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchAssets(1);
    fetchStats();
  }, [fetchAssets, fetchStats]);

  // Reload when filters change
  useEffect(() => {
    fetchAssets(1);
  }, [state.filters, fetchAssets]);

  const refresh = useCallback(async () => {
    await Promise.all([fetchAssets(1), fetchStats()]);
  }, [fetchAssets, fetchStats]);

  const loadMore = useCallback(async () => {
    if (state.hasMore && !state.loading) {
      await fetchAssets(state.page + 1, true);
    }
  }, [state.hasMore, state.loading, state.page, fetchAssets]);

  // Selection methods
  const selectAsset = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      selectedIds: new Set([...prev.selectedIds, id]),
    }));
  }, []);

  const deselectAsset = useCallback((id: string) => {
    setState((prev) => {
      const next = new Set(prev.selectedIds);
      next.delete(id);
      return { ...prev, selectedIds: next };
    });
  }, []);

  const toggleAsset = useCallback((id: string) => {
    setState((prev) => {
      const next = new Set(prev.selectedIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { ...prev, selectedIds: next };
    });
  }, []);

  const selectAll = useCallback(() => {
    setState((prev) => ({
      ...prev,
      selectedIds: new Set(prev.assets.map((a) => a.id)),
    }));
  }, []);

  const clearSelection = useCallback(() => {
    setState((prev) => ({ ...prev, selectedIds: new Set() }));
  }, []);

  // Filter methods
  const setCollection = useCallback((collection: Collection | undefined) => {
    setState((prev) => ({
      ...prev,
      filters: { ...prev.filters, collection },
      selectedIds: new Set(),
    }));
  }, []);

  const setType = useCallback((type: AssetType | undefined) => {
    setState((prev) => ({
      ...prev,
      filters: { ...prev.filters, type },
      selectedIds: new Set(),
    }));
  }, []);

  const setSearch = useCallback((search: string) => {
    setState((prev) => ({
      ...prev,
      filters: { ...prev.filters, search: search || undefined },
    }));
  }, []);

  const setViewMode = useCallback((viewMode: ViewMode) => {
    setState((prev) => ({ ...prev, viewMode }));
  }, []);

  // CRUD methods
  const uploadAsset = useCallback(async (
    file: File,
    collection: Collection
  ): Promise<Asset | null> => {
    try {
      const asset = await api.assets.upload(file, collection);
      setState((prev) => ({
        ...prev,
        assets: [asset, ...prev.assets],
        total: prev.total + 1,
      }));
      return asset;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Upload failed';
      setState((prev) => ({ ...prev, error: message }));
      return null;
    }
  }, []);

  const updateAsset = useCallback(async (
    id: string,
    data: AssetUpdateRequest
  ): Promise<Asset | null> => {
    try {
      const updated = await api.assets.update(id, data);
      setState((prev) => ({
        ...prev,
        assets: prev.assets.map((a) => (a.id === id ? updated : a)),
      }));
      return updated;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Update failed';
      setState((prev) => ({ ...prev, error: message }));
      return null;
    }
  }, []);

  const deleteAsset = useCallback(async (id: string): Promise<boolean> => {
    try {
      await api.assets.delete(id);
      setState((prev) => ({
        ...prev,
        assets: prev.assets.filter((a) => a.id !== id),
        total: prev.total - 1,
        selectedIds: (() => {
          const next = new Set(prev.selectedIds);
          next.delete(id);
          return next;
        })(),
      }));
      return true;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Delete failed';
      setState((prev) => ({ ...prev, error: message }));
      return false;
    }
  }, []);

  const deleteSelected = useCallback(async (): Promise<number> => {
    const ids = Array.from(state.selectedIds);
    let deleted = 0;

    for (const id of ids) {
      const success = await deleteAsset(id);
      if (success) deleted++;
    }

    return deleted;
  }, [state.selectedIds, deleteAsset]);

  // Batch operations
  const startBatchGeneration = useCallback(async (
    provider?: string,
    quality?: 'draft' | 'standard' | 'high'
  ): Promise<BatchJob | null> => {
    const assetIds = Array.from(state.selectedIds);
    if (assetIds.length === 0) {
      setState((prev) => ({ ...prev, error: 'No assets selected' }));
      return null;
    }

    try {
      const job = await api.batch.start({
        asset_ids: assetIds,
        provider,
        quality,
      });
      return job;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Batch generation failed';
      setState((prev) => ({ ...prev, error: message }));
      return null;
    }
  }, [state.selectedIds]);

  return {
    ...state,
    refresh,
    loadMore,
    selectAsset,
    deselectAsset,
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
  };
}

// Hook for batch job status polling
export function useBatchJob(jobId: string | null) {
  const [job, setJob] = useState<BatchJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }

    let cancelled = false;
    let intervalId: NodeJS.Timeout;

    const poll = async () => {
      if (cancelled) return;

      setLoading(true);
      try {
        const status = await api.batch.getStatus(jobId);
        if (!cancelled) {
          setJob(status);
          setError(null);

          // Stop polling if job is complete
          if (['completed', 'failed'].includes(status.status)) {
            clearInterval(intervalId);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Failed to get job status');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    poll();

    // Poll every 2 seconds
    intervalId = setInterval(poll, 2000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [jobId]);

  const pause = useCallback(async () => {
    if (!jobId) return null;
    try {
      const updated = await api.batch.pause(jobId);
      setJob(updated);
      return updated;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to pause');
      return null;
    }
  }, [jobId]);

  const resume = useCallback(async () => {
    if (!jobId) return null;
    try {
      const updated = await api.batch.resume(jobId);
      setJob(updated);
      return updated;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to resume');
      return null;
    }
  }, [jobId]);

  const cancel = useCallback(async () => {
    if (!jobId) return null;
    try {
      const updated = await api.batch.cancel(jobId);
      setJob(updated);
      return updated;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to cancel');
      return null;
    }
  }, [jobId]);

  return { job, loading, error, pause, resume, cancel };
}
