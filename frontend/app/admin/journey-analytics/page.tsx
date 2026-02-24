'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Compass,
  Users,
  Trophy,
  Gift,
  TrendingUp,
  Clock,
  MousePointerClick,
  Activity,
  History,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CollectionData {
  name: string;
  slug: string;
  borderColor: string;
  rooms: RoomData[];
  totalExplorers: number;
  avgCompletion: number;
  mostPopularRoom: string;
  hotspotClickRate: number;
  rewardRedemptions: number;
}

interface RoomData {
  name: string;
  collection: string;
  visits: number;
  avgTimeSeconds: number;
  hotspotClicks: number;
  conversionRate: number;
}

interface FunnelStep {
  label: string;
  count: number;
  dropOff: number;
}

interface StatsData {
  totalExplorers: number;
  completionRate: number;
  rewardRedemptions: number;
  conversionUplift: number;
}

interface RealTimeData {
  blackRoseActive: number;
  loveHurtsActive: number;
  signatureActive: number;
  totalActive: number;
}

interface WeeklyTrend {
  week: string;
  explorers: number;
  completions: number;
  conversions: number;
}

// ---------------------------------------------------------------------------
// Simulated Data
// ---------------------------------------------------------------------------

const SIMULATED_STATS: StatsData = {
  totalExplorers: 12_847,
  completionRate: 73.2,
  rewardRedemptions: 4_391,
  conversionUplift: 34.8,
};

const SIMULATED_COLLECTIONS: CollectionData[] = [
  {
    name: 'Black Rose',
    slug: 'black-rose',
    borderColor: '#C0C0C0',
    rooms: [
      { name: 'Cathedral Entrance', collection: 'Black Rose', visits: 4210, avgTimeSeconds: 145, hotspotClicks: 1893, conversionRate: 12.4 },
      { name: 'Rose Garden Hall', collection: 'Black Rose', visits: 3580, avgTimeSeconds: 198, hotspotClicks: 2145, conversionRate: 15.7 },
      { name: 'Stained Glass Gallery', collection: 'Black Rose', visits: 2940, avgTimeSeconds: 167, hotspotClicks: 1420, conversionRate: 11.2 },
      { name: 'Crypt Collection', collection: 'Black Rose', visits: 2150, avgTimeSeconds: 212, hotspotClicks: 1680, conversionRate: 18.3 },
    ],
    totalExplorers: 4210,
    avgCompletion: 78,
    mostPopularRoom: 'Rose Garden Hall',
    hotspotClickRate: 42.3,
    rewardRedemptions: 1847,
  },
  {
    name: 'Love Hurts',
    slug: 'love-hurts',
    borderColor: '#DC143C',
    rooms: [
      { name: 'Castle Gate', collection: 'Love Hurts', visits: 3890, avgTimeSeconds: 132, hotspotClicks: 1567, conversionRate: 10.8 },
      { name: 'Throne Room', collection: 'Love Hurts', visits: 3420, avgTimeSeconds: 224, hotspotClicks: 2310, conversionRate: 19.1 },
      { name: 'Dungeon Vault', collection: 'Love Hurts', visits: 2780, avgTimeSeconds: 189, hotspotClicks: 1890, conversionRate: 16.5 },
      { name: 'Tower Balcony', collection: 'Love Hurts', visits: 2100, avgTimeSeconds: 156, hotspotClicks: 1120, conversionRate: 13.2 },
    ],
    totalExplorers: 3890,
    avgCompletion: 71,
    mostPopularRoom: 'Throne Room',
    hotspotClickRate: 38.7,
    rewardRedemptions: 1342,
  },
  {
    name: 'Signature',
    slug: 'signature',
    borderColor: '#B76E79',
    rooms: [
      { name: 'City Rooftop', collection: 'Signature', visits: 5120, avgTimeSeconds: 178, hotspotClicks: 2890, conversionRate: 14.6 },
      { name: 'Bridge Walkway', collection: 'Signature', visits: 4350, avgTimeSeconds: 201, hotspotClicks: 2450, conversionRate: 17.8 },
      { name: 'Golden Hour Terrace', collection: 'Signature', visits: 3780, avgTimeSeconds: 245, hotspotClicks: 2670, conversionRate: 21.3 },
      { name: 'Skyline Lounge', collection: 'Signature', visits: 2610, avgTimeSeconds: 193, hotspotClicks: 1540, conversionRate: 15.9 },
    ],
    totalExplorers: 5120,
    avgCompletion: 72,
    mostPopularRoom: 'Golden Hour Terrace',
    hotspotClickRate: 45.1,
    rewardRedemptions: 1202,
  },
];

const SIMULATED_FUNNEL: FunnelStep[] = [
  { label: 'Entered Immersive', count: 12_847, dropOff: 0 },
  { label: 'Explored 2+ Rooms', count: 9_402, dropOff: 26.8 },
  { label: 'Viewed Product', count: 6_831, dropOff: 27.3 },
  { label: 'Added to Cart', count: 3_218, dropOff: 52.9 },
  { label: 'Pre-Ordered', count: 1_847, dropOff: 42.6 },
];

const SIMULATED_REALTIME: RealTimeData = {
  blackRoseActive: 47,
  loveHurtsActive: 32,
  signatureActive: 58,
  totalActive: 137,
};

const SIMULATED_WEEKLY: WeeklyTrend[] = [
  { week: 'Feb 3', explorers: 1420, completions: 1038, conversions: 198 },
  { week: 'Feb 10', explorers: 1680, completions: 1210, conversions: 245 },
  { week: 'Feb 17', explorers: 1950, completions: 1430, conversions: 312 },
  { week: 'Feb 24', explorers: 2310, completions: 1720, conversions: 387 },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function JourneyAnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [collections, setCollections] = useState<CollectionData[]>([]);
  const [funnel, setFunnel] = useState<FunnelStep[]>([]);
  const [realTime, setRealTime] = useState<RealTimeData | null>(null);
  const [weekly, setWeekly] = useState<WeeklyTrend[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setStats(SIMULATED_STATS);
      setCollections(SIMULATED_COLLECTIONS);
      setFunnel(SIMULATED_FUNNEL);
      setRealTime(SIMULATED_REALTIME);
      setWeekly(SIMULATED_WEEKLY);
      setLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return <JourneyAnalyticsSkeleton />;
  }

  // Build flat room list for heatmap table, sorted by visits descending
  const allRooms: RoomData[] = collections
    .flatMap((c) => c.rooms)
    .sort((a, b) => b.visits - a.visits);

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
                <Compass className="h-6 w-6 text-white" />
              </div>
              Journey Analytics
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Track immersive experience engagement and conversion impact
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#B76E79] text-[#B76E79]">
              <div className="h-2 w-2 rounded-full mr-2 bg-[#B76E79] animate-pulse" />
              3 Collections Active
            </Badge>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <GradientStatCard
          title="Total Explorers"
          value={formatNumber(stats?.totalExplorers ?? 0)}
          icon={Users}
          gradient="from-[#B76E79] to-rose-600"
        />
        <GradientStatCard
          title="Completion Rate"
          value={`${stats?.completionRate ?? 0}%`}
          icon={Trophy}
          gradient="from-emerald-500 to-teal-500"
        />
        <GradientStatCard
          title="Reward Redemptions"
          value={formatNumber(stats?.rewardRedemptions ?? 0)}
          icon={Gift}
          gradient="from-amber-500 to-orange-500"
        />
        <GradientStatCard
          title="Conversion Uplift"
          value={`+${stats?.conversionUplift ?? 0}%`}
          icon={TrendingUp}
          gradient="from-blue-500 to-cyan-500"
        />
      </div>

      {/* Collection Breakdown Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {collections.map((collection) => (
          <CollectionBreakdownCard key={collection.slug} collection={collection} />
        ))}
      </div>

      {/* Conversion Funnel */}
      <ConversionFunnelCard steps={funnel} />

      {/* Room Heatmap Table */}
      <RoomHeatmapTable rooms={allRooms} />

      {/* Real-Time / Historical Tabs */}
      <Tabs defaultValue="realtime" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="realtime" className="data-[state=active]:bg-gray-700">
            <Activity className="mr-2 h-4 w-4" />
            Real-Time
          </TabsTrigger>
          <TabsTrigger value="historical" className="data-[state=active]:bg-gray-700">
            <History className="mr-2 h-4 w-4" />
            Historical
          </TabsTrigger>
        </TabsList>

        <TabsContent value="realtime">
          <RealTimePanel data={realTime} />
        </TabsContent>

        <TabsContent value="historical">
          <HistoricalPanel trends={weekly} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

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

function CollectionBreakdownCard({ collection }: { collection: CollectionData }) {
  const maxVisits = Math.max(...collection.rooms.map((r) => r.visits));

  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
      <div className="h-1" style={{ backgroundColor: collection.borderColor }} />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white">{collection.name}</CardTitle>
          <Badge
            variant="outline"
            style={{
              borderColor: collection.borderColor,
              color: collection.borderColor,
            }}
          >
            {collection.rooms.length} rooms
          </Badge>
        </div>
        <CardDescription className="text-gray-500">
          {collection.avgCompletion}% avg completion
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-gray-800/50 px-3 py-2">
            <p className="text-xs text-gray-500">Popular Room</p>
            <p className="text-sm font-medium text-white truncate">{collection.mostPopularRoom}</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 px-3 py-2">
            <p className="text-xs text-gray-500">Hotspot CTR</p>
            <p className="text-sm font-medium text-white">{collection.hotspotClickRate}%</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 px-3 py-2">
            <p className="text-xs text-gray-500">Explorers</p>
            <p className="text-sm font-medium text-white">{formatNumber(collection.totalExplorers)}</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 px-3 py-2">
            <p className="text-xs text-gray-500">Rewards</p>
            <p className="text-sm font-medium text-white">{formatNumber(collection.rewardRedemptions)}</p>
          </div>
        </div>

        {/* Room Visit Bar Chart */}
        <div className="space-y-2">
          <p className="text-xs text-gray-500 font-medium">Room Visits</p>
          {collection.rooms.map((room) => (
            <div key={room.name} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400 truncate max-w-[60%]">{room.name}</span>
                <span className="text-gray-300 font-medium">{formatNumber(room.visits)}</span>
              </div>
              <div className="h-2 w-full rounded-full bg-gray-800">
                <div
                  className="h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${(room.visits / maxVisits) * 100}%`,
                    backgroundColor: collection.borderColor,
                    opacity: 0.8,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ConversionFunnelCard({ steps }: { steps: FunnelStep[] }) {
  const maxCount = steps[0]?.count ?? 1;

  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
      <div className="h-1 bg-gradient-to-r from-[#B76E79] to-[#D4AF37]" />
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-[#B76E79]" />
          Conversion Funnel
        </CardTitle>
        <CardDescription className="text-gray-400">
          Immersive experience to pre-order conversion path
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {steps.map((step, index) => {
          const widthPercent = (step.count / maxCount) * 100;
          return (
            <div key={step.label} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="flex items-center justify-center h-6 w-6 rounded-full bg-gray-800 text-xs font-medium text-gray-400">
                    {index + 1}
                  </span>
                  <span className="text-gray-300 font-medium">{step.label}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-white font-bold">{formatNumber(step.count)}</span>
                  {step.dropOff > 0 && (
                    <span className="text-red-400 text-xs">-{step.dropOff}%</span>
                  )}
                </div>
              </div>
              <div className="h-8 w-full rounded-lg bg-gray-800/50 overflow-hidden">
                <div
                  className="h-8 rounded-lg bg-gradient-to-r from-[#B76E79] to-[#D4AF37] transition-all duration-700 flex items-center justify-end pr-3"
                  style={{
                    width: `${Math.max(widthPercent, 8)}%`,
                    opacity: 1 - index * 0.12,
                  }}
                >
                  <span className="text-xs font-medium text-white/90">
                    {widthPercent.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

function RoomHeatmapTable({ rooms }: { rooms: RoomData[] }) {
  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
      <div className="h-1 bg-gradient-to-r from-[#B76E79] to-[#D4AF37]" />
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <MousePointerClick className="h-5 w-5 text-[#D4AF37]" />
          Room Heatmap
        </CardTitle>
        <CardDescription className="text-gray-400">
          All rooms across collections sorted by visit count
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left py-3 px-3 text-gray-500 font-medium">Room Name</th>
                <th className="text-left py-3 px-3 text-gray-500 font-medium">Collection</th>
                <th className="text-right py-3 px-3 text-gray-500 font-medium">Visits</th>
                <th className="text-right py-3 px-3 text-gray-500 font-medium">Avg Time</th>
                <th className="text-right py-3 px-3 text-gray-500 font-medium">Hotspot Clicks</th>
                <th className="text-right py-3 px-3 text-gray-500 font-medium">Conversion Rate</th>
              </tr>
            </thead>
            <tbody>
              {rooms.map((room, index) => {
                const isTopThree = index < 3;
                return (
                  <tr
                    key={`${room.collection}-${room.name}`}
                    className={`border-b border-gray-800/50 transition-colors ${
                      isTopThree
                        ? 'bg-[#B76E79]/5 hover:bg-[#B76E79]/10'
                        : 'hover:bg-gray-800/50'
                    }`}
                  >
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        {isTopThree && (
                          <span className="flex items-center justify-center h-5 w-5 rounded-full bg-[#B76E79]/20 text-[#B76E79] text-xs font-bold">
                            {index + 1}
                          </span>
                        )}
                        <span className={`font-medium ${isTopThree ? 'text-white' : 'text-gray-300'}`}>
                          {room.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <Badge variant="secondary" className="bg-gray-800 text-gray-400 text-xs">
                        {room.collection}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className={`font-medium ${isTopThree ? 'text-white' : 'text-gray-300'}`}>
                        {formatNumber(room.visits)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right text-gray-400">
                      {formatTime(room.avgTimeSeconds)}
                    </td>
                    <td className="py-3 px-3 text-right text-gray-400">
                      {formatNumber(room.hotspotClicks)}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span
                        className={`font-medium ${
                          room.conversionRate >= 18
                            ? 'text-emerald-400'
                            : room.conversionRate >= 14
                            ? 'text-amber-400'
                            : 'text-gray-400'
                        }`}
                      >
                        {room.conversionRate}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function RealTimePanel({ data }: { data: RealTimeData | null }) {
  if (!data) return null;

  const collections = [
    { name: 'Black Rose', active: data.blackRoseActive, color: '#C0C0C0' },
    { name: 'Love Hurts', active: data.loveHurtsActive, color: '#DC143C' },
    { name: 'Signature', active: data.signatureActive, color: '#B76E79' },
  ];

  return (
    <div className="space-y-4">
      {/* Total Active */}
      <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
        <div className="h-1 bg-gradient-to-r from-emerald-500 to-teal-500" />
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Currently Exploring</p>
              <p className="text-4xl font-bold text-white mt-1">{data.totalActive}</p>
              <p className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                <Activity className="h-3 w-3" />
                Live - updates every 30s
              </p>
            </div>
            <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
              <Users className="h-8 w-8 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Per-Collection Active */}
      <div className="grid gap-4 md:grid-cols-3">
        {collections.map((collection) => (
          <Card
            key={collection.name}
            className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm"
          >
            <div className="h-1" style={{ backgroundColor: collection.color }} />
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">{collection.name}</p>
                  <p className="text-2xl font-bold text-white mt-1">{collection.active}</p>
                  <p className="text-xs text-gray-500 mt-1">active explorers</p>
                </div>
                <div
                  className="h-10 w-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${collection.color}20` }}
                >
                  <Activity className="h-5 w-5" style={{ color: collection.color }} />
                </div>
              </div>
              {/* Simple activity indicator bar */}
              <div className="mt-3 h-2 w-full rounded-full bg-gray-800">
                <div
                  className="h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${(collection.active / data.totalActive) * 100}%`,
                    backgroundColor: collection.color,
                  }}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function HistoricalPanel({ trends }: { trends: WeeklyTrend[] }) {
  const maxExplorers = Math.max(...trends.map((t) => t.explorers));

  return (
    <Card className="bg-gray-900/80 border-gray-700 overflow-hidden backdrop-blur-sm">
      <div className="h-1 bg-gradient-to-r from-[#B76E79] to-[#D4AF37]" />
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <History className="h-5 w-5 text-[#D4AF37]" />
          Weekly Trends
        </CardTitle>
        <CardDescription className="text-gray-400">
          Journey engagement metrics over the past 4 weeks
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Column Headers */}
          <div className="grid grid-cols-5 gap-4 text-xs text-gray-500 font-medium pb-2 border-b border-gray-800">
            <span>Week</span>
            <span className="text-right">Explorers</span>
            <span className="text-right">Completions</span>
            <span className="text-right">Conversions</span>
            <span>Distribution</span>
          </div>

          {trends.map((trend) => (
            <div key={trend.week} className="grid grid-cols-5 gap-4 items-center">
              <span className="text-sm text-gray-300 font-medium">{trend.week}</span>
              <span className="text-sm text-white text-right font-medium">
                {formatNumber(trend.explorers)}
              </span>
              <span className="text-sm text-emerald-400 text-right font-medium">
                {formatNumber(trend.completions)}
              </span>
              <span className="text-sm text-[#B76E79] text-right font-medium">
                {formatNumber(trend.conversions)}
              </span>
              <div className="flex items-center gap-1 h-6">
                <div
                  className="h-full rounded-sm bg-white/20 transition-all duration-500"
                  style={{ width: `${(trend.explorers / maxExplorers) * 100}%` }}
                  title={`Explorers: ${trend.explorers}`}
                />
                <div
                  className="h-full rounded-sm bg-emerald-500/40 transition-all duration-500"
                  style={{ width: `${(trend.completions / maxExplorers) * 100}%` }}
                  title={`Completions: ${trend.completions}`}
                />
                <div
                  className="h-full rounded-sm bg-[#B76E79]/60 transition-all duration-500"
                  style={{ width: `${(trend.conversions / maxExplorers) * 100}%` }}
                  title={`Conversions: ${trend.conversions}`}
                />
              </div>
            </div>
          ))}

          {/* Legend */}
          <div className="flex items-center gap-4 pt-3 border-t border-gray-800">
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <div className="h-2.5 w-2.5 rounded-sm bg-white/20" />
              Explorers
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <div className="h-2.5 w-2.5 rounded-sm bg-emerald-500/40" />
              Completions
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <div className="h-2.5 w-2.5 rounded-sm bg-[#B76E79]/60" />
              Conversions
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function JourneyAnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-80 bg-gray-800" />
        ))}
      </div>
      <Skeleton className="h-64 bg-gray-800" />
      <Skeleton className="h-72 bg-gray-800" />
      <Skeleton className="h-48 bg-gray-800" />
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

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}m ${secs}s`;
}
