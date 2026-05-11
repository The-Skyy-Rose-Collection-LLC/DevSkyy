import { fetchWithTimeout, getAuthHeaders, handleResponse } from '../client';
import { MonitoringHealthResponseSchema } from '../schemas';
import type { MonitoringHealthResponse } from '../types';

const BASE = '/api/v1';

export const monitoring = {
    async health(): Promise<MonitoringHealthResponse> {
        const res = await fetchWithTimeout(`${BASE}/monitoring/health`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, MonitoringHealthResponseSchema);
    },
};
