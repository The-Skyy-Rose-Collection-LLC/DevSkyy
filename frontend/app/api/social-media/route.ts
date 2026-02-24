/**
 * Social Media Pipeline - Main Status Route
 *
 * GET /api/social-media
 *   Returns connection status for all 4 platforms.
 *   Query params:
 *     ?dry_run=true  - Returns simulated "all green" status for testing
 */

import { NextRequest, NextResponse } from 'next/server';
import { getPlatformConnections, hasLlmKey } from '@/lib/social-media/config';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = request.nextUrl;
    const dryRun = searchParams.get('dry_run') === 'true';

    if (dryRun) {
      return NextResponse.json({
        success: true,
        dry_run: true,
        timestamp: new Date().toISOString(),
        llm_available: true,
        platforms: [
          { platform: 'instagram', label: 'Instagram', connected: true, env_var: 'INSTAGRAM_ACCESS_TOKEN', env_present: true, error: null },
          { platform: 'tiktok', label: 'TikTok', connected: true, env_var: 'TIKTOK_ACCESS_TOKEN', env_present: true, error: null },
          { platform: 'twitter', label: 'X / Twitter', connected: true, env_var: 'TWITTER_API_KEY', env_present: true, error: null },
          { platform: 'facebook', label: 'Facebook', connected: true, env_var: 'FACEBOOK_ACCESS_TOKEN', env_present: true, error: null },
        ],
      });
    }

    const platforms = getPlatformConnections();
    const connectedCount = platforms.filter((p) => p.connected).length;

    return NextResponse.json({
      success: true,
      dry_run: false,
      timestamp: new Date().toISOString(),
      llm_available: hasLlmKey(),
      connected_count: connectedCount,
      total_platforms: platforms.length,
      platforms,
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: 'Internal server error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
