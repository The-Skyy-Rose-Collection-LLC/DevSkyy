export class ApiError extends Error {
    constructor(
        message: string,
        public readonly status: number,
        public readonly code?: string,
        public readonly details?: unknown
    ) {
        super(message);
        this.name = 'ApiError';
        Object.setPrototypeOf(this, ApiError.prototype);
    }

    static isApiError(error: unknown): error is ApiError {
        return error instanceof ApiError;
    }

    static fromResponse(status: number, body: unknown): ApiError {
        if (typeof body === 'object' && body !== null) {
            const { detail, message, code } = body as Record<string, unknown>;
            return new ApiError(
                String(detail || message || 'Request failed'),
                status,
                typeof code === 'string' ? code : undefined,
                body
            );
        }
        return new ApiError('Request failed', status);
    }
}
