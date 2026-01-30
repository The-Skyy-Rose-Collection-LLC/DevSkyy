import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout, handleResponse, handleArrayResponse } from '../client';
import {
    ProviderInfoSchema,
    ProviderStatsSchema,
    HistoryEntrySchema,
    CompetitionResponseSchema
} from '../schemas';
import type {
    ProviderInfo,
    ProviderStats,
    HistoryEntry,
    CompetitionResponse,
    CompetitionRequest
} from '../types';

export const roundTable = {
    getProviders: async (): Promise<ProviderInfo[]> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/round-table/providers`, {
            headers: await getAuthHeaders(),
        });
        return handleArrayResponse(res, ProviderInfoSchema);
    },

    getStats: async (): Promise<ProviderStats[]> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/round-table/stats`, {
            headers: await getAuthHeaders(),
        });
        return handleArrayResponse(res, ProviderStatsSchema);
    },

    getHistory: async (limit = 10, offset = 0): Promise<HistoryEntry[]> => {
        // Sanitize inputs
        const safeLimit = Math.min(Math.max(1, limit), 100);
        const safeOffset = Math.max(0, offset);

        const res = await fetchWithTimeout(
            `${API_URL}/api/v1/round-table?limit=${safeLimit}&offset=${safeOffset}`,
            { headers: await getAuthHeaders() }
        );
        return handleArrayResponse(res, HistoryEntrySchema);
    },

    compete: async (request: CompetitionRequest): Promise<CompetitionResponse> => {
        // Validate input
        if (!request.prompt?.trim()) {
            throw new ApiError('Prompt is required', 400, 'INVALID_INPUT');
        }
        if (request.prompt.length > 10000) {
            throw new ApiError('Prompt too long (max 10000 chars)', 400, 'INVALID_INPUT');
        }

        const res = await fetchWithTimeout(`${API_URL}/api/v1/round-table/compete`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify({
                prompt: request.prompt.trim(),
                providers: request.providers,
                evaluation_criteria: request.evaluation_criteria,
            }),
        });
        return handleResponse(res, CompetitionResponseSchema);
    },
};
