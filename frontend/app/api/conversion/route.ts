/**
 * Conversion Analytics API — Unified Event Collection
 *
 * POST /api/conversion
 *   Body: { events: ConversionEvent[] }
 *   Accepts batched events from WordPress CIE, Aurora, Pulse,
 *   Magnetic Obsidian, Cross-Sell, Journey Gamification, APE engines.
 *
 * GET /api/conversion
 *   Returns aggregated conversion metrics for the dashboard.
 *
 * Bridges WordPress-side client engines to Next.js dashboard analytics.
 */

import { NextRequest, NextResponse } from 'next/server';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ConversionEvent {
  event: string;
  timestamp: string;
  page: string;
  source: string;
  data: Record<string, unknown>;
}

interface AggregatedMetrics {
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
  top_products: Array<{
    sku: string;
    views: number;
    heat_score: number;
    cart_adds: number;
  }>;
  collection_breakdown: Record<string, {
    views: number;
    engagement_rate: number;
    conversion_rate: number;
  }>;
  hourly_trend: Array<{
    hour: string;
    events: number;
    conversions: number;
  }>;
}

// ---------------------------------------------------------------------------
// In-memory event store (bounded with LRU eviction)
// ---------------------------------------------------------------------------

const MAX_EVENTS = 50_000;
const events: ConversionEvent[] = [];
const sessionSet = new Set<string>();

function addEvents(batch: ConversionEvent[]): void {
  for (const event of batch) {
    if (events.length >= MAX_EVENTS) {
      events.shift(); // FIFO eviction
    }
    events.push(event);

    // Track unique sessions from page path
    if (event.data?.session_id) {
      sessionSet.add(String(event.data.session_id));
      if (sessionSet.size > 100_000) {
        // Evict oldest
        const first = sessionSet.values().next().value;
        if (first !== undefined) sessionSet.delete(first);
      }
    }
  }
}

function aggregateMetrics(): AggregatedMetrics {
  const funnel = {
    page_views: 0,
    product_views: 0,
    add_to_cart: 0,
    checkout_initiated: 0,
    pre_orders: 0,
  };

  const engagement = {
    avg_scroll_depth: 0,
    avg_time_on_page: 0,
    hotspot_clicks: 0,
    room_transitions: 0,
    panel_opens: 0,
  };

  const drivers = {
    social_proof_shown: 0,
    social_proof_clicks: 0,
    exit_intent_shown: 0,
    exit_intent_converted: 0,
    floating_cta_shown: 0,
    floating_cta_clicked: 0,
    bundle_suggestions_shown: 0,
    bundle_accepted: 0,
    journey_completed: 0,
    reward_claimed: 0,
  };

  const productMap = new Map<string, { views: number; heat: number; carts: number }>();
  const collectionMap = new Map<string, { views: number; engagements: number; conversions: number }>();
  const hourlyMap = new Map<string, { events: number; conversions: number }>();

  let scrollSum = 0;
  let scrollCount = 0;
  let timeSum = 0;
  let timeCount = 0;

  for (const ev of events) {
    const hour = ev.timestamp.slice(0, 13); // YYYY-MM-DDTHH
    const hourEntry = hourlyMap.get(hour) ?? { events: 0, conversions: 0 };
    hourEntry.events++;

    switch (ev.event) {
      case 'page_view':
        funnel.page_views++;
        break;
      case 'product_view':
      case 'panel_open':
        funnel.product_views++;
        engagement.panel_opens++;
        if (ev.data?.sku) {
          const sku = String(ev.data.sku);
          const prod = productMap.get(sku) ?? { views: 0, heat: 0, carts: 0 };
          prod.views++;
          prod.heat += Number(ev.data.heat_score ?? 5);
          productMap.set(sku, prod);
        }
        break;
      case 'add_to_cart':
        funnel.add_to_cart++;
        hourEntry.conversions++;
        if (ev.data?.sku) {
          const sku = String(ev.data.sku);
          const prod = productMap.get(sku) ?? { views: 0, heat: 0, carts: 0 };
          prod.carts++;
          productMap.set(sku, prod);
        }
        break;
      case 'checkout_initiated':
        funnel.checkout_initiated++;
        hourEntry.conversions++;
        break;
      case 'pre_order_completed':
        funnel.pre_orders++;
        hourEntry.conversions++;
        break;
      case 'hotspot_click':
        engagement.hotspot_clicks++;
        break;
      case 'room_transition':
        engagement.room_transitions++;
        break;
      case 'social_proof_shown':
        drivers.social_proof_shown++;
        break;
      case 'social_proof_clicked':
        drivers.social_proof_clicks++;
        break;
      case 'exit_intent_shown':
        drivers.exit_intent_shown++;
        break;
      case 'exit_intent_converted':
        drivers.exit_intent_converted++;
        hourEntry.conversions++;
        break;
      case 'floating_cta_shown':
        drivers.floating_cta_shown++;
        break;
      case 'floating_cta_clicked':
        drivers.floating_cta_clicked++;
        break;
      case 'bundle_suggestion_shown':
        drivers.bundle_suggestions_shown++;
        break;
      case 'bundle_accepted':
        drivers.bundle_accepted++;
        break;
      case 'journey_completed':
        drivers.journey_completed++;
        break;
      case 'reward_claimed':
        drivers.reward_claimed++;
        break;
      case 'scroll_depth':
        scrollSum += Number(ev.data?.depth ?? 0);
        scrollCount++;
        break;
      case 'time_on_page':
        timeSum += Number(ev.data?.seconds ?? 0);
        timeCount++;
        break;
    }

    // Track collection breakdown
    if (ev.data?.collection) {
      const col = String(ev.data.collection);
      const colEntry = collectionMap.get(col) ?? { views: 0, engagements: 0, conversions: 0 };
      colEntry.views++;
      if (['hotspot_click', 'panel_open', 'add_to_cart'].includes(ev.event)) {
        colEntry.engagements++;
      }
      if (['add_to_cart', 'pre_order_completed'].includes(ev.event)) {
        colEntry.conversions++;
      }
      collectionMap.set(col, colEntry);
    }

    hourlyMap.set(hour, hourEntry);
  }

  engagement.avg_scroll_depth = scrollCount > 0 ? Math.round(scrollSum / scrollCount) : 0;
  engagement.avg_time_on_page = timeCount > 0 ? Math.round(timeSum / timeCount) : 0;

  const topProducts = Array.from(productMap.entries())
    .map(([sku, data]) => ({
      sku,
      views: data.views,
      heat_score: data.views > 0 ? Math.round(data.heat / data.views) : 0,
      cart_adds: data.carts,
    }))
    .sort((a, b) => b.heat_score - a.heat_score)
    .slice(0, 10);

  const collectionBreakdown: AggregatedMetrics['collection_breakdown'] = {};
  for (const [col, data] of collectionMap.entries()) {
    collectionBreakdown[col] = {
      views: data.views,
      engagement_rate: data.views > 0 ? Math.round((data.engagements / data.views) * 100) : 0,
      conversion_rate: data.views > 0 ? Math.round((data.conversions / data.views) * 10000) / 100 : 0,
    };
  }

  const hourlyTrend = Array.from(hourlyMap.entries())
    .map(([hour, data]) => ({
      hour,
      events: data.events,
      conversions: data.conversions,
    }))
    .sort((a, b) => a.hour.localeCompare(b.hour))
    .slice(-24);

  return {
    total_events: events.length,
    unique_sessions: sessionSet.size,
    funnel,
    engagement,
    conversion_drivers: drivers,
    top_products: topProducts,
    collection_breakdown: collectionBreakdown,
    hourly_trend: hourlyTrend,
  };
}

// ---------------------------------------------------------------------------
// CORS helpers
// ---------------------------------------------------------------------------

const ALLOWED_ORIGINS = ['https://skyyrose.co', 'https://www.skyyrose.co'];

function corsHeaders(request?: NextRequest): HeadersInit {
  const origin = request?.headers.get('origin') ?? '';
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'X-Requested-With, Content-Type, Authorization',
    'Access-Control-Allow-Credentials': 'true',
  };
}

// ---------------------------------------------------------------------------
// Route handlers
// ---------------------------------------------------------------------------

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, { status: 204, headers: corsHeaders(request) });
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { events?: unknown[] };

    if (!Array.isArray(body.events) || body.events.length === 0) {
      return NextResponse.json(
        { success: false, error: 'events array is required' },
        { status: 400, headers: corsHeaders(request) }
      );
    }

    // Cap batch size to prevent abuse
    if (body.events.length > 500) {
      return NextResponse.json(
        { success: false, error: 'Maximum 500 events per batch' },
        { status: 400, headers: corsHeaders(request) }
      );
    }

    const validated: ConversionEvent[] = [];
    for (const raw of body.events) {
      if (
        typeof raw === 'object' &&
        raw !== null &&
        typeof (raw as Record<string, unknown>).event === 'string'
      ) {
        const r = raw as Record<string, unknown>;
        validated.push({
          event: String(r.event),
          timestamp: typeof r.timestamp === 'string' ? r.timestamp : new Date().toISOString(),
          page: typeof r.page === 'string' ? r.page : '/',
          source: typeof r.source === 'string' ? r.source : 'unknown',
          data: typeof r.data === 'object' && r.data !== null ? r.data as Record<string, unknown> : {},
        });
      }
    }

    addEvents(validated);

    return NextResponse.json(
      { success: true, accepted: validated.length, total_stored: events.length },
      { headers: corsHeaders(request) }
    );
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        { success: false, error: 'Invalid JSON' },
        { status: 400, headers: corsHeaders(request) }
      );
    }
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500, headers: corsHeaders(request) }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const metrics = aggregateMetrics();
    return NextResponse.json(
      { success: true, timestamp: new Date().toISOString(), metrics },
      { headers: corsHeaders(request) }
    );
  } catch {
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
