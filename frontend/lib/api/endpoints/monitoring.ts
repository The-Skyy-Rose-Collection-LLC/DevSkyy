import { fetchWithTimeout, getAuthHeaders, handleResponse } from '../client';
import { MonitoringHealthResponseSchema, MonitoringMetricsResponseSchema } from '../schemas';
import type { MonitoringHealthResponse, MonitoringMetricsResponse } from '../types';

const BASE = '/api/v1';

export interface MonitoringMetricsOptions {
    /** Metric categories to retrieve (backend default: health + performance). */
    metrics?: string[];
    /** Time window: 1h, 24h, 7d, 30d (backend default: 1h). */
    timeRange?: string;
}

export const monitoring = {
    async health(): Promise<MonitoringHealthResponse> {
        const res = await fetchWithTimeout(`${BASE}/monitoring/health`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, MonitoringHealthResponseSchema);
    },

    async metrics(options: MonitoringMetricsOptions = {}): Promise<MonitoringMetricsResponse> {
        const params = new URLSearchParams();
        for (const metric of options.metrics ?? []) {
            params.append('metrics', metric);
        }
        if (options.timeRange) {
            params.set('time_range', options.timeRange);
        }
        const query = params.toString();
        const res = await fetchWithTimeout(`${BASE}/monitoring/metrics${query ? `?${query}` : ''}`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, MonitoringMetricsResponseSchema);
    },
};
