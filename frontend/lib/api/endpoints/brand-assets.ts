import { API_URL } from '../config';
import { ApiError } from '../errors';
import { getAuthHeaders, fetchWithTimeout, handleResponse } from '../client';
import {
    BrandAssetSchema,
    BrandAssetsListResponseSchema,
    BulkIngestionJobSchema,
    TrainingReadinessResponseSchema,
} from '../schemas';
import type {
    BrandAsset,
    BrandAssetsListResponse,
    BrandAssetListFilters,
    BulkIngestionJob,
    BulkIngestionRequest,
    TrainingReadinessResponse,
} from '../types';

const BASE = '/api/v1/brand-assets';

export const brandAssets = {
    /** GET /brand-assets/training-readiness — status, category breakdown, recommendations. */
    trainingReadiness: async (minimumAssets?: number): Promise<TrainingReadinessResponse> => {
        const params = new URLSearchParams();
        if (minimumAssets) params.set('minimum_assets', String(minimumAssets));
        const query = params.toString();
        const res = await fetchWithTimeout(
            `${API_URL}${BASE}/training-readiness${query ? `?${query}` : ''}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, TrainingReadinessResponseSchema);
    },

    /** GET /brand-assets/assets — filtered, paginated list of ingested brand assets. */
    list: async (filters?: BrandAssetListFilters): Promise<BrandAssetsListResponse> => {
        const params = new URLSearchParams();
        if (filters?.category) params.set('category', filters.category);
        if (filters?.approvalStatus) params.set('approval_status', filters.approvalStatus);
        if (filters?.campaign) params.set('campaign', filters.campaign);
        if (filters?.page) params.set('page', String(filters.page));
        if (filters?.pageSize) params.set('page_size', String(Math.min(filters.pageSize, 100)));

        const res = await fetchWithTimeout(`${API_URL}${BASE}/assets?${params.toString()}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, BrandAssetsListResponseSchema);
    },

    /** POST /brand-assets/ingest/bulk — kicks off background ingestion, returns a job to poll. */
    bulkIngest: async (request: BulkIngestionRequest): Promise<BulkIngestionJob> => {
        const res = await fetchWithTimeout(`${API_URL}${BASE}/ingest/bulk`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(request),
        });
        return handleResponse(res, BulkIngestionJobSchema);
    },

    /** GET /brand-assets/ingest/{job_id} — poll bulk ingestion progress. */
    getIngestionJob: async (jobId: string): Promise<BulkIngestionJob> => {
        if (!jobId || !/^[a-zA-Z0-9_-]+$/.test(jobId)) {
            throw new ApiError('Invalid job ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}${BASE}/ingest/${jobId}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, BulkIngestionJobSchema);
    },

    /** PATCH /brand-assets/assets/{asset_id}/approve — approve an asset for training use. */
    approve: async (assetId: string): Promise<BrandAsset> => {
        if (!assetId || !/^[a-zA-Z0-9_-]+$/.test(assetId)) {
            throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}${BASE}/assets/${assetId}/approve`, {
            method: 'PATCH',
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, BrandAssetSchema);
    },

    /** PATCH /brand-assets/assets/{asset_id}/reject — reject an asset from training use; optional reason is stored in metadata.notes. */
    reject: async (assetId: string, reason?: string): Promise<BrandAsset> => {
        if (!assetId || !/^[a-zA-Z0-9_-]+$/.test(assetId)) {
            throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
        }
        const params = new URLSearchParams();
        if (reason) params.set('reason', reason);
        const query = params.toString();
        const res = await fetchWithTimeout(
            `${API_URL}${BASE}/assets/${assetId}/reject${query ? `?${query}` : ''}`,
            { method: 'PATCH', headers: await getAuthHeaders() }
        );
        return handleResponse(res, BrandAssetSchema);
    },
};
