"""
Tests for Elite Studio A/B Comparison Tracker (monitoring/ab_comparison.py).

Uses fakeredis for in-memory Redis simulation — no live Redis required.
Falls back gracefully when fakeredis is not installed.
"""

from __future__ import annotations

import math

import pytest

try:
    import fakeredis

    FAKEREDIS_AVAILABLE = True
except ImportError:
    FAKEREDIS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not FAKEREDIS_AVAILABLE, reason="fakeredis not installed"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_redis():
    """Return a fresh fakeredis instance."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture()
def tracker(fake_redis):
    """Return an ABComparisonTracker wired to fakeredis."""
    from monitoring.ab_comparison import ABComparisonTracker

    t = ABComparisonTracker()
    t._redis = fake_redis
    return t


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    def test_record_stores_in_sorted_set(self, tracker, fake_redis):
        tracker.record("gemini", "gemini-2.5-flash", 0.85, "job-001")
        key = "elite_studio:ab:gemini:gemini-2.5-flash"
        assert fake_redis.zcard(key) == 1

    def test_record_score_is_correct(self, tracker, fake_redis):
        tracker.record("gemini", "gemini-2.5-flash", 0.92, "job-002")
        key = "elite_studio:ab:gemini:gemini-2.5-flash"
        members = fake_redis.zrangebyscore(key, 0.0, 1.0, withscores=True)
        assert len(members) == 1
        member, score = members[0]
        assert member == "job-002"
        assert abs(score - 0.92) < 1e-6

    def test_record_multiple_jobs(self, tracker, fake_redis):
        for i, score in enumerate([0.7, 0.8, 0.9]):
            tracker.record("gemini", "model-x", score, f"job-{i:03d}")
        key = "elite_studio:ab:gemini:model-x"
        assert fake_redis.zcard(key) == 3

    def test_record_multiple_providers(self, tracker, fake_redis):
        tracker.record("gemini", "flash", 0.8, "job-g")
        tracker.record("openai", "gpt-image", 0.75, "job-o")
        assert fake_redis.zcard("elite_studio:ab:gemini:flash") == 1
        assert fake_redis.zcard("elite_studio:ab:openai:gpt-image") == 1

    def test_record_without_redis_does_not_raise(self):
        from monitoring.ab_comparison import ABComparisonTracker
        import unittest.mock as mock

        t = ABComparisonTracker()
        # Patch _get_redis to simulate unavailable Redis
        with mock.patch.object(t, "_get_redis", return_value=None):
            t.record("gemini", "model", 0.9, "job-x")  # must not raise


# ---------------------------------------------------------------------------
# report()
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_empty_when_no_data(self, tracker):
        report = tracker.report()
        assert report.providers == {}
        assert "T" in report.generated_at  # ISO format

    def test_report_single_provider(self, tracker):
        scores = [0.6, 0.7, 0.8, 0.9]
        for i, s in enumerate(scores):
            tracker.record("gemini", "flash", s, f"j{i}")
        report = tracker.report()
        assert "gemini:flash" in report.providers
        stats = report.providers["gemini:flash"]
        assert stats.sample_count == 4
        assert abs(stats.mean_score - sum(scores) / len(scores)) < 0.01

    def test_report_multi_provider(self, tracker):
        for i, s in enumerate([0.7, 0.8, 0.9]):
            tracker.record("gemini", "flash", s, f"gj{i}")
        for i, s in enumerate([0.5, 0.6]):
            tracker.record("openai", "gpt-img", s, f"oj{i}")
        report = tracker.report()
        assert "gemini:flash" in report.providers
        assert "openai:gpt-img" in report.providers

    def test_report_win_rate(self, tracker):
        # 3 above 0.8, 2 below
        scores = [0.9, 0.85, 0.82, 0.75, 0.6]
        for i, s in enumerate(scores):
            tracker.record("gemini", "flash", s, f"wr{i}")
        report = tracker.report()
        stats = report.providers["gemini:flash"]
        assert abs(stats.win_rate - 3 / 5) < 0.01

    def test_report_p50_p95(self, tracker):
        # 10 evenly spaced scores [0.1, 0.2, ..., 1.0]
        scores = [i / 10 for i in range(1, 11)]
        for i, s in enumerate(scores):
            tracker.record("gemini", "flash", s, f"p{i}")
        report = tracker.report()
        stats = report.providers["gemini:flash"]
        # p50 ≈ 0.55, p95 ≈ 0.955
        assert 0.5 <= stats.p50 <= 0.6
        assert stats.p95 > 0.9

    def test_report_std_dev_nonzero(self, tracker):
        for i, s in enumerate([0.5, 0.7, 0.9]):
            tracker.record("gemini", "flash", s, f"sd{i}")
        report = tracker.report()
        stats = report.providers["gemini:flash"]
        assert stats.std_dev > 0.0

    def test_report_std_dev_zero_for_identical_scores(self, tracker):
        for i in range(5):
            tracker.record("openai", "img", 0.75, f"id{i}")
        report = tracker.report()
        stats = report.providers["openai:img"]
        assert abs(stats.std_dev) < 1e-6


# ---------------------------------------------------------------------------
# Statistical helpers (_compute_stats, _percentile)
# ---------------------------------------------------------------------------


class TestStatHelpers:
    def test_percentile_single_element(self):
        from monitoring.ab_comparison import _percentile

        assert _percentile([0.8], 50) == 0.8
        assert _percentile([0.8], 95) == 0.8

    def test_percentile_empty(self):
        from monitoring.ab_comparison import _percentile

        assert _percentile([], 50) == 0.0

    def test_percentile_two_elements(self):
        from monitoring.ab_comparison import _percentile

        result = _percentile([0.0, 1.0], 50)
        assert abs(result - 0.5) < 1e-9

    def test_compute_stats_fields(self):
        from monitoring.ab_comparison import _compute_stats

        scores = [0.6, 0.7, 0.8, 0.9]
        stats = _compute_stats("gemini", "flash", scores, win_threshold=0.8)
        assert stats.provider == "gemini"
        assert stats.model == "flash"
        assert stats.sample_count == 4
        assert abs(stats.mean_score - 0.75) < 0.01
        assert stats.std_dev > 0
        assert stats.win_rate == 0.5  # 2/4 above 0.8

    def test_compute_stats_all_winning(self):
        from monitoring.ab_comparison import _compute_stats

        scores = [0.9, 0.95, 1.0]
        stats = _compute_stats("gemini", "m", scores, win_threshold=0.8)
        assert stats.win_rate == 1.0

    def test_compute_stats_none_winning(self):
        from monitoring.ab_comparison import _compute_stats

        scores = [0.1, 0.2, 0.3]
        stats = _compute_stats("gemini", "m", scores, win_threshold=0.8)
        assert stats.win_rate == 0.0
