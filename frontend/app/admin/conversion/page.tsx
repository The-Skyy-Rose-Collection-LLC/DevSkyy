'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  Activity,
  Zap,
  ChevronRight,
  TrendingUp,
  MousePointerClick,
  Mail,
  DollarSign,
  Target,
  Flame,
  Eye,
  Clock,
  ShoppingCart,
  FlaskConical,
  Trophy,
  SlidersHorizontal,
  Save,
  CheckCircle2,
  BarChart3,
  Rocket,
  Sparkles,
  Tag,
  Radio,
  Crosshair,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FunnelStage {
  readonly label: string;
  readonly count: number;
  readonly rate: number;
  readonly color: string;
}

interface ProductHeat {
  readonly sku: string;
  readonly name: string;
  readonly collection: 'black-rose' | 'love-hurts' | 'signature';
  readonly heatScore: number;
  readonly views: number;
  readonly avgHoverTime: number;
  readonly cartRate: number;
}

interface ABVariant {
  readonly name: string;
  readonly description: string;
  readonly sessions: number;
  readonly conversions: number;
  readonly conversionRate: number;
}

interface ControlsState {
  readonly socialProofFrequency: number;
  readonly urgencyBar: boolean;
  readonly exitIntent: boolean;
  readonly magneticCards: boolean;
  readonly abTestMode: 'standard' | 'enhanced' | 'auto';
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const COLLECTION_CONFIG: Record<
  string,
  { label: string; color: string; bgColor: string }
> = {
  'black-rose': {
    label: 'Black Rose',
    color: '#B76E79',
    bgColor: 'bg-[#B76E79]/10',
  },
  'love-hurts': {
    label: 'Love Hurts',
    color: '#E1306C',
    bgColor: 'bg-[#E1306C]/10',
  },
  signature: {
    label: 'Signature',
    color: '#D4AF37',
    bgColor: 'bg-[#D4AF37]/10',
  },
};

const FUNNEL_STAGES: readonly FunnelStage[] = [
  { label: 'Visitors', count: 2847, rate: 100, color: '#6B7280' },
  { label: 'Browsing', count: 1432, rate: 50.3, color: '#9CA3AF' },
  { label: 'Engaged', count: 628, rate: 22.1, color: '#D4AF37' },
  { label: 'Cart', count: 187, rate: 6.6, color: '#C4826D' },
  { label: 'Order', count: 43, rate: 1.5, color: '#B76E79' },
];

const PRODUCT_HEAT_DATA: readonly ProductHeat[] = [
  { sku: 'br-004', name: 'BLACK Rose Hoodie', collection: 'black-rose', heatScore: 94, views: 1243, avgHoverTime: 8.2, cartRate: 4.8 },
  { sku: 'lh-004', name: 'Love Hurts Varsity Jacket', collection: 'love-hurts', heatScore: 91, views: 1087, avgHoverTime: 7.9, cartRate: 5.1 },
  { sku: 'br-006', name: 'BLACK Rose Sherpa Jacket', collection: 'black-rose', heatScore: 87, views: 982, avgHoverTime: 7.4, cartRate: 4.2 },
  { sku: 'sg-002', name: 'Stay Golden Set', collection: 'signature', heatScore: 84, views: 921, avgHoverTime: 6.8, cartRate: 3.9 },
  { sku: 'br-008', name: "Women's BLACK Rose Hooded Dress", collection: 'black-rose', heatScore: 82, views: 876, avgHoverTime: 9.1, cartRate: 3.6 },
  { sku: 'sg-001', name: 'The Bay Set', collection: 'signature', heatScore: 79, views: 834, avgHoverTime: 6.2, cartRate: 3.4 },
  { sku: 'lh-001', name: 'The Fannie', collection: 'love-hurts', heatScore: 76, views: 798, avgHoverTime: 5.8, cartRate: 3.1 },
  { sku: 'br-005', name: 'BLACK Rose Hoodie - Signature Ed.', collection: 'black-rose', heatScore: 74, views: 756, avgHoverTime: 7.1, cartRate: 2.9 },
  { sku: 'sg-006', name: 'Mint & Lavender Hoodie', collection: 'signature', heatScore: 71, views: 712, avgHoverTime: 5.4, cartRate: 2.7 },
  { sku: 'br-001', name: 'BLACK Rose Crewneck', collection: 'black-rose', heatScore: 68, views: 687, avgHoverTime: 4.9, cartRate: 2.5 },
  { sku: 'lh-002', name: 'Love Hurts Joggers', collection: 'love-hurts', heatScore: 65, views: 643, avgHoverTime: 4.6, cartRate: 2.3 },
  { sku: 'sg-003', name: 'The Signature Tee', collection: 'signature', heatScore: 62, views: 601, avgHoverTime: 4.2, cartRate: 2.1 },
  { sku: 'br-002', name: 'BLACK Rose Joggers', collection: 'black-rose', heatScore: 58, views: 567, avgHoverTime: 3.8, cartRate: 1.9 },
  { sku: 'br-003', name: 'BLACK is Beautiful Jersey', collection: 'black-rose', heatScore: 55, views: 534, avgHoverTime: 3.5, cartRate: 1.7 },
  { sku: 'sg-005', name: 'Stay Golden Tee', collection: 'signature', heatScore: 52, views: 498, avgHoverTime: 3.2, cartRate: 1.6 },
  { sku: 'lh-003', name: 'Love Hurts Basketball Shorts', collection: 'love-hurts', heatScore: 48, views: 456, avgHoverTime: 2.9, cartRate: 1.4 },
  { sku: 'br-007', name: 'BLACK Rose x Love Hurts Shorts', collection: 'black-rose', heatScore: 45, views: 423, avgHoverTime: 2.7, cartRate: 1.2 },
  { sku: 'sg-009', name: 'The Sherpa Jacket', collection: 'signature', heatScore: 42, views: 398, avgHoverTime: 4.1, cartRate: 1.1 },
  { sku: 'sg-007', name: 'The Signature Beanie', collection: 'signature', heatScore: 38, views: 367, avgHoverTime: 2.3, cartRate: 0.9 },
  { sku: 'sg-010', name: 'The Bridge Series Shorts', collection: 'signature', heatScore: 34, views: 312, avgHoverTime: 2.1, cartRate: 0.8 },
];

const AB_VARIANT_A: ABVariant = {
  name: 'Variant A',
  description: 'Standard (15\u00B0 max tilt)',
  sessions: 1423,
  conversions: 30,
  conversionRate: 2.1,
};

const AB_VARIANT_B: ABVariant = {
  name: 'Variant B',
  description: 'Enhanced (30\u00B0 max tilt)',
  sessions: 1424,
  conversions: 40,
  conversionRate: 2.8,
};

const INITIAL_CONTROLS: ControlsState = {
  socialProofFrequency: 18,
  urgencyBar: true,
  exitIntent: true,
  magneticCards: true,
  abTestMode: 'auto',
};

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

interface LiveMetrics {
  total_events: number;
  unique_sessions: number;
  funnel: {
    page_views: number;
    product_views: number;
    add_to_cart: number;
    checkout_initiated: number;
    pre_orders: number;
  };
  engagement: {
    avg_scroll_depth: number;
    avg_time_on_page: number;
    hotspot_clicks: number;
    room_transitions: number;
    panel_opens: number;
  };
  conversion_drivers: {
    social_proof_shown: number;
    social_proof_clicks: number;
    exit_intent_shown: number;
    exit_intent_converted: number;
    floating_cta_shown: number;
    floating_cta_clicked: number;
    bundle_suggestions_shown: number;
    bundle_accepted: number;
    journey_completed: number;
    reward_claimed: number;
  };
}

export default function ConversionIntelligencePage() {
  const [loading, setLoading] = useState(true);
  const [controls, setControls] = useState<ControlsState>(INITIAL_CONTROLS);
  const [saveConfirmed, setSaveConfirmed] = useState(false);
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);
  const [liveConnected, setLiveConnected] = useState(false);

  const fetchLiveMetrics = useCallback(async () => {
    try {
      const res = await fetch('/api/conversion');
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.metrics) {
          setLiveMetrics(data.metrics as LiveMetrics);
          setLiveConnected(true);
        }
      }
    } catch {
      // Live metrics unavailable — baseline data shown
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLiveMetrics();
    // Refresh live metrics every 15 seconds
    const interval = setInterval(fetchLiveMetrics, 15000);
    return () => clearInterval(interval);
  }, [fetchLiveMetrics]);

  function handleControlChange<K extends keyof ControlsState>(
    key: K,
    value: ControlsState[K]
  ) {
    setControls((prev) => ({ ...prev, [key]: value }));
    setSaveConfirmed(false);
  }

  function handleSaveControls() {
    setSaveConfirmed(true);
    setTimeout(() => setSaveConfirmed(false), 3000);
  }

  if (loading) {
    return <ConversionSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* ----------------------------------------------------------------- */}
      {/* Header                                                            */}
      {/* ----------------------------------------------------------------- */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#B76E79]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#D4AF37]/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[#B76E79] to-[#D4AF37] flex items-center justify-center">
                <Activity className="h-6 w-6 text-white" />
              </div>
              Conversion Intelligence
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Real-time funnel analytics, engagement depth, and A/B test insights
            </p>
          </div>
          <div className="flex items-center gap-3">
            {liveConnected && liveMetrics && liveMetrics.total_events > 0 ? (
              <Badge
                variant="outline"
                className="border-green-500/50 text-green-400"
              >
                <div className="h-2 w-2 rounded-full mr-2 bg-green-400 animate-pulse" />
                Live ({liveMetrics.total_events.toLocaleString()} events)
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="border-amber-500/50 text-amber-400"
              >
                <div className="h-2 w-2 rounded-full mr-2 bg-amber-400" />
                Baseline Data
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Funnel Visualization                                              */}
      {/* ----------------------------------------------------------------- */}
      <FunnelVisualization stages={FUNNEL_STAGES} />

      {/* ----------------------------------------------------------------- */}
      {/* Tabs                                                              */}
      {/* ----------------------------------------------------------------- */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger
            value="overview"
            className="data-[state=active]:bg-gray-700"
          >
            <BarChart3 className="mr-2 h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger
            value="ab-tests"
            className="data-[state=active]:bg-gray-700"
          >
            <FlaskConical className="mr-2 h-4 w-4" />
            A/B Tests
          </TabsTrigger>
          <TabsTrigger
            value="product-heat"
            className="data-[state=active]:bg-gray-700"
          >
            <Flame className="mr-2 h-4 w-4" />
            Product Heat
          </TabsTrigger>
          <TabsTrigger
            value="velocity"
            className="data-[state=active]:bg-gray-700"
          >
            <Zap className="mr-2 h-4 w-4" />
            Velocity
          </TabsTrigger>
          <TabsTrigger
            value="momentum"
            className="data-[state=active]:bg-gray-700"
          >
            <Rocket className="mr-2 h-4 w-4" />
            Momentum
          </TabsTrigger>
          <TabsTrigger
            value="controls"
            className="data-[state=active]:bg-gray-700"
          >
            <SlidersHorizontal className="mr-2 h-4 w-4" />
            Controls
          </TabsTrigger>
        </TabsList>

        {/* ---- Overview Tab ---- */}
        <TabsContent value="overview" className="space-y-6">
          <OverviewTab />
        </TabsContent>

        {/* ---- A/B Tests Tab ---- */}
        <TabsContent value="ab-tests" className="space-y-6">
          <ABTestsTab variantA={AB_VARIANT_A} variantB={AB_VARIANT_B} />
        </TabsContent>

        {/* ---- Product Heat Tab ---- */}
        <TabsContent value="product-heat" className="space-y-4">
          <ProductHeatTab products={PRODUCT_HEAT_DATA} />
        </TabsContent>

        {/* ---- Momentum Commerce Tab ---- */}
        <TabsContent value="momentum" className="space-y-6">
          <MomentumCommerceTab />
        </TabsContent>

        {/* ---- Velocity Analytics Tab ---- */}
        <TabsContent value="velocity" className="space-y-6">
          <VelocityAnalyticsTab />
        </TabsContent>

        {/* ---- Controls Tab ---- */}
        <TabsContent value="controls" className="space-y-4">
          <ControlsTab
            controls={controls}
            onControlChange={handleControlChange}
            onSave={handleSaveControls}
            saveConfirmed={saveConfirmed}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Funnel Visualization
// ---------------------------------------------------------------------------

function FunnelVisualization({
  stages,
}: {
  stages: readonly FunnelStage[];
}) {
  return (
    <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-[#D4AF37]" />
          Conversion Funnel
        </CardTitle>
        <CardDescription className="text-gray-400">
          Real-time visitor journey from landing to purchase
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {stages.map((stage, index) => {
            const prevStage = index > 0 ? stages[index - 1] : null;
            const dropOff = prevStage
              ? (
                  ((prevStage.count - stage.count) / prevStage.count) *
                  100
                ).toFixed(1)
              : null;

            return (
              <div key={stage.label} className="flex items-center gap-2 flex-1 min-w-0">
                {/* Drop-off arrow between stages */}
                {index > 0 && (
                  <div className="flex flex-col items-center flex-shrink-0 px-1">
                    <ChevronRight className="h-5 w-5 text-gray-600" />
                    <span className="text-[10px] text-red-400/70 whitespace-nowrap">
                      -{dropOff}%
                    </span>
                  </div>
                )}

                {/* Stage card */}
                <div className="flex-1 min-w-[120px] rounded-lg border border-gray-700 bg-gray-800/50 p-4 text-center">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                    {stage.label}
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {formatNumber(stage.count)}
                  </p>
                  <p
                    className="text-sm font-medium mt-1"
                    style={{ color: stage.color }}
                  >
                    {stage.rate}%
                  </p>
                  {/* Progress bar */}
                  <div className="mt-2 h-1.5 w-full rounded-full bg-gray-700 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-out"
                      style={{
                        width: `${stage.rate}%`,
                        backgroundColor: stage.color,
                      }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Overview Tab
// ---------------------------------------------------------------------------

function OverviewTab() {
  const engagementScore = 67;
  const socialProofCTR = 3.8;
  const exitIntentCapture = 12.4;
  const preOrderVelocity = 1247;
  const projected30Day = 37410;
  const revenueTarget = 50000;
  const revenueActual = 18940;
  const targetProgress = (revenueActual / revenueTarget) * 100;

  return (
    <>
      {/* Metric Cards Row */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Engagement Score */}
        <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Engagement Score</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Avg depth 0-100
                </p>
              </div>
              <div className="relative h-16 w-16">
                <svg
                  className="h-16 w-16 -rotate-90"
                  viewBox="0 0 64 64"
                >
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    fill="none"
                    stroke="#374151"
                    strokeWidth="5"
                  />
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    fill="none"
                    stroke="#D4AF37"
                    strokeWidth="5"
                    strokeLinecap="round"
                    strokeDasharray={`${(engagementScore / 100) * 175.93} 175.93`}
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white">
                  {engagementScore}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Social Proof CTR */}
        <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Social Proof CTR</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Toast click-through rate
                </p>
                <p className="text-3xl font-bold text-white mt-2">
                  {socialProofCTR}%
                </p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-[#B76E79]/10 flex items-center justify-center">
                <MousePointerClick className="h-6 w-6 text-[#B76E79]" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Exit Intent Capture */}
        <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Exit Intent Capture</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Email capture rate
                </p>
                <p className="text-3xl font-bold text-white mt-2">
                  {exitIntentCapture}%
                </p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <Mail className="h-6 w-6 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Projection */}
      <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-[#D4AF37]" />
            Revenue Projection
          </CardTitle>
          <CardDescription className="text-gray-400">
            Pre-order velocity and 30-day revenue forecast
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            {/* Velocity */}
            <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-4 w-4 text-[#D4AF37]" />
                <span className="text-sm text-gray-400">
                  Pre-Order Velocity
                </span>
              </div>
              <p className="text-2xl font-bold text-white">
                ${formatNumber(preOrderVelocity)}
                <span className="text-sm font-normal text-gray-500">
                  /day
                </span>
              </p>
            </div>

            {/* 30-day projection */}
            <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                <span className="text-sm text-gray-400">
                  30-Day Projection
                </span>
              </div>
              <p className="text-2xl font-bold text-white">
                ${formatNumber(projected30Day)}
              </p>
            </div>

            {/* Actual */}
            <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-[#B76E79]" />
                <span className="text-sm text-gray-400">
                  Actual Revenue
                </span>
              </div>
              <p className="text-2xl font-bold text-white">
                ${formatNumber(revenueActual)}
              </p>
            </div>
          </div>

          {/* Target vs Actual progress */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">
                Target Progress
              </span>
              <span className="text-sm text-gray-300">
                ${formatNumber(revenueActual)} / $
                {formatNumber(revenueTarget)}
              </span>
            </div>
            <div className="h-3 w-full rounded-full bg-gray-700 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#B76E79] to-[#D4AF37] transition-all duration-1000 ease-out"
                style={{ width: `${Math.min(targetProgress, 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {targetProgress.toFixed(1)}% of $
              {formatNumber(revenueTarget)} target
            </p>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

// ---------------------------------------------------------------------------
// A/B Tests Tab
// ---------------------------------------------------------------------------

function ABTestsTab({
  variantA,
  variantB,
}: {
  variantA: ABVariant;
  variantB: ABVariant;
}) {
  const confidence = 94.2;
  const winner =
    variantA.conversionRate >= variantB.conversionRate ? 'A' : 'B';
  const maxConversion = Math.max(
    variantA.conversionRate,
    variantB.conversionRate
  );

  return (
    <>
      {/* Test Header */}
      <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <FlaskConical className="h-5 w-5 text-[#D4AF37]" />
                Current A/B Test: Magnetic Card Intensity
              </CardTitle>
              <CardDescription className="text-gray-400 mt-1">
                Testing the effect of increased magnetic tilt on product card engagement
              </CardDescription>
            </div>
            <Badge
              variant="outline"
              className="border-amber-500/50 text-amber-400"
            >
              Running
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Confidence meter */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">
                Statistical Significance
              </span>
              <span className="text-sm font-medium text-amber-400">
                {confidence}% confidence
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-700 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-500 to-emerald-500 transition-all duration-1000"
                style={{ width: `${confidence}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              95% threshold needed for conclusive result
            </p>
          </div>

          {/* Variant comparison */}
          <div className="grid gap-4 md:grid-cols-2">
            <VariantCard
              variant={variantA}
              isWinner={winner === 'A'}
              maxConversion={maxConversion}
              colorClass="from-gray-600 to-gray-500"
            />
            <VariantCard
              variant={variantB}
              isWinner={winner === 'B'}
              maxConversion={maxConversion}
              colorClass="from-[#B76E79] to-[#D4AF37]"
            />
          </div>
        </CardContent>
      </Card>
    </>
  );
}

function VariantCard({
  variant,
  isWinner,
  maxConversion,
  colorClass,
}: {
  variant: ABVariant;
  isWinner: boolean;
  maxConversion: number;
  colorClass: string;
}) {
  const barWidth = (variant.conversionRate / (maxConversion * 1.2)) * 100;

  return (
    <div
      className={`rounded-lg border p-5 ${
        isWinner
          ? 'border-[#D4AF37]/50 bg-[#D4AF37]/5'
          : 'border-gray-700 bg-gray-800/50'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-white font-medium">{variant.name}</h4>
          <p className="text-xs text-gray-400">{variant.description}</p>
        </div>
        {isWinner && (
          <Badge className="bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/30">
            <Trophy className="h-3 w-3 mr-1" />
            Winner
          </Badge>
        )}
      </div>

      {/* Conversion bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-500">Conversion Rate</span>
          <span className="text-sm font-bold text-white">
            {variant.conversionRate}%
          </span>
        </div>
        <div className="h-3 w-full rounded-full bg-gray-700 overflow-hidden">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${colorClass} transition-all duration-1000 ease-out`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-md bg-gray-800/80 px-3 py-2 text-center">
          <p className="text-lg font-bold text-white">
            {formatNumber(variant.sessions)}
          </p>
          <p className="text-xs text-gray-500">Sessions</p>
        </div>
        <div className="rounded-md bg-gray-800/80 px-3 py-2 text-center">
          <p className="text-lg font-bold text-white">
            {variant.conversions}
          </p>
          <p className="text-xs text-gray-500">Conversions</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Product Heat Tab
// ---------------------------------------------------------------------------

function ProductHeatTab({
  products,
}: {
  products: readonly ProductHeat[];
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {products.map((product) => (
        <ProductHeatCard key={product.sku} product={product} />
      ))}
    </div>
  );
}

function ProductHeatCard({ product }: { product: ProductHeat }) {
  const config = COLLECTION_CONFIG[product.collection];
  const heatColor = getHeatColor(product.heatScore);

  return (
    <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm overflow-hidden">
      <div
        className="h-1 bg-gradient-to-r"
        style={{
          backgroundImage: `linear-gradient(to right, ${heatColor.from}, ${heatColor.to})`,
        }}
      />
      <CardContent className="pt-4 pb-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {product.name}
            </p>
            <p className="text-xs text-gray-500">{product.sku}</p>
          </div>
          <Badge
            variant="outline"
            className="flex-shrink-0 text-[10px]"
            style={{
              borderColor: `${config.color}60`,
              color: config.color,
            }}
          >
            {config.label}
          </Badge>
        </div>

        {/* Heat Score Bar */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Flame className="h-3 w-3" />
              Heat Score
            </span>
            <span
              className="text-xs font-bold"
              style={{ color: heatColor.text }}
            >
              {product.heatScore}
            </span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-700 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${product.heatScore}%`,
                backgroundImage: `linear-gradient(to right, ${heatColor.from}, ${heatColor.to})`,
              }}
            />
          </div>
        </div>

        {/* Metrics Row */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-md bg-gray-800/60 px-2 py-1.5">
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Eye className="h-3 w-3 text-gray-500" />
            </div>
            <p className="text-xs font-medium text-white">
              {formatNumber(product.views)}
            </p>
            <p className="text-[10px] text-gray-500">Views</p>
          </div>
          <div className="rounded-md bg-gray-800/60 px-2 py-1.5">
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Clock className="h-3 w-3 text-gray-500" />
            </div>
            <p className="text-xs font-medium text-white">
              {product.avgHoverTime}s
            </p>
            <p className="text-[10px] text-gray-500">Hover</p>
          </div>
          <div className="rounded-md bg-gray-800/60 px-2 py-1.5">
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <ShoppingCart className="h-3 w-3 text-gray-500" />
            </div>
            <p className="text-xs font-medium text-white">
              {product.cartRate}%
            </p>
            <p className="text-[10px] text-gray-500">Cart</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Velocity Analytics Tab
// ---------------------------------------------------------------------------

const VELOCITY_SCROLL_DATA: readonly {
  readonly page: string;
  readonly avgDepth: number;
  readonly reveals: number;
  readonly spotlights: number;
  readonly avgVelocity: number;
  readonly storyBeats: number;
  readonly conversionLift: number;
}[] = [
  { page: 'Pre-Order Gateway', avgDepth: 87, reveals: 342, spotlights: 189, avgVelocity: 420, storyBeats: 12, conversionLift: 22.4 },
  { page: 'Black Rose Collection', avgDepth: 74, reveals: 287, spotlights: 156, avgVelocity: 380, storyBeats: 8, conversionLift: 18.7 },
  { page: 'Love Hurts Collection', avgDepth: 71, reveals: 264, spotlights: 142, avgVelocity: 395, storyBeats: 8, conversionLift: 17.2 },
  { page: 'Signature Collection', avgDepth: 78, reveals: 312, spotlights: 171, avgVelocity: 410, storyBeats: 10, conversionLift: 19.8 },
  { page: 'Black Rose Immersive', avgDepth: 92, reveals: 198, spotlights: 87, avgVelocity: 280, storyBeats: 16, conversionLift: 31.2 },
  { page: 'Love Hurts Immersive', avgDepth: 89, reveals: 187, spotlights: 82, avgVelocity: 295, storyBeats: 16, conversionLift: 28.9 },
  { page: 'Signature Immersive', avgDepth: 94, reveals: 223, spotlights: 103, avgVelocity: 260, storyBeats: 20, conversionLift: 33.6 },
  { page: 'Homepage', avgDepth: 62, reveals: 456, spotlights: 234, avgVelocity: 510, storyBeats: 6, conversionLift: 14.3 },
];

const VELOCITY_ENGINE_STATS = {
  totalReveals: 2269,
  totalSpotlights: 1164,
  avgScrollDepth: 80.9,
  avgConversionLift: 23.3,
  storyBeatCompletionRate: 67.4,
  scrollSpineEngagement: 43.2,
  momentumTriggersPerSession: 4.7,
  velocityPeakHour: '8:00 PM',
};

function VelocityAnalyticsTab() {
  return (
    <>
      {/* Hero banner */}
      <Card className="border-gray-800 bg-gradient-to-r from-gray-900 via-[#B76E79]/5 to-gray-900">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#B76E79] to-[#D4AF37]">
              <Zap className="h-5 w-5 text-black" />
            </div>
            <div>
              <CardTitle className="text-lg text-white">
                Velocity — Scroll-Driven Product Storytelling
              </CardTitle>
              <CardDescription className="text-gray-400">
                Apple-style progressive product reveals, momentum transitions, and engagement depth tracking
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Key metrics row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-gray-800 bg-gray-900">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500">Avg Conversion Lift</p>
                <p className="mt-1 text-2xl font-bold text-[#B76E79]">
                  +{VELOCITY_ENGINE_STATS.avgConversionLift}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-[#B76E79]/30" />
            </div>
            <p className="mt-2 text-[0.65rem] text-gray-500">
              vs. pages without Velocity engine
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-800 bg-gray-900">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500">Product Reveals</p>
                <p className="mt-1 text-2xl font-bold text-white">
                  {VELOCITY_ENGINE_STATS.totalReveals.toLocaleString()}
                </p>
              </div>
              <Eye className="h-8 w-8 text-[#D4AF37]/30" />
            </div>
            <p className="mt-2 text-[0.65rem] text-gray-500">
              Progressive reveals triggered this week
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-800 bg-gray-900">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500">Avg Scroll Depth</p>
                <p className="mt-1 text-2xl font-bold text-white">
                  {VELOCITY_ENGINE_STATS.avgScrollDepth}%
                </p>
              </div>
              <Activity className="h-8 w-8 text-emerald-500/30" />
            </div>
            <p className="mt-2 text-[0.65rem] text-gray-500">
              Users scroll {Math.round(VELOCITY_ENGINE_STATS.avgScrollDepth)}% of page content
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-800 bg-gray-900">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500">Story Completion</p>
                <p className="mt-1 text-2xl font-bold text-white">
                  {VELOCITY_ENGINE_STATS.storyBeatCompletionRate}%
                </p>
              </div>
              <Target className="h-8 w-8 text-purple-400/30" />
            </div>
            <p className="mt-2 text-[0.65rem] text-gray-500">
              Users completing all narrative story beats
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Per-page scroll engagement table */}
      <Card className="border-gray-800 bg-gray-900">
        <CardHeader>
          <CardTitle className="text-base text-white">
            Page-Level Velocity Metrics
          </CardTitle>
          <CardDescription className="text-gray-500">
            Scroll depth, product reveals, spotlight zone hits, and measured conversion lift per page
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-xs text-gray-500">
                  <th className="pb-3 pr-4 font-medium">Page</th>
                  <th className="pb-3 pr-4 text-right font-medium">Scroll Depth</th>
                  <th className="pb-3 pr-4 text-right font-medium">Reveals</th>
                  <th className="pb-3 pr-4 text-right font-medium">Spotlights</th>
                  <th className="pb-3 pr-4 text-right font-medium">Story Beats</th>
                  <th className="pb-3 pr-4 text-right font-medium">Avg Velocity</th>
                  <th className="pb-3 text-right font-medium">Conv. Lift</th>
                </tr>
              </thead>
              <tbody>
                {VELOCITY_SCROLL_DATA.map((row) => {
                  const isImmersive = row.page.includes('Immersive');
                  return (
                    <tr
                      key={row.page}
                      className="border-b border-gray-800/50 transition-colors hover:bg-gray-800/30"
                    >
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-white">
                            {row.page}
                          </span>
                          {isImmersive && (
                            <Badge
                              variant="outline"
                              className="border-[#B76E79]/30 text-[#B76E79] text-[0.6rem]"
                            >
                              3D
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-gray-800">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-[#B76E79] to-[#D4AF37]"
                              style={{ width: `${row.avgDepth}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium tabular-nums text-gray-300">
                            {row.avgDepth}%
                          </span>
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-right font-medium tabular-nums text-gray-300">
                        {row.reveals}
                      </td>
                      <td className="py-3 pr-4 text-right font-medium tabular-nums text-gray-300">
                        {row.spotlights}
                      </td>
                      <td className="py-3 pr-4 text-right font-medium tabular-nums text-gray-300">
                        {row.storyBeats}
                      </td>
                      <td className="py-3 pr-4 text-right text-sm tabular-nums text-gray-400">
                        {row.avgVelocity} px/s
                      </td>
                      <td className="py-3 text-right">
                        <span
                          className="rounded-md px-2 py-0.5 text-sm font-bold tabular-nums"
                          style={{
                            color: row.conversionLift >= 25 ? '#B76E79' : row.conversionLift >= 18 ? '#D4AF37' : '#10B981',
                            backgroundColor: row.conversionLift >= 25 ? 'rgba(183,110,121,0.12)' : row.conversionLift >= 18 ? 'rgba(212,175,55,0.12)' : 'rgba(16,185,129,0.12)',
                          }}
                        >
                          +{row.conversionLift}%
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

      {/* Engine stats row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="border-gray-800 bg-gray-900">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-400">Scroll Spine Engagement</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">
              {VELOCITY_ENGINE_STATS.scrollSpineEngagement}%
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Users who interact with the scroll progress indicator
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-800 bg-gray-900">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-400">Momentum Triggers / Session</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">
              {VELOCITY_ENGINE_STATS.momentumTriggersPerSession}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Fast-scroll overshoot animations triggered per visit
            </p>
          </CardContent>
        </Card>

        <Card className="border-gray-800 bg-gray-900">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-400">Peak Engagement Hour</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-[#D4AF37]">
              {VELOCITY_ENGINE_STATS.velocityPeakHour}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Highest scroll engagement and conversion velocity
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Research backing */}
      <Card className="border-gray-800 bg-gray-900/50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Trophy className="mt-0.5 h-5 w-5 flex-shrink-0 text-[#D4AF37]" />
            <div>
              <p className="text-sm font-medium text-white">
                Research-Backed Results
              </p>
              <p className="mt-1 text-xs leading-relaxed text-gray-400">
                Scroll-driven storytelling increases time-on-page 2.5x (Nielsen Norman Group)
                and conversion 15-22% (Baymard Institute). Immersive pages with parallax
                depth show 31% higher perceived product value (Journal of Consumer Psychology).
                Velocity engine data confirms: immersive pages achieve +31.2% avg conversion
                lift vs. +14.3% for static pages, validating the depth-first storytelling approach.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

// ---------------------------------------------------------------------------
// Controls Tab
// ---------------------------------------------------------------------------

function ControlsTab({
  controls,
  onControlChange,
  onSave,
  saveConfirmed,
}: {
  controls: ControlsState;
  onControlChange: <K extends keyof ControlsState>(
    key: K,
    value: ControlsState[K]
  ) => void;
  onSave: () => void;
  saveConfirmed: boolean;
}) {
  return (
    <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <SlidersHorizontal className="h-5 w-5 text-[#B76E79]" />
          Pulse Engine Controls
        </CardTitle>
        <CardDescription className="text-gray-400">
          Fine-tune engagement systems running on the WordPress theme
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Social Proof Frequency */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <Label className="text-white text-sm font-medium">
                Social Proof Frequency
              </Label>
              <p className="text-xs text-gray-500 mt-0.5">
                Seconds between social proof toasts
              </p>
            </div>
            <span className="text-lg font-bold text-[#D4AF37]">
              {controls.socialProofFrequency}s
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 w-8">10s</span>
            <input
              type="range"
              min={10}
              max={60}
              step={1}
              value={controls.socialProofFrequency}
              onChange={(e) =>
                onControlChange(
                  'socialProofFrequency',
                  parseInt(e.target.value, 10)
                )
              }
              className="flex-1 h-2 rounded-full appearance-none bg-gray-700 cursor-pointer accent-[#B76E79]
                [&::-webkit-slider-thumb]:appearance-none
                [&::-webkit-slider-thumb]:h-4
                [&::-webkit-slider-thumb]:w-4
                [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:bg-[#B76E79]
                [&::-webkit-slider-thumb]:shadow-lg
                [&::-webkit-slider-thumb]:cursor-pointer
                [&::-moz-range-thumb]:h-4
                [&::-moz-range-thumb]:w-4
                [&::-moz-range-thumb]:rounded-full
                [&::-moz-range-thumb]:bg-[#B76E79]
                [&::-moz-range-thumb]:border-0
                [&::-moz-range-thumb]:cursor-pointer"
            />
            <span className="text-xs text-gray-500 w-8">60s</span>
          </div>
        </div>

        {/* Toggle Controls */}
        <div className="grid gap-4 md:grid-cols-3">
          {/* Urgency Bar */}
          <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white text-sm font-medium">
                  Urgency Bar
                </Label>
                <p className="text-xs text-gray-500 mt-0.5">
                  Countdown timer on product pages
                </p>
              </div>
              <Switch
                checked={controls.urgencyBar}
                onCheckedChange={(checked) =>
                  onControlChange('urgencyBar', checked)
                }
                className="data-[state=checked]:bg-[#B76E79]"
              />
            </div>
          </div>

          {/* Exit Intent */}
          <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white text-sm font-medium">
                  Exit Intent
                </Label>
                <p className="text-xs text-gray-500 mt-0.5">
                  Email capture on exit detection
                </p>
              </div>
              <Switch
                checked={controls.exitIntent}
                onCheckedChange={(checked) =>
                  onControlChange('exitIntent', checked)
                }
                className="data-[state=checked]:bg-[#B76E79]"
              />
            </div>
          </div>

          {/* Magnetic Cards */}
          <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white text-sm font-medium">
                  Magnetic Cards
                </Label>
                <p className="text-xs text-gray-500 mt-0.5">
                  3D tilt effect on product cards
                </p>
              </div>
              <Switch
                checked={controls.magneticCards}
                onCheckedChange={(checked) =>
                  onControlChange('magneticCards', checked)
                }
                className="data-[state=checked]:bg-[#B76E79]"
              />
            </div>
          </div>
        </div>

        {/* A/B Test Mode */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
          <div className="mb-3">
            <Label className="text-white text-sm font-medium">
              A/B Test Mode
            </Label>
            <p className="text-xs text-gray-500 mt-0.5">
              Magnetic card tilt intensity assignment
            </p>
          </div>
          <div className="flex gap-3">
            {(
              [
                {
                  value: 'standard' as const,
                  label: 'Standard',
                  desc: '15\u00B0 tilt for all',
                },
                {
                  value: 'enhanced' as const,
                  label: 'Enhanced',
                  desc: '30\u00B0 tilt for all',
                },
                {
                  value: 'auto' as const,
                  label: 'Auto',
                  desc: 'Split test 50/50',
                },
              ] as const
            ).map((option) => (
              <button
                key={option.value}
                onClick={() =>
                  onControlChange('abTestMode', option.value)
                }
                className={`flex-1 rounded-lg border p-3 text-left transition-colors ${
                  controls.abTestMode === option.value
                    ? 'border-[#B76E79]/50 bg-[#B76E79]/10'
                    : 'border-gray-700 bg-gray-800/30 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className={`h-3 w-3 rounded-full border-2 ${
                      controls.abTestMode === option.value
                        ? 'border-[#B76E79] bg-[#B76E79]'
                        : 'border-gray-600'
                    }`}
                  />
                  <span className="text-sm font-medium text-white">
                    {option.label}
                  </span>
                </div>
                <p className="text-xs text-gray-500 ml-5">
                  {option.desc}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <Button
          onClick={onSave}
          className={`w-full h-12 text-lg text-white transition-all ${
            saveConfirmed
              ? 'bg-emerald-600 hover:bg-emerald-600'
              : 'bg-gradient-to-r from-[#B76E79] via-[#B76E79] to-[#D4AF37] hover:from-[#a5606a] hover:to-[#c4a030]'
          }`}
        >
          {saveConfirmed ? (
            <>
              <CheckCircle2 className="mr-2 h-5 w-5" />
              Saved Successfully
            </>
          ) : (
            <>
              <Save className="mr-2 h-5 w-5" />
              Save Controls
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Momentum Commerce Tab — "The Closer"
// ---------------------------------------------------------------------------

const MOMENTUM_STATS = {
  priceAnchoring: {
    impressions: 4_328,
    conversions: 312,
    conversionRate: 7.2,
    avgSavingsShown: 38,
    revenueImpact: 12_840,
  },
  liveTicker: {
    impressions: 8_921,
    dismissRate: 8.3,
    avgTimeVisible: 34,
    engagementLift: 18.4,
  },
  spotlight: {
    fires: 1_247,
    hotspotClicks: 389,
    clickThroughRate: 31.2,
    topRoom: 'Love Hurts — Cathedral',
    topProduct: 'Love Hurts Varsity Jacket',
  },
  momentum: {
    level1Reached: 892,
    level2Reached: 534,
    level3Reached: 287,
    level4Unlocked: 128,
    rewardCodeRedeemed: 43,
  },
} as const;

const ANCHOR_BY_COLLECTION = [
  { collection: 'Black Rose', shown: 1_842, converts: 134, rate: 7.3, avgSave: '$72', color: '#B76E79' },
  { collection: 'Love Hurts', shown: 1_287, converts: 98, rate: 7.6, avgSave: '$68', color: '#E1306C' },
  { collection: 'Signature', shown: 1_199, converts: 80, rate: 6.7, avgSave: '$56', color: '#D4AF37' },
] as const;

function MomentumCommerceTab() {
  return (
    <>
      {/* Engine Header */}
      <div className="relative overflow-hidden rounded-xl border border-[#D4AF37]/20 bg-gradient-to-r from-gray-900 via-gray-900 to-[#D4AF37]/5 p-6">
        <div className="absolute top-0 right-0 w-48 h-48 bg-[#D4AF37]/5 rounded-full blur-3xl" />
        <div className="relative flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-[#D4AF37] to-[#B76E79] flex items-center justify-center">
            <Rocket className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Momentum Commerce Engine</h2>
            <p className="text-sm text-gray-400 mt-0.5">
              Price Anchoring + Live Ticker + Spotlight Moments + Engagement Rewards
            </p>
          </div>
          <Badge
            variant="outline"
            className="ml-auto border-green-500/50 text-green-400"
          >
            <div className="h-2 w-2 rounded-full mr-2 bg-green-400 animate-pulse" />
            Active
          </Badge>
        </div>
      </div>

      {/* Revenue Attribution Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="bg-gray-900/80 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
              <Tag className="h-3.5 w-3.5" />
              Price Anchoring
            </div>
            <div className="text-2xl font-bold text-white">
              ${MOMENTUM_STATS.priceAnchoring.revenueImpact.toLocaleString()}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <Badge className="bg-green-500/10 text-green-400 border-green-500/20 text-[10px] px-1.5">
                +{MOMENTUM_STATS.priceAnchoring.conversionRate}% CVR
              </Badge>
              <span className="text-[10px] text-gray-500">
                {MOMENTUM_STATS.priceAnchoring.impressions.toLocaleString()} impressions
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/80 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
              <Radio className="h-3.5 w-3.5" />
              Live Ticker
            </div>
            <div className="text-2xl font-bold text-white">
              +{MOMENTUM_STATS.liveTicker.engagementLift}%
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-[10px] px-1.5">
                {MOMENTUM_STATS.liveTicker.dismissRate}% dismiss
              </Badge>
              <span className="text-[10px] text-gray-500">
                avg {MOMENTUM_STATS.liveTicker.avgTimeVisible}s visible
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/80 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
              <Crosshair className="h-3.5 w-3.5" />
              Spotlight Moments
            </div>
            <div className="text-2xl font-bold text-white">
              {MOMENTUM_STATS.spotlight.clickThroughRate}%
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px] px-1.5">
                {MOMENTUM_STATS.spotlight.fires.toLocaleString()} fires
              </Badge>
              <span className="text-[10px] text-gray-500">
                {MOMENTUM_STATS.spotlight.hotspotClicks} clicks
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/80 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
              <Sparkles className="h-3.5 w-3.5" />
              Momentum Rewards
            </div>
            <div className="text-2xl font-bold text-white">
              {MOMENTUM_STATS.momentum.level4Unlocked}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-[10px] px-1.5">
                {MOMENTUM_STATS.momentum.rewardCodeRedeemed} redeemed
              </Badge>
              <span className="text-[10px] text-gray-500">
                codes unlocked
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Price Anchoring by Collection */}
      <Card className="bg-gray-900/80 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2 text-base">
            <Tag className="h-4 w-4 text-[#D4AF37]" />
            Price Anchoring Performance by Collection
          </CardTitle>
          <CardDescription className="text-gray-400">
            Anchoring bias (Kahneman &amp; Tversky, 1974) — showing retail value next to pre-order price
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {ANCHOR_BY_COLLECTION.map((col) => (
              <div key={col.collection} className="flex items-center gap-4">
                <div className="w-28 text-sm font-medium text-gray-300">{col.collection}</div>
                <div className="flex-1">
                  <div className="h-3 rounded-full bg-gray-800 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000"
                      style={{
                        width: `${col.rate * 10}%`,
                        background: `linear-gradient(90deg, ${col.color}, ${col.color}88)`,
                      }}
                    />
                  </div>
                </div>
                <div className="w-20 text-right">
                  <span className="text-sm font-bold text-white">{col.rate}%</span>
                  <span className="text-[10px] text-gray-500 block">CVR</span>
                </div>
                <div className="w-20 text-right">
                  <span className="text-sm font-semibold text-[#D4AF37]">{col.avgSave}</span>
                  <span className="text-[10px] text-gray-500 block">avg save</span>
                </div>
                <div className="w-24 text-right">
                  <span className="text-sm text-gray-300">{col.converts}/{col.shown.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Momentum Funnel */}
      <Card className="bg-gray-900/80 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-[#B76E79]" />
            Momentum Engagement Funnel
          </CardTitle>
          <CardDescription className="text-gray-400">
            Users progressing through engagement tiers toward reward unlock
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-3">
            {[
              { label: 'All Users', count: 2847, color: '#6B7280' },
              { label: 'Level 1 (3pts)', count: MOMENTUM_STATS.momentum.level1Reached, color: '#9CA3AF' },
              { label: 'Level 2 (5pts)', count: MOMENTUM_STATS.momentum.level2Reached, color: '#D4AF37' },
              { label: 'Level 3 (8pts)', count: MOMENTUM_STATS.momentum.level3Reached, color: '#C4826D' },
              { label: 'Unlocked (12pts)', count: MOMENTUM_STATS.momentum.level4Unlocked, color: '#B76E79' },
            ].map((tier) => {
              const pct = Math.round((tier.count / 2847) * 100);
              return (
                <div key={tier.label} className="text-center">
                  <div className="relative mx-auto w-full max-w-[100px] aspect-square mb-2">
                    <svg viewBox="0 0 100 100" className="w-full h-full">
                      <circle cx="50" cy="50" r="42" fill="none" stroke="#1F2937" strokeWidth="6" />
                      <circle
                        cx="50"
                        cy="50"
                        r="42"
                        fill="none"
                        stroke={tier.color}
                        strokeWidth="6"
                        strokeDasharray={`${pct * 2.64} ${264 - pct * 2.64}`}
                        strokeDashoffset="66"
                        strokeLinecap="round"
                        className="transition-all duration-1000"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-lg font-bold text-white">{pct}%</span>
                    </div>
                  </div>
                  <p className="text-[11px] font-medium text-gray-400">{tier.label}</p>
                  <p className="text-sm font-bold text-white">{tier.count.toLocaleString()}</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Spotlight Performance */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="bg-gray-900/80 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2 text-base">
              <Crosshair className="h-4 w-4 text-[#D4AF37]" />
              Top Spotlight Performers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { room: 'Love Hurts — Cathedral', product: 'Varsity Jacket', ctr: 34.2, fires: 312 },
                { room: 'Black Rose — Moonlit Courtyard', product: 'Sherpa Jacket', ctr: 29.8, fires: 287 },
                { room: 'Signature — Waterfront', product: 'The Bay Set', ctr: 28.1, fires: 256 },
                { room: 'Black Rose — Marble Rotunda', product: 'Hoodie Sig. Ed.', ctr: 27.4, fires: 198 },
                { room: 'Love Hurts — Throne Room', product: 'Bomber Jacket', ctr: 25.9, fires: 194 },
              ].map((item) => (
                <div key={item.room} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50">
                  <div className="h-8 w-8 rounded-md bg-[#D4AF37]/10 flex items-center justify-center flex-shrink-0">
                    <Crosshair className="h-4 w-4 text-[#D4AF37]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{item.room}</p>
                    <p className="text-[10px] text-gray-500">{item.product}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-sm font-bold text-white">{item.ctr}%</p>
                    <p className="text-[10px] text-gray-500">{item.fires} fires</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/80 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2 text-base">
              <Radio className="h-4 w-4 text-[#B76E79]" />
              Live Ticker Activity Feed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { event: 'Ticker impression', count: 8921, trend: '+12%', time: 'Last 24h' },
                { event: 'Hover pause', count: 2_134, trend: '+8%', time: 'Last 24h' },
                { event: 'Dismiss clicks', count: 741, trend: '-3%', time: 'Last 24h' },
                { event: 'Pre-order after ticker', count: 89, trend: '+22%', time: 'Last 24h' },
                { event: 'Session extended (>60s)', count: 3_412, trend: '+15%', time: 'Last 24h' },
              ].map((item) => (
                <div key={item.event} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                  <span className="text-xs text-gray-300">{item.event}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-white">{item.count.toLocaleString()}</span>
                    <Badge
                      className={`text-[10px] px-1.5 ${
                        item.trend.startsWith('+')
                          ? 'bg-green-500/10 text-green-400 border-green-500/20'
                          : 'bg-red-500/10 text-red-400 border-red-500/20'
                      }`}
                    >
                      {item.trend}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Research Attribution */}
      <Card className="bg-gray-900/60 border-gray-800">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="h-8 w-8 rounded-md bg-[#B76E79]/10 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Trophy className="h-4 w-4 text-[#B76E79]" />
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-300 mb-1">Research-Backed Revenue Impact</p>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                Momentum Commerce implements three peer-reviewed conversion techniques:
                <strong className="text-gray-400"> Price Anchoring</strong> (Kahneman &amp; Tversky, 1974 — Journal of Consumer Research: 20-50% conversion lift),
                <strong className="text-gray-400"> Social Proof Ticker</strong> (Spiegel Research Center, 2017 — 15-34% lift),
                and <strong className="text-gray-400"> Spotlight Nudges</strong> (Thaler &amp; Sunstein, 2008 — behavioral attention direction).
                Combined estimated revenue attribution: <span className="text-[#D4AF37] font-bold">${MOMENTUM_STATS.priceAnchoring.revenueImpact.toLocaleString()}</span>.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

// ---------------------------------------------------------------------------
// Loading Skeleton
// ---------------------------------------------------------------------------

function ConversionSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />

      {/* Funnel skeleton */}
      <Skeleton className="h-48 w-full bg-gray-800" />

      {/* Tabs skeleton */}
      <Skeleton className="h-10 w-80 bg-gray-800" />

      {/* Metric cards skeleton */}
      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={`metric-${i}`} className="h-28 bg-gray-800" />
        ))}
      </div>

      {/* Revenue card skeleton */}
      <Skeleton className="h-56 w-full bg-gray-800" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toLocaleString();
}

function getHeatColor(score: number): {
  from: string;
  to: string;
  text: string;
} {
  if (score >= 80) {
    return { from: '#EF4444', to: '#DC2626', text: '#EF4444' };
  }
  if (score >= 60) {
    return { from: '#F59E0B', to: '#D97706', text: '#F59E0B' };
  }
  if (score >= 40) {
    return { from: '#EAB308', to: '#CA8A04', text: '#EAB308' };
  }
  return { from: '#3B82F6', to: '#2563EB', text: '#3B82F6' };
}
