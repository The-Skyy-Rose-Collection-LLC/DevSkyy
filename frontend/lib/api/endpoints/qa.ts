import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout, handleResponse } from '../client';
import { QAReviewListResponseSchema, QAReviewSchema } from '../schemas';
import type { QAReviewListResponse, QAReview, QAReviewRequest, RegenerateRequest } from '../types';

export const qa = {
    getReviews: async (status?: string): Promise<QAReviewListResponse> => {
        const params = status ? `?status=${status}` : '';
        const res = await fetchWithTimeout(
            `${API_URL}/api/v1/qa/reviews${params}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, QAReviewListResponseSchema);
    },

    getReview: async (id: string): Promise<QAReview> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/qa/reviews/${id}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, QAReviewSchema);
    },

    submitReview: async (id: string, data: QAReviewRequest): Promise<QAReview> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/qa/reviews/${id}`, {
            method: 'PATCH',
            headers: await getAuthHeaders(),
            body: JSON.stringify(data),
        });
        return handleResponse(res, QAReviewSchema);
    },

    regenerate: async (id: string, data?: RegenerateRequest): Promise<QAReview> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`${API_URL}/api/v1/qa/reviews/${id}/regenerate`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(data || {}),
        });
        return handleResponse(res, QAReviewSchema);
    },
};
