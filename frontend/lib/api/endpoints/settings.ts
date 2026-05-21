import { fetchWithTimeout, getAuthHeaders, handleResponse } from '../client';
import { SettingsSchema } from '../schemas';
import type { Settings } from '../types';

/**
 * Settings API client for the dashboard.
 * Uses a Next.js API route that persists settings to a local JSON file or backend.
 */
export async function fetchSettings(): Promise<Settings> {
    const headers = await getAuthHeaders();
    const response = await fetchWithTimeout('/api/settings', {
        headers,
    });
    return handleResponse(response, SettingsSchema);
}

export async function updateSettings(settings: Settings): Promise<Settings> {
    const headers = await getAuthHeaders();
    const response = await fetchWithTimeout('/api/settings', {
        method: 'POST',
        headers,
        body: JSON.stringify(settings),
    });
    return handleResponse(response, SettingsSchema);
}
