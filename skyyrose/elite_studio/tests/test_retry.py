"""Tests for retry logic — shared transient error handling."""

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.retry import is_transient_error, retry_on_transient


class TestIsTransientError:
    def test_timeout(self):
        assert is_transient_error("The read operation timed out")

    def test_429(self):
        assert is_transient_error("429 Too Many Requests")

    def test_503(self):
        assert is_transient_error("503 Service Unavailable")

    def test_overloaded(self):
        assert is_transient_error("overloaded_error")

    def test_not_transient(self):
        assert not is_transient_error("Invalid API key")

    def test_not_transient_404(self):
        assert not is_transient_error("404 Not Found")

    def test_case_insensitive(self):
        assert is_transient_error("TIMED OUT waiting for response")


class TestRetryOnTransient:
    def test_success_first_try(self):
        fn = MagicMock(return_value="ok")
        result = retry_on_transient(fn, label="[test]")
        assert result == "ok"
        assert fn.call_count == 1

    @patch("skyyrose.elite_studio.retry.time.sleep")
    def test_retry_on_transient_then_succeed(self, mock_sleep):
        fn = MagicMock(side_effect=[Exception("timed out"), "recovered"])
        result = retry_on_transient(fn, label="[test]")
        assert result == "recovered"
        assert fn.call_count == 2
        mock_sleep.assert_called_once()

    def test_non_transient_raises_immediately(self):
        fn = MagicMock(side_effect=Exception("Invalid API key"))
        with pytest.raises(Exception, match="Invalid API key"):
            retry_on_transient(fn, label="[test]")
        assert fn.call_count == 1  # No retry on non-transient

    @patch("skyyrose.elite_studio.retry.time.sleep")
    def test_all_retries_exhausted(self, mock_sleep):
        fn = MagicMock(side_effect=[Exception("timed out"), Exception("timed out again")])
        with pytest.raises(Exception, match="timed out again"):
            retry_on_transient(fn, label="[test]", max_retries=2)
        assert fn.call_count == 2

    @patch("skyyrose.elite_studio.retry.time.sleep")
    def test_custom_delay(self, mock_sleep):
        fn = MagicMock(side_effect=[Exception("503 error"), "ok"])
        retry_on_transient(fn, label="[test]", delay=10.0)
        mock_sleep.assert_called_once_with(10.0)

    @patch("skyyrose.elite_studio.retry.time.sleep")
    def test_no_label_still_works(self, mock_sleep):
        fn = MagicMock(side_effect=[Exception("timeout"), "ok"])
        result = retry_on_transient(fn)  # no label
        assert result == "ok"
