'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Share2,
  Send,
  Calendar,
  BarChart3,
  Loader2,
  CheckCircle2,
  Clock,
  Sparkles,
  TrendingUp,
  Eye,
  Heart,
  MessageCircle,
  Repeat2,
  Play,
  Megaphone,
  Hash,
  FileText,
  AlertCircle,
} from 'lucide-react';
import type {
  SocialPost,
  SocialAnalytics,
  Campaign,
} from '@/lib/api/endpoints/social-media';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PLATFORM_CONFIG: Record<
  string,
  { label: string; color: string; bgColor: string; borderColor: string }
> = {
  instagram: {
    label: 'Instagram',
    color: '#E1306C',
    bgColor: 'bg-[#E1306C]/10',
    borderColor: 'border-[#E1306C]/30',
  },
  tiktok: {
    label: 'TikTok',
    color: '#000000',
    bgColor: 'bg-white/10',
    borderColor: 'border-white/20',
  },
  twitter: {
    label: 'X / Twitter',
    color: '#1DA1F2',
    bgColor: 'bg-[#1DA1F2]/10',
    borderColor: 'border-[#1DA1F2]/30',
  },
  facebook: {
    label: 'Facebook',
    color: '#4267B2',
    bgColor: 'bg-[#4267B2]/10',
    borderColor: 'border-[#4267B2]/30',
  },
};

const COLLECTIONS = [
  { value: 'black-rose', label: 'Black Rose' },
  { value: 'love-hurts', label: 'Love Hurts' },
  { value: 'signature', label: 'Signature' },
];

const PRODUCT_SKUS = [
  { value: 'br-001', label: 'BLACK Rose Crewneck', collection: 'black-rose' },
  { value: 'br-002', label: 'BLACK Rose Joggers', collection: 'black-rose' },
  { value: 'br-003', label: 'BLACK is Beautiful Jersey', collection: 'black-rose' },
  { value: 'br-004', label: 'BLACK Rose Hoodie', collection: 'black-rose' },
  { value: 'br-005', label: 'BLACK Rose Hoodie - Signature Ed.', collection: 'black-rose' },
  { value: 'br-006', label: 'BLACK Rose Sherpa Jacket', collection: 'black-rose' },
  { value: 'br-007', label: 'BLACK Rose x Love Hurts Shorts', collection: 'black-rose' },
  { value: 'br-008', label: "Women's BLACK Rose Hooded Dress", collection: 'black-rose' },
  { value: 'lh-001', label: 'The Fannie', collection: 'love-hurts' },
  { value: 'lh-002', label: 'Love Hurts Joggers', collection: 'love-hurts' },
  { value: 'lh-003', label: 'Love Hurts Basketball Shorts', collection: 'love-hurts' },
  { value: 'lh-004', label: 'Love Hurts Varsity Jacket', collection: 'love-hurts' },
  { value: 'sg-001', label: 'The Bay Set', collection: 'signature' },
  { value: 'sg-002', label: 'Stay Golden Set', collection: 'signature' },
  { value: 'sg-003', label: 'The Signature Tee', collection: 'signature' },
  { value: 'sg-005', label: 'Stay Golden Tee', collection: 'signature' },
  { value: 'sg-006', label: 'Mint & Lavender Hoodie', collection: 'signature' },
  { value: 'sg-007', label: 'The Signature Beanie', collection: 'signature' },
  { value: 'sg-009', label: 'The Sherpa Jacket', collection: 'signature' },
  { value: 'sg-010', label: 'The Bridge Series Shorts', collection: 'signature' },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function SocialMediaPage() {
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<SocialAnalytics | null>(null);
  const [queue, setQueue] = useState<SocialPost[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  // Post generator state
  const [selectedSku, setSelectedSku] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState('instagram');
  const [generating, setGenerating] = useState(false);
  const [generatedPost, setGeneratedPost] = useState<SocialPost | null>(null);

  // Campaign generator state
  const [campaignCollection, setCampaignCollection] = useState('black-rose');
  const [campaignName, setCampaignName] = useState('');
  const [generatingCampaign, setGeneratingCampaign] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      // Simulated initial data since the backend API may not be running yet.
      // Replace with real API calls once the backend endpoints are live:
      //   const [analyticsData, queueData] = await Promise.all([
      //     getAnalytics(),
      //     getPostQueue(),
      //   ]);
      const analyticsData: SocialAnalytics = {
        platforms: {
          instagram: { posts: 24, likes: 1840, comments: 312, shares: 89, reach: 14200 },
          tiktok: { posts: 18, views: 52300, likes: 4100, shares: 620 },
          twitter: { posts: 31, likes: 892, retweets: 234, impressions: 28400 },
          facebook: { posts: 12, likes: 456, comments: 78, shares: 34, reach: 8900 },
        },
        total_posts: 85,
        total_queue: 7,
        total_published: 78,
      };
      setAnalytics(analyticsData);
      setQueue([]);
      setError(null);
    } catch (err) {
      setError('Failed to load social media data. Backend may be offline.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleGeneratePost() {
    if (!selectedSku) return;
    setGenerating(true);
    setError(null);

    try {
      // Simulated post generation -- replace with real API call:
      //   const post = await generatePost(selectedSku, selectedPlatform);
      const product = PRODUCT_SKUS.find((p) => p.value === selectedSku);
      const post: SocialPost = {
        id: Math.random().toString(36).slice(2, 14),
        platform: selectedPlatform as SocialPost['platform'],
        content_type: 'product_launch',
        caption: `${product?.label ?? selectedSku} from the SkyyRose ${product?.collection?.replace('-', ' ')} collection. Where Love Meets Luxury.`,
        hashtags: ['#SkyyRose', '#WhereLoveMeetsLuxury', '#LuxuryFashion'],
        media_urls: [],
        product_sku: selectedSku,
        collection: product?.collection ?? '',
        scheduled_at: null,
        published_at: null,
        status: 'draft',
        engagement: {},
      };
      setGeneratedPost(post);
      setQueue((prev) => [post, ...prev]);
    } catch (err) {
      setError('Failed to generate post. Please try again.');
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateCampaign() {
    if (!campaignCollection || !campaignName.trim()) return;
    setGeneratingCampaign(true);
    setError(null);

    try {
      // Simulated campaign generation -- replace with real API call:
      //   const campaign = await generateCampaign(campaignCollection, campaignName);
      const collectionProducts = PRODUCT_SKUS.filter(
        (p) => p.collection === campaignCollection
      );
      const campaignPosts: SocialPost[] = [];
      for (const product of collectionProducts.slice(0, 3)) {
        for (const platform of ['instagram', 'tiktok', 'twitter', 'facebook'] as const) {
          campaignPosts.push({
            id: Math.random().toString(36).slice(2, 14),
            platform,
            content_type: 'collection_drop',
            caption: `${product.label} -- ${campaignName}`,
            hashtags: ['#SkyyRose', '#WhereLoveMeetsLuxury'],
            media_urls: [],
            product_sku: product.value,
            collection: campaignCollection,
            scheduled_at: null,
            published_at: null,
            status: 'draft',
            engagement: {},
          });
        }
      }

      const campaign: Campaign = {
        id: Math.random().toString(36).slice(2, 14),
        name: campaignName,
        collection: campaignCollection,
        posts: campaignPosts,
        created_at: new Date().toISOString(),
        status: 'draft',
      };
      setCampaigns((prev) => [campaign, ...prev]);
      setQueue((prev) => [...campaignPosts, ...prev]);
      setCampaignName('');
    } catch (err) {
      setError('Failed to generate campaign. Please try again.');
    } finally {
      setGeneratingCampaign(false);
    }
  }

  if (loading) {
    return <SocialMediaSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#B76E79]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#D4AF37]/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[#B76E79] to-[#D4AF37] flex items-center justify-center">
                <Megaphone className="h-6 w-6 text-white" />
              </div>
              Social Media Command Center
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Generate, schedule, and track content across Instagram, TikTok, X, and Facebook
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#B76E79] text-[#B76E79]">
              <div className="h-2 w-2 rounded-full mr-2 bg-[#B76E79] animate-pulse" />
              SkyyRose Brand
            </Badge>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto text-red-400 hover:text-red-300"
            onClick={() => setError(null)}
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Platform Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        {Object.entries(PLATFORM_CONFIG).map(([key, config]) => {
          const stats = analytics?.platforms[key];
          return (
            <PlatformStatCard
              key={key}
              platform={config.label}
              color={config.color}
              bgColor={config.bgColor}
              posts={stats?.posts ?? 0}
              engagement={
                (stats?.likes ?? 0) +
                (stats?.comments ?? 0) +
                (stats?.shares ?? 0) +
                (stats?.retweets ?? 0)
              }
              reach={stats?.reach ?? stats?.impressions ?? stats?.views ?? 0}
            />
          );
        })}
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <GradientStatCard
          title="Total Posts"
          value={analytics?.total_posts ?? 0}
          icon={FileText}
          gradient="from-[#B76E79] to-[#D4AF37]"
        />
        <GradientStatCard
          title="In Queue"
          value={queue.length}
          icon={Clock}
          gradient="from-amber-500 to-orange-500"
        />
        <GradientStatCard
          title="Published"
          value={analytics?.total_published ?? 0}
          icon={CheckCircle2}
          gradient="from-emerald-500 to-teal-500"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="generate" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="generate" className="data-[state=active]:bg-gray-700">
            <Sparkles className="mr-2 h-4 w-4" />
            Generate
          </TabsTrigger>
          <TabsTrigger value="queue" className="data-[state=active]:bg-gray-700">
            <Calendar className="mr-2 h-4 w-4" />
            Queue ({queue.length})
          </TabsTrigger>
          <TabsTrigger value="campaigns" className="data-[state=active]:bg-gray-700">
            <Megaphone className="mr-2 h-4 w-4" />
            Campaigns
          </TabsTrigger>
          <TabsTrigger value="analytics" className="data-[state=active]:bg-gray-700">
            <BarChart3 className="mr-2 h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Generate Tab */}
        <TabsContent value="generate" className="space-y-6">
          {/* Quick Post Generator */}
          <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-[#B76E79]" />
                Quick Post Generator
              </CardTitle>
              <CardDescription className="text-gray-400">
                Generate platform-optimized captions from product data with SkyyRose brand voice
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label className="text-gray-300">Product</Label>
                  <select
                    value={selectedSku}
                    onChange={(e) => setSelectedSku(e.target.value)}
                    className="w-full h-10 rounded-md bg-gray-800 border border-gray-700 text-white px-3"
                  >
                    <option value="">Select a product...</option>
                    <optgroup label="Black Rose Collection">
                      {PRODUCT_SKUS.filter((p) => p.collection === 'black-rose').map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="Love Hurts Collection">
                      {PRODUCT_SKUS.filter((p) => p.collection === 'love-hurts').map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="Signature Collection">
                      {PRODUCT_SKUS.filter((p) => p.collection === 'signature').map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-300">Platform</Label>
                  <div className="flex gap-2">
                    {Object.entries(PLATFORM_CONFIG).map(([key, config]) => (
                      <Button
                        key={key}
                        variant={selectedPlatform === key ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedPlatform(key)}
                        className={
                          selectedPlatform === key
                            ? 'text-white'
                            : 'border-gray-700 text-gray-400'
                        }
                        style={
                          selectedPlatform === key
                            ? { backgroundColor: config.color }
                            : undefined
                        }
                      >
                        {config.label}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>

              <Button
                onClick={handleGeneratePost}
                disabled={generating || !selectedSku}
                className="w-full bg-gradient-to-r from-[#B76E79] via-[#B76E79] to-[#D4AF37] hover:from-[#a5606a] hover:to-[#c4a030] h-12 text-lg text-white"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-5 w-5" />
                    Generate Post
                  </>
                )}
              </Button>

              {/* Generated Post Preview */}
              {generatedPost && (
                <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-white">Generated Post Preview</h3>
                    <Badge
                      variant="outline"
                      style={{
                        borderColor: PLATFORM_CONFIG[generatedPost.platform]?.color,
                        color: PLATFORM_CONFIG[generatedPost.platform]?.color,
                      }}
                    >
                      {PLATFORM_CONFIG[generatedPost.platform]?.label}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {generatedPost.caption}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {generatedPost.hashtags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center text-xs text-[#B76E79] bg-[#B76E79]/10 px-2 py-0.5 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button size="sm" variant="outline" className="border-gray-700 text-gray-300">
                      <Calendar className="mr-1 h-3 w-3" />
                      Schedule
                    </Button>
                    <Button
                      size="sm"
                      className="bg-[#B76E79] hover:bg-[#a5606a] text-white"
                    >
                      <Send className="mr-1 h-3 w-3" />
                      Publish Now
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Campaign Generator */}
          <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Megaphone className="h-5 w-5 text-[#D4AF37]" />
                Campaign Generator
              </CardTitle>
              <CardDescription className="text-gray-400">
                Generate a multi-platform campaign for an entire collection
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label className="text-gray-300">Collection</Label>
                  <select
                    value={campaignCollection}
                    onChange={(e) => setCampaignCollection(e.target.value)}
                    className="w-full h-10 rounded-md bg-gray-800 border border-gray-700 text-white px-3"
                  >
                    {COLLECTIONS.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-300">Campaign Name</Label>
                  <Input
                    placeholder="e.g. Spring 2026 Drop"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                  />
                </div>
              </div>
              <Button
                onClick={handleGenerateCampaign}
                disabled={generatingCampaign || !campaignName.trim()}
                className="w-full bg-gradient-to-r from-[#D4AF37] to-[#B76E79] hover:from-[#c4a030] hover:to-[#a5606a] h-12 text-lg text-white"
              >
                {generatingCampaign ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Generating Campaign...
                  </>
                ) : (
                  <>
                    <Megaphone className="mr-2 h-5 w-5" />
                    Generate Campaign ({PRODUCT_SKUS.filter((p) => p.collection === campaignCollection).length} products x 4 platforms)
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Queue Tab */}
        <TabsContent value="queue">
          {queue.length === 0 ? (
            <Card className="bg-gray-900 border-gray-800 py-12">
              <CardContent className="text-center">
                <Calendar className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500">No posts in queue</p>
                <p className="text-gray-600 text-sm mt-1">
                  Generate posts from the Generate tab to get started
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {queue.map((post) => (
                <QueueItem key={post.id} post={post} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Campaigns Tab */}
        <TabsContent value="campaigns">
          {campaigns.length === 0 ? (
            <Card className="bg-gray-900 border-gray-800 py-12">
              <CardContent className="text-center">
                <Megaphone className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500">No campaigns yet</p>
                <p className="text-gray-600 text-sm mt-1">
                  Use the Campaign Generator to create multi-platform campaigns
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {campaigns.map((campaign) => (
                <CampaignCard key={campaign.id} campaign={campaign} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics">
          <div className="grid gap-4 md:grid-cols-2">
            {Object.entries(PLATFORM_CONFIG).map(([key, config]) => {
              const stats = analytics?.platforms[key];
              if (!stats) return null;
              return (
                <AnalyticsCard
                  key={key}
                  platform={config.label}
                  color={config.color}
                  stats={stats}
                />
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PlatformStatCard({
  platform,
  color,
  bgColor,
  posts,
  engagement,
  reach,
}: {
  platform: string;
  color: string;
  bgColor: string;
  posts: number;
  engagement: number;
  reach: number;
}) {
  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
      <div className="h-1" style={{ backgroundColor: color }} />
      <CardContent className="pt-5 pb-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-white">{platform}</span>
          <div
            className={`h-8 w-8 rounded-lg ${bgColor} flex items-center justify-center`}
          >
            <Share2 className="h-4 w-4" style={{ color }} />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-lg font-bold text-white">{posts}</p>
            <p className="text-xs text-gray-500">Posts</p>
          </div>
          <div>
            <p className="text-lg font-bold text-white">{formatNumber(engagement)}</p>
            <p className="text-xs text-gray-500">Engage</p>
          </div>
          <div>
            <p className="text-lg font-bold text-white">{formatNumber(reach)}</p>
            <p className="text-xs text-gray-500">Reach</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GradientStatCard({
  title,
  value,
  icon: Icon,
  gradient,
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  gradient: string;
}) {
  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
      <div className={`h-1 bg-gradient-to-r ${gradient}`} />
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">{title}</p>
            <p className="text-2xl font-bold text-white mt-1">{value}</p>
          </div>
          <div
            className={`h-12 w-12 rounded-xl bg-gradient-to-br ${gradient} bg-opacity-10 flex items-center justify-center`}
          >
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function QueueItem({ post }: { post: SocialPost }) {
  const config = PLATFORM_CONFIG[post.platform];
  const statusStyles: Record<string, string> = {
    draft: 'border-gray-500 text-gray-400',
    scheduled: 'border-amber-500 text-amber-400',
    published: 'border-green-500 text-green-400',
    failed: 'border-red-500 text-red-400',
  };

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <div className="h-1" style={{ backgroundColor: config?.color ?? '#666' }} />
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div
            className={`h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0 ${config?.bgColor ?? 'bg-gray-800'}`}
          >
            <Hash className="h-5 w-5" style={{ color: config?.color ?? '#999' }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-sm font-medium text-white truncate">
                {config?.label ?? post.platform} - {post.product_sku}
              </span>
              <Badge variant="outline" className={statusStyles[post.status]}>
                {post.status}
              </Badge>
            </div>
            <p className="text-xs text-gray-400 line-clamp-2">{post.caption}</p>
            {post.scheduled_at && (
              <p className="text-xs text-amber-400 mt-1 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Scheduled: {new Date(post.scheduled_at).toLocaleString()}
              </p>
            )}
          </div>
          <div className="flex gap-1 flex-shrink-0">
            <Button size="sm" variant="ghost" className="text-gray-400 hover:text-white h-8 w-8 p-0">
              <Calendar className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" className="text-[#B76E79] hover:text-[#d4919c] h-8 w-8 p-0">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function CampaignCard({ campaign }: { campaign: Campaign }) {
  const collection = COLLECTIONS.find((c) => c.value === campaign.collection);
  const platformCounts = campaign.posts.reduce(
    (acc, post) => {
      acc[post.platform] = (acc[post.platform] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <div className="h-1 bg-gradient-to-r from-[#B76E79] to-[#D4AF37]" />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white">{campaign.name}</CardTitle>
          <Badge variant="outline" className="border-[#D4AF37] text-[#D4AF37]">
            {campaign.status}
          </Badge>
        </div>
        <CardDescription className="text-gray-500">
          {collection?.label ?? campaign.collection} Collection - {campaign.posts.length} posts
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2 mb-3">
          {Object.entries(platformCounts).map(([platform, count]) => {
            const config = PLATFORM_CONFIG[platform];
            return (
              <Badge
                key={platform}
                variant="secondary"
                className="bg-gray-800 text-gray-300 text-xs"
              >
                <span
                  className="h-2 w-2 rounded-full mr-1 inline-block"
                  style={{ backgroundColor: config?.color }}
                />
                {config?.label}: {count}
              </Badge>
            );
          })}
        </div>
        <p className="text-xs text-gray-500">
          Created: {new Date(campaign.created_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  );
}

function AnalyticsCard({
  platform,
  color,
  stats,
}: {
  platform: string;
  color: string;
  stats: Record<string, number | undefined>;
}) {
  const metrics = Object.entries(stats).filter(
    ([, val]) => val !== undefined && val !== null
  );

  const metricIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    posts: FileText,
    likes: Heart,
    comments: MessageCircle,
    shares: Share2,
    reach: Eye,
    views: Eye,
    retweets: Repeat2,
    impressions: TrendingUp,
  };

  return (
    <Card className="bg-gray-900 border-gray-800 overflow-hidden">
      <div className="h-1" style={{ backgroundColor: color }} />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white">{platform}</CardTitle>
          <div
            className="h-8 w-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${color}20` }}
          >
            <BarChart3 className="h-4 w-4" style={{ color }} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {metrics.map(([key, value]) => {
            const Icon = metricIcons[key] ?? TrendingUp;
            return (
              <div
                key={key}
                className="flex items-center gap-2 rounded-lg bg-gray-800/50 px-3 py-2"
              >
                <Icon className="h-4 w-4 text-gray-500 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-white">{formatNumber(value ?? 0)}</p>
                  <p className="text-xs text-gray-500 capitalize">{key}</p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function SocialMediaSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-28 bg-gray-800" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-64 bg-gray-800" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}
