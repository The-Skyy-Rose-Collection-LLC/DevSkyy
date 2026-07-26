import { ApiError } from '../errors';
import { fetchWithTimeout, handleResponse } from '../client';
import { QAReviewListResponseSchema, QAReviewSchema } from '../schemas';
import type { QAReviewListResponse, QAReview, QAReviewRequest, RegenerateRequest } from '../types';

// Relative paths — these hit this Next.js app's own Route Handlers
// (app/api/v1/qa/reviews/**), which forward the request to FastAPI with the
// backend JWT from the caller's NextAuth session (see lib/api/server-proxy.ts).
// The browser never needs an Authorization header here: the session cookie
// already rides along on same-origin requests.
const JSON_HEADERS = { 'Content-Type': 'application/json' };

export const qa = {
    getReviews: async (status?: string): Promise<QAReviewListResponse> => {
        const params = status ? `?status=${status}` : '';
        const res = await fetchWithTimeout(`/api/v1/qa/reviews${params}`, {});
        return handleResponse(res, QAReviewListResponseSchema);
    },

    getReview: async (id: string): Promise<QAReview> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`/api/v1/qa/reviews/${id}`, {});
        return handleResponse(res, QAReviewSchema);
    },

    submitReview: async (id: string, data: QAReviewRequest): Promise<QAReview> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`/api/v1/qa/reviews/${id}`, {
            method: 'PATCH',
            headers: JSON_HEADERS,
            body: JSON.stringify(data),
        });
        return handleResponse(res, QAReviewSchema);
    },

    regenerate: async (id: string, data?: RegenerateRequest): Promise<QAReview> => {
        if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
            throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(`/api/v1/qa/reviews/${id}/regenerate`, {
            method: 'POST',
            headers: JSON_HEADERS,
            body: JSON.stringify(data || {}),
        });
        return handleResponse(res, QAReviewSchema);
    },
};
