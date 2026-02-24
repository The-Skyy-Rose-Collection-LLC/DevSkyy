/**
 * Social Media Pipeline API Endpoints
 *
 * Manages social media content generation, scheduling,
 * and analytics for the SkyyRose platform.
 */

import { ApiError } from '../errors';
import { API_URL } from '../config';
import { getAuthHeaders, fetchWithTimeout } from '../client';

export interface SocialPost {
  id: string;
  platform: 'instagram' | 'tiktok' | 'twitter' | 'facebook';
  content_type: string;
  caption: string;
  hashtags: string[];
  media_urls: string[];
  product_sku: string;
  collection: string;
  scheduled_at: string | null;
  published_at: string | null;
  status: 'draft' | 'scheduled' | 'published' | 'failed';
  engagement: Record<string, number>;
}

export interface PlatformAnalytics {
  posts: number;
  likes: number;
  comments?: number;
  shares: number;
  reach?: number;
  views?: number;
  retweets?: number;
  impressions?: number;
}

export interface SocialAnalytics {
  platforms: Record<string, PlatformAnalytics>;
  total_posts: number;
  total_queue: number;
  total_published: number;
}

export interface Campaign {
  id: string;
  name: string;
  collection: string;
  posts: SocialPost[];
  created_at: string;
  status: 'draft' | 'active' | 'completed';
}

/**
 * Generate a social media post for a product
 */
export async function generatePost(
  productSku: string,
  platform: string,
  contentType: string = 'product_launch'
): Promise<SocialPost> {
  if (!productSku?.trim()) {
    throw new ApiError('Product SKU is required', 400, 'INVALID_INPUT');
  }
  if (!platform?.trim()) {
    throw new ApiError('Platform is required', 400, 'INVALID_INPUT');
  }

  const res = await fetchWithTimeout(`${API_URL}/api/v1/social-media/generate`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify({
      product_sku: productSku.trim(),
      platform: platform.trim(),
      content_type: contentType,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw ApiError.fromResponse(res.status, body);
  }
  return res.json();
}

/**
 * Schedule a post for publishing
 */
export async function schedulePost(
  postId: string,
  scheduledAt: string
): Promise<{ success: boolean }> {
  if (!postId?.trim()) {
    throw new ApiError('Post ID is required', 400, 'INVALID_INPUT');
  }

  const res = await fetchWithTimeout(`${API_URL}/api/v1/social-media/schedule`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify({
      post_id: postId.trim(),
      scheduled_at: scheduledAt,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw ApiError.fromResponse(res.status, body);
  }
  return res.json();
}

/**
 * Get the post queue
 */
export async function getPostQueue(): Promise<SocialPost[]> {
  const res = await fetchWithTimeout(`${API_URL}/api/v1/social-media/queue`, {
    headers: await getAuthHeaders(),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw ApiError.fromResponse(res.status, body);
  }
  return res.json();
}

/**
 * Get analytics across all platforms
 */
export async function getAnalytics(): Promise<SocialAnalytics> {
  const res = await fetchWithTimeout(`${API_URL}/api/v1/social-media/analytics`, {
    headers: await getAuthHeaders(),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw ApiError.fromResponse(res.status, body);
  }
  return res.json();
}

/**
 * Generate a multi-platform campaign for a collection
 */
export async function generateCampaign(
  collection: string,
  campaignName: string
): Promise<Campaign> {
  if (!collection?.trim()) {
    throw new ApiError('Collection is required', 400, 'INVALID_INPUT');
  }
  if (!campaignName?.trim()) {
    throw new ApiError('Campaign name is required', 400, 'INVALID_INPUT');
  }

  const res = await fetchWithTimeout(`${API_URL}/api/v1/social-media/campaign`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify({
      collection: collection.trim(),
      campaign_name: campaignName.trim(),
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw ApiError.fromResponse(res.status, body);
  }
  return res.json();
}

/**
 * Publish a post
 */
export async function publishPost(postId: string): Promise<{ success: boolean }> {
  if (!postId?.trim()) {
    throw new ApiError('Post ID is required', 400, 'INVALID_INPUT');
  }

  const res = await fetchWithTimeout(`${API_URL}/api/v1/social-media/publish`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify({ post_id: postId.trim() }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw ApiError.fromResponse(res.status, body);
  }
  return res.json();
}

/**
 * Bundled social media API namespace
 */
export const socialMedia = {
  generatePost,
  schedulePost,
  getPostQueue,
  getAnalytics,
  generateCampaign,
  publishPost,
};
