/**
 * BullMQ Queue Definitions
 *
 * Defines job queues with retry policies, concurrency limits, and rate limiting.
 * Requires Redis (REDIS_URL env var) as the backing store.
 */

import { Queue } from 'bullmq';

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

function parseRedisUrl(url: string) {
  try {
    const parsed = new URL(url);
    return {
      host: parsed.hostname || 'localhost',
      port: parseInt(parsed.port || '6379', 10),
      password: parsed.password || undefined,
      db: parsed.pathname ? parseInt(parsed.pathname.slice(1) || '0', 10) : 0,
    };
  } catch {
    return { host: 'localhost', port: 6379 };
  }
}

const connection = parseRedisUrl(REDIS_URL);

export type JobType =
  | 'generate-3d-asset'
  | 'process-image'
  | 'sync-wordpress'
  | 'send-email';

export interface JobData {
  'generate-3d-asset': {
    productId: string;
    prompt: string;
    provider: 'tripo' | 'meshy';
    outputFormat: 'glb' | 'fbx' | 'obj' | 'usdz';
  };
  'process-image': {
    sourceUrl: string;
    operations: Array<'resize' | 'optimize' | 'watermark' | 'convert'>;
    outputFormat: 'webp' | 'png' | 'jpg';
    maxWidth?: number;
  };
  'sync-wordpress': {
    action: 'sync-products' | 'sync-media' | 'sync-theme' | 'full-sync';
    productIds?: string[];
    force?: boolean;
  };
  'send-email': {
    to: string;
    subject: string;
    template: 'pre-order-confirmation' | 'shipping-notification' | 'welcome';
    data: Record<string, string>;
  };
}

const defaultJobOptions = {
  attempts: 3,
  backoff: {
    type: 'exponential' as const,
    delay: 5000, // 5s base, then 10s, 20s
  },
  removeOnComplete: {
    count: 100, // Keep last 100 completed jobs
  },
  removeOnFail: {
    count: 500, // Keep last 500 failed jobs for debugging
  },
};

export const queues: Record<JobType, Queue> = {
  'generate-3d-asset': new Queue('generate-3d-asset', {
    connection,
    defaultJobOptions: {
      ...defaultJobOptions,
      attempts: 2, // 3D generation is expensive, fewer retries
    },
  }),
  'process-image': new Queue('process-image', {
    connection,
    defaultJobOptions,
  }),
  'sync-wordpress': new Queue('sync-wordpress', {
    connection,
    defaultJobOptions: {
      ...defaultJobOptions,
      attempts: 5, // WordPress can be flaky
    },
  }),
  'send-email': new Queue('send-email', {
    connection,
    defaultJobOptions: {
      ...defaultJobOptions,
      attempts: 3,
    },
  }),
};

export async function addJob<T extends JobType>(
  type: T,
  data: JobData[T],
  options?: { priority?: number; delay?: number }
) {
  const queue = queues[type];
  const job = await queue.add(type, data, {
    priority: options?.priority,
    delay: options?.delay,
  });
  return {
    id: job.id,
    name: job.name,
    queue: type,
  };
}

export async function getQueueStats(type: JobType) {
  const queue = queues[type];
  const [waiting, active, completed, failed, delayed] = await Promise.all([
    queue.getWaitingCount(),
    queue.getActiveCount(),
    queue.getCompletedCount(),
    queue.getFailedCount(),
    queue.getDelayedCount(),
  ]);

  return { waiting, active, completed, failed, delayed };
}

export async function getAllQueueStats() {
  const stats: Record<string, Awaited<ReturnType<typeof getQueueStats>>> = {};
  for (const type of Object.keys(queues) as JobType[]) {
    stats[type] = await getQueueStats(type);
  }
  return stats;
}
