import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout, handleResponse } from '../client';
import {
    CompetitorSchema,
    CompetitorListResponseSchema,
    CompetitorAssetListResponseSchema,
    StyleAnalyticsResponseSchema,
    CompetitorAnalyticsSummarySchema,
} from '../schemas';
import type {
    Competitor,
    CompetitorListResponse,
    CompetitorAssetListResponse,
    CompetitorAssetListFilters,
    CompetitorCreateRequest,
    StyleAnalyticsResponse,
    CompetitorAnalyticsSummary,
} from '../types';

const BASE = '/api/v1/competitors';

function assertValidId(id: string): void {
    if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid competitor ID format', 400, 'INVALID_INPUT');
    }
}

export const competitors = {
    /** GET /competitors — list all tracked competitor brands. Restricted to strategy/marketing/admin roles. */
    list: async (): Promise<CompetitorListResponse> => {
        const res = await fetchWithTimeout(`${API_URL}${BASE}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, CompetitorListResponseSchema);
    },

    /** POST /competitors — register a new competitor brand for tracking. */
    create: async (request: CompetitorCreateRequest): Promise<Competitor> => {
        const res = await fetchWithTimeout(`${API_URL}${BASE}`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(request),
        });
        return handleResponse(res, CompetitorSchema);
    },

    /** DELETE /competitors/{id} — remove a competitor and all associated assets. */
    remove: async (id: string): Promise<void> => {
        assertValidId(id);
        const res = await fetchWithTimeout(`${API_URL}${BASE}/${id}`, {
            method: 'DELETE',
            headers: await getAuthHeaders(),
        });
        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw ApiError.fromResponse(res.status, body);
        }
    },

    /** GET /competitors/assets — filtered, paginated list of competitor product images. */
    listAssets: async (filters?: CompetitorAssetListFilters): Promise<CompetitorAssetListResponse> => {
        const params = new URLSearchParams();
        if (filters?.competitorId) params.set('competitor_id', filters.competitorId);
        if (filters?.competitorCategory) params.set('competitor_category', filters.competitorCategory);
        if (filters?.pricePositioning) params.set('price_positioning', filters.pricePositioning);
        if (filters?.page) params.set('page', String(filters.page));
        if (filters?.pageSize) params.set('page_size', String(Math.min(filters.pageSize, 100)));

        const res = await fetchWithTimeout(`${API_URL}${BASE}/assets?${params.toString()}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, CompetitorAssetListResponseSchema);
    },

    /** GET /competitors/analytics/style-distribution — style/composition/color/price analytics across competitor assets. */
    styleAnalytics: async (competitorId?: string): Promise<StyleAnalyticsResponse> => {
        const params = new URLSearchParams();
        if (competitorId) params.set('competitor_id', competitorId);
        const query = params.toString();
        const res = await fetchWithTimeout(
            `${API_URL}${BASE}/analytics/style-distribution${query ? `?${query}` : ''}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, StyleAnalyticsResponseSchema);
    },

    /** GET /competitors/analytics/summary — high-level counts by category/price-positioning. */
    summary: async (): Promise<CompetitorAnalyticsSummary> => {
        const res = await fetchWithTimeout(`${API_URL}${BASE}/analytics/summary`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, CompetitorAnalyticsSummarySchema);
    },
};
