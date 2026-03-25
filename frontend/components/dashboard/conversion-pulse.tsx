'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  DollarSign,
  TrendingUp,
  ShoppingBag,
  ShoppingCart,
  Eye,
  BarChart2,
} from 'lucide-react';

// ─── Brand ───────────────────────────────────────────────────────────────────

const BRAND = {
  roseGold: '#B76E79',
  gold: '#D4AF37',
} as const;

// ─── Types ────────────────────────────────────────────────────────────────────

type EventType = 'pre-order' | 'add-to-cart' | 'page-view';

interface Collection {
  name: string;
  color: string;
  bg: string;
}

interface ConversionEvent {
  id: string;
  ts: Date;
  type: EventType;
  product: string;
  collection: Collection;
  amount: number | null;
}

interface SparkPoint {
  minute: number;
  conversions: number;
}

interface LiveMetrics {
  liveVisitors: number;
  todayRevenue: number;
  conversionRate: number;
  avgOrderValue: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const COLLECTIONS: Record<string, Collection> = {
  'Black Rose': {
    name: 'Black Rose',
    color: '#B76E79',
    bg: 'rgba(183,110,121,0.15)',
  },
  'Love Hurts': {
    name: 'Love Hurts',
    color: '#D4AF37',
    bg: 'rgba(212,175,55,0.15)',
  },
  Signature: {
    name: 'Signature',
    color: '#818CF8',
    bg: 'rgba(129,140,248,0.15)',
  },
};

const PRODUCTS: Array<{ name: string; collection: string; price: number }> = [
  { name: 'BLACK Rose Hoodie', collection: 'Black Rose', price: 185 },
  { name: 'BLACK Rose Sherpa Jacket', collection: 'Black Rose', price: 245 },
  { name: 'BLACK Rose Varsity', collection: 'Black Rose', price: 220 },
  { name: 'Love Hurts Hoodie', collection: 'Love Hurts', price: 185 },
  { name: 'Love Hurts Varsity Jacket', collection: 'Love Hurts', price: 245 },
  { name: 'Love Hurts Tee', collection: 'Love Hurts', price: 65 },
  { name: 'Signature Rose Gold Hoodie', collection: 'Signature', price: 195 },
  { name: 'Signature Bomber Jacket', collection: 'Signature', price: 265 },
  { name: 'Signature Polo', collection: 'Signature', price: 95 },
];

const EVENT_TYPE_CONFIG: Record<
  EventType,
  { label: string; icon: React.ComponentType<{ className?: string }>; color: string }
> = {
  'pre-order': { label: 'Pre-Order', icon: ShoppingBag, color: '#4ade80' },
  'add-to-cart': { label: 'Add to Cart', icon: ShoppingCart, color: BRAND.roseGold },
  'page-view': { label: 'Page View', icon: Eye, color: '#60a5fa' },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

function randomBetween(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function generateEvent(): ConversionEvent {
  const rand = Math.random();
  const type: EventType =
    rand < 0.15 ? 'pre-order' : rand < 0.45 ? 'add-to-cart' : 'page-view';

  const product = PRODUCTS[randomBetween(0, PRODUCTS.length - 1)];
  const collection = COLLECTIONS[product.collection];

  const amount =
    type === 'pre-order'
      ? product.price
      : type === 'add-to-cart'
      ? product.price
      : null;

  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    ts: new Date(),
    type,
    product: product.name,
    collection,
    amount,
  };
}

// ─── Sparkline SVG ───────────────────────────────────────────────────────────

function Sparkline({ data }: { data: SparkPoint[] }) {
  const W = 280;
  const H = 40;
  const maxVal = Math.max(...data.map((d) => d.conversions), 1);

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * W;
    const y = H - (d.conversions / maxVal) * (H - 4) - 2;
    return `${x},${y}`;
  });

  const polylineStr = points.join(' ');

  // Area fill path
  const areaPath =
    data.length > 1
      ? `M0,${H} ` +
        points.join(' L') +
        ` L${W},${H} Z`
      : '';

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      aria-label="Conversion trend sparkline"
    >
      <defs>
        <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={BRAND.roseGold} stopOpacity="0.35" />
          <stop offset="100%" stopColor={BRAND.roseGold} stopOpacity="0.0" />
        </linearGradient>
      </defs>
      {areaPath && (
        <path d={areaPath} fill="url(#sparkFill)" />
      )}
      {data.length > 1 && (
        <polyline
          points={polylineStr}
          fill="none"
          stroke={BRAND.roseGold}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      {/* Current value dot */}
      {data.length > 0 && (
        <circle
          cx={W}
          cy={
            H -
            (data[data.length - 1].conversions / maxVal) * (H - 4) -
            2
          }
          r="3"
          fill={BRAND.roseGold}
        />
      )}
    </svg>
  );
}

// ─── Animated Counter Hook ────────────────────────────────────────────────────

function useAnimatedCounter(target: number, duration = 600): number {
  const [count, setCount] = useState(target);
  const startRef = useRef<number | null>(null);
  const frameRef = useRef<number>(0);
  const prevTargetRef = useRef(target);

  useEffect(() => {
    const from = prevTargetRef.current;
    prevTargetRef.current = target;
    startRef.current = null;

    function animate(ts: number) {
      if (startRef.current === null) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(from + (target - from) * eased));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    }

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target, duration]);

  return count;
}

// ─── Top Metric Card ──────────────────────────────────────────────────────────

function MetricChip({
  label,
  value,
  icon: Icon,
  color,
  pulse,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  pulse?: boolean;
}) {
  return (
    <div
      className="flex flex-col gap-1.5 rounded-xl p-3 border border-gray-800 transition-all hover:border-gray-700"
      style={{
        background: 'rgba(17,17,17,0.7)',
        backdropFilter: 'blur(12px)',
      }}
    >
      <div className="flex items-center gap-2">
        {pulse && (
          <span className="relative flex h-2.5 w-2.5 shrink-0">
            <span
              className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
              style={{ backgroundColor: color }}
            />
            <span
              className="relative inline-flex h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: color }}
            />
          </span>
        )}
        {!pulse && <span className="shrink-0" style={{ color }}><Icon className="h-3.5 w-3.5" /></span>}
        <span className="text-xs text-gray-400 truncate">{label}</span>
      </div>
      <p
        className="text-lg font-bold tabular-nums leading-none"
        style={{ color }}
      >
        {value}
      </p>
    </div>
  );
}

// ─── Event Row ────────────────────────────────────────────────────────────────

function EventRow({ event }: { event: ConversionEvent }) {
  const cfg = EVENT_TYPE_CONFIG[event.type];
  const Icon = cfg.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 60, scale: 0.97 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: -30, scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 340, damping: 30 }}
      className="flex items-center gap-3 rounded-lg px-3 py-2.5 border border-gray-800/60 transition-colors hover:border-gray-700/80"
      style={{
        background: 'rgba(24,24,27,0.55)',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Event type icon */}
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
        style={{
          background: `${cfg.color}18`,
          border: `1px solid ${cfg.color}30`,
        }}
      >
        <span style={{ color: cfg.color }}><Icon className="h-4 w-4" /></span>
      </div>

      {/* Product + collection */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-white leading-tight">
          {event.product}
        </p>
        <div className="mt-0.5 flex items-center gap-2">
          <span
            className="inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold leading-none"
            style={{
              color: event.collection.color,
              background: event.collection.bg,
              border: `1px solid ${event.collection.color}30`,
            }}
          >
            {event.collection.name}
          </span>
          <span
            className="text-[10px] font-medium rounded-full px-1.5 py-0.5 leading-none"
            style={{
              color: cfg.color,
              background: `${cfg.color}18`,
            }}
          >
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Amount + timestamp */}
      <div className="flex shrink-0 flex-col items-end gap-0.5">
        {event.amount !== null ? (
          <span className="text-sm font-bold" style={{ color: cfg.color }}>
            ${event.amount}
          </span>
        ) : (
          <span className="text-xs text-gray-600">—</span>
        )}
        <span className="text-[10px] font-mono text-gray-600">
          {formatTime(event.ts)}
        </span>
      </div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

const MAX_EVENTS = 20;
const SPARK_MINUTES = 12;

export function ConversionPulse() {
  // Event stream
  const [events, setEvents] = useState<ConversionEvent[]>(() =>
    Array.from({ length: 6 }, generateEvent)
  );

  // Sparkline: conversions per minute over last SPARK_MINUTES
  const [spark, setSpark] = useState<SparkPoint[]>(() =>
    Array.from({ length: SPARK_MINUTES }, (_, i) => ({
      minute: i,
      conversions: randomBetween(0, 8),
    }))
  );

  // Live metrics
  const [metrics, setMetrics] = useState<LiveMetrics>({
    liveVisitors: randomBetween(180, 320),
    todayRevenue: randomBetween(4200, 6800),
    conversionRate: parseFloat((Math.random() * 4 + 3.5).toFixed(1)),
    avgOrderValue: randomBetween(165, 225),
  });

  // Schedule next event
  const scheduleNext = useCallback(() => {
    const delay = randomBetween(3000, 8000);
    return setTimeout(() => {
      const evt = generateEvent();

      setEvents((prev) => [evt, ...prev].slice(0, MAX_EVENTS));

      // Update sparkline current minute bucket
      setSpark((prev) => {
        const updated = [...prev];
        updated[SPARK_MINUTES - 1] = {
          ...updated[SPARK_MINUTES - 1],
          conversions:
            evt.type !== 'page-view'
              ? updated[SPARK_MINUTES - 1].conversions + 1
              : updated[SPARK_MINUTES - 1].conversions,
        };
        return updated;
      });

      // Nudge metrics
      setMetrics((prev) => {
        const revenueGain =
          evt.type === 'pre-order' && evt.amount ? evt.amount : 0;
        const newRevenue = prev.todayRevenue + revenueGain;
        const newVisitors = Math.max(
          80,
          Math.min(500, prev.liveVisitors + randomBetween(-6, 9))
        );
        const newConvRate = parseFloat(
          Math.max(
            1.5,
            Math.min(12, prev.conversionRate + (Math.random() - 0.47) * 0.15)
          ).toFixed(1)
        );
        return {
          liveVisitors: newVisitors,
          todayRevenue: newRevenue,
          conversionRate: newConvRate,
          avgOrderValue: prev.avgOrderValue,
        };
      });
    }, delay);
  }, []);

  // Rolling event timer
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    function loop() {
      timer = scheduleNext();
      // After a random delay, schedule the next call
      // We chain via the setTimeout callback itself — each fired event reschedules
    }

    // Self-rescheduling loop
    function fire() {
      const evt = generateEvent();
      setEvents((prev) => [evt, ...prev].slice(0, MAX_EVENTS));
      setSpark((prev) => {
        const updated = [...prev];
        updated[SPARK_MINUTES - 1] = {
          ...updated[SPARK_MINUTES - 1],
          conversions:
            evt.type !== 'page-view'
              ? updated[SPARK_MINUTES - 1].conversions + 1
              : updated[SPARK_MINUTES - 1].conversions,
        };
        return updated;
      });
      setMetrics((prev) => {
        const revenueGain =
          evt.type === 'pre-order' && evt.amount ? evt.amount : 0;
        return {
          liveVisitors: Math.max(
            80,
            Math.min(500, prev.liveVisitors + randomBetween(-6, 9))
          ),
          todayRevenue: prev.todayRevenue + revenueGain,
          conversionRate: parseFloat(
            Math.max(
              1.5,
              Math.min(12, prev.conversionRate + (Math.random() - 0.47) * 0.15)
            ).toFixed(1)
          ),
          avgOrderValue: prev.avgOrderValue,
        };
      });
      timer = setTimeout(fire, randomBetween(3000, 8000));
    }

    timer = setTimeout(fire, randomBetween(2000, 5000));
    return () => clearTimeout(timer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Advance sparkline bucket every 60 s
  useEffect(() => {
    const interval = setInterval(() => {
      setSpark((prev) => [
        ...prev.slice(1),
        { minute: prev[prev.length - 1].minute + 1, conversions: 0 },
      ]);
    }, 60_000);
    return () => clearInterval(interval);
  }, []);

  // Animated counters
  const animVisitors = useAnimatedCounter(metrics.liveVisitors);
  const animRevenue = useAnimatedCounter(metrics.todayRevenue);
  const animAOV = useAnimatedCounter(metrics.avgOrderValue);

  return (
    <Card
      className="overflow-hidden border-rose-500/20 transition-all hover:border-rose-500/40"
      style={{
        background: 'rgba(17,17,17,0.65)',
        backdropFilter: 'blur(24px) saturate(1.3)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.3)',
      }}
    >
      {/* Animated top accent bar */}
      <div
        className="h-[3px]"
        style={{
          background: `linear-gradient(90deg, ${BRAND.roseGold}, ${BRAND.gold}, ${BRAND.roseGold})`,
          backgroundSize: '200% 100%',
          animation: 'cpGradientShift 5s ease-in-out infinite',
        }}
      />

      <style>{`
        @keyframes cpGradientShift {
          0%, 100% { background-position: 0% 50%; }
          50%       { background-position: 100% 50%; }
        }
      `}</style>

      {/* ── Header ─────────────────────────────────────────────── */}
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
              style={{
                background: `linear-gradient(135deg, ${BRAND.roseGold}22, ${BRAND.gold}10)`,
                border: `1px solid ${BRAND.roseGold}30`,
              }}
            >
              <span style={{ color: BRAND.roseGold }}><BarChart2 className="h-5 w-5" /></span>
            </div>
            <div>
              <CardTitle className="text-white font-bold tracking-tight">
                Conversion Pulse
              </CardTitle>
              <CardDescription className="text-gray-400 font-medium">
                Live sales measurement &amp; event feed
              </CardDescription>
            </div>
          </div>

          {/* LIVE badge */}
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span
                className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
                style={{ backgroundColor: BRAND.roseGold }}
              />
              <span
                className="relative inline-flex h-3 w-3 rounded-full"
                style={{ backgroundColor: BRAND.roseGold }}
              />
            </span>
            <Badge
              className="border px-2 py-0.5 text-xs font-bold"
              style={{
                borderColor: `${BRAND.roseGold}40`,
                background: `${BRAND.roseGold}12`,
                color: BRAND.roseGold,
              }}
            >
              LIVE
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5 pb-5">
        {/* ── 4 Key Metrics ─────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
          <MetricChip
            label="Live Visitors"
            value={animVisitors.toLocaleString()}
            icon={Users}
            color={BRAND.roseGold}
            pulse
          />
          <MetricChip
            label="Today's Revenue"
            value={`$${animRevenue.toLocaleString()}`}
            icon={DollarSign}
            color="#4ade80"
          />
          <MetricChip
            label="Conversion Rate"
            value={`${metrics.conversionRate}%`}
            icon={TrendingUp}
            color={BRAND.gold}
          />
          <MetricChip
            label="Avg Order Value"
            value={`$${animAOV}`}
            icon={ShoppingBag}
            color="#60a5fa"
          />
        </div>

        {/* ── Sparkline ─────────────────────────────────────────── */}
        <div
          className="rounded-xl border border-gray-800 px-4 py-3"
          style={{
            background: 'rgba(24,24,27,0.5)',
            backdropFilter: 'blur(8px)',
          }}
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400">
              Conversion trend — last 12 min
            </span>
            <span className="text-[10px] font-mono text-gray-600">
              pre-orders + add-to-carts
            </span>
          </div>
          <Sparkline data={spark} />
        </div>

        {/* ── Live Event Feed ───────────────────────────────────── */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-300">
              Live Event Feed
            </span>
            <span className="text-[10px] text-gray-600">
              {events.length} recent events
            </span>
          </div>

          {/* Scrollable list — max 380 px tall */}
          <div
            className="space-y-1.5 overflow-y-auto pr-1"
            style={{ maxHeight: '380px' }}
          >
            <AnimatePresence initial={false}>
              {events.map((evt) => (
                <EventRow key={evt.id} event={evt} />
              ))}
            </AnimatePresence>
          </div>
        </div>

        {/* ── Legend ───────────────────────────────────────────── */}
        <div className="flex flex-wrap items-center gap-3 pt-1">
          {(Object.entries(EVENT_TYPE_CONFIG) as Array<[EventType, (typeof EVENT_TYPE_CONFIG)[EventType]]>).map(
            ([type, cfg]) => {
              const Icon = cfg.icon;
              return (
                <div key={type} className="flex items-center gap-1.5">
                  <span style={{ color: cfg.color }}><Icon className="h-3 w-3" /></span>
                  <span className="text-[10px] text-gray-500">{cfg.label}</span>
                </div>
              );
            }
          )}
          <span className="ml-auto text-[10px] text-gray-700">
            Events generate every 3–8 s
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export default ConversionPulse;
