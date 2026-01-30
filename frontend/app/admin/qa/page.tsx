'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCcw,
  TrendingUp,
  Loader2,
} from 'lucide-react';
import { api, type QAReview } from '@/lib/api';

// Extracted Components
import { StatCard } from '@/components/admin/qa/StatCard';
import { ReviewListItem } from '@/components/admin/qa/ReviewListItem';
import { ReviewDetail } from '@/components/admin/qa/ReviewDetail';
import { QASkeleton } from '@/components/admin/qa/QASkeleton';

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
        {selectedReview ? (
          <div className="lg:col-span-2">
            <ReviewDetail
              review={selectedReview}
              currentIndex={currentIndex}
              totalReviews={reviews.length}
              submitting={submitting}
              onPrev={goToPrev}
              onNext={goToNext}
              onSubmit={submitReview}
              onRegenerate={regenerate}
            />
          </div>
        ) : (
          reviews.length === 0 && (
            <Card className="bg-gray-900/80 border-gray-700 lg:col-span-2">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <CheckCircle2 className="h-16 w-16 text-gray-600 mb-4" />
                <h3 className="text-xl font-medium text-white mb-2">All Caught Up!</h3>
                <p className="text-gray-400">
                  No reviews pending. Generate more 3D models to populate the queue.
                </p>
              </CardContent>
            </Card>
          )
        )}
      </div>
    </div>
  );
}
