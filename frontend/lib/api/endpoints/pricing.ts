import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout, handleResponse } from '../client';
import { DynamicPricingResponseSchema } from '../schemas';
import type { DynamicPricingRequest, DynamicPricingResponse } from '../types';

export const pricing = {
    /** POST /commerce/pricing/optimize — ML + market-intelligence price optimization for a set of SKUs. */
    optimize: async (request: DynamicPricingRequest): Promise<DynamicPricingResponse> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/commerce/pricing/optimize`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(request),
        }, 60000); // pricing agent init + per-SKU optimization can take a while
        return handleResponse(res, DynamicPricingResponseSchema);
    },
};
