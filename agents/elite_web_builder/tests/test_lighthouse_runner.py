"""Tests for tools/lighthouse_runner.py — Lighthouse performance measurement.

TDD: These tests were written FIRST, before the implementation.
All subprocess calls are mocked — never runs real Lighthouse in tests.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.lighthouse_runner import (
    LighthouseError,
    LighthouseResult,
    check_performance_budget,
    format_report,
    run_lighthouse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_LIGHTHOUSE_JSON = {
    "categories": {
        "performance": {"score": 0.92},
        "accessibility": {"score": 0.95},
        "best-practices": {"score": 0.88},
        "seo": {"score": 0.90},
    },
    "audits": {
        "first-contentful-paint": {
            "id": "first-contentful-paint",
            "title": "First Contentful Paint",
            "score": 1,
            "numericValue": 1200.0,
        },
        "largest-contentful-paint": {
            "id": "largest-contentful-paint",
            "title": "Largest Contentful Paint",
            "score": 0.8,
            "numericValue": 2500.0,
        },
        "total-blocking-time": {
            "id": "total-blocking-time",
            "title": "Total Blocking Time",
            "score": 1,
            "numericValue": 50.0,
        },
        "cumulative-layout-shift": {
            "id": "cumulative-layout-shift",
            "title": "Cumulative Layout Shift",
            "score": 1,
            "numericValue": 0.02,
        },
        "speed-index": {
            "id": "speed-index",
            "title": "Speed Index",
            "score": 0.9,
            "numericValue": 1800.0,
        },
        "render-blocking-resources": {
            "id": "render-blocking-resources",
            "title": "Eliminate render-blocking resources",
            "score": 0,
            "numericValue": 350.0,
        },
        "uses-responsive-images": {
            "id": "uses-responsive-images",
            "title": "Properly size images",
            "score": 0.5,
            "numericValue": 1200.0,
        },
        "color-contrast": {
            "id": "color-contrast",
            "title": "Background and foreground colors have sufficient contrast",
            "score": 1,
            "numericValue": None,
        },
    },
}


def _make_result(
    *,
    performance: float = 92.0,
    accessibility: float = 95.0,
    best_practices: float = 88.0,
    seo: float = 90.0,
) -> LighthouseResult:
    """Helper to build a LighthouseResult for testing."""
    return LighthouseResult(
        url="https://example.com",
        performance_score=performance,
        accessibility_score=accessibility,
        best_practices_score=best_practices,
        seo_score=seo,
        metrics={
            "FCP": 1200.0,
            "LCP": 2500.0,
            "TBT": 50.0,
            "CLS": 0.02,
            "SI": 1800.0,
        },
        audits=[
            {"id": "render-blocking-resources", "title": "Eliminate render-blocking resources", "score": 0},
            {"id": "uses-responsive-images", "title": "Properly size images", "score": 0.5},
        ],
        timestamp="2026-02-20T12:00:00Z",
    )


# ---------------------------------------------------------------------------
# LighthouseResult dataclass tests
# ---------------------------------------------------------------------------


class TestLighthouseResult:
    def test_creation(self) -> None:
        result = _make_result()
        assert result.url == "https://example.com"
        assert result.performance_score == 92.0
        assert result.accessibility_score == 95.0
        assert result.best_practices_score == 88.0
        assert result.seo_score == 90.0

    def test_frozen_url(self) -> None:
        result = _make_result()
        with pytest.raises(AttributeError):
            result.url = "https://changed.com"  # type: ignore[misc]

    def test_frozen_performance_score(self) -> None:
        result = _make_result()
        with pytest.raises(AttributeError):
            result.performance_score = 50.0  # type: ignore[misc]

    def test_frozen_metrics(self) -> None:
        """The reference itself is frozen; dict contents are a copy concern."""
        result = _make_result()
        with pytest.raises(AttributeError):
            result.metrics = {}  # type: ignore[misc]

    def test_frozen_audits(self) -> None:
        result = _make_result()
        with pytest.raises(AttributeError):
            result.audits = []  # type: ignore[misc]

    def test_metrics_contain_expected_keys(self) -> None:
        result = _make_result()
        for key in ("FCP", "LCP", "TBT", "CLS", "SI"):
            assert key in result.metrics

    def test_audits_are_list(self) -> None:
        result = _make_result()
        assert isinstance(result.audits, list)
        assert len(result.audits) == 2

    def test_timestamp_is_string(self) -> None:
        result = _make_result()
        assert isinstance(result.timestamp, str)
        assert "2026" in result.timestamp


# ---------------------------------------------------------------------------
# run_lighthouse tests (mocked subprocess)
# ---------------------------------------------------------------------------


class TestRunLighthouse:
    @patch("tools.lighthouse_runner._get_timestamp", return_value="2026-02-20T12:00:00Z")
    @patch("tools.lighthouse_runner.subprocess.run")
    def test_success_mobile(self, mock_run: MagicMock, mock_ts: MagicMock) -> None:
        """Successful run parses JSON and returns LighthouseResult."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(SAMPLE_LIGHTHOUSE_JSON),
            stderr="",
        )
        result = run_lighthouse("https://example.com")

        assert isinstance(result, LighthouseResult)
        assert result.url == "https://example.com"
        assert result.performance_score == 92.0
        assert result.accessibility_score == 95.0
        assert result.best_practices_score == 88.0
        assert result.seo_score == 90.0
        assert result.metrics["FCP"] == 1200.0
        assert result.metrics["LCP"] == 2500.0
        assert result.metrics["TBT"] == 50.0
        assert result.metrics["CLS"] == 0.02
        assert result.metrics["SI"] == 1800.0
        assert result.timestamp == "2026-02-20T12:00:00Z"

    @patch("tools.lighthouse_runner._get_timestamp", return_value="2026-02-20T12:00:00Z")
    @patch("tools.lighthouse_runner.subprocess.run")
    def test_success_desktop(self, mock_run: MagicMock, mock_ts: MagicMock) -> None:
        """Desktop mode should pass --preset=desktop flag."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(SAMPLE_LIGHTHOUSE_JSON),
            stderr="",
        )
        result = run_lighthouse("https://example.com", device="desktop")

        call_args = mock_run.call_args[0][0]
        assert "--preset=desktop" in call_args
        assert isinstance(result, LighthouseResult)

    @patch("tools.lighthouse_runner._get_timestamp", return_value="2026-02-20T12:00:00Z")
    @patch("tools.lighthouse_runner.subprocess.run")
    def test_custom_categories(self, mock_run: MagicMock, mock_ts: MagicMock) -> None:
        """Should only request specified categories."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(SAMPLE_LIGHTHOUSE_JSON),
            stderr="",
        )
        run_lighthouse("https://example.com", categories=["performance", "seo"])

        call_args = mock_run.call_args[0][0]
        assert "--only-categories=performance,seo" in call_args

    @patch("tools.lighthouse_runner._get_timestamp", return_value="2026-02-20T12:00:00Z")
    @patch("tools.lighthouse_runner.subprocess.run")
    def test_failed_audits_collected(self, mock_run: MagicMock, mock_ts: MagicMock) -> None:
        """Audits with score < 1 should be included in the failed list."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(SAMPLE_LIGHTHOUSE_JSON),
            stderr="",
        )
        result = run_lighthouse("https://example.com")

        audit_ids = [a["id"] for a in result.audits]
        assert "render-blocking-resources" in audit_ids
        assert "uses-responsive-images" in audit_ids
        # Passing audits should NOT be in the list
        assert "first-contentful-paint" not in audit_ids
        assert "color-contrast" not in audit_ids

    @patch("tools.lighthouse_runner.subprocess.run")
    def test_lighthouse_not_installed(self, mock_run: MagicMock) -> None:
        """Should raise LighthouseError when npx/lighthouse is not found."""
        mock_run.side_effect = FileNotFoundError("npx not found")
        with pytest.raises(LighthouseError, match="not installed"):
            run_lighthouse("https://example.com")

    @patch("tools.lighthouse_runner.subprocess.run")
    def test_nonzero_exit_code(self, mock_run: MagicMock) -> None:
        """Non-zero exit code from lighthouse should raise LighthouseError."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Chrome could not be found",
        )
        with pytest.raises(LighthouseError, match="exit code 1"):
            run_lighthouse("https://example.com")

    @patch("tools.lighthouse_runner.subprocess.run")
    def test_malformed_json(self, mock_run: MagicMock) -> None:
        """Malformed JSON output should raise LighthouseError."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NOT VALID JSON {{{{",
            stderr="",
        )
        with pytest.raises(LighthouseError, match="Failed to parse"):
            run_lighthouse("https://example.com")

    @patch("tools.lighthouse_runner.subprocess.run")
    def test_missing_categories_key(self, mock_run: MagicMock) -> None:
        """JSON without 'categories' key should raise LighthouseError."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"audits": {}}),
            stderr="",
        )
        with pytest.raises(LighthouseError, match="Missing 'categories'"):
            run_lighthouse("https://example.com")

    def test_empty_url_raises(self) -> None:
        """Empty URL should raise ValueError immediately."""
        with pytest.raises(ValueError, match="url must not be empty"):
            run_lighthouse("")

    def test_whitespace_url_raises(self) -> None:
        """Whitespace-only URL should raise ValueError."""
        with pytest.raises(ValueError, match="url must not be empty"):
            run_lighthouse("   ")

    def test_invalid_device_raises(self) -> None:
        """Device must be 'mobile' or 'desktop'."""
        with pytest.raises(ValueError, match="device must be"):
            run_lighthouse("https://example.com", device="tablet")

    @patch("tools.lighthouse_runner._get_timestamp", return_value="2026-02-20T12:00:00Z")
    @patch("tools.lighthouse_runner.subprocess.run")
    def test_missing_category_defaults_to_zero(self, mock_run: MagicMock, mock_ts: MagicMock) -> None:
        """If a category is missing from the report, score defaults to 0."""
        partial_json = {
            "categories": {
                "performance": {"score": 0.75},
                # accessibility, best-practices, seo all missing
            },
            "audits": {},
        }
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(partial_json),
            stderr="",
        )
        result = run_lighthouse("https://example.com")
        assert result.performance_score == 75.0
        assert result.accessibility_score == 0.0
        assert result.best_practices_score == 0.0
        assert result.seo_score == 0.0

    @patch("tools.lighthouse_runner.subprocess.run")
    def test_subprocess_timeout(self, mock_run: MagicMock) -> None:
        """Subprocess timeout should raise LighthouseError."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="npx", timeout=120)
        with pytest.raises(LighthouseError, match="timed out"):
            run_lighthouse("https://example.com")


# ---------------------------------------------------------------------------
# check_performance_budget tests
# ---------------------------------------------------------------------------


class TestCheckPerformanceBudget:
    def test_all_passing_default_budget(self) -> None:
        """All scores above default thresholds should pass."""
        result = _make_result(
            performance=92.0,
            accessibility=95.0,
            best_practices=88.0,
            seo=90.0,
        )
        budget_check = check_performance_budget(result)

        assert budget_check["overall"] == "pass"
        assert budget_check["performance"]["status"] == "pass"
        assert budget_check["accessibility"]["status"] == "pass"
        assert budget_check["best_practices"]["status"] == "pass"
        assert budget_check["seo"]["status"] == "pass"

    def test_performance_failing(self) -> None:
        """Performance below threshold should fail."""
        result = _make_result(performance=65.0)
        budget_check = check_performance_budget(result)

        assert budget_check["overall"] == "fail"
        assert budget_check["performance"]["status"] == "fail"
        assert budget_check["performance"]["actual"] == 65.0
        assert budget_check["performance"]["threshold"] == 80.0

    def test_accessibility_failing(self) -> None:
        result = _make_result(accessibility=70.0)
        budget_check = check_performance_budget(result)

        assert budget_check["overall"] == "fail"
        assert budget_check["accessibility"]["status"] == "fail"

    def test_multiple_failures(self) -> None:
        """Multiple categories below threshold all reported."""
        result = _make_result(
            performance=50.0,
            accessibility=60.0,
            best_practices=70.0,
            seo=40.0,
        )
        budget_check = check_performance_budget(result)

        assert budget_check["overall"] == "fail"
        assert budget_check["performance"]["status"] == "fail"
        assert budget_check["accessibility"]["status"] == "fail"
        assert budget_check["best_practices"]["status"] == "fail"
        assert budget_check["seo"]["status"] == "fail"

    def test_custom_budget(self) -> None:
        """Custom budget thresholds should override defaults."""
        result = _make_result(
            performance=92.0,
            accessibility=95.0,
            best_practices=88.0,
            seo=90.0,
        )
        strict_budget = {
            "performance": 95.0,
            "accessibility": 98.0,
            "best_practices": 90.0,
            "seo": 95.0,
        }
        budget_check = check_performance_budget(result, budget=strict_budget)

        assert budget_check["overall"] == "fail"
        assert budget_check["performance"]["status"] == "fail"
        assert budget_check["accessibility"]["status"] == "fail"
        assert budget_check["best_practices"]["status"] == "fail"
        assert budget_check["seo"]["status"] == "fail"

    def test_custom_budget_partial_override(self) -> None:
        """Partial custom budget uses defaults for missing keys."""
        result = _make_result(performance=92.0, seo=90.0)
        partial_budget = {"performance": 95.0}
        budget_check = check_performance_budget(result, budget=partial_budget)

        # Performance uses custom threshold (95), fails at 92
        assert budget_check["performance"]["status"] == "fail"
        assert budget_check["performance"]["threshold"] == 95.0
        # SEO uses default (80), passes at 90
        assert budget_check["seo"]["status"] == "pass"
        assert budget_check["seo"]["threshold"] == 80.0

    def test_exact_threshold_passes(self) -> None:
        """Score exactly equal to threshold should pass."""
        result = _make_result(performance=80.0)
        budget_check = check_performance_budget(result)
        assert budget_check["performance"]["status"] == "pass"

    def test_budget_check_contains_url(self) -> None:
        """Budget check result should include the URL."""
        result = _make_result()
        budget_check = check_performance_budget(result)
        assert budget_check["url"] == "https://example.com"

    def test_budget_check_immutability(self) -> None:
        """check_performance_budget returns a new dict every time."""
        result = _make_result()
        check1 = check_performance_budget(result)
        check2 = check_performance_budget(result)
        assert check1 is not check2
        assert check1 == check2


# ---------------------------------------------------------------------------
# format_report tests
# ---------------------------------------------------------------------------


class TestFormatReport:
    def test_contains_url(self) -> None:
        result = _make_result()
        report = format_report(result)
        assert "https://example.com" in report

    def test_contains_all_scores(self) -> None:
        result = _make_result()
        report = format_report(result)
        assert "92.0" in report
        assert "95.0" in report
        assert "88.0" in report
        assert "90.0" in report

    def test_contains_metrics(self) -> None:
        result = _make_result()
        report = format_report(result)
        assert "FCP" in report
        assert "LCP" in report
        assert "TBT" in report
        assert "CLS" in report
        assert "SI" in report

    def test_contains_failed_audits(self) -> None:
        result = _make_result()
        report = format_report(result)
        assert "render-blocking-resources" in report
        assert "Properly size images" in report

    def test_returns_string(self) -> None:
        result = _make_result()
        report = format_report(result)
        assert isinstance(report, str)

    def test_markdown_headers(self) -> None:
        """Report should use markdown headers."""
        result = _make_result()
        report = format_report(result)
        assert "# Lighthouse Report" in report
        assert "## Scores" in report

    def test_empty_audits(self) -> None:
        """Report with no failed audits should still render."""
        result = LighthouseResult(
            url="https://clean.example.com",
            performance_score=100.0,
            accessibility_score=100.0,
            best_practices_score=100.0,
            seo_score=100.0,
            metrics={"FCP": 500.0, "LCP": 1000.0, "TBT": 0.0, "CLS": 0.0, "SI": 600.0},
            audits=[],
            timestamp="2026-02-20T12:00:00Z",
        )
        report = format_report(result)
        assert "https://clean.example.com" in report
        assert "100.0" in report

    def test_timestamp_in_report(self) -> None:
        result = _make_result()
        report = format_report(result)
        assert "2026-02-20T12:00:00Z" in report
