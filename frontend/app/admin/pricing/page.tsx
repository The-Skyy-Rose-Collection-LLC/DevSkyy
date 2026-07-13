'use client';

import { useState, type FormEvent } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { LoadingState } from '@/components/shared/LoadingState';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { Tag, TrendingUp, TrendingDown, Minus, Loader2, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api';
import type { DynamicPricingResponse, DynamicPricingRequest } from '@/lib/api/types';

const STRATEGY_OPTIONS: { value: NonNullable<DynamicPricingRequest['strategy']>; label: string; description: string }[] = [
  { value: 'ml_optimized', label: 'ML Optimized', description: 'Machine learning price optimization' },
  { value: 'competitive', label: 'Competitive', description: 'Match or beat competitor pricing' },
  { value: 'demand_based', label: 'Demand Based', description: 'Adjust based on demand signals' },
  { value: 'time_based', label: 'Time Based', description: 'Dynamic pricing by time of day/week' },
];

function parseSkus(raw: string): string[] {
  return Array.from(
    new Set(
      raw
        .split(/[\s,]+/)
        .map((s) => s.trim())
        .filter(Boolean)
    )
  );
}

export default function PricingPage() {
  const [skuInput, setSkuInput] = useState('');
  const [strategy, setStrategy] = useState<NonNullable<DynamicPricingRequest['strategy']>>('ml_optimized');
  const [minMargin, setMinMargin] = useState('');
  const [maxDiscount, setMaxDiscount] = useState('');

  const [submittedCount, setSubmittedCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DynamicPricingResponse | null>(null);

  const skus = parseSkus(skuInput);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (skus.length === 0) {
      setError('Enter at least one SKU to optimize.');
      return;
    }

    const constraints: Record<string, unknown> = {};
    if (minMargin.trim()) constraints.min_margin = Number(minMargin);
    if (maxDiscount.trim()) constraints.max_discount = Number(maxDiscount);

    setLoading(true);
    setError(null);
    setResult(null);
    setSubmittedCount(skus.length);
    try {
      const response = await api.pricing.optimize({
        product_ids: skus,
        strategy,
        constraints: Object.keys(constraints).length > 0 ? constraints : undefined,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Price optimization failed');
    } finally {
      setLoading(false);
    }
  }

  const skippedCount = result ? Math.max(0, submittedCount - result.optimizations.length) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Tag className="h-7 w-7 text-rose-400" />
          Dynamic Pricing
        </h1>
        <p className="text-gray-400 mt-1">
          Run ML-driven price optimization across SKUs using market intelligence and demand signals
        </p>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle>Optimize Pricing</CardTitle>
          <CardDescription>Enter SKUs (comma or newline separated) and choose a strategy</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="pricing-skus">Product SKUs</Label>
              <Textarea
                id="pricing-skus"
                value={skuInput}
                onChange={(e) => setSkuInput(e.target.value)}
                placeholder="br-001, sg-002, lh-003"
                className="bg-gray-800 border-gray-700 text-white font-mono text-sm"
                rows={3}
              />
              <p className="text-xs text-gray-500">
                {skus.length} SKU{skus.length === 1 ? '' : 's'} parsed
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Strategy</Label>
                <Select value={strategy} onValueChange={(v) => setStrategy(v as typeof strategy)}>
                  <SelectTrigger aria-label="Pricing strategy" className="bg-gray-800 border-gray-700 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STRATEGY_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  {STRATEGY_OPTIONS.find((o) => o.value === strategy)?.description}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="pricing-min-margin">Min Margin (optional, 0-1)</Label>
                <Input
                  id="pricing-min-margin"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={minMargin}
                  onChange={(e) => setMinMargin(e.target.value)}
                  placeholder="0.20"
                  className="bg-gray-800 border-gray-700 text-white"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pricing-max-discount">Max Discount (optional, 0-1)</Label>
                <Input
                  id="pricing-max-discount"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={maxDiscount}
                  onChange={(e) => setMaxDiscount(e.target.value)}
                  placeholder="0.30"
                  className="bg-gray-800 border-gray-700 text-white"
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <Button type="submit" disabled={loading} className="bg-rose-500 hover:bg-rose-600">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Optimizing...
                </>
              ) : (
                'Optimize Pricing'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle>Results</CardTitle>
          <CardDescription>Recommended price changes from the last optimization run</CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <LoadingState message="Running pricing agent..." />}

          {!loading && !result && !error && (
            <EmptyState
              icon={Tag}
              title="No optimization run yet"
              description="Enter SKUs above and run an optimization to see recommended pricing."
            />
          )}

          {!loading && error && !result && (
            <ErrorState title="Optimization failed" message={error} />
          )}

          {!loading && result && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3 text-sm text-gray-400">
                <Badge variant="outline" className="border-gray-700 text-gray-300">
                  {result.strategy.replace('_', ' ')}
                </Badge>
                <span>{result.total_products} product{result.total_products === 1 ? '' : 's'} optimized</span>
                <span>{new Date(result.timestamp).toLocaleString()}</span>
                {skippedCount > 0 && (
                  <span className="text-amber-400">
                    {skippedCount} SKU{skippedCount === 1 ? '' : 's'} skipped (not in catalog or no recommendation)
                  </span>
                )}
              </div>

              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-transparent">
                    <TableHead className="text-gray-400">SKU</TableHead>
                    <TableHead className="text-gray-400 text-right">Current Price</TableHead>
                    <TableHead className="text-gray-400 text-right">Optimized Price</TableHead>
                    <TableHead className="text-gray-400 text-right">Change</TableHead>
                    <TableHead className="text-gray-400 text-right">Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.optimizations.map((opt) => {
                    const isUp = opt.price_change > 0;
                    const isDown = opt.price_change < 0;
                    return (
                      <TableRow key={opt.product_id} className="border-gray-800 hover:bg-gray-800/50">
                        <TableCell className="font-mono text-white">{opt.product_id}</TableCell>
                        <TableCell className="text-right text-gray-300">${opt.current_price.toFixed(2)}</TableCell>
                        <TableCell className="text-right text-white font-medium">
                          ${opt.optimized_price.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right">
                          <span
                            className={`inline-flex items-center gap-1 justify-end ${isUp ? 'text-emerald-400' : isDown ? 'text-red-400' : 'text-gray-500'
                              }`}
                          >
                            {isUp ? <TrendingUp className="h-3.5 w-3.5" /> : isDown ? <TrendingDown className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
                            {opt.price_change_pct > 0 ? '+' : ''}{opt.price_change_pct.toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell className="text-right text-gray-300">
                          {(opt.confidence * 100).toFixed(0)}%
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
