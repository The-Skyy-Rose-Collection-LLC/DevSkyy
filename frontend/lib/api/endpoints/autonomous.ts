import { fetchWithTimeout, getAuthHeaders, handleResponse } from '../client';
import { API_URL } from '../config';
import {
    AutonomousOperationSchema,
    AutonomousHistoryEntrySchema,
    AutonomousOperationsResponseSchema,
} from '../schemas';
import type {
    AutonomousOperation,
    AutonomousHistoryEntry,
    AutonomousOperationsResponse,
} from '../types';
import { z } from 'zod';

const BASE = '/api/v1';

export const autonomous = {
    async list(): Promise<AutonomousOperationsResponse> {
        const res = await fetchWithTimeout(`${API_URL}${BASE}/autonomous/operations`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, AutonomousOperationsResponseSchema);
    },

    async start(id: string): Promise<AutonomousOperation> {
        const res = await fetchWithTimeout(`${API_URL}${BASE}/autonomous/operations/${id}/start`, {
            method: 'POST',
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, AutonomousOperationSchema);
    },

    async stop(id: string): Promise<AutonomousOperation> {
        const res = await fetchWithTimeout(`${API_URL}${BASE}/autonomous/operations/${id}/stop`, {
            method: 'POST',
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, AutonomousOperationSchema);
    },

    async history(id: string, limit = 50): Promise<AutonomousHistoryEntry[]> {
        const res = await fetchWithTimeout(
            `${BASE}/autonomous/operations/${id}/history?limit=${limit}`,
            { headers: await getAuthHeaders() },
        );
        return handleResponse(res, z.array(AutonomousHistoryEntrySchema));
    },
};
