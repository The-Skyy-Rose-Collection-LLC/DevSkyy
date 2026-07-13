import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthToken, getAuthHeaders, fetchWithTimeout, handleResponse } from '../client';
import {
    AssetListResponseSchema,
    AssetSchema,
    SkuImageCountsSchema,
    HfDatasetsResponseSchema,
    AssetIngestResponseSchema,
    AssetJobResponseSchema,
} from '../schemas';
import type {
    AssetListResponse,
    Asset,
    AssetFilters,
    AssetUpdateRequest,
    SkuImageCounts,
    HfDatasetsResponse,
    AssetIngestResponse,
    AssetIngestOptions,
    AssetJobResponse,
} from '../types';

export const assets = {
    getList: async (filters?: AssetFilters): Promise<AssetListResponse> => {
        const params = new URLSearchParams();
        if (filters?.collection) params.set('collection', filters.collection);
        if (filters?.type) params.set('type', filters.type);
        if (filters?.search) params.set('search', filters.search);
        if (filters?.page) params.set('page', String(filters.page));
        if (filters?.limit) params.set('limit', String(Math.min(filters.limit, 100)));

        const res = await fetchWithTimeout(
            `${API_URL}/api/v1/assets?${params.toString()}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, AssetListResponseSchema);
    },

    get: async (id: string): Promise<Asset> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/${id}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, AssetSchema);
    },

    update: async (id: string, data: AssetUpdateRequest): Promise<Asset> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/${id}`, {
            method: 'PATCH',
            headers: await getAuthHeaders(),
            body: JSON.stringify(data),
        });
        return handleResponse(res, AssetSchema);
    },

    delete: async (id: string): Promise<void> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/${id}`, {
            method: 'DELETE',
            headers: await getAuthHeaders(),
        });
        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw ApiError.fromResponse(res.status, body);
        }
    },

    upload: async (file: File, collection: string): Promise<Asset> => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('collection', collection);

        const token = getAuthToken();
        const headers: HeadersInit = {
            'X-Request-ID': crypto.randomUUID(),
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/upload`, {
            method: 'POST',
            headers,
            body: formData,
        }, 120000); // 2 minute timeout for uploads
        return handleResponse(res, AssetSchema);
    },

    /** POST /assets/ingest — submit an image for the ML processing pipeline; returns a job_id to poll via getJob(). */
    ingest: async (file: File, options?: AssetIngestOptions): Promise<AssetIngestResponse> => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('source', options?.source ?? 'dashboard');
        if (options?.productId) formData.append('product_id', options.productId);
        formData.append('processing_profile', options?.processingProfile ?? 'full');
        if (options?.callbackUrl) formData.append('callback_url', options.callbackUrl);

        const token = getAuthToken();
        const headers: HeadersInit = {
            'X-Request-ID': crypto.randomUUID(),
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/ingest`, {
            method: 'POST',
            headers,
            body: formData,
        }, 120000); // 2 minute timeout for uploads
        return handleResponse(res, AssetIngestResponseSchema);
    },

    /** GET /assets/jobs/{job_id} — poll ML processing pipeline job status. */
    getJob: async (jobId: string): Promise<AssetJobResponse> => {
        if (!jobId || !/^[a-zA-Z0-9_-]+$/.test(jobId)) {
            throw new ApiError('Invalid job ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/jobs/${jobId}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, AssetJobResponseSchema);
    },

    getCollectionStats: async (): Promise<Record<string, number>> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/stats/collections`, {
            headers: await getAuthHeaders(),
        });
        const data = await res.json();
        return data as Record<string, number>;
    },

    perSku: async (): Promise<SkuImageCounts> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/per-sku`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, SkuImageCountsSchema);
    },

    datasets: async (): Promise<HfDatasetsResponse> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/datasets`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, HfDatasetsResponseSchema);
    },
};
