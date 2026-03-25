/**
 * Social Media Pipeline - Publish Route
 *
 * POST /api/social-media/publish
 *   Body: { post_id: string, platform: string, caption?: string, media_urls?: string[] }
 *   Returns: { success: boolean, platform, platform_post_id?, ... }
 *
 * Contains integration stubs for each platform's real API.
 * When the relevant env var is present, attempts the real API call.
 * When missing, returns a simulated success with a flag.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getPlatformConnection, getPlatformToken, type PlatformId } from '@/lib/social-media/config';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PublishRequest {
  post_id: string;
  platform: PlatformId;
  caption?: string;
  media_urls?: string[];
}

interface PublishResult {
  success: boolean;
  simulated: boolean;
  platform: string;
  post_id: string;
  platform_post_id: string | null;
  published_at: string;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Platform publishers
// ---------------------------------------------------------------------------

async function publishToInstagram(
  postId: string,
  caption?: string,
  mediaUrls?: string[]
): Promise<PublishResult> {
  const connection = getPlatformConnection('instagram');
  const now = new Date().toISOString();

  if (!connection.connected) {
    return {
      success: true,
      simulated: true,
      platform: 'instagram',
      post_id: postId,
      platform_post_id: `sim_ig_${Date.now()}`,
      published_at: now,
      error: null,
    };
  }

  // Real Instagram Graph API integration
  // Step 1: Create media container
  // Step 2: Publish the container
  const token = getPlatformToken('instagram');
  const accountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;

  try {
    // Create media container
    const containerParams = new URLSearchParams({
      caption: caption ?? '',
      access_token: token!,
    });

    // If media URLs provided, use them; otherwise create a text-only post
    if (mediaUrls && mediaUrls.length > 0) {
      containerParams.set('image_url', mediaUrls[0]);
    }

    const containerRes = await fetch(
      `https://graph.facebook.com/v19.0/${accountId}/media?${containerParams.toString()}`,
      { method: 'POST' }
    );

    if (!containerRes.ok) {
      const errorBody = await containerRes.json().catch(() => ({}));
      return {
        success: false,
        simulated: false,
        platform: 'instagram',
        post_id: postId,
        platform_post_id: null,
        published_at: now,
        error: `Instagram API error: ${(errorBody as Record<string, unknown>).error ?? containerRes.statusText}`,
      };
    }

    const containerData = (await containerRes.json()) as { id: string };

    // Publish the container
    const publishRes = await fetch(
      `https://graph.facebook.com/v19.0/${accountId}/media_publish`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          creation_id: containerData.id,
          access_token: token!,
        }).toString(),
      }
    );

    if (!publishRes.ok) {
      const errorBody = await publishRes.json().catch(() => ({}));
      return {
        success: false,
        simulated: false,
        platform: 'instagram',
        post_id: postId,
        platform_post_id: null,
        published_at: now,
        error: `Instagram publish error: ${(errorBody as Record<string, unknown>).error ?? publishRes.statusText}`,
      };
    }

    const publishData = (await publishRes.json()) as { id: string };
    return {
      success: true,
      simulated: false,
      platform: 'instagram',
      post_id: postId,
      platform_post_id: publishData.id,
      published_at: now,
      error: null,
    };
  } catch {
    return {
      success: false,
      simulated: false,
      platform: 'instagram',
      post_id: postId,
      platform_post_id: null,
      published_at: now,
      error: 'Instagram API connection failed',
    };
  }
}

async function publishToTiktok(
  postId: string,
  caption?: string,
  mediaUrls?: string[]
): Promise<PublishResult> {
  const connection = getPlatformConnection('tiktok');
  const now = new Date().toISOString();

  if (!connection.connected) {
    return {
      success: true,
      simulated: true,
      platform: 'tiktok',
      post_id: postId,
      platform_post_id: `sim_tt_${Date.now()}`,
      published_at: now,
      error: null,
    };
  }

  // Real TikTok Content Posting API integration
  const token = getPlatformToken('tiktok');

  try {
    // TikTok requires video content -- photo mode or direct post
    const res = await fetch('https://open.tiktokapis.com/v2/post/publish/content/init/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        post_info: {
          title: caption ?? '',
          privacy_level: 'PUBLIC_TO_EVERYONE',
        },
        source_info: {
          source: 'PULL_FROM_URL',
          video_url: mediaUrls?.[0] ?? '',
        },
      }),
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      return {
        success: false,
        simulated: false,
        platform: 'tiktok',
        post_id: postId,
        platform_post_id: null,
        published_at: now,
        error: `TikTok API error: ${JSON.stringify(errorBody)}`,
      };
    }

    const data = (await res.json()) as { data?: { publish_id?: string } };
    return {
      success: true,
      simulated: false,
      platform: 'tiktok',
      post_id: postId,
      platform_post_id: data.data?.publish_id ?? null,
      published_at: now,
      error: null,
    };
  } catch {
    return {
      success: false,
      simulated: false,
      platform: 'tiktok',
      post_id: postId,
      platform_post_id: null,
      published_at: now,
      error: 'TikTok API connection failed',
    };
  }
}

async function publishToTwitter(
  postId: string,
  caption?: string,
  _mediaUrls?: string[]
): Promise<PublishResult> {
  const connection = getPlatformConnection('twitter');
  const now = new Date().toISOString();

  if (!connection.connected) {
    return {
      success: true,
      simulated: true,
      platform: 'twitter',
      post_id: postId,
      platform_post_id: `sim_tw_${Date.now()}`,
      published_at: now,
      error: null,
    };
  }

  // Real X/Twitter v2 API integration
  // Uses OAuth 1.0a User Context (requires all 4 keys)
  const apiKey = process.env.TWITTER_API_KEY!;
  const apiSecret = process.env.TWITTER_API_SECRET!;
  const accessToken = process.env.TWITTER_ACCESS_TOKEN!;
  const accessSecret = process.env.TWITTER_ACCESS_SECRET!;

  try {
    // Twitter v2 tweet creation endpoint
    // Note: Full OAuth 1.0a signature generation is required in production.
    // For now, we use Bearer token approach with the API key for the stub.
    const credentials = Buffer.from(`${apiKey}:${apiSecret}`).toString('base64');

    const res = await fetch('https://api.twitter.com/2/tweets', {
      method: 'POST',
      headers: {
        Authorization: `Basic ${credentials}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: (caption ?? '').slice(0, 280),
      }),
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      return {
        success: false,
        simulated: false,
        platform: 'twitter',
        post_id: postId,
        platform_post_id: null,
        published_at: now,
        error: `Twitter API error: ${JSON.stringify(errorBody)}`,
      };
    }

    const data = (await res.json()) as { data?: { id?: string } };
    return {
      success: true,
      simulated: false,
      platform: 'twitter',
      post_id: postId,
      platform_post_id: data.data?.id ?? null,
      published_at: now,
      error: null,
    };
  } catch {
    return {
      success: false,
      simulated: false,
      platform: 'twitter',
      post_id: postId,
      platform_post_id: null,
      published_at: now,
      error: 'Twitter API connection failed',
    };
  }
}

async function publishToFacebook(
  postId: string,
  caption?: string,
  mediaUrls?: string[]
): Promise<PublishResult> {
  const connection = getPlatformConnection('facebook');
  const now = new Date().toISOString();

  if (!connection.connected) {
    return {
      success: true,
      simulated: true,
      platform: 'facebook',
      post_id: postId,
      platform_post_id: `sim_fb_${Date.now()}`,
      published_at: now,
      error: null,
    };
  }

  // Real Facebook Graph API integration
  const token = getPlatformToken('facebook');
  const pageId = process.env.FACEBOOK_PAGE_ID;

  try {
    const params: Record<string, string> = {
      message: caption ?? '',
      access_token: token!,
    };

    // Attach photo if media URL provided
    if (mediaUrls && mediaUrls.length > 0) {
      params.url = mediaUrls[0];
    }

    const endpoint = mediaUrls && mediaUrls.length > 0
      ? `https://graph.facebook.com/v19.0/${pageId}/photos`
      : `https://graph.facebook.com/v19.0/${pageId}/feed`;

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(params).toString(),
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      return {
        success: false,
        simulated: false,
        platform: 'facebook',
        post_id: postId,
        platform_post_id: null,
        published_at: now,
        error: `Facebook API error: ${JSON.stringify(errorBody)}`,
      };
    }

    const data = (await res.json()) as { id?: string; post_id?: string };
    return {
      success: true,
      simulated: false,
      platform: 'facebook',
      post_id: postId,
      platform_post_id: data.post_id ?? data.id ?? null,
      published_at: now,
      error: null,
    };
  } catch {
    return {
      success: false,
      simulated: false,
      platform: 'facebook',
      post_id: postId,
      platform_post_id: null,
      published_at: now,
      error: 'Facebook API connection failed',
    };
  }
}

// ---------------------------------------------------------------------------
// Publisher dispatch
// ---------------------------------------------------------------------------

const PUBLISHERS: Record<PlatformId, (postId: string, caption?: string, mediaUrls?: string[]) => Promise<PublishResult>> = {
  instagram: publishToInstagram,
  tiktok: publishToTiktok,
  twitter: publishToTwitter,
  facebook: publishToFacebook,
};

// ---------------------------------------------------------------------------
// Route handler
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as PublishRequest;

    // Validate required fields
    if (!body.post_id?.trim()) {
      return NextResponse.json(
        { success: false, error: 'post_id is required' },
        { status: 400 }
      );
    }

    if (!body.platform?.trim()) {
      return NextResponse.json(
        { success: false, error: 'platform is required' },
        { status: 400 }
      );
    }

    const validPlatforms: PlatformId[] = ['instagram', 'tiktok', 'twitter', 'facebook'];
    if (!validPlatforms.includes(body.platform)) {
      return NextResponse.json(
        { success: false, error: `Invalid platform. Must be one of: ${validPlatforms.join(', ')}` },
        { status: 400 }
      );
    }

    const publisher = PUBLISHERS[body.platform];
    const result = await publisher(body.post_id.trim(), body.caption, body.media_urls);

    const statusCode = result.success ? 200 : 502;
    return NextResponse.json(result, { status: statusCode });
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
