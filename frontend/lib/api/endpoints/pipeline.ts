import { ApiError } from '../errors';
import { getAuthHeaders, fetchWithTimeout, handleResponse, handleArrayResponse } from '../client';
import {
    PipelineStatusSchema,
    Provider3DSchema,
    Job3DSchema
} from '../schemas';
import type {
    PipelineStatus,
    Provider3D,
    Job3D,
    TextTo3DRequest,
    ImageTo3DRequest
} from '../types';

// 3D pipeline routes live in the Next.js app — use relative URLs
const PIPELINE_BASE = '/api/v1/3d';

export const pipeline3d = {
    getStatus: async (): Promise<PipelineStatus> => {
        const res = await fetchWithTimeout(`${PIPELINE_BASE}/status`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, PipelineStatusSchema);
    },

    getProviders: async (): Promise<Provider3D[]> => {
        const res = await fetchWithTimeout(`${PIPELINE_BASE}/providers`, {
            headers: await getAuthHeaders(),
        });
        return handleArrayResponse(res, Provider3DSchema);
    },

    getJobs: async (limit = 20): Promise<Job3D[]> => {
        const safeLimit = Math.min(Math.max(1, limit), 100);
        const res = await fetchWithTimeout(
            `${PIPELINE_BASE}/jobs?limit=${safeLimit}`,
            { headers: await getAuthHeaders() }
        );
        return handleArrayResponse(res, Job3DSchema);
    },

    getJob: async (jobId: string): Promise<Job3D> => {
        if (!jobId || !/^[a-zA-Z0-9_-]+$/.test(jobId)) {
            throw new ApiError('Invalid job ID format', 400, 'INVALID_INPUT');
        }

        const res = await fetchWithTimeout(`${PIPELINE_BASE}/jobs/${jobId}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, Job3DSchema);
    },

    generateFromText: async (request: TextTo3DRequest): Promise<Job3D> => {
        if (!request.prompt?.trim()) {
            throw new ApiError('Prompt is required', 400, 'INVALID_INPUT');
        }
        if (request.prompt.length > 5000) {
            throw new ApiError('Prompt too long (max 5000 chars)', 400, 'INVALID_INPUT');
        }

        const res = await fetchWithTimeout(`${PIPELINE_BASE}/generate/text`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify({
                prompt: request.prompt.trim(),
                provider: request.provider,
                quality: request.quality || 'standard',
            }),
        });
        return handleResponse(res, Job3DSchema);
    },

    generateFromImage: async (request: ImageTo3DRequest): Promise<Job3D> => {
        try {
            new URL(request.image_url);
        } catch {
            throw new ApiError('Invalid image URL', 400, 'INVALID_INPUT');
        }

        if (request.image_url.length > 2000) {
            throw new ApiError('Image URL too long', 400, 'INVALID_INPUT');
        }

        const res = await fetchWithTimeout(`${PIPELINE_BASE}/generate/image`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify({
                image_url: request.image_url,
                provider: request.provider,
                quality: request.quality || 'standard',
            }),
        });
        return handleResponse(res, Job3DSchema);
    },
};
