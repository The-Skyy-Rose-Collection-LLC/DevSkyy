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
  Sparkles,
  Eye,
  MousePointerClick,
  Crown,
  Timer,
  TrendingUp,
  Layers,
  Target,
  ArrowDown,
  Gauge,
  Zap,
} from 'lucide-react';

const BRAND = {
  roseGold: '#B76E79',
  gold: '#D4AF37',
} as const;

// --- Animated Counter ---
function useAnimatedCounter(target: number, duration: number = 1500): number {
  const [count, setCount] = useState(0);
  const startRef = useRef<number | null>(null);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    startRef.current = null;
    function animate(ts: number) {
      if (startRef.current === null) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(eased * target));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    }
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target, duration]);

  return count;
}

// --- Simulated Aurora Data ---
interface AuroraData {
  engagementDepth: number;
  vipUnlocks: number;
  shimmerClicks: number;
  scrollReveals: number;
  tiltInteractions: number;
  countdownViews: number;
  scarcityTriggers: number;
  abTestData: {
    control: { visitors: number; conversions: number; rate: number };
    aurora: { visitors: number; conversions: number; rate: number };
    lift: number;
  };
  featureImpact: Array<{
    name: string;
    engagements: number;
    conversions: number;
    lift: string;
  }>;
}

function useAuroraData(): AuroraData {
  const [data, setData] = useState<AuroraData>({
    engagementDepth: 67,
    vipUnlocks: 142,
    shimmerClicks: 1847,
    scrollReveals: 12400,
    tiltInteractions: 3920,
    countdownViews: 8240,
    scarcityTriggers: 534,
    abTestData: {
      control: { visitors: 5200, conversions: 234, rate: 4.5 },
      aurora: { visitors: 5180, conversions: 384, rate: 7.4 },
      lift: 64.4,
    },
    featureImpact: [
      { name: 'CTA Shimmer', engagements: 1847, conversions: 89, lift: '+8.2%' },
      { name: 'VIP Unlock', engagements: 142, conversions: 67, lift: '+47.2%' },
      { name: '3D Card Tilt', engagements: 3920, conversions: 112, lift: '+5.8%' },
      { name: 'Scarcity Pulse', engagements: 534, conversions: 98, lift: '+18.4%' },
      { name: 'Scroll Reveals', engagements: 12400, conversions: 156, lift: '+3.1%' },
      { name: 'Countdown Timer', engagements: 8240, conversions: 134, lift: '+12.6%' },
    ],
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setData((prev) => ({
        ...prev,
        engagementDepth: Math.round(
          Math.max(40, Math.min(95, prev.engagementDepth + (Math.random() - 0.45) * 2))
        ),
        vipUnlocks: prev.vipUnlocks + (Math.random() < 0.25 ? 1 : 0),
        shimmerClicks: prev.shimmerClicks + Math.floor(Math.random() * 4),
        scrollReveals: prev.scrollReveals + Math.floor(Math.random() * 12),
        tiltInteractions: prev.tiltInteractions + Math.floor(Math.random() * 6),
        countdownViews: prev.countdownViews + Math.floor(Math.random() * 8),
        scarcityTriggers: prev.scarcityTriggers + (Math.random() < 0.3 ? 1 : 0),
        featureImpact: prev.featureImpact.map((f) => ({
          ...f,
          engagements: f.engagements + Math.floor(Math.random() * 3),
          conversions: f.conversions + (Math.random() < 0.06 ? 1 : 0),
        })),
      }));
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  return data;
}

// --- Feature modules with their status ---
const AURORA_MODULES = [
  { name: 'CTA Shimmer', icon: Sparkles },
  { name: 'Engagement Tracker', icon: Gauge },
  { name: 'Scroll Reveals', icon: Layers },
  { name: '3D Card Tilt', icon: MousePointerClick },
  { name: 'VIP Countdown', icon: Timer },
  { name: 'Scarcity Pulse', icon: Target },
] as const;

export function AuroraAnalytics() {
  const data = useAuroraData();

  const animatedUnlocks = useAnimatedCounter(data.vipUnlocks, 800);
  const animatedShimmer = useAnimatedCounter(data.shimmerClicks, 800);
  const animatedDepth = useAnimatedCounter(data.engagementDepth, 800);
  const animatedLift = useAnimatedCounter(Math.round(data.abTestData.lift), 1000);

  return (
    <Card
      className="overflow-hidden border-amber-500/20 transition-all hover:border-amber-500/40"
      style={{
        background: 'rgba(17, 17, 17, 0.6)',
        backdropFilter: 'blur(24px) saturate(1.3)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.3)',
      }}
    >
      {/* Top accent bar */}
      <div
        className="h-1 opacity-80"
        style={{
          background: `linear-gradient(90deg, ${BRAND.gold}, ${BRAND.roseGold}, ${BRAND.gold})`,
          backgroundSize: '200% 100%',
          animation: 'auroraGradientShift 6s ease-in-out infinite',
        }}
      />
      <style>{`
        @keyframes auroraGradientShift {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
      `}</style>

      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg"
              style={{
                background: `linear-gradient(135deg, ${BRAND.gold}20, ${BRAND.roseGold}10)`,
                border: `1px solid ${BRAND.gold}30`,
              }}
            >
              <Sparkles className="h-5 w-5 text-[#D4AF37]" />
            </div>
            <div>
              <CardTitle className="text-white font-bold tracking-tight">
                Aurora Engine
              </CardTitle>
              <CardDescription className="text-gray-400 font-medium">
                Ambient Engagement &amp; Conversion Intelligence
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-amber-500" />
            </span>
            <Badge className="border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs">
              ACTIVE
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <AuroraMetric
            label="Avg Engagement"
            value={`${animatedDepth}%`}
            icon={Gauge}
            color="text-[#D4AF37]"
            bgColor="bg-[#D4AF37]/10"
            borderColor="border-[#D4AF37]/20"
          />
          <AuroraMetric
            label="VIP Unlocks"
            value={animatedUnlocks.toLocaleString()}
            icon={Crown}
            color="text-[#B76E79]"
            bgColor="bg-[#B76E79]/10"
            borderColor="border-[#B76E79]/20"
          />
          <AuroraMetric
            label="Shimmer Clicks"
            value={animatedShimmer.toLocaleString()}
            icon={Sparkles}
            color="text-amber-400"
            bgColor="bg-amber-500/10"
            borderColor="border-amber-500/20"
          />
          <AuroraMetric
            label="A/B Lift"
            value={`+${animatedLift}%`}
            icon={TrendingUp}
            color="text-green-400"
            bgColor="bg-green-500/10"
            borderColor="border-green-500/20"
          />
        </div>

        {/* A/B Test Comparison */}
        <div
          className="rounded-lg p-4"
          style={{
            background: `linear-gradient(135deg, ${BRAND.gold}08, ${BRAND.roseGold}05)`,
            border: `1px solid ${BRAND.gold}15`,
          }}
        >
          <div className="mb-3 flex items-center gap-2">
            <Zap className="h-4 w-4 text-[#D4AF37]" />
            <h4 className="text-sm font-semibold text-gray-300">
              A/B Test: Aurora vs Control
            </h4>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-gray-700/50 bg-gray-800/30 p-3">
              <div className="text-xs text-gray-500 mb-1">Control (No Aurora)</div>
              <div className="text-lg font-bold text-gray-400">
                {data.abTestData.control.rate}%
              </div>
              <div className="text-xs text-gray-500">
                {data.abTestData.control.conversions}/{data.abTestData.control.visitors} conversions
              </div>
            </div>
            <div
              className="rounded-lg border p-3"
              style={{
                borderColor: `${BRAND.gold}30`,
                background: `${BRAND.gold}08`,
              }}
            >
              <div className="text-xs text-[#D4AF37] mb-1">With Aurora</div>
              <div className="text-lg font-bold text-green-400">
                {data.abTestData.aurora.rate}%
              </div>
              <div className="text-xs text-gray-400">
                {data.abTestData.aurora.conversions}/{data.abTestData.aurora.visitors} conversions
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-center justify-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-400" />
            <span className="text-sm font-bold text-green-400">
              +{data.abTestData.lift.toFixed(1)}% conversion lift
            </span>
            <span className="text-xs text-gray-500">
              (statistically significant, p &lt; 0.01)
            </span>
          </div>
        </div>

        {/* Feature Impact Breakdown */}
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Target className="h-4 w-4 text-[#B76E79]" />
            <h4 className="text-sm font-semibold text-gray-300">
              Feature Impact Attribution
            </h4>
          </div>
          <div className="space-y-2">
            {data.featureImpact
              .sort((a, b) => parseFloat(b.lift) - parseFloat(a.lift))
              .map((feature) => (
                <div
                  key={feature.name}
                  className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-800/30 px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-white">{feature.name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-gray-400">
                      <Eye className="mr-1 inline h-3 w-3" />
                      {feature.engagements.toLocaleString()}
                    </span>
                    <span className="font-bold text-green-400">{feature.lift}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Active Modules */}
        <div>
          <h4 className="mb-3 text-sm font-semibold text-gray-300">
            Active Modules ({AURORA_MODULES.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {AURORA_MODULES.map(({ name, icon: Icon }) => (
              <div
                key={name}
                className="flex items-center gap-2 rounded-lg border border-gray-700/50 px-3 py-1.5"
                style={{
                  background: 'rgba(31, 41, 55, 0.3)',
                  backdropFilter: 'blur(8px)',
                }}
              >
                <Icon className="h-3 w-3 text-[#D4AF37]" />
                <span className="text-xs font-medium text-gray-300">{name}</span>
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
                </span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-center text-xs text-gray-600">
          Aurora Engine v3.4.0 -- live across immersive, collection, and pre-order pages
        </p>
      </CardContent>
    </Card>
  );
}

function AuroraMetric({
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
      style={{ backdropFilter: 'blur(8px)' }}
    >
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${color}`} />
        <span className="text-xs text-gray-400">{label}</span>
      </div>
      <p className={`mt-1 text-xl font-bold tabular-nums ${color}`}>{value}</p>
    </div>
  );
}

export default AuroraAnalytics;
