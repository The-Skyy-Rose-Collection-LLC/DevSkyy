'use client';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Activity,
  Eye,
  MousePointerClick,
  DollarSign,
  TrendingUp,
  Trophy,
  Flame,
  Globe,
} from 'lucide-react';

// SkyyRose brand colors
const BRAND = {
  roseGold: '#B76E79',
  gold: '#D4AF37',
} as const;

// Simulated live metrics (hardcoded until backend tracking is live)
const LIVE_METRICS = [
  {
    label: 'Conversion Lift',
    value: '+14.2%',
    icon: TrendingUp,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/20',
  },
  {
    label: 'Social Proof Views',
    value: '2,847',
    icon: Eye,
    color: 'text-[#B76E79]',
    bgColor: 'bg-[#B76E79]/10',
    borderColor: 'border-[#B76E79]/20',
  },
  {
    label: 'Urgency Clicks',
    value: '423',
    icon: MousePointerClick,
    color: 'text-[#D4AF37]',
    bgColor: 'bg-[#D4AF37]/10',
    borderColor: 'border-[#D4AF37]/20',
  },
  {
    label: 'Revenue Impact',
    value: '+$12,340',
    icon: DollarSign,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/20',
  },
] as const;

// Active Pulse features
const ACTIVE_FEATURES = [
  'Social Proof Toasts',
  'Live Viewer Counts',
  'Scarcity Badges',
  'VIP Countdown',
  'Popularity Heat',
] as const;

// Top performing products by social proof engagement
const TOP_PRODUCTS = [
  { name: 'BLACK Rose Hoodie', proofViews: 89, conversions: 12 },
  { name: 'Love Hurts Varsity Jacket', proofViews: 67, conversions: 8 },
  { name: 'The Bay Set', proofViews: 54, conversions: 6 },
] as const;

// Platform breakdown showing conversion lift per source
const PLATFORM_BREAKDOWN = [
  { name: 'Immersive Pages', lift: '+18.3%', barWidth: 'w-[87%]' },
  { name: 'Collection Pages', lift: '+11.7%', barWidth: 'w-[56%]' },
  { name: 'Pre-Order Gateway', lift: '+21.4%', barWidth: 'w-full' },
] as const;

/**
 * PulseAnalytics - Dashboard widget for "The Pulse" social proof engine.
 *
 * Displays real-time effectiveness metrics for social proof features
 * running on the WordPress storefront. All data is currently simulated
 * (hardcoded) until the backend tracking pipeline is connected.
 */
export function PulseAnalytics() {
  return (
    <Card className="glass overflow-hidden border-rose-500/20 transition-all hover:border-rose-500/40">
      {/* Top accent bar */}
      <div
        className="h-1 opacity-80"
        style={{
          background: `linear-gradient(to right, ${BRAND.roseGold}, ${BRAND.gold}, ${BRAND.roseGold})`,
        }}
      />

      {/* Header */}
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#B76E79]/10">
              <Activity className="h-5 w-5 text-[#B76E79]" />
            </div>
            <div>
              <CardTitle className="text-white font-bold tracking-tight">
                The Pulse
              </CardTitle>
              <CardDescription className="text-gray-400 font-medium">
                Real-Time Social Proof Engine
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-green-500" />
            </span>
            <Badge className="border-green-500/30 bg-green-500/10 text-green-400 text-xs">
              LIVE
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Live Metrics Row */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {LIVE_METRICS.map((metric) => {
            const Icon = metric.icon;
            return (
              <div
                key={metric.label}
                className={`rounded-lg border ${metric.borderColor} ${metric.bgColor} p-3`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${metric.color}`} />
                  <span className="text-xs text-gray-400">{metric.label}</span>
                </div>
                <p className={`mt-1 text-xl font-bold ${metric.color}`}>
                  {metric.value}
                </p>
              </div>
            );
          })}
        </div>

        {/* Active Features Section */}
        <div>
          <h4 className="mb-3 text-sm font-semibold text-gray-300">
            Active Features
          </h4>
          <div className="flex flex-wrap gap-2">
            {ACTIVE_FEATURES.map((feature) => (
              <div
                key={feature}
                className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800/50 px-3 py-1.5"
              >
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
                </span>
                <span className="text-xs font-medium text-gray-300">
                  {feature}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Performing Products */}
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Trophy className="h-4 w-4 text-[#D4AF37]" />
            <h4 className="text-sm font-semibold text-gray-300">
              Top Performing Products
            </h4>
          </div>
          <div className="space-y-2">
            {TOP_PRODUCTS.map((product, index) => (
              <div
                key={product.name}
                className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-800/30 px-3 py-2"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold"
                    style={{
                      backgroundColor:
                        index === 0
                          ? `${BRAND.gold}20`
                          : 'rgba(107, 114, 128, 0.2)',
                      color:
                        index === 0 ? BRAND.gold : 'rgb(156, 163, 175)',
                    }}
                  >
                    {index + 1}
                  </span>
                  <span className="text-sm font-medium text-white">
                    {product.name}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <span className="text-gray-400">
                    <Eye className="mr-1 inline h-3 w-3" />
                    {product.proofViews} views
                  </span>
                  <span className="text-green-400">
                    <Flame className="mr-1 inline h-3 w-3" />
                    {product.conversions} conv
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Platform Breakdown */}
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Globe className="h-4 w-4 text-[#B76E79]" />
            <h4 className="text-sm font-semibold text-gray-300">
              Platform Breakdown
            </h4>
          </div>
          <div className="space-y-3">
            {PLATFORM_BREAKDOWN.map((platform) => (
              <div key={platform.name}>
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-400">
                    {platform.name}
                  </span>
                  <span className="text-xs font-bold text-green-400">
                    {platform.lift} conversion lift
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-gray-800">
                  <div
                    className={`h-2 rounded-full ${platform.barWidth}`}
                    style={{
                      background: `linear-gradient(to right, ${BRAND.roseGold}, ${BRAND.gold})`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-gray-600">
          Simulated data -- live tracking pipeline pending
        </p>
      </CardContent>
    </Card>
  );
}

export default PulseAnalytics;
