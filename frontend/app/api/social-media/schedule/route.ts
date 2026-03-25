/**
 * Social Media Pipeline - Schedule Route
 *
 * POST /api/social-media/schedule
 *   Body: { post_id: string, scheduled_at: string }
 *   Returns: { success: boolean, post_id, scheduled_at }
 *
 * Stores scheduled posts in-memory. Ready for Redis/DB backend.
 */

import { NextRequest, NextResponse } from 'next/server';

// ---------------------------------------------------------------------------
// In-memory schedule store (replace with Redis/DB in production)
// ---------------------------------------------------------------------------

interface ScheduledEntry {
  post_id: string;
  scheduled_at: string;
  created_at: string;
  status: 'pending' | 'published' | 'failed';
}

// Using a Map with LRU-style cap to prevent unbounded growth
const MAX_SCHEDULED_ENTRIES = 10_000;
const scheduledPosts = new Map<string, ScheduledEntry>();

function addScheduledEntry(entry: ScheduledEntry): void {
  // Evict oldest if at capacity
  if (scheduledPosts.size >= MAX_SCHEDULED_ENTRIES) {
    const oldestKey = scheduledPosts.keys().next().value;
    if (oldestKey !== undefined) {
      scheduledPosts.delete(oldestKey);
    }
  }
  scheduledPosts.set(entry.post_id, entry);
}

// ---------------------------------------------------------------------------
// POST handler
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { post_id?: string; scheduled_at?: string };

    // Validate required fields
    if (!body.post_id?.trim()) {
      return NextResponse.json(
        { success: false, error: 'post_id is required' },
        { status: 400 }
      );
    }

    if (!body.scheduled_at?.trim()) {
      return NextResponse.json(
        { success: false, error: 'scheduled_at is required (ISO 8601 datetime)' },
        { status: 400 }
      );
    }

    // Validate the datetime
    const scheduledDate = new Date(body.scheduled_at);
    if (isNaN(scheduledDate.getTime())) {
      return NextResponse.json(
        { success: false, error: 'scheduled_at must be a valid ISO 8601 datetime' },
        { status: 400 }
      );
    }

    // Ensure the scheduled time is in the future
    if (scheduledDate.getTime() < Date.now()) {
      return NextResponse.json(
        { success: false, error: 'scheduled_at must be in the future' },
        { status: 400 }
      );
    }

    const entry: ScheduledEntry = {
      post_id: body.post_id.trim(),
      scheduled_at: scheduledDate.toISOString(),
      created_at: new Date().toISOString(),
      status: 'pending',
    };

    addScheduledEntry(entry);

    return NextResponse.json({
      success: true,
      post_id: entry.post_id,
      scheduled_at: entry.scheduled_at,
      created_at: entry.created_at,
      status: entry.status,
      queue_size: scheduledPosts.size,
    });
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        { success: false, error: 'Invalid JSON in request body' },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// ---------------------------------------------------------------------------
// GET handler - Retrieve scheduled posts
// ---------------------------------------------------------------------------

export async function GET() {
  try {
    const entries = Array.from(scheduledPosts.values()).sort(
      (a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
    );

    return NextResponse.json({
      success: true,
      count: entries.length,
      scheduled_posts: entries,
    });
  } catch {
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
