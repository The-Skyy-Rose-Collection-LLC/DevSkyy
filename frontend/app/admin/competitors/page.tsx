'use client';

import { useState, type FormEvent } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from '@/components/ui/dialog';
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
import { Binoculars, Plus, Trash2, ShieldAlert, ExternalLink, Loader2 } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import type { CompetitorCategory, PricePositioning } from '@/lib/api/types';

const CATEGORY_OPTIONS: { value: CompetitorCategory; label: string }[] = [
  { value: 'direct', label: 'Direct' },
  { value: 'indirect', label: 'Indirect' },
  { value: 'aspirational', label: 'Aspirational' },
  { value: 'emerging', label: 'Emerging' },
];

const PRICE_OPTIONS: { value: PricePositioning; label: string }[] = [
  { value: 'budget', label: 'Budget' },
  { value: 'mid_range', label: 'Mid-Range' },
  { value: 'premium', label: 'Premium' },
  { value: 'luxury', label: 'Luxury' },
  { value: 'ultra_luxury', label: 'Ultra Luxury' },
];

const CATEGORY_BADGE: Record<CompetitorCategory, string> = {
  direct: 'border-rose-600 text-rose-400',
  indirect: 'border-blue-600 text-blue-400',
  aspirational: 'border-purple-600 text-purple-400',
  emerging: 'border-emerald-600 text-emerald-400',
};

const emptyForm = {
  name: '',
  category: 'direct' as CompetitorCategory,
  price_positioning: 'premium' as PricePositioning,
  website: '',
  notes: '',
};

export default function CompetitorsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['competitors'],
    queryFn: async () => {
      const [list, summary, analytics] = await Promise.all([
        api.competitors.list(),
        api.competitors.summary(),
        api.competitors.styleAnalytics(),
      ]);
      return { list, summary, analytics };
    },
    retry: false,
  });

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      await api.competitors.create({
        name: form.name.trim(),
        category: form.category,
        price_positioning: form.price_positioning,
        website: form.website.trim() || undefined,
        notes: form.notes.trim() || undefined,
      });
      setForm(emptyForm);
      setShowCreate(false);
      await queryClient.invalidateQueries({ queryKey: ['competitors'] });
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create competitor');
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await api.competitors.remove(id);
      await queryClient.invalidateQueries({ queryKey: ['competitors'] });
    } finally {
      setDeletingId(null);
    }
  }

  const isForbidden = ApiError.isApiError(error) && error.status === 403;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Binoculars className="h-7 w-7 text-rose-400" />
            Competitor Intelligence
          </h1>
          <p className="text-gray-400 mt-1">
            Track competitor brands and analyze their product imagery for style and pricing signals
          </p>
        </div>
        {!isForbidden && (
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="bg-rose-500 hover:bg-rose-600">
                <Plus className="mr-2 h-4 w-4" />
                Add Competitor
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-gray-900 border-gray-700 text-white">
              <DialogHeader>
                <DialogTitle>Add Competitor</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Register a competitor brand for tracking and analysis.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="competitor-name">Name</Label>
                  <Input
                    id="competitor-name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="Competitor brand name"
                    className="bg-gray-800 border-gray-700 text-white"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Select
                      value={form.category}
                      onValueChange={(v) => setForm({ ...form, category: v as CompetitorCategory })}
                    >
                      <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CATEGORY_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Price Positioning</Label>
                    <Select
                      value={form.price_positioning}
                      onValueChange={(v) => setForm({ ...form, price_positioning: v as PricePositioning })}
                    >
                      <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PRICE_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="competitor-website">Website (optional)</Label>
                  <Input
                    id="competitor-website"
                    type="url"
                    value={form.website}
                    onChange={(e) => setForm({ ...form, website: e.target.value })}
                    placeholder="https://example.com"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="competitor-notes">Notes (optional)</Label>
                  <Textarea
                    id="competitor-notes"
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                {createError && (
                  <p className="text-sm text-red-400">{createError}</p>
                )}
                <DialogFooter>
                  <Button type="submit" disabled={creating} className="bg-rose-500 hover:bg-rose-600">
                    {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Add Competitor'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {isLoading && <LoadingState message="Loading competitor intelligence..." fullPage />}

      {!isLoading && isForbidden && (
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center gap-4 text-center">
              <div className="rounded-full bg-amber-500/10 p-3">
                <ShieldAlert className="h-8 w-8 text-amber-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Access Restricted</h3>
                <p className="mt-1 text-sm text-gray-400 max-w-md">
                  Competitor analysis is restricted to strategy, marketing, and admin roles.
                  Contact an administrator if you believe you should have access.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!isLoading && error && !isForbidden && (
        <ErrorState
          title="Failed to load competitor intelligence"
          message={error instanceof Error ? error.message : 'Unknown error'}
          onRetry={() => refetch()}
          fullPage
        />
      )}

      {!isLoading && !error && data && (
        <>
          {/* Summary */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="pt-6">
                <p className="text-sm text-gray-400">Competitors Tracked</p>
                <p className="text-2xl font-bold text-white mt-1">{data.summary.total_competitors}</p>
              </CardContent>
            </Card>
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="pt-6">
                <p className="text-sm text-gray-400">Assets Analyzed</p>
                <p className="text-2xl font-bold text-white mt-1">{data.summary.total_assets}</p>
              </CardContent>
            </Card>
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="pt-6">
                <p className="text-sm text-gray-400">Categories Represented</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {Object.keys(data.summary.competitors_by_category).length}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Competitors table */}
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle>Competitors</CardTitle>
              <CardDescription>Tracked competitor brands and their positioning</CardDescription>
            </CardHeader>
            <CardContent>
              {data.list.competitors.length === 0 ? (
                <EmptyState
                  icon={Binoculars}
                  title="No competitors tracked yet"
                  description="Add a competitor brand to start tracking their product imagery and pricing."
                  actionText="Add Competitor"
                  onAction={() => setShowCreate(true)}
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="border-gray-800 hover:bg-transparent">
                      <TableHead className="text-gray-400">Name</TableHead>
                      <TableHead className="text-gray-400">Category</TableHead>
                      <TableHead className="text-gray-400">Price Positioning</TableHead>
                      <TableHead className="text-gray-400">Website</TableHead>
                      <TableHead className="text-gray-400 text-right">Assets</TableHead>
                      <TableHead className="text-gray-400 w-10"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.list.competitors.map((competitor) => (
                      <TableRow key={competitor.id} className="border-gray-800 hover:bg-gray-800/50">
                        <TableCell className="font-medium text-white">{competitor.name}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={CATEGORY_BADGE[competitor.category]}>
                            {competitor.category}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-gray-300">
                          {competitor.price_positioning.replace('_', ' ')}
                        </TableCell>
                        <TableCell>
                          {competitor.website ? (
                            <a
                              href={competitor.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-rose-400 hover:text-rose-300 inline-flex items-center gap-1 text-sm"
                            >
                              Visit <ExternalLink className="h-3 w-3" />
                            </a>
                          ) : (
                            <span className="text-gray-600">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right text-gray-300">
                          {data.summary.assets_per_competitor[competitor.name] ?? 0}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8 text-gray-500 hover:text-red-400"
                            disabled={deletingId === competitor.id}
                            onClick={() => handleDelete(competitor.id)}
                          >
                            {deletingId === competitor.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Analytics panel */}
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle>Style Analytics</CardTitle>
              <CardDescription>
                Distribution across analyzed competitor assets
                {data.analytics.total_assets === 0 && ' — style categories default to "other" until the vision model is wired'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data.analytics.total_assets === 0 ? (
                <EmptyState
                  title="No competitor assets analyzed yet"
                  description="Style and price analytics appear here once competitor product images are uploaded."
                />
              ) : (
                <div className="grid gap-8 md:grid-cols-2">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">Style Distribution</h4>
                    <div className="space-y-2">
                      {data.analytics.style_distribution.map((s) => (
                        <div key={s.style}>
                          <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>{s.style.replace('_', ' ')}</span>
                            <span>{s.count} ({s.percentage}%)</span>
                          </div>
                          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-rose-500 to-purple-600"
                              style={{ width: `${s.percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">Composition Distribution</h4>
                    <div className="space-y-2">
                      {data.analytics.composition_distribution.map((c) => (
                        <div key={c.composition}>
                          <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>{c.composition.replace('_', ' ')}</span>
                            <span>{c.count} ({c.percentage}%)</span>
                          </div>
                          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-emerald-500"
                              style={{ width: `${c.percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  {data.analytics.price_by_competitor.length > 0 && (
                    <div className="md:col-span-2">
                      <h4 className="text-sm font-semibold text-gray-300 mb-3">Price by Competitor</h4>
                      <Table>
                        <TableHeader>
                          <TableRow className="border-gray-800 hover:bg-transparent">
                            <TableHead className="text-gray-400">Competitor</TableHead>
                            <TableHead className="text-gray-400 text-right">Avg Price</TableHead>
                            <TableHead className="text-gray-400 text-right">Min</TableHead>
                            <TableHead className="text-gray-400 text-right">Max</TableHead>
                            <TableHead className="text-gray-400 text-right">Assets</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data.analytics.price_by_competitor.map((p) => (
                            <TableRow key={p.competitor_id} className="border-gray-800 hover:bg-gray-800/50">
                              <TableCell className="text-white">{p.competitor_name}</TableCell>
                              <TableCell className="text-right text-gray-300">
                                {p.average_price != null ? `$${p.average_price.toFixed(2)}` : '—'}
                              </TableCell>
                              <TableCell className="text-right text-gray-300">
                                {p.min_price != null ? `$${p.min_price.toFixed(2)}` : '—'}
                              </TableCell>
                              <TableCell className="text-right text-gray-300">
                                {p.max_price != null ? `$${p.max_price.toFixed(2)}` : '—'}
                              </TableCell>
                              <TableCell className="text-right text-gray-300">{p.asset_count}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
