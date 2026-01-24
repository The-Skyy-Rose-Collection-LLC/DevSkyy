'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCcw,
  Eye,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Target,
  Palette,
  Box,
  Ruler,
  Sparkles,
  Layers,
  AlertTriangle,
  TrendingUp,
  Filter,
  Loader2,
} from 'lucide-react';
import { api, type QAReview, type QAReviewListResponse } from '@/lib/api';
import { ModelViewerFallback } from '@/components/three-viewer';

const FIDELITY_THRESHOLD = 98;

const FIDELITY_ASPECTS = [
  { key: 'geometry', label: 'Geometry', icon: Box, description: 'Silhouette matching' },
  { key: 'materials', label: 'Materials', icon: Layers, description: 'PBR accuracy' },
  { key: 'colors', label: 'Colors', icon: Palette, description: 'Delta E < 2' },
  { key: 'proportions', label: 'Proportions', icon: Ruler, description: 'Dimension matching' },
  { key: 'branding', label: 'Branding', icon: Target, description: 'Logo placement' },
  { key: 'texture_detail', label: 'Texture', icon: Sparkles, description: 'High-res comparison' },
] as const;

export default function QAPage() {
  const [reviews, setReviews] = useState<QAReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    pending: 0,
    approved: 0,
    rejected: 0,
    total: 0,
  });
  const [selectedReview, setSelectedReview] = useState<QAReview | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);
  const [submitting, setSubmitting] = useState(false);

  // Fetch reviews
  const fetchReviews = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.qa.getReviews(filterStatus);
      setReviews(response.reviews);
      setStats({
        pending: response.pending_count,
        approved: response.approved_count,
        rejected: response.rejected_count,
        total: response.total,
      });
      if (response.reviews.length > 0 && !selectedReview) {
        setSelectedReview(response.reviews[0]);
        setCurrentIndex(0);
      }
    } catch (err) {
      console.error('Failed to fetch reviews:', err);
    } finally {
      setLoading(false);
    }
  }, [filterStatus, selectedReview]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  // Navigate between reviews
  const goToNext = useCallback(() => {
    if (currentIndex < reviews.length - 1) {
      setCurrentIndex((i) => i + 1);
      setSelectedReview(reviews[currentIndex + 1]);
    }
  }, [currentIndex, reviews]);

  const goToPrev = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1);
      setSelectedReview(reviews[currentIndex - 1]);
    }
  }, [currentIndex, reviews]);

  // Submit review
  const submitReview = useCallback(async (status: 'approved' | 'rejected', notes?: string) => {
    if (!selectedReview) return;

    setSubmitting(true);
    try {
      await api.qa.submitReview(selectedReview.id, { status, notes });
      await fetchReviews();
      // Auto-advance to next pending review
      const nextPending = reviews.find((r, i) => i > currentIndex && r.status === 'pending');
      if (nextPending) {
        setSelectedReview(nextPending);
        setCurrentIndex(reviews.indexOf(nextPending));
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
    } finally {
      setSubmitting(false);
    }
  }, [selectedReview, fetchReviews, reviews, currentIndex]);

  // Regenerate model
  const regenerate = useCallback(async () => {
    if (!selectedReview) return;

    setSubmitting(true);
    try {
      await api.qa.regenerate(selectedReview.id);
      await fetchReviews();
    } catch (err) {
      console.error('Failed to regenerate:', err);
    } finally {
      setSubmitting(false);
    }
  }, [selectedReview, fetchReviews]);

  if (loading && reviews.length === 0) {
    return <QASkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 border border-gray-700">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-green-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                <CheckCircle2 className="h-6 w-6 text-white" />
              </div>
              Fidelity QA
            </h1>
            <p className="text-gray-400 mt-2 ml-15">
              Review and approve 3D model quality against reference images
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-amber-500 text-amber-400">
              {stats.pending} Pending
            </Badge>
            <Button
              variant="outline"
              className="border-gray-700"
              onClick={fetchReviews}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCcw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Pending Review"
          value={stats.pending}
          icon={Clock}
          color="amber"
          onClick={() => setFilterStatus(filterStatus === 'pending' ? undefined : 'pending')}
          active={filterStatus === 'pending'}
        />
        <StatCard
          title="Approved"
          value={stats.approved}
          icon={CheckCircle2}
          color="green"
          onClick={() => setFilterStatus(filterStatus === 'approved' ? undefined : 'approved')}
          active={filterStatus === 'approved'}
        />
        <StatCard
          title="Rejected"
          value={stats.rejected}
          icon={XCircle}
          color="red"
          onClick={() => setFilterStatus(filterStatus === 'rejected' ? undefined : 'rejected')}
          active={filterStatus === 'rejected'}
        />
        <StatCard
          title="Avg Fidelity"
          value={`${reviews.length > 0
            ? (reviews.reduce((sum, r) => sum + r.fidelity_score, 0) / reviews.length).toFixed(1)
            : 0}%`}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Review List */}
        <Card className="bg-gray-900/80 border-gray-700 lg:col-span-1">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white text-lg">Reviews</CardTitle>
              <Badge variant="secondary" className="bg-gray-800">
                {reviews.length}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0 max-h-[600px] overflow-auto">
            {reviews.map((review, index) => (
              <ReviewListItem
                key={review.id}
                review={review}
                isSelected={selectedReview?.id === review.id}
                onClick={() => {
                  setSelectedReview(review);
                  setCurrentIndex(index);
                }}
              />
            ))}
            {reviews.length === 0 && (
              <div className="py-12 text-center text-gray-500">
                No reviews to display
              </div>
            )}
          </CardContent>
        </Card>

        {/* Review Detail */}
        {selectedReview && (
          <Card className="bg-gray-900/80 border-gray-700 lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-white">Review #{selectedReview.id.slice(0, 8)}</CardTitle>
                  <CardDescription className="text-gray-400">
                    Compare reference image with generated 3D model
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="icon"
                    variant="ghost"
                    className="text-gray-400"
                    onClick={goToPrev}
                    disabled={currentIndex === 0}
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </Button>
                  <span className="text-gray-400 text-sm">
                    {currentIndex + 1} / {reviews.length}
                  </span>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="text-gray-400"
                    onClick={goToNext}
                    disabled={currentIndex === reviews.length - 1}
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
                      src={selectedReview.reference_image_url}
                      alt="Reference"
                      className="w-full h-full object-cover"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-400">Generated 3D Model</Label>
                  <div className="aspect-square rounded-lg overflow-hidden bg-gray-800">
                    <ModelViewerFallback
                      modelUrl={selectedReview.generated_model_url}
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
                        className={`h-full transition-all ${
                          selectedReview.fidelity_score >= FIDELITY_THRESHOLD
                            ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                            : selectedReview.fidelity_score >= 90
                            ? 'bg-gradient-to-r from-yellow-500 to-amber-500'
                            : 'bg-gradient-to-r from-red-500 to-rose-500'
                        }`}
                        style={{ width: `${selectedReview.fidelity_score}%` }}
                      />
                    </div>
                    <span className={`text-xl font-bold ${
                      selectedReview.fidelity_score >= FIDELITY_THRESHOLD
                        ? 'text-green-400'
                        : selectedReview.fidelity_score >= 90
                        ? 'text-yellow-400'
                        : 'text-red-400'
                    }`}>
                      {selectedReview.fidelity_score.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Fidelity Breakdown */}
                {selectedReview.fidelity_breakdown && (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {FIDELITY_ASPECTS.map((aspect) => {
                      const value = selectedReview.fidelity_breakdown?.[
                        aspect.key as keyof typeof selectedReview.fidelity_breakdown
                      ];
                      if (value === undefined) return null;

                      const Icon = aspect.icon;
                      return (
                        <div
                          key={aspect.key}
                          className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg"
                        >
                          <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${
                            value >= FIDELITY_THRESHOLD
                              ? 'bg-green-500/10 text-green-400'
                              : value >= 90
                              ? 'bg-yellow-500/10 text-yellow-400'
                              : 'bg-red-500/10 text-red-400'
                          }`}>
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
                {selectedReview.fidelity_score < FIDELITY_THRESHOLD && (
                  <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
                    <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                    <span className="text-sm">
                      Below {FIDELITY_THRESHOLD}% fidelity threshold. Consider regenerating with higher quality settings.
                    </span>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              {selectedReview.status === 'pending' && (
                <div className="flex gap-3 pt-4 border-t border-gray-700">
                  <Button
                    className="flex-1 bg-green-600 hover:bg-green-700"
                    onClick={() => submitReview('approved')}
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
                    onClick={() => submitReview('rejected')}
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
                    onClick={regenerate}
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
              {selectedReview.status !== 'pending' && (
                <div className={`flex items-center justify-center gap-2 p-4 rounded-lg ${
                  selectedReview.status === 'approved'
                    ? 'bg-green-500/10 text-green-400'
                    : selectedReview.status === 'rejected'
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-blue-500/10 text-blue-400'
                }`}>
                  {selectedReview.status === 'approved' ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : selectedReview.status === 'rejected' ? (
                    <XCircle className="h-5 w-5" />
                  ) : (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  )}
                  <span className="font-medium capitalize">
                    {selectedReview.status === 'regenerating' ? 'Regenerating...' : selectedReview.status}
                  </span>
                  {selectedReview.reviewed_at && (
                    <span className="text-gray-500 ml-2">
                      ({new Date(selectedReview.reviewed_at).toLocaleDateString()})
                    </span>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {!selectedReview && reviews.length === 0 && (
          <Card className="bg-gray-900/80 border-gray-700 lg:col-span-2">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <CheckCircle2 className="h-16 w-16 text-gray-600 mb-4" />
              <h3 className="text-xl font-medium text-white mb-2">All Caught Up!</h3>
              <p className="text-gray-400">
                No reviews pending. Generate more 3D models to populate the queue.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

// Stat Card
function StatCard({
  title,
  value,
  icon: Icon,
  color,
  onClick,
  active,
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'amber' | 'green' | 'red' | 'purple';
  onClick?: () => void;
  active?: boolean;
}) {
  const colorMap = {
    amber: 'from-amber-500 to-orange-500',
    green: 'from-green-500 to-emerald-500',
    red: 'from-red-500 to-rose-500',
    purple: 'from-purple-500 to-pink-500',
  };

  return (
    <Card
      className={`bg-gray-900/80 border-gray-700 overflow-hidden cursor-pointer transition-all ${
        active ? 'ring-1 ring-rose-500' : ''
      }`}
      onClick={onClick}
    >
      <div className={`h-1 bg-gradient-to-r ${colorMap[color]}`} />
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">{title}</p>
            <p className="text-2xl font-bold text-white mt-1">{value}</p>
          </div>
          <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${colorMap[color]} flex items-center justify-center`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Review List Item
function ReviewListItem({
  review,
  isSelected,
  onClick,
}: {
  review: QAReview;
  isSelected: boolean;
  onClick: () => void;
}) {
  const statusColors = {
    pending: 'bg-amber-500/10 text-amber-400',
    approved: 'bg-green-500/10 text-green-400',
    rejected: 'bg-red-500/10 text-red-400',
    regenerating: 'bg-blue-500/10 text-blue-400',
  };

  return (
    <div
      className={`flex items-center gap-3 p-4 cursor-pointer border-b border-gray-800 transition-colors ${
        isSelected ? 'bg-gray-800' : 'hover:bg-gray-800/50'
      }`}
      onClick={onClick}
    >
      <div className="h-12 w-12 rounded-lg bg-gray-800 overflow-hidden flex-shrink-0">
        <img
          src={review.reference_image_url}
          alt=""
          className="w-full h-full object-cover"
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-white text-sm font-medium truncate">
            #{review.id.slice(0, 8)}
          </span>
          <Badge className={statusColors[review.status]} variant="secondary">
            {review.status}
          </Badge>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full ${
                review.fidelity_score >= FIDELITY_THRESHOLD
                  ? 'bg-green-500'
                  : review.fidelity_score >= 90
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${review.fidelity_score}%` }}
            />
          </div>
          <span className="text-gray-500 text-xs">
            {review.fidelity_score.toFixed(0)}%
          </span>
        </div>
      </div>
      <ChevronRight className="h-4 w-4 text-gray-500 flex-shrink-0" />
    </div>
  );
}

// Skeleton loader
function QASkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-2xl bg-gray-800" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 bg-gray-800" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Skeleton className="h-96 bg-gray-800" />
        <Skeleton className="h-96 bg-gray-800 lg:col-span-2" />
      </div>
    </div>
  );
}
