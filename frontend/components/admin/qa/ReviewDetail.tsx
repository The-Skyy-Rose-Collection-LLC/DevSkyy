import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
    CheckCircle2,
    XCircle,
    Loader2,
    ChevronLeft,
    ChevronRight,
    ThumbsUp,
    ThumbsDown,
    RotateCcw,
    Box,
    Layers,
    Palette,
    Ruler,
    Target,
    Sparkles,
    AlertTriangle,
} from 'lucide-react';
import { ModelViewerFallback } from '@/components/three-viewer';
import type { QAReview } from '@/lib/api';

const FIDELITY_THRESHOLD = 98;

const FIDELITY_ASPECTS = [
    { key: 'geometry', label: 'Geometry', icon: Box, description: 'Silhouette matching' },
    { key: 'materials', label: 'Materials', icon: Layers, description: 'PBR accuracy' },
    { key: 'colors', label: 'Colors', icon: Palette, description: 'Delta E < 2' },
    { key: 'proportions', label: 'Proportions', icon: Ruler, description: 'Dimension matching' },
    { key: 'branding', label: 'Branding', icon: Target, description: 'Logo placement' },
    { key: 'texture_detail', label: 'Texture', icon: Sparkles, description: 'High-res comparison' },
] as const;

interface ReviewDetailProps {
    review: QAReview;
    currentIndex: number;
    totalReviews: number;
    submitting: boolean;
    onPrev: () => void;
    onNext: () => void;
    onSubmit: (status: 'approved' | 'rejected', notes?: string) => void;
    onRegenerate: () => void;
}

export function ReviewDetail({
    review,
    currentIndex,
    totalReviews,
    submitting,
    onPrev,
    onNext,
    onSubmit,
    onRegenerate,
}: ReviewDetailProps) {
    return (
        <Card className="bg-gray-900/80 border-gray-700">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-white">Review #{review.id.slice(0, 8)}</CardTitle>
                        <CardDescription className="text-gray-400">
                            Compare reference image with generated 3D model
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            size="icon"
                            variant="ghost"
                            className="text-gray-400"
                            onClick={onPrev}
                            disabled={currentIndex === 0}
                        >
                            <ChevronLeft className="h-5 w-5" />
                        </Button>
                        <span className="text-gray-400 text-sm">
                            {currentIndex + 1} / {totalReviews}
                        </span>
                        <Button
                            size="icon"
                            variant="ghost"
                            className="text-gray-400"
                            onClick={onNext}
                            disabled={currentIndex === totalReviews - 1}
                        >
                            <ChevronRight className="h-5 w-5" />
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Side-by-side comparison */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label className="text-gray-400">Reference Image</Label>
                        <div className="aspect-square rounded-lg overflow-hidden bg-gray-800">
                            <img
                                src={review.reference_image_url}
                                alt="Reference"
                                className="w-full h-full object-cover"
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label className="text-gray-400">Generated 3D Model</Label>
                        <div className="aspect-square rounded-lg overflow-hidden bg-gray-800">
                            <ModelViewerFallback
                                modelUrl={review.generated_model_url}
                                height="100%"
                                arEnabled
                            />
                        </div>
                    </div>
                </div>

                {/* Fidelity Score */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <Label className="text-gray-300">Overall Fidelity Score</Label>
                        <div className="flex items-center gap-3">
                            <div className="w-32 h-3 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all ${review.fidelity_score >= FIDELITY_THRESHOLD
                                            ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                                            : review.fidelity_score >= 90
                                                ? 'bg-gradient-to-r from-yellow-500 to-amber-500'
                                                : 'bg-gradient-to-r from-red-500 to-rose-500'
                                        }`}
                                    style={{ width: `${review.fidelity_score}%` }}
                                />
                            </div>
                            <span
                                className={`text-xl font-bold ${review.fidelity_score >= FIDELITY_THRESHOLD
                                        ? 'text-green-400'
                                        : review.fidelity_score >= 90
                                            ? 'text-yellow-400'
                                            : 'text-red-400'
                                    }`}
                            >
                                {review.fidelity_score.toFixed(1)}%
                            </span>
                        </div>
                    </div>

                    {/* Fidelity Breakdown */}
                    {review.fidelity_breakdown && (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                            {FIDELITY_ASPECTS.map((aspect) => {
                                const value =
                                    review.fidelity_breakdown?.[
                                    aspect.key as keyof typeof review.fidelity_breakdown
                                    ];
                                if (value === undefined) return null;

                                const Icon = aspect.icon;
                                return (
                                    <div
                                        key={aspect.key}
                                        className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg"
                                    >
                                        <div
                                            className={`h-8 w-8 rounded-lg flex items-center justify-center ${value >= FIDELITY_THRESHOLD
                                                    ? 'bg-green-500/10 text-green-400'
                                                    : value >= 90
                                                        ? 'bg-yellow-500/10 text-yellow-400'
                                                        : 'bg-red-500/10 text-red-400'
                                                }`}
                                        >
                                            <Icon className="h-4 w-4" />
                                        </div>
                                        <div>
                                            <p className="text-white text-sm font-medium">{aspect.label}</p>
                                            <p className="text-gray-500 text-xs">{value.toFixed(1)}%</p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Threshold warning */}
                    {review.fidelity_score < FIDELITY_THRESHOLD && (
                        <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
                            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                            <span className="text-sm">
                                Below {FIDELITY_THRESHOLD}% fidelity threshold. Consider regenerating with higher quality settings.
                            </span>
                        </div>
                    )}
                </div>

                {/* Action Buttons */}
                {review.status === 'pending' && (
                    <div className="flex gap-3 pt-4 border-t border-gray-700">
                        <Button
                            className="flex-1 bg-green-600 hover:bg-green-700"
                            onClick={() => onSubmit('approved')}
                            disabled={submitting}
                        >
                            {submitting ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <ThumbsUp className="mr-2 h-4 w-4" />
                            )}
                            Approve
                        </Button>
                        <Button
                            className="flex-1 bg-red-600 hover:bg-red-700"
                            onClick={() => onSubmit('rejected')}
                            disabled={submitting}
                        >
                            {submitting ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <ThumbsDown className="mr-2 h-4 w-4" />
                            )}
                            Reject
                        </Button>
                        <Button
                            variant="outline"
                            className="border-gray-700"
                            onClick={onRegenerate}
                            disabled={submitting}
                        >
                            {submitting ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <RotateCcw className="mr-2 h-4 w-4" />
                            )}
                            Regenerate
                        </Button>
                    </div>
                )}

                {/* Status badge for already reviewed */}
                {review.status !== 'pending' && (
                    <div
                        className={`flex items-center justify-center gap-2 p-4 rounded-lg ${review.status === 'approved'
                                ? 'bg-green-500/10 text-green-400'
                                : review.status === 'rejected'
                                    ? 'bg-red-500/10 text-red-400'
                                    : 'bg-blue-500/10 text-blue-400'
                            }`}
                    >
                        {review.status === 'approved' ? (
                            <CheckCircle2 className="h-5 w-5" />
                        ) : review.status === 'rejected' ? (
                            <XCircle className="h-5 w-5" />
                        ) : (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        )}
                        <span className="font-medium capitalize">
                            {review.status === 'regenerating' ? 'Regenerating...' : review.status}
                        </span>
                        {review.reviewed_at && (
                            <span className="text-gray-500 ml-2">
                                ({new Date(review.reviewed_at).toLocaleDateString()})
                            </span>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
