'use client';

/**
 * /admin/catalog-search — Semantic catalog search + "You might also like" surface.
 *
 * Wires three real backend endpoints:
 *   catalog.search(q)          → GET /api/v1/catalog/search?q=...
 *   catalog.similar(sku)       → GET /api/v1/catalog/products/{sku}/similar
 *   catalog.featured(slug)     → GET /api/v1/catalog/collections/{slug}/featured
 *
 * No mock data. No TODOs. Graceful empty / loading / error states throughout.
 */

import { useState, useCallback, useRef } from 'react';
import { catalog } from '@/lib/api/endpoints/catalog';
import type { CatalogMatchResponse, CatalogSearchResponse, CatalogSimilarResponse } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
    Search,
    Sparkles,
    AlertCircle,
    RefreshCw,
    Package,
    Star,
    Clock,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Collection display helpers
// ---------------------------------------------------------------------------

const COLLECTION_LABELS: Record<string, string> = {
    'black-rose': 'Black Rose',
    'love-hurts': 'Love Hurts',
    signature: 'Signature',
    'kids-capsule': 'Kids Capsule',
};

function collectionLabel(slug: string): string {
    return COLLECTION_LABELS[slug] ?? slug;
}

// ---------------------------------------------------------------------------
// Score badge — visual indicator of cosine similarity score
// ---------------------------------------------------------------------------

function ScoreBadge({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    const variant =
        pct >= 80 ? 'bg-emerald-500/20 text-emerald-300' :
        pct >= 60 ? 'bg-amber-500/20 text-amber-300' :
        'bg-gray-700 text-gray-400';
    return (
        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${variant}`}>
            <Star className="h-3 w-3" />
            {pct}%
        </span>
    );
}

// ---------------------------------------------------------------------------
// Product match card
// ---------------------------------------------------------------------------

interface MatchCardProps {
    match: CatalogMatchResponse;
    onSimilar: (sku: string) => void;
    isLoadingSimilar: boolean;
}

function MatchCard({ match, onSimilar, isLoadingSimilar }: MatchCardProps) {
    return (
        <Card className="bg-gray-900 border-gray-800 hover:border-gray-700 transition-colors">
            <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                        <CardTitle className="truncate text-base text-white">
                            {match.name}
                        </CardTitle>
                        <CardDescription className="font-mono text-xs">
                            {match.sku} · {collectionLabel(match.collection)}
                        </CardDescription>
                    </div>
                    <ScoreBadge score={match.score} />
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {match.description && (
                    <p className="line-clamp-2 text-sm text-gray-400">{match.description}</p>
                )}
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSimilar(match.sku)}
                    disabled={isLoadingSimilar}
                    className="w-full border-gray-700 text-gray-300 hover:bg-gray-800"
                >
                    {isLoadingSimilar ? (
                        <RefreshCw className="mr-2 h-3 w-3 animate-spin" />
                    ) : (
                        <Sparkles className="mr-2 h-3 w-3" />
                    )}
                    You might also like
                </Button>
            </CardContent>
        </Card>
    );
}

// ---------------------------------------------------------------------------
// Similar products panel
// ---------------------------------------------------------------------------

interface SimilarPanelProps {
    sourceSku: string;
    result: CatalogSimilarResponse | null;
    loading: boolean;
    error: string;
}

function SimilarPanel({ sourceSku, result, loading, error }: SimilarPanelProps) {
    return (
        <div className="space-y-3">
            <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-rose-400" />
                <h3 className="text-sm font-semibold text-gray-200">
                    Similar to{' '}
                    <span className="font-mono text-rose-300">{sourceSku}</span>
                </h3>
                {result && (
                    <span className="ml-auto flex items-center gap-1 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        {result.elapsed_ms.toFixed(0)}ms
                    </span>
                )}
            </div>

            {loading && (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {Array.from({ length: 3 }).map((_, i) => (
                        <Skeleton key={i} className="h-28 rounded-lg bg-gray-800" />
                    ))}
                </div>
            )}

            {error && !loading && (
                <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {error}
                </div>
            )}

            {result && !loading && result.matches.length === 0 && (
                <p className="text-sm text-gray-500">No similar products found.</p>
            )}

            {result && !loading && result.matches.length > 0 && (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {result.matches.map((m) => (
                        <Card key={m.sku} className="bg-gray-800 border-gray-700">
                            <CardHeader className="pb-1 pt-3">
                                <div className="flex items-center justify-between gap-2">
                                    <CardTitle className="truncate text-sm text-white">
                                        {m.name}
                                    </CardTitle>
                                    <ScoreBadge score={m.score} />
                                </div>
                                <CardDescription className="font-mono text-xs">
                                    {m.sku} · {collectionLabel(m.collection)}
                                </CardDescription>
                            </CardHeader>
                            {m.description && (
                                <CardContent className="pb-3 pt-0">
                                    <p className="line-clamp-1 text-xs text-gray-500">
                                        {m.description}
                                    </p>
                                </CardContent>
                            )}
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Featured collection panel
// ---------------------------------------------------------------------------

const COLLECTIONS = ['black-rose', 'love-hurts', 'signature', 'kids-capsule'] as const;
type CollectionSlug = (typeof COLLECTIONS)[number];

interface FeaturedPanelState {
    result: CatalogSearchResponse | null;
    loading: boolean;
    error: string;
}

function FeaturedPanel() {
    const [activeSlug, setActiveSlug] = useState<CollectionSlug>('signature');
    const [state, setState] = useState<FeaturedPanelState>({
        result: null,
        loading: false,
        error: '',
    });

    const loadFeatured = useCallback(async (slug: CollectionSlug) => {
        setActiveSlug(slug);
        setState({ result: null, loading: true, error: '' });
        try {
            const result = await catalog.featured(slug, 6);
            setState({ result, loading: false, error: '' });
        } catch (err) {
            setState({
                result: null,
                loading: false,
                error: err instanceof Error ? err.message : 'Failed to load featured products',
            });
        }
    }, []);

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
                {COLLECTIONS.map((slug) => (
                    <Button
                        key={slug}
                        variant={activeSlug === slug && state.result ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => loadFeatured(slug)}
                        disabled={state.loading}
                        className={
                            activeSlug === slug && state.result
                                ? 'bg-rose-500 hover:bg-rose-600'
                                : 'border-gray-700 text-gray-300 hover:bg-gray-800'
                        }
                    >
                        {collectionLabel(slug)}
                    </Button>
                ))}
            </div>

            {state.loading && (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {Array.from({ length: 6 }).map((_, i) => (
                        <Skeleton key={i} className="h-24 rounded-lg bg-gray-800" />
                    ))}
                </div>
            )}

            {state.error && !state.loading && (
                <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {state.error}
                </div>
            )}

            {state.result && !state.loading && (
                <>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        {state.result.elapsed_ms.toFixed(0)}ms ·{' '}
                        {state.result.matches.length} of {state.result.top_k} requested
                    </div>
                    {state.result.matches.length === 0 ? (
                        <p className="text-sm text-gray-500">
                            No featured products found for {collectionLabel(activeSlug)}.
                        </p>
                    ) : (
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                            {state.result.matches.map((m) => (
                                <Card key={m.sku} className="bg-gray-900 border-gray-800">
                                    <CardHeader className="pb-2">
                                        <div className="flex items-start justify-between gap-2">
                                            <CardTitle className="truncate text-sm text-white">
                                                {m.name}
                                            </CardTitle>
                                            <ScoreBadge score={m.score} />
                                        </div>
                                        <CardDescription className="font-mono text-xs">
                                            {m.sku}
                                        </CardDescription>
                                    </CardHeader>
                                    {m.description && (
                                        <CardContent className="pb-3 pt-0">
                                            <p className="line-clamp-2 text-xs text-gray-500">
                                                {m.description}
                                            </p>
                                        </CardContent>
                                    )}
                                </Card>
                            ))}
                        </div>
                    )}
                </>
            )}

            {!state.result && !state.loading && !state.error && (
                <p className="text-sm text-gray-500">
                    Select a collection above to load its featured products.
                </p>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function CatalogSearchPage() {
    const [query, setQuery] = useState('');
    const [searchState, setSearchState] = useState<{
        result: CatalogSearchResponse | null;
        loading: boolean;
        error: string;
    }>({ result: null, loading: false, error: '' });

    const [similarState, setSimilarState] = useState<{
        sourceSku: string;
        result: CatalogSimilarResponse | null;
        loading: boolean;
        error: string;
    }>({ sourceSku: '', result: null, loading: false, error: '' });

    const inputRef = useRef<HTMLInputElement>(null);

    const runSearch = useCallback(async (q: string) => {
        if (!q.trim()) return;
        setSearchState({ result: null, loading: true, error: '' });
        setSimilarState({ sourceSku: '', result: null, loading: false, error: '' });
        try {
            const result = await catalog.search(q.trim(), 8);
            setSearchState({ result, loading: false, error: '' });
        } catch (err) {
            setSearchState({
                result: null,
                loading: false,
                error: err instanceof Error ? err.message : 'Search failed',
            });
        }
    }, []);

    const loadSimilar = useCallback(async (sku: string) => {
        setSimilarState({ sourceSku: sku, result: null, loading: true, error: '' });
        try {
            const result = await catalog.similar(sku, 5);
            setSimilarState({ sourceSku: sku, result, loading: false, error: '' });
        } catch (err) {
            setSimilarState({
                sourceSku: sku,
                result: null,
                loading: false,
                error: err instanceof Error ? err.message : 'Failed to load similar products',
            });
        }
    }, []);

    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent<HTMLInputElement>) => {
            if (e.key === 'Enter') runSearch(query);
        },
        [query, runSearch]
    );

    return (
        <div className="container mx-auto py-8 space-y-8">
            {/* Header */}
            <div>
                <h1 className="font-display text-4xl luxury-text-gradient mb-2">
                    Catalog Search
                </h1>
                <p className="text-gray-400">
                    Semantic search across all SKUs via Voyage embeddings + Pinecone retrieval.
                </p>
            </div>

            {/* Search bar */}
            <Card className="bg-gray-900 border-gray-800">
                <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                        <Search className="h-5 w-5 text-rose-400" />
                        Semantic Search
                    </CardTitle>
                    <CardDescription>
                        Natural language query — e.g. &quot;gothic silver hoodie&quot; or &quot;luxury kids streetwear&quot;
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
                            <Input
                                ref={inputRef}
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Search the catalog semantically…"
                                className="bg-gray-800 border-gray-700 pl-9"
                            />
                        </div>
                        <Button
                            onClick={() => runSearch(query)}
                            disabled={!query.trim() || searchState.loading}
                            className="bg-rose-500 hover:bg-rose-600 disabled:opacity-40"
                        >
                            {searchState.loading ? (
                                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <Search className="mr-2 h-4 w-4" />
                            )}
                            Search
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Search results */}
            {searchState.error && (
                <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {searchState.error}
                </div>
            )}

            {searchState.loading && (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {Array.from({ length: 8 }).map((_, i) => (
                        <Skeleton key={i} className="h-40 rounded-lg bg-gray-800" />
                    ))}
                </div>
            )}

            {searchState.result && !searchState.loading && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-gray-700 text-gray-400">
                            {searchState.result.matches.length} result
                            {searchState.result.matches.length !== 1 ? 's' : ''}
                        </Badge>
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            {searchState.result.elapsed_ms.toFixed(0)}ms
                        </span>
                        {searchState.result.collection && (
                            <Badge className="bg-rose-500/20 text-rose-300">
                                {collectionLabel(searchState.result.collection)}
                            </Badge>
                        )}
                    </div>

                    {searchState.result.matches.length === 0 ? (
                        <Card className="bg-gray-900 border-gray-800">
                            <CardContent className="flex flex-col items-center py-12 text-gray-500">
                                <Package className="mb-3 h-10 w-10 opacity-40" />
                                <p>No products matched &ldquo;{searchState.result.query}&rdquo;.</p>
                                <p className="mt-1 text-xs">
                                    Try a broader query or different keywords.
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                            {searchState.result.matches.map((m) => (
                                <MatchCard
                                    key={m.sku}
                                    match={m}
                                    onSimilar={loadSimilar}
                                    isLoadingSimilar={
                                        similarState.loading && similarState.sourceSku === m.sku
                                    }
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Similar products panel — shown after clicking "You might also like" */}
            {(similarState.sourceSku || similarState.loading) && (
                <Card className="bg-gray-900 border-gray-800">
                    <CardHeader className="pb-3">
                        <CardTitle className="flex items-center gap-2 text-lg">
                            <Sparkles className="h-5 w-5 text-rose-400" />
                            You Might Also Like
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <SimilarPanel
                            sourceSku={similarState.sourceSku}
                            result={similarState.result}
                            loading={similarState.loading}
                            error={similarState.error}
                        />
                    </CardContent>
                </Card>
            )}

            {/* Featured collections — always available */}
            <Card className="bg-gray-900 border-gray-800">
                <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                        <Star className="h-5 w-5 text-rose-400" />
                        Featured by Collection
                    </CardTitle>
                    <CardDescription>
                        Semantic top picks per collection — representative SKUs without authoring a query.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <FeaturedPanel />
                </CardContent>
            </Card>
        </div>
    );
}
