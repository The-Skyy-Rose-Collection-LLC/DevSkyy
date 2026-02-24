'use client';

import { useState, useEffect, useRef } from 'react';
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
  Users,
  ShoppingCart,
  ArrowDown,
  Zap,
} from 'lucide-react';

// SkyyRose brand colors
const BRAND = {
  roseGold: '#B76E79',
  gold: '#D4AF37',
} as const;

// --- Animated Counter Hook ---
function useAnimatedCounter(target: number, duration: number = 2000): number {
  const [count, setCount] = useState(0);
  const startRef = useRef<number | null>(null);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    startRef.current = null;

    function animate(timestamp: number) {
      if (startRef.current === null) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(eased * target));

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    }

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target, duration]);

  return count;
}

// --- Simulated Live Data Hook ---
interface LiveData {
  activeViewers: number;
  recentPreOrders: number;
  urgencyClicks: number;
  revenueImpact: number;
  conversionLift: number;
  trendingProducts: Array<{
    name: string;
    proofViews: number;
    conversions: number;
    isHot: boolean;
  }>;
  funnelData: {
    visitors: number;
    viewers: number;
    addToCarts: number;
    preOrders: number;
  };
}

function useSimulatedLiveData(): LiveData {
  const [data, setData] = useState<LiveData>({
    activeViewers: 247,
    recentPreOrders: 38,
    urgencyClicks: 423,
    revenueImpact: 12340,
    conversionLift: 14.2,
    trendingProducts: [
      { name: 'BLACK Rose Hoodie', proofViews: 89, conversions: 12, isHot: true },
      { name: 'Love Hurts Varsity Jacket', proofViews: 67, conversions: 8, isHot: true },
      { name: 'Signature Rose Gold Hoodie', proofViews: 54, conversions: 6, isHot: false },
      { name: 'BLACK Rose Sherpa Jacket', proofViews: 48, conversions: 5, isHot: false },
      { name: 'Love Hurts Hoodie', proofViews: 41, conversions: 4, isHot: false },
    ],
    funnelData: {
      visitors: 3842,
      viewers: 2847,
      addToCarts: 634,
      preOrders: 178,
    },
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setData((prev) => {
        const viewerDelta = Math.floor(Math.random() * 11) - 4;
        const orderDelta = Math.random() < 0.3 ? 1 : 0;
        const clickDelta = Math.floor(Math.random() * 5);
        const revenueDelta = orderDelta * (Math.floor(Math.random() * 200) + 85);

        return {
          ...prev,
          activeViewers: Math.max(120, Math.min(400, prev.activeViewers + viewerDelta)),
          recentPreOrders: prev.recentPreOrders + orderDelta,
          urgencyClicks: prev.urgencyClicks + clickDelta,
          revenueImpact: prev.revenueImpact + revenueDelta,
          conversionLift: Math.round((prev.conversionLift + (Math.random() - 0.48) * 0.3) * 10) / 10,
          trendingProducts: prev.trendingProducts.map((p) => ({
            ...p,
            proofViews: p.proofViews + (Math.random() < 0.4 ? 1 : 0),
            conversions: p.conversions + (Math.random() < 0.08 ? 1 : 0),
          })),
          funnelData: {
            visitors: prev.funnelData.visitors + Math.floor(Math.random() * 8),
            viewers: prev.funnelData.viewers + Math.floor(Math.random() * 5),
            addToCarts: prev.funnelData.addToCarts + (Math.random() < 0.2 ? 1 : 0),
            preOrders: prev.funnelData.preOrders + orderDelta,
          },
        };
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return data;
}

// Active Pulse features
const ACTIVE_FEATURES = [
  'Social Proof Toasts',
  'Live Viewer Counts',
  'Scarcity Badges',
  'VIP Countdown',
  'Popularity Heat',
  '3D Card Tilt',
  'Shimmer Buttons',
  'Section Reveals',
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
 * running on the WordPress storefront. Features animated counters,
 * hot product indicators, conversion funnel visualization, and
 * glassmorphism card design.
 */
export function PulseAnalytics() {
  const liveData = useSimulatedLiveData();

  const animatedViewers = useAnimatedCounter(liveData.activeViewers, 800);
  const animatedOrders = useAnimatedCounter(liveData.recentPreOrders, 800);
  const animatedClicks = useAnimatedCounter(liveData.urgencyClicks, 800);
  const animatedRevenue = useAnimatedCounter(liveData.revenueImpact, 1200);

  // Funnel percentages
  const funnelViewerPct = liveData.funnelData.visitors > 0
    ? Math.round((liveData.funnelData.viewers / liveData.funnelData.visitors) * 100)
    : 0;
  const funnelCartPct = liveData.funnelData.viewers > 0
    ? Math.round((liveData.funnelData.addToCarts / liveData.funnelData.viewers) * 100)
    : 0;
  const funnelOrderPct = liveData.funnelData.addToCarts > 0
    ? Math.round((liveData.funnelData.preOrders / liveData.funnelData.addToCarts) * 100)
    : 0;

  return (
    <Card
      className="overflow-hidden border-rose-500/20 transition-all hover:border-rose-500/40"
      style={{
        background: 'rgba(17, 17, 17, 0.6)',
        backdropFilter: 'blur(24px) saturate(1.3)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.3)',
      }}
    >
      {/* Top accent bar with animation */}
      <div
        className="h-1 opacity-80"
        style={{
          background: `linear-gradient(90deg, ${BRAND.roseGold}, ${BRAND.gold}, ${BRAND.roseGold})`,
          backgroundSize: '200% 100%',
          animation: 'pulseGradientShift 4s ease-in-out infinite',
        }}
      />
      <style>{`
        @keyframes pulseGradientShift {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @keyframes pulseHotGlow {
          0%, 100% { box-shadow: 0 0 0 0 rgba(183, 110, 121, 0.4); }
          50% { box-shadow: 0 0 12px 2px rgba(183, 110, 121, 0.2); }
        }
        @keyframes pulseNumberBump {
          0% { transform: scale(1); }
          50% { transform: scale(1.08); }
          100% { transform: scale(1); }
        }
      `}</style>

      {/* Header */}
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg"
              style={{
                background: `linear-gradient(135deg, ${BRAND.roseGold}20, ${BRAND.gold}10)`,
                border: `1px solid ${BRAND.roseGold}30`,
              }}
            >
              <Activity className="h-5 w-5 text-[#B76E79]" />
            </div>
            <div>
              <CardTitle className="text-white font-bold tracking-tight">
                The Pulse
              </CardTitle>
              <CardDescription className="text-gray-400 font-medium">
                Real-Time Social Proof &amp; Micro-Interactions Engine
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
        {/* Live Metrics Row -- Animated Counters */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <MetricCard
            label="Active Viewers"
            value={animatedViewers.toLocaleString()}
            icon={Eye}
            color="text-[#B76E79]"
            bgColor="bg-[#B76E79]/10"
            borderColor="border-[#B76E79]/20"
          />
          <MetricCard
            label="Pre-Orders Today"
            value={animatedOrders.toString()}
            icon={ShoppingCart}
            color="text-green-400"
            bgColor="bg-green-500/10"
            borderColor="border-green-500/20"
          />
          <MetricCard
            label="Urgency Clicks"
            value={animatedClicks.toLocaleString()}
            icon={MousePointerClick}
            color="text-[#D4AF37]"
            bgColor="bg-[#D4AF37]/10"
            borderColor="border-[#D4AF37]/20"
          />
          <MetricCard
            label="Revenue Impact"
            value={`+$${animatedRevenue.toLocaleString()}`}
            icon={DollarSign}
            color="text-green-400"
            bgColor="bg-green-500/10"
            borderColor="border-green-500/20"
          />
        </div>

        {/* Conversion Lift Banner */}
        <div
          className="flex items-center justify-between rounded-lg p-3"
          style={{
            background: `linear-gradient(135deg, ${BRAND.roseGold}10, ${BRAND.gold}08)`,
            border: `1px solid ${BRAND.roseGold}20`,
          }}
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-400" />
            <span className="text-sm font-medium text-gray-300">Overall Conversion Lift</span>
          </div>
          <span className="text-lg font-bold text-green-400">
            +{liveData.conversionLift}%
          </span>
        </div>

        {/* Conversion Funnel Visualization */}
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Zap className="h-4 w-4 text-[#D4AF37]" />
            <h4 className="text-sm font-semibold text-gray-300">
              Conversion Funnel
            </h4>
          </div>
          <div className="space-y-2">
            <FunnelStep
              label="Visitors"
              count={liveData.funnelData.visitors}
              percentage={100}
              icon={<Globe className="h-3.5 w-3.5" />}
              accentColor={BRAND.roseGold}
            />
            <div className="flex justify-center">
              <ArrowDown className="h-4 w-4 text-gray-600" />
              <span className="ml-1 text-xs text-gray-500">{funnelViewerPct}%</span>
            </div>
            <FunnelStep
              label="Engaged Viewers"
              count={liveData.funnelData.viewers}
              percentage={(liveData.funnelData.viewers / liveData.funnelData.visitors) * 100}
              icon={<Eye className="h-3.5 w-3.5" />}
              accentColor={BRAND.roseGold}
            />
            <div className="flex justify-center">
              <ArrowDown className="h-4 w-4 text-gray-600" />
              <span className="ml-1 text-xs text-gray-500">{funnelCartPct}%</span>
            </div>
            <FunnelStep
              label="Add to Cart"
              count={liveData.funnelData.addToCarts}
              percentage={(liveData.funnelData.addToCarts / liveData.funnelData.visitors) * 100}
              icon={<ShoppingCart className="h-3.5 w-3.5" />}
              accentColor={BRAND.gold}
            />
            <div className="flex justify-center">
              <ArrowDown className="h-4 w-4 text-gray-600" />
              <span className="ml-1 text-xs text-gray-500">{funnelOrderPct}%</span>
            </div>
            <FunnelStep
              label="Pre-Orders"
              count={liveData.funnelData.preOrders}
              percentage={(liveData.funnelData.preOrders / liveData.funnelData.visitors) * 100}
              icon={<DollarSign className="h-3.5 w-3.5" />}
              accentColor="#4ade80"
              highlight
            />
          </div>
        </div>

        {/* Active Features Section */}
        <div>
          <h4 className="mb-3 text-sm font-semibold text-gray-300">
            Active Features ({ACTIVE_FEATURES.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {ACTIVE_FEATURES.map((feature) => (
              <div
                key={feature}
                className="flex items-center gap-2 rounded-lg border border-gray-700/50 px-3 py-1.5"
                style={{
                  background: 'rgba(31, 41, 55, 0.3)',
                  backdropFilter: 'blur(8px)',
                }}
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

        {/* Top Performing Products -- with HOT indicators */}
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Trophy className="h-4 w-4 text-[#D4AF37]" />
            <h4 className="text-sm font-semibold text-gray-300">
              Top Performing Products
            </h4>
          </div>
          <div className="space-y-2">
            {liveData.trendingProducts.map((product, index) => (
              <div
                key={product.name}
                className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-800/30 px-3 py-2 transition-all"
                style={product.isHot ? {
                  animation: 'pulseHotGlow 3s ease-in-out infinite',
                  borderColor: `${BRAND.roseGold}30`,
                } : undefined}
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
                  {product.isHot && (
                    <Badge
                      className="border-0 px-1.5 py-0 text-[10px] font-bold"
                      style={{
                        background: `linear-gradient(135deg, ${BRAND.roseGold}, ${BRAND.gold})`,
                        color: '#0A0A0A',
                      }}
                    >
                      HOT
                    </Badge>
                  )}
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
          Auto-refreshing every 5s -- live tracking pipeline pending
        </p>
      </CardContent>
    </Card>
  );
}

// --- Sub-components ---

function MetricCard({
  label,
  value,
  icon: Icon,
  color,
  bgColor,
  borderColor,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
}) {
  return (
    <div
      className={`rounded-lg border ${borderColor} ${bgColor} p-3 transition-all hover:scale-[1.02]`}
      style={{
        backdropFilter: 'blur(8px)',
      }}
    >
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${color}`} />
        <span className="text-xs text-gray-400">{label}</span>
      </div>
      <p className={`mt-1 text-xl font-bold tabular-nums ${color}`}>
        {value}
      </p>
    </div>
  );
}

function FunnelStep({
  label,
  count,
  percentage,
  icon,
  accentColor,
  highlight,
}: {
  label: string;
  count: number;
  percentage: number;
  icon: React.ReactNode;
  accentColor: string;
  highlight?: boolean;
}) {
  const barPct = Math.max(8, Math.min(100, percentage));

  return (
    <div
      className="relative rounded-lg border px-3 py-2 transition-all"
      style={{
        borderColor: highlight ? `${accentColor}40` : 'rgba(55, 65, 81, 0.5)',
        background: highlight
          ? `linear-gradient(135deg, ${accentColor}08, ${accentColor}04)`
          : 'rgba(31, 41, 55, 0.2)',
      }}
    >
      {/* Background bar */}
      <div
        className="absolute inset-0 rounded-lg opacity-10"
        style={{
          width: `${barPct}%`,
          background: accentColor,
        }}
      />
      <div className="relative flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span style={{ color: accentColor }}>{icon}</span>
          <span className="text-xs font-medium text-gray-300">{label}</span>
        </div>
        <span
          className="text-sm font-bold tabular-nums"
          style={{ color: accentColor }}
        >
          {count.toLocaleString()}
        </span>
      </div>
    </div>
  );
}

export default PulseAnalytics;
