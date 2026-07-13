import { fetchWithTimeout, getAuthHeaders, handleResponse } from '../client';
import { API_URL } from '../config';
import { AgentListResponseSchema } from '../schemas';
import type { AgentListResponse } from '../types';

const BASE = '/api/v1';

export const agents = {
    async list(): Promise<AgentListResponse> {
        const res = await fetchWithTimeout(`${API_URL}${BASE}/agents`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, AgentListResponseSchema);
    },
};
