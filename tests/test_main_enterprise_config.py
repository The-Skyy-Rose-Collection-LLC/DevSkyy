"""Tests for main_enterprise.py config-parsing helpers (Sentry sample rates, CORS
origin-regex override) — see docs on _parse_sentry_sample_rate / _resolve_cors_origin_regex.
"""

import re

from main_enterprise import _parse_sentry_sample_rate, _resolve_cors_origin_regex

DEFAULT_CORS_REGEX = r"https://[a-zA-Z0-9-]+\.(vercel\.app|devskyy\.app)"


class TestParseSentrySampleRate:
    def test_missing_returns_default(self):
        assert _parse_sentry_sample_rate(None, default=0.25) == 0.25

    def test_empty_string_returns_default(self):
        assert _parse_sentry_sample_rate("  ", default=0.25) == 0.25

    def test_valid_value_in_range(self):
        assert _parse_sentry_sample_rate("0.3", default=0.1) == 0.3

    def test_zero_is_not_treated_as_missing(self):
        assert _parse_sentry_sample_rate("0", default=0.9) == 0.0

    def test_one_is_valid(self):
        assert _parse_sentry_sample_rate("1", default=0.1) == 1.0

    def test_non_numeric_returns_default(self):
        assert _parse_sentry_sample_rate("not-a-number", default=0.4) == 0.4

    def test_out_of_range_high_returns_default(self):
        assert _parse_sentry_sample_rate("1.5", default=0.2) == 0.2

    def test_out_of_range_negative_returns_default(self):
        assert _parse_sentry_sample_rate("-0.1", default=0.2) == 0.2


class TestResolveCorsOriginRegex:
    def test_missing_returns_default_pattern(self):
        assert _resolve_cors_origin_regex(None) == DEFAULT_CORS_REGEX

    def test_empty_string_returns_default_pattern(self):
        assert _resolve_cors_origin_regex("") == DEFAULT_CORS_REGEX

    def test_whitespace_only_returns_default_pattern(self):
        assert _resolve_cors_origin_regex("   ") == DEFAULT_CORS_REGEX

    def test_custom_override_is_returned_verbatim(self):
        custom = r"https://.*\.example\.com"
        assert _resolve_cors_origin_regex(custom) == custom

    def test_default_pattern_compiles(self):
        re.compile(DEFAULT_CORS_REGEX)  # must not raise

    def test_default_pattern_matches_devskyy_subdomain(self):
        assert re.fullmatch(DEFAULT_CORS_REGEX, "https://dashboard.devskyy.app")

    def test_default_pattern_rejects_bare_domain(self):
        # bare https://devskyy.app has no subdomain label — regex requires one
        assert not re.fullmatch(DEFAULT_CORS_REGEX, "https://devskyy.app")
