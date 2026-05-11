import { fetchWithTimeout, getAuthHeaders, handleResponse } from '../client';
import { AgentListResponseSchema } from '../schemas';
import type { AgentListResponse } from '../types';

const BASE = '/api/v1';

export const agents = {
    async list(): Promise<AgentListResponse> {
        const res = await fetchWithTimeout(`${BASE}/agents`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, AgentListResponseSchema);
    },
};
