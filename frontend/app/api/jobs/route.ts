import { NextResponse } from 'next/server';
import type { JobType, JobData } from '@/lib/queue/queues';

export async function POST(request: Request) {
  try {
    const { type, data, options } = (await request.json()) as {
      type: JobType;
      data: JobData[JobType];
      options?: { priority?: number; delay?: number };
    };

    if (!type || !data) {
      return NextResponse.json(
        { error: 'Missing type or data' },
        { status: 400 },
      );
    }

    const validTypes: JobType[] = [
      'generate-3d-asset',
      'process-image',
      'sync-wordpress',
      'send-email',
    ];

    if (!validTypes.includes(type)) {
      return NextResponse.json(
        { error: `Invalid job type: ${type}` },
        { status: 400 },
      );
    }

    // Dynamic import to avoid loading BullMQ at build time
    const { addJob } = await import('@/lib/queue/queues');
    const job = await addJob(type, data, options);

    return NextResponse.json({ success: true, job });
  } catch {
    return NextResponse.json(
      { error: 'Failed to enqueue job' },
      { status: 500 },
    );
  }
}

export async function GET() {
  try {
    const { getAllQueueStats } = await import('@/lib/queue/queues');
    const stats = await getAllQueueStats();
    return NextResponse.json({ stats });
  } catch {
    return NextResponse.json(
      { error: 'Failed to get queue stats' },
      { status: 500 },
    );
  }
}
