'use client';

import { useState, useEffect, useCallback } from 'react';
import { autonomous as autonomousApi } from '@/lib/api/endpoints/autonomous';
import type { AutonomousOperation, AutonomousHistoryEntry } from '@/lib/api/types';

interface UseAutonomousState {
    operations: AutonomousOperation[];
    total: number;
    loading: boolean;
    error: string | null;
    actionLoading: string | null;
}

export function useAutonomous() {
    const [state, setState] = useState<UseAutonomousState>({
        operations: [],
        total: 0,
        loading: true,
        error: null,
        actionLoading: null,
    });

    const load = useCallback(async () => {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        try {
            const data = await autonomousApi.list();
            setState((prev) => ({
                ...prev,
                operations: data.operations,
                total: data.total,
                loading: false,
                error: null,
            }));
        } catch (err) {
            setState((prev) => ({
                ...prev,
                loading: false,
                error: err instanceof Error ? err.message : 'Failed to load autonomous operations',
            }));
        }
    }, []);

    useEffect(() => {
        void load();
        const interval = setInterval(() => { void load(); }, 15000);
        return () => clearInterval(interval);
    }, [load]);

    const start = useCallback(async (id: string): Promise<void> => {
        setState((prev) => ({ ...prev, actionLoading: id }));
        try {
            const updated = await autonomousApi.start(id);
            setState((prev) => ({
                ...prev,
                actionLoading: null,
                operations: prev.operations.map((op) => (op.id === id ? updated : op)),
            }));
        } catch (err) {
            setState((prev) => ({
                ...prev,
                actionLoading: null,
                error: err instanceof Error ? err.message : `Failed to start ${id}`,
            }));
        }
    }, []);

    const stop = useCallback(async (id: string): Promise<void> => {
        setState((prev) => ({ ...prev, actionLoading: id }));
        try {
            const updated = await autonomousApi.stop(id);
            setState((prev) => ({
                ...prev,
                actionLoading: null,
                operations: prev.operations.map((op) => (op.id === id ? updated : op)),
            }));
        } catch (err) {
            setState((prev) => ({
                ...prev,
                actionLoading: null,
                error: err instanceof Error ? err.message : `Failed to stop ${id}`,
            }));
        }
    }, []);

    const fetchHistory = useCallback(
        async (id: string, limit = 50): Promise<AutonomousHistoryEntry[]> => {
            return autonomousApi.history(id, limit);
        },
        [],
    );

    return { ...state, refresh: load, start, stop, fetchHistory };
}
