'use client';

import { useState, useEffect, useCallback } from 'react';
import { monitoring as monitoringApi } from '@/lib/api/endpoints/monitoring';
import type { MonitoringHealthResponse } from '@/lib/api/types';

interface UseMonitoringState {
    data: MonitoringHealthResponse | null;
    loading: boolean;
    error: string | null;
}

export function useMonitoring() {
    const [state, setState] = useState<UseMonitoringState>({
        data: null,
        loading: true,
        error: null,
    });

    const load = useCallback(async () => {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        try {
            const data = await monitoringApi.health();
            setState({ data, loading: false, error: null });
        } catch (err) {
            setState((prev) => ({
                ...prev,
                loading: false,
                error: err instanceof Error ? err.message : 'Failed to load monitoring data',
            }));
        }
    }, []);

    useEffect(() => {
        load();
        const interval = setInterval(load, 30000);
        return () => clearInterval(interval);
    }, [load]);

    return { ...state, refresh: load };
}
