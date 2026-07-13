'use client';

import { useState, useEffect, useCallback } from 'react';
import { monitoring as monitoringApi } from '@/lib/api/endpoints/monitoring';
import type { MonitoringHealthResponse, MonitoringMetricsResponse } from '@/lib/api/types';

interface UseMonitoringState {
    data: MonitoringHealthResponse | null;
    metrics: MonitoringMetricsResponse | null;
    loading: boolean;
    error: string | null;
}

export function useMonitoring() {
    const [state, setState] = useState<UseMonitoringState>({
        data: null,
        metrics: null,
        loading: true,
        error: null,
    });

    const load = useCallback(async () => {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        // Health and metrics load independently — one failing must not blank
        // the other, so settle both and surface the first error (if any).
        const [health, metrics] = await Promise.allSettled([
            monitoringApi.health(),
            monitoringApi.metrics(),
        ]);
        setState((prev) => ({
            data: health.status === 'fulfilled' ? health.value : prev.data,
            metrics: metrics.status === 'fulfilled' ? metrics.value : prev.metrics,
            loading: false,
            error:
                health.status === 'rejected'
                    ? health.reason instanceof Error
                        ? health.reason.message
                        : 'Failed to load monitoring data'
                    : metrics.status === 'rejected'
                        ? metrics.reason instanceof Error
                            ? metrics.reason.message
                            : 'Failed to load monitoring metrics'
                        : null,
        }));
    }, []);

    useEffect(() => {
        load();
        const interval = setInterval(load, 30000);
        return () => clearInterval(interval);
    }, [load]);

    return { ...state, refresh: load };
}
