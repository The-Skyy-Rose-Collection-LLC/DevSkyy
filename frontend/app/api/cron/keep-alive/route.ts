import { NextRequest, NextResponse } from 'next/server';

/**
 * Keep-Alive Cron Job
 *
 * Pings the Fly.io backend every 10 minutes to maintain app responsiveness.
 * Fly.io free tier apps auto-stop after 30 minutes of inactivity, but this cron
 *
 * Vercel Cron: Runs on schedule defined in vercel.json
 * Security: Verifies CRON_SECRET to prevent unauthorized execution
 */

const BACKEND_URL = process.env.BACKEND_URL || 'https://devskyy.fly.dev';

export async function GET(request: NextRequest) {
  // Verify cron secret for security
  const authHeader = request.headers.get('authorization');
  const cronSecret = process.env.CRON_SECRET;

  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  const startTime = Date.now();

  try {
    // Ping backend health endpoint
    const response = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      headers: {
        'User-Agent': 'DevSkyy-KeepAlive-Cron/1.0',
        'Accept': 'application/json',
      },
      // 30 second timeout - backend should be warm from previous ping
      signal: AbortSignal.timeout(30000),
    });

    const duration = Date.now() - startTime;
    const data = await response.json();

    if (!response.ok) {
      console.error(`[Keep-Alive] Backend returned ${response.status}`, data);
      return NextResponse.json(
        {
          success: false,
          backend_status: response.status,
          backend_url: BACKEND_URL,
          duration_ms: duration,
          error: 'Backend health check failed',
          details: data,
          timestamp: new Date().toISOString(),
        },
        { status: 200 } // Return 200 to cron so it doesn't retry
      );
    }

    console.log(`[Keep-Alive] Backend pinged successfully in ${duration}ms`);

    return NextResponse.json({
      success: true,
      backend_status: response.status,
      backend_url: BACKEND_URL,
      backend_health: data.status,
      backend_agents: data.agents?.total,
      duration_ms: duration,
      message: 'Backend kept alive',
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    const duration = Date.now() - startTime;

    console.error('[Keep-Alive] Failed to ping backend:', error);

    return NextResponse.json(
      {
        success: false,
        backend_url: BACKEND_URL,
        duration_ms: duration,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 200 } // Return 200 to cron so it doesn't retry
    );
  }
}
