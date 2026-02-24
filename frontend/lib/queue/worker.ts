/**
 * BullMQ Worker Process
 *
 * Processes background jobs. Run as a separate process:
 *   npx tsx frontend/lib/queue/worker.ts
 *
 * Or import and start programmatically.
 */

import { Worker, Job } from 'bullmq';
import type { JobType, JobData } from './queues';

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

// Job handlers
async function handleGenerate3D(job: Job<JobData['generate-3d-asset']>) {
  const { productId, prompt, provider, outputFormat } = job.data;

  await job.updateProgress(10);

  // Call the appropriate backend API
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/v1/3d/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ productId, prompt, provider, outputFormat }),
  });

  if (!response.ok) {
    throw new Error(`3D generation failed: ${response.status}`);
  }

  await job.updateProgress(100);
  return await response.json();
}

async function handleProcessImage(job: Job<JobData['process-image']>) {
  const { sourceUrl, operations, outputFormat, maxWidth } = job.data;
  await job.updateProgress(10);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/v1/media/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sourceUrl, operations, outputFormat, maxWidth }),
  });

  if (!response.ok) {
    throw new Error(`Image processing failed: ${response.status}`);
  }

  await job.updateProgress(100);
  return await response.json();
}

async function handleSyncWordPress(job: Job<JobData['sync-wordpress']>) {
  const { action, productIds, force } = job.data;
  await job.updateProgress(10);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/v1/wordpress/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, productIds, force }),
  });

  if (!response.ok) {
    throw new Error(`WordPress sync failed: ${response.status}`);
  }

  await job.updateProgress(100);
  return await response.json();
}

async function handleSendEmail(job: Job<JobData['send-email']>) {
  const { to, subject, template, data } = job.data;
  await job.updateProgress(10);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/v1/notifications/email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to, subject, template, data }),
  });

  if (!response.ok) {
    throw new Error(`Email send failed: ${response.status}`);
  }

  await job.updateProgress(100);
  return await response.json();
}

const handlers: Record<JobType, (job: Job) => Promise<unknown>> = {
  'generate-3d-asset': handleGenerate3D,
  'process-image': handleProcessImage,
  'sync-wordpress': handleSyncWordPress,
  'send-email': handleSendEmail,
};

// Create workers for each queue
export function startWorkers() {
  const workers: Worker[] = [];

  for (const [queueName, handler] of Object.entries(handlers)) {
    const concurrency = queueName === 'generate-3d-asset' ? 2 : 5;

    const worker = new Worker(
      queueName,
      async (job) => {
        console.log(`[${queueName}] Processing job ${job.id}`);
        try {
          const result = await handler(job);
          console.log(`[${queueName}] Job ${job.id} completed`);
          return result;
        } catch (error) {
          console.error(`[${queueName}] Job ${job.id} failed:`, error);
          throw error;
        }
      },
      { connection, concurrency }
    );

    worker.on('failed', (job, err) => {
      console.error(
        `[${queueName}] Job ${job?.id} failed after ${job?.attemptsMade} attempts:`,
        err.message
      );
    });

    workers.push(worker);
  }

  console.log(`Started ${workers.length} BullMQ workers`);
  return workers;
}

// Auto-start when run directly
if (typeof require !== 'undefined' && require.main === module) {
  startWorkers();
}
