import { z } from 'zod';
import { ApiError } from './errors';

const REQUEST_TIMEOUT = 30000; // 30 seconds

export function getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
}

export async function getAuthHeaders(): Promise<HeadersInit> {
    const token = getAuthToken();
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'X-Request-ID': crypto.randomUUID(),
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

export async function fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeout = REQUEST_TIMEOUT
): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
        });
        return response;
    } finally {
        clearTimeout(timeoutId);
    }
}

export async function handleResponse<T>(
    response: Response,
    schema: z.ZodType<T>
): Promise<T> {
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw ApiError.fromResponse(response.status, body);
    }

    const data = await response.json();

    // Validate response against schema
    const result = schema.safeParse(data);
    if (!result.success) {
        console.error('API response validation failed:', result.error.issues);
        throw new ApiError(
            'Invalid API response format',
            500,
            'VALIDATION_ERROR',
            result.error.issues
        );
    }

    return result.data;
}

export async function handleArrayResponse<T>(
    response: Response,
    schema: z.ZodType<T>
): Promise<T[]> {
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw ApiError.fromResponse(response.status, body);
    }

    const data = await response.json();

    if (!Array.isArray(data)) {
        throw new ApiError('Expected array response', 500, 'INVALID_FORMAT');
    }

    // Validate each item
    const results: T[] = [];
    for (const item of data) {
        const result = schema.safeParse(item);
        if (result.success) {
            results.push(result.data);
        } else {
            console.warn('Skipping invalid item:', result.error.issues);
        }
    }

    return results;
}
