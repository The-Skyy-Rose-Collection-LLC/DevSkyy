import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout, handleResponse } from '../client';
import {
    TrainingProgressSchema,
    TrainingJobsListSchema,
} from '../schemas';
import type {
    TrainingProgress,
    TrainingJobsList,
} from '../types';

const JOB_ID_RE = /^[a-zA-Z0-9_-]+$/;
const MAX_JOB_ID_LENGTH = 128;

export const training = {
    getStatus: async (): Promise<TrainingProgress> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/training/status`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, TrainingProgressSchema);
    },

    getJobs: async (): Promise<TrainingJobsList> => {
        const res = await fetchWithTimeout(`${API_URL}/api/v1/training/jobs`, {
            headers: await getAuthHeaders(),
        });
        return handleResponse(res, TrainingJobsListSchema);
    },

    getJob: async (jobId: string): Promise<TrainingProgress> => {
        if (!JOB_ID_RE.test(jobId) || jobId.length > MAX_JOB_ID_LENGTH) {
            throw new ApiError('Invalid job ID format', 400, 'INVALID_INPUT');
        }
        const res = await fetchWithTimeout(
            `${API_URL}/api/v1/training/jobs/${encodeURIComponent(jobId)}`,
            { headers: await getAuthHeaders() }
        );
        return handleResponse(res, TrainingProgressSchema);
    },
};
