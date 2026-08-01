/**
 * Order aggregation for the Operator Console — derives every revenue/status
 * number the console shows from real `WcOrder[]` (lib/wp/client.ts#getOrders),
 * never from hardcoded figures. WooCommerce's real status enum is
 * pending|processing|on-hold|completed|cancelled|refunded|failed|trash — it
 * has no native "New"/"Shipped"/"Fulfilled" vocabulary, so `mapOrderStatus`
 * is an explicit, disclosed mapping, not a 1:1 passthrough.
 */
import type { CatalogProduct } from '@/lib/catalog';
import type { WcOrder } from '@/lib/wp/client';
import { statusPillColors } from './brand';

export interface OrderStatusView {
  label: string;
  bg: string;
  color: string;
}

/** Maps a real WC order status to the console's display vocabulary. */
export function mapOrderStatus(wcStatus: string, acc?: string): OrderStatusView {
  switch (wcStatus) {
    case 'completed':
      return { label: 'Fulfilled', ...statusPillColors('success') };
    case 'processing':
      return { label: 'Processing', ...statusPillColors('warning') };
    case 'shipped': // custom status some shipment-tracking plugins add
      return { label: 'Shipped', ...statusPillColors('accent', acc) };
    case 'pending':
      return { label: 'Pending', ...statusPillColors('idle') };
    case 'on-hold':
      return { label: 'New', ...statusPillColors('idle') };
    case 'cancelled':
      return { label: 'Cancelled', ...statusPillColors('danger') };
    case 'refunded':
      return { label: 'Refunded', ...statusPillColors('danger') };
    case 'failed':
      return { label: 'Failed', ...statusPillColors('danger') };
    default:
      return { label: wcStatus, ...statusPillColors('idle') };
  }
}

export function orderTotal(order: WcOrder): number {
  const total = order.total;
  return typeof total === 'string' || typeof total === 'number' ? Number(total) || 0 : 0;
}

export function orderCustomerName(order: WcOrder): string {
  const billing = order.billing as { first_name?: string; last_name?: string } | undefined;
  const first = billing?.first_name?.trim() ?? '';
  const last = billing?.last_name?.trim() ?? '';
  if (!first && !last) return 'Guest';
  const lastInitial = last ? `${last[0]}.` : '';
  return first && last ? `${first} ${lastInitial}` : first || last;
}

interface OrderLineItem {
  name?: string;
  sku?: string;
  quantity?: number;
  total?: string | number;
}

export function orderLineItems(order: WcOrder): OrderLineItem[] {
  return Array.isArray(order.line_items) ? (order.line_items as OrderLineItem[]) : [];
}

/** "Piece" column: first line item's name, "+N more" suffixed if there are others. */
export function orderPieceSummary(order: WcOrder): string {
  const items = orderLineItems(order);
  if (items.length === 0) return '—';
  const first = items[0];
  const qty = first.quantity && first.quantity > 1 ? ` ×${first.quantity}` : '';
  const extra = items.length > 1 ? ` +${items.length - 1} more` : '';
  return `${first.name ?? 'Item'}${qty}${extra}`;
}

/** Best-effort collection slug for an order via its first line item's SKU. */
export function orderCollection(order: WcOrder, skuToCollection: Map<string, string>): string {
  const items = orderLineItems(order);
  for (const item of items) {
    const collection = item.sku ? skuToCollection.get(item.sku) : undefined;
    if (collection) return collection;
  }
  return 'Other';
}

export function buildSkuToCollectionMap(products: CatalogProduct[]): Map<string, string> {
  return new Map(products.map((p) => [p.sku, p.collection]));
}

export interface RevenueKpis {
  revenue: number;
  orderCount: number;
  avgOrder: number;
}

export function computeKpis(orders: WcOrder[]): RevenueKpis {
  const revenueOrders = orders.filter((o) => !['cancelled', 'refunded', 'failed', 'trash'].includes(o.status));
  const revenue = revenueOrders.reduce((sum, o) => sum + orderTotal(o), 0);
  const orderCount = revenueOrders.length;
  const avgOrder = orderCount > 0 ? revenue / orderCount : 0;
  return { revenue, orderCount, avgOrder };
}

export interface CollectionRevenue {
  slug: string;
  revenue: number;
  share: number;
}

/** Revenue per collection, attributed via each order's line-item SKUs. */
export function revenueByCollection(orders: WcOrder[], skuToCollection: Map<string, string>): CollectionRevenue[] {
  const totals = new Map<string, number>();
  for (const order of orders) {
    if (['cancelled', 'refunded', 'failed', 'trash'].includes(order.status)) continue;
    for (const item of orderLineItems(order)) {
      const collection = item.sku ? skuToCollection.get(item.sku) : undefined;
      if (!collection) continue;
      const lineTotal = typeof item.total === 'string' || typeof item.total === 'number' ? Number(item.total) || 0 : 0;
      totals.set(collection, (totals.get(collection) ?? 0) + lineTotal);
    }
  }
  const grandTotal = Array.from(totals.values()).reduce((a, b) => a + b, 0);
  return Array.from(totals.entries())
    .map(([slug, revenue]) => ({ slug, revenue, share: grandTotal > 0 ? revenue / grandTotal : 0 }))
    .sort((a, b) => b.revenue - a.revenue);
}

export interface CustomerAggregate {
  orderCount: number;
  spend: number;
}

export function orderDate(order: WcOrder): Date | null {
  const raw = order.date_created;
  if (typeof raw !== 'string') return null;
  const d = new Date(raw);
  return Number.isNaN(d.getTime()) ? null : d;
}

export type Timeframe = 'Today' | '7 Days' | '30 Days';

const TIMEFRAME_DAYS: Record<Timeframe, number> = { Today: 1, '7 Days': 7, '30 Days': 30 };

/** Client-side slice of an already-fetched order batch — no extra network
 *  call per timeframe switch. `referenceDate` should be the batch's own
 *  latest order date (stable across renders), not `new Date()`. */
export function filterByTimeframe(orders: WcOrder[], timeframe: Timeframe, referenceDate: Date): WcOrder[] {
  const days = TIMEFRAME_DAYS[timeframe];
  const cutoff = referenceDate.getTime() - days * 24 * 60 * 60 * 1000;
  return orders.filter((o) => {
    const d = orderDate(o);
    return d !== null && d.getTime() >= cutoff;
  });
}

/** Daily trailing buckets (oldest first) ending at `referenceDate`, for KPI
 *  card sparklines. `metric` picks revenue-sum or order-count per day. */
export function dailySeries(orders: WcOrder[], days: number, referenceDate: Date, metric: 'revenue' | 'count'): number[] {
  const buckets = new Array(days).fill(0) as number[];
  const msPerDay = 24 * 60 * 60 * 1000;
  const windowStart = referenceDate.getTime() - days * msPerDay;

  for (const order of orders) {
    if (['cancelled', 'refunded', 'failed', 'trash'].includes(order.status)) continue;
    const d = orderDate(order);
    if (!d) continue;
    const offsetMs = d.getTime() - windowStart;
    if (offsetMs < 0) continue;
    const bucket = Math.min(days - 1, Math.floor(offsetMs / msPerDay));
    buckets[bucket] += metric === 'revenue' ? orderTotal(order) : 1;
  }
  return buckets;
}

export function latestOrderDate(orders: WcOrder[]): Date {
  return orders.reduce<Date | null>((latest, o) => {
    const d = orderDate(o);
    return d && (!latest || d > latest) ? d : latest;
  }, null) ?? new Date(0);
}

/** Buckets orders into `weeks` trailing 7-day windows, oldest first, for the
 *  revenue chart's x-axis. `weeksAgo` shifts the whole window back further
 *  (e.g. weeksAgo=5 with weeks=5 gets the *prior* 5-week period for the
 *  chart's comparison line). Real orders only — no synthetic data. */
export function weeklyRevenueSeries(orders: WcOrder[], weeks = 5, weeksAgo = 0): number[] {
  const now = orders.reduce<Date | null>((latest, o) => {
    const d = orderDate(o);
    return d && (!latest || d > latest) ? d : latest;
  }, null) ?? new Date(0);

  const buckets = new Array(weeks).fill(0) as number[];
  const msPerWeek = 7 * 24 * 60 * 60 * 1000;
  const windowEnd = now.getTime() - weeksAgo * msPerWeek;
  const windowStart = windowEnd - weeks * msPerWeek;

  for (const order of orders) {
    if (['cancelled', 'refunded', 'failed', 'trash'].includes(order.status)) continue;
    const d = orderDate(order);
    if (!d) continue;
    const offsetMs = d.getTime() - windowStart;
    if (offsetMs < 0 || d.getTime() > windowEnd) continue;
    const bucket = Math.min(weeks - 1, Math.floor(offsetMs / msPerWeek));
    buckets[bucket] += orderTotal(order);
  }
  return buckets;
}

export function aggregateByCustomer(orders: WcOrder[]): Map<number, CustomerAggregate> {
  const map = new Map<number, CustomerAggregate>();
  for (const order of orders) {
    const id = typeof order.customer_id === 'number' ? order.customer_id : 0;
    if (id === 0) continue; // guest checkout — no customer record to attribute to
    if (['cancelled', 'refunded', 'failed', 'trash'].includes(order.status)) continue;
    const existing = map.get(id) ?? { orderCount: 0, spend: 0 };
    map.set(id, { orderCount: existing.orderCount + 1, spend: existing.spend + orderTotal(order) });
  }
  return map;
}
