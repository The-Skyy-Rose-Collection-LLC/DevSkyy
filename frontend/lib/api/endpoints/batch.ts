import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout, handleResponse, handleArrayResponse } from '../client';
import { BatchJobSchema } from '../schemas';
import type { BatchJob, BatchGenerationRequest } from '../types';

export const batch = {
    start: async (data: BatchGenerationRequest): Promise<BatchJob> => {
        if (!data.asset_ids?.length) {
            throw new ApiError('At least one asset ID is required', 400, 'INVALID_INPUT');
        }
        if (data.asset_ids.length > 500) {
            throw new ApiError('Maximum 500 assets per batch', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/generate`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(data),
        });
        return handleResponse(res, BatchJobSchema);
    },

    getStatus: async (id: string): Promise<BatchJob> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, BatchJobSchema);
    },

    pause: async (id: string): Promise<BatchJob> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}/pause`, {
            method: 'POST',
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, BatchJobSchema);
    },

    resume: async (id: string): Promise<BatchJob> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}/resume`, {
            method: 'POST',
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, BatchJobSchema);
    },

    cancel: async (id: string): Promise<BatchJob> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}/cancel`, {
            method: 'POST',
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, BatchJobSchema);
    },

    list: async (): Promise<BatchJob[]> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/batch`, {
            headers: await getAuthHeaders(),
        });
        return handleArrayResponse(res, BatchJobSchema);
    },
};
