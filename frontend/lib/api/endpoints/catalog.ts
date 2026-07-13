import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout, handleResponse } from '../client';
import {
    CatalogSearchResponseSchema,
    CatalogSimilarResponseSchema,
} from '../schemas';
import type {
    CatalogSearchResponse,
    CatalogSimilarResponse,
} from '../types';

// SKU format: lowercase alphanum + hyphens (e.g. "br-001", "sg-014")
const SKU_RE = /^[a-z0-9][a-z0-9-]{1,31}$/;
// Collection slug: lowercase alphanum + hyphens (e.g. "black-rose", "signature")
const SLUG_RE = /^[a-z][a-z0-9-]*$/;

export const catalog = {
    /**
     * Semantic search across all catalog SKUs.
     * Calls GET /api/v1/catalog/search?q=...&top_k=...
     */
    search: async (
        q: string,
        top_k = 5,
        collection?: string
    ): Promise<CatalogSearchResponse> => {
        if (!q.trim()) {
            throw new ApiError('Search query is required', 400, 'INVALID_INPUT');
        }
        if (q.length > 500) {
            throw new ApiError('Query too long (max 500 chars)', 400, 'INVALID_INPUT');
        }

        const safeTopK = Math.min(Math.max(1, top_k), 20);
        const params = new URLSearchParams({ q: q.trim(), top_k: String(safeTopK) });
        if (collection) {
            if (!SLUG_RE.test(collection)) {
                throw new ApiError(
                    `Invalid collection slug: ${collection}`,
                    400,
                    'INVALID_INPUT'
                );
            }
            params.set('collection', collection);
        }

        const res = await fetchWithTimeout(
            `${API_URL}/api/v1/catalog/search?${params.toString()}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, CatalogSearchResponseSchema);
    },

    /**
     * Top-k semantically similar SKUs for a given SKU (excludes the source SKU).
     * Calls GET /api/v1/catalog/products/{sku}/similar
     */
    similar: async (sku: string, top_k = 5): Promise<CatalogSimilarResponse> => {
        if (!sku || !SKU_RE.test(sku)) {
            throw new ApiError(`Invalid SKU format: ${sku}`, 400, 'INVALID_INPUT');
        }

        const safeTopK = Math.min(Math.max(1, top_k), 20);
        const res = await fetchWithTimeout(
            `${API_URL}/api/v1/catalog/products/${encodeURIComponent(sku)}/similar?top_k=${safeTopK}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, CatalogSimilarResponseSchema);
    },

    /**
     * Top-k featured products for a collection (semantic retrieval scoped by slug).
     * Calls GET /api/v1/catalog/collections/{slug}/featured
     */
    featured: async (slug: string, top_k = 5): Promise<CatalogSearchResponse> => {
        if (!slug || !SLUG_RE.test(slug)) {
            throw new ApiError(`Invalid collection slug: ${slug}`, 400, 'INVALID_INPUT');
        }

        const safeTopK = Math.min(Math.max(1, top_k), 20);
        const res = await fetchWithTimeout(
            `${API_URL}/api/v1/catalog/collections/${encodeURIComponent(slug)}/featured?top_k=${safeTopK}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, CatalogSearchResponseSchema);
    },
};
