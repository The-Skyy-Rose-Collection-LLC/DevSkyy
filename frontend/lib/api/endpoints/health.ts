import { z } from 'zod';
import { API_URL } from '../config';
import { fetchWithTimeout, handleResponse } from '../client';
import { HealthResponseSchema } from '../schemas';
import type { HealthResponse } from '../types';

export const health = {
    check: async (): Promise<HealthResponse> => {
        const res = await fetchWithTimeout(`${API_URL}/health`, {
            headers: { 'Content-Type': 'application/json' },
        });
        return handleResponse(res, HealthResponseSchema);
    },

    ready: async (): Promise<{ status: string }> => {
        const res = await fetchWithTimeout(`${API_URL}/ready`, {
            headers: { 'Content-Type': 'application/json' },
        });
        return handleResponse(res, z.object({ status: z.string() }));
    },
};
