import { API_URL } from './config';
import { ApiError } from './errors';
import { roundTable } from './endpoints/round-table';
import { pipeline3d } from './endpoints/pipeline';
import { assets } from './endpoints/assets';
import { agents } from './endpoints/agents';
import { monitoring } from './endpoints/monitoring';
import { autonomous } from './endpoints/autonomous';
import { qa } from './endpoints/qa';
import { batch } from './endpoints/batch';
import { health } from './endpoints/health';
import { socialMedia } from './endpoints/social-media';
import * as settings from './endpoints/settings';
import * as tasks from './endpoints/tasks';

// Re-export types
export * from './types';
export { ApiError, API_URL };

// Main API client
export const api = {
    roundTable,
    pipeline3d,
    assets,
    agents,
    monitoring,
    autonomous,
    qa,
    batch,
    health,
    socialMedia,
    settings,
    tasks,
};

export default api;
