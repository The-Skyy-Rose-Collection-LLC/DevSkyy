import { API_URL } from './config';
import { ApiError } from './errors';
import { roundTable } from './endpoints/round-table';
import { pipeline3d } from './endpoints/pipeline';
import { assets } from './endpoints/assets';
import { qa } from './endpoints/qa';
import { batch } from './endpoints/batch';
import { health } from './endpoints/health';

// Re-export types
export * from './types';
export { ApiError, API_URL };

// Main API client
export const api = {
    roundTable,
    pipeline3d,
    assets,
    qa,
    batch,
    health,
};

export default api;
