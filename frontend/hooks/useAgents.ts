'use client';

import { useState, useEffect, useCallback } from 'react';
import { agents as agentsApi } from '@/lib/api/endpoints/agents';
import type { AgentListResponse } from '@/lib/api/types';

interface UseAgentsState {
    data: AgentListResponse | null;
    loading: boolean;
    error: string | null;
}

export function useAgents() {
    const [state, setState] = useState<UseAgentsState>({
        data: null,
        loading: true,
        error: null,
    });

    const load = useCallback(async () => {
        setState(prev => ({ ...prev, loading: true, error: null }));
        try {
            const data = await agentsApi.list();
            setState({ data, loading: false, error: null });
        } catch (err) {
            setState(prev => ({
                ...prev,
                loading: false,
                error: err instanceof Error ? err.message : 'Failed to load agents',
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
