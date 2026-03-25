/**
 * Social Media Pipeline - Analytics Route
 *
 * GET /api/social-media/analytics
 *   Query params:
 *     ?dry_run=true  - Always returns simulated data
 *   Returns: SocialAnalytics with per-platform metrics
 *
 * When platform API keys are present, fetches real metrics.
 * When keys are missing, returns realistic simulated data with a flag.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getPlatformConnection, getPlatformToken, type PlatformId } from '@/lib/social-media/config';

// ---------------------------------------------------------------------------
// Types (mirrors lib/api/endpoints/social-media.ts)
// ---------------------------------------------------------------------------

interface PlatformAnalytics {
  posts: number;
  likes: number;
  comments?: number;
  shares: number;
  reach?: number;
  views?: number;
  retweets?: number;
  impressions?: number;
}

interface AnalyticsResponse {
  success: boolean;
  simulated: boolean;
  timestamp: string;
  platforms: Record<string, PlatformAnalytics & { simulated: boolean }>;
  total_posts: number;
  total_queue: number;
  total_published: number;
}

// ---------------------------------------------------------------------------
// Simulated analytics (realistic baseline data)
// ---------------------------------------------------------------------------

function getSimulatedAnalytics(): Record<string, PlatformAnalytics & { simulated: boolean }> {
  return {
    instagram: {
      posts: 24,
      likes: 1840,
      comments: 312,
      shares: 89,
      reach: 14200,
      simulated: true,
    },
    tiktok: {
      posts: 18,
      likes: 4100,
      shares: 620,
      views: 52300,
      simulated: true,
    },
    twitter: {
      posts: 31,
      likes: 892,
      shares: 234,
      retweets: 234,
      impressions: 28400,
      simulated: true,
    },
    facebook: {
      posts: 12,
      likes: 456,
      comments: 78,
      shares: 34,
      reach: 8900,
      simulated: true,
    },
  };
}

// ---------------------------------------------------------------------------
// Real platform analytics fetchers
// ---------------------------------------------------------------------------

async function fetchInstagramAnalytics(): Promise<PlatformAnalytics & { simulated: boolean }> {
  const connection = getPlatformConnection('instagram');
  if (!connection.connected) {
    return { ...getSimulatedAnalytics().instagram };
  }

  const token = getPlatformToken('instagram');
  const accountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;

  try {
    // Fetch account insights
    const insightsRes = await fetch(
      `https://graph.facebook.com/v19.0/${accountId}/insights?metric=impressions,reach,profile_views&period=day&access_token=${token}`
    );

    // Fetch media for engagement counts
    const mediaRes = await fetch(
      `https://graph.facebook.com/v19.0/${accountId}/media?fields=like_count,comments_count,shares&limit=50&access_token=${token}`
    );

    if (!insightsRes.ok || !mediaRes.ok) {
      return { ...getSimulatedAnalytics().instagram };
    }

    const mediaData = (await mediaRes.json()) as {
      data: Array<{ like_count?: number; comments_count?: number; shares?: number }>;
    };

    let totalLikes = 0;
    let totalComments = 0;
    let totalShares = 0;
    for (const post of mediaData.data ?? []) {
      totalLikes += post.like_count ?? 0;
      totalComments += post.comments_count ?? 0;
      totalShares += post.shares ?? 0;
    }

    const insightsData = (await insightsRes.json()) as {
      data: Array<{ name: string; values: Array<{ value: number }> }>;
    };
    const reachMetric = insightsData.data?.find((m) => m.name === 'reach');
    const reach = reachMetric?.values?.[0]?.value ?? 0;

    return {
      posts: mediaData.data?.length ?? 0,
      likes: totalLikes,
      comments: totalComments,
      shares: totalShares,
      reach,
      simulated: false,
    };
  } catch {
    return { ...getSimulatedAnalytics().instagram };
  }
}

async function fetchTiktokAnalytics(): Promise<PlatformAnalytics & { simulated: boolean }> {
  const connection = getPlatformConnection('tiktok');
  if (!connection.connected) {
    return { ...getSimulatedAnalytics().tiktok };
  }

  const token = getPlatformToken('tiktok');

  try {
    const res = await fetch('https://open.tiktokapis.com/v2/video/list/?fields=like_count,share_count,view_count,comment_count', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ max_count: 50 }),
    });

    if (!res.ok) {
      return { ...getSimulatedAnalytics().tiktok };
    }

    const data = (await res.json()) as {
      data?: {
        videos?: Array<{
          like_count?: number;
          share_count?: number;
          view_count?: number;
          comment_count?: number;
        }>;
      };
    };

    const videos = data.data?.videos ?? [];
    let likes = 0;
    let shares = 0;
    let views = 0;

    for (const video of videos) {
      likes += video.like_count ?? 0;
      shares += video.share_count ?? 0;
      views += video.view_count ?? 0;
    }

    return {
      posts: videos.length,
      likes,
      shares,
      views,
      simulated: false,
    };
  } catch {
    return { ...getSimulatedAnalytics().tiktok };
  }
}

async function fetchTwitterAnalytics(): Promise<PlatformAnalytics & { simulated: boolean }> {
  const connection = getPlatformConnection('twitter');
  if (!connection.connected) {
    return { ...getSimulatedAnalytics().twitter };
  }

  try {
    // Twitter v2 API -- get user tweets with public metrics
    const apiKey = process.env.TWITTER_API_KEY!;
    const apiSecret = process.env.TWITTER_API_SECRET!;

    // Get bearer token
    const credentials = Buffer.from(`${apiKey}:${apiSecret}`).toString('base64');
    const tokenRes = await fetch('https://api.twitter.com/oauth2/token', {
      method: 'POST',
      headers: {
        Authorization: `Basic ${credentials}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'grant_type=client_credentials',
    });

    if (!tokenRes.ok) {
      return { ...getSimulatedAnalytics().twitter };
    }

    const tokenData = (await tokenRes.json()) as { access_token: string };

    // Get user's tweets with metrics
    // Note: requires the user ID -- in production, this would be configured
    const userId = process.env.TWITTER_USER_ID;
    if (!userId) {
      return { ...getSimulatedAnalytics().twitter };
    }

    const tweetsRes = await fetch(
      `https://api.twitter.com/2/users/${userId}/tweets?max_results=50&tweet.fields=public_metrics`,
      {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
      }
    );

    if (!tweetsRes.ok) {
      return { ...getSimulatedAnalytics().twitter };
    }

    const tweetsData = (await tweetsRes.json()) as {
      data?: Array<{
        public_metrics?: {
          like_count?: number;
          retweet_count?: number;
          reply_count?: number;
          impression_count?: number;
        };
      }>;
    };

    const tweets = tweetsData.data ?? [];
    let likes = 0;
    let retweets = 0;
    let impressions = 0;

    for (const tweet of tweets) {
      const m = tweet.public_metrics;
      likes += m?.like_count ?? 0;
      retweets += m?.retweet_count ?? 0;
      impressions += m?.impression_count ?? 0;
    }

    return {
      posts: tweets.length,
      likes,
      shares: retweets,
      retweets,
      impressions,
      simulated: false,
    };
  } catch {
    return { ...getSimulatedAnalytics().twitter };
  }
}

async function fetchFacebookAnalytics(): Promise<PlatformAnalytics & { simulated: boolean }> {
  const connection = getPlatformConnection('facebook');
  if (!connection.connected) {
    return { ...getSimulatedAnalytics().facebook };
  }

  const token = getPlatformToken('facebook');
  const pageId = process.env.FACEBOOK_PAGE_ID;

  try {
    const res = await fetch(
      `https://graph.facebook.com/v19.0/${pageId}/posts?fields=likes.summary(true),comments.summary(true),shares&limit=50&access_token=${token}`
    );

    if (!res.ok) {
      return { ...getSimulatedAnalytics().facebook };
    }

    const data = (await res.json()) as {
      data?: Array<{
        likes?: { summary?: { total_count?: number } };
        comments?: { summary?: { total_count?: number } };
        shares?: { count?: number };
      }>;
    };

    const posts = data.data ?? [];
    let likes = 0;
    let comments = 0;
    let shares = 0;

    for (const post of posts) {
      likes += post.likes?.summary?.total_count ?? 0;
      comments += post.comments?.summary?.total_count ?? 0;
      shares += post.shares?.count ?? 0;
    }

    // Fetch page insights for reach
    const insightsRes = await fetch(
      `https://graph.facebook.com/v19.0/${pageId}/insights?metric=page_impressions_unique&period=days_28&access_token=${token}`
    );

    let reach = 0;
    if (insightsRes.ok) {
      const insightsData = (await insightsRes.json()) as {
        data?: Array<{ values?: Array<{ value?: number }> }>;
      };
      reach = insightsData.data?.[0]?.values?.[0]?.value ?? 0;
    }

    return {
      posts: posts.length,
      likes,
      comments,
      shares,
      reach,
      simulated: false,
    };
  } catch {
    return { ...getSimulatedAnalytics().facebook };
  }
}

// ---------------------------------------------------------------------------
// Route handler
// ---------------------------------------------------------------------------

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = request.nextUrl;
    const dryRun = searchParams.get('dry_run') === 'true';

    let platforms: Record<string, PlatformAnalytics & { simulated: boolean }>;
    let allSimulated: boolean;

    if (dryRun) {
      platforms = getSimulatedAnalytics();
      allSimulated = true;
    } else {
      // Fetch all platforms in parallel
      const [instagram, tiktok, twitter, facebook] = await Promise.all([
        fetchInstagramAnalytics(),
        fetchTiktokAnalytics(),
        fetchTwitterAnalytics(),
        fetchFacebookAnalytics(),
      ]);

      platforms = { instagram, tiktok, twitter, facebook };
      allSimulated = Object.values(platforms).every((p) => p.simulated);
    }

    // Calculate totals
    let totalPosts = 0;
    let totalPublished = 0;
    for (const p of Object.values(platforms)) {
      totalPosts += p.posts;
      totalPublished += p.posts; // All fetched posts are published
    }

    const response: AnalyticsResponse = {
      success: true,
      simulated: allSimulated,
      timestamp: new Date().toISOString(),
      platforms,
      total_posts: totalPosts,
      total_queue: 0, // Queue is tracked separately in the schedule route
      total_published: totalPublished,
    };

    return NextResponse.json(response);
  } catch {
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
