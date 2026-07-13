"""Tests for main_enterprise.py config-parsing helpers (Sentry sample rates, CORS
origin-regex override) — see docs on _parse_sentry_sample_rate / _resolve_cors_origin_regex.
"""

import re

from main_enterprise import (
    _parse_sentry_sample_rate,
    _resolve_cors_origin_regex,
    _resolve_schema_url,
)

DEFAULT_CORS_REGEX = (
    r"^https://("
    r"([a-z0-9-]+\.)?devskyy\.app"
    r"|devskyy-[a-z0-9-]+-skyyroseco\.vercel\.app"
    r")$"
)


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

    def test_default_pattern_matches_bare_and_www_and_app_devskyy(self):
        # The bare production domain and its real subdomains MUST be allowed —
        # the old pattern rejected the bare domain, which was itself a defect.
        for origin in (
            "https://devskyy.app",
            "https://www.devskyy.app",
            "https://app.devskyy.app",
            "https://api.devskyy.app",
        ):
            assert re.fullmatch(DEFAULT_CORS_REGEX, origin), origin

    def test_default_pattern_matches_project_vercel_previews_only(self):
        assert re.fullmatch(DEFAULT_CORS_REGEX, "https://devskyy-abc123-skyyroseco.vercel.app")

    def test_default_pattern_rejects_attacker_origins(self):
        # The core fix: credentialed CORS must NOT reflect attacker-registrable
        # origins. Every one of these previously matched the *.vercel.app hole
        # or could suffix-extend an unanchored match.
        for origin in (
            "https://evil.vercel.app",  # any attacker Vercel app
            "https://devskyy-x-attacker.vercel.app",  # not the -skyyroseco project
            "https://devskyy.app.evil.com",  # suffix smuggling
            "https://evildevskyy.app",  # prefix smuggling
            "http://devskyy.app",  # non-TLS
            "https://notdevskyy.app",
        ):
            assert not re.fullmatch(DEFAULT_CORS_REGEX, origin), origin


class TestResolveSchemaUrl:
    """The /docs, /redoc, and /openapi.json endpoints must be DISABLED in
    production — /openapi.json alone leaks every route + parameter on the
    internet-facing backend. A revert to serving them in prod must fail CI.
    """

    def test_production_disables_openapi(self):
        assert _resolve_schema_url("production", "/openapi.json") is None

    def test_production_disables_docs_and_redoc(self):
        assert _resolve_schema_url("production", "/docs") is None
        assert _resolve_schema_url("production", "/redoc") is None

    def test_development_serves_the_path(self):
        assert _resolve_schema_url("development", "/openapi.json") == "/openapi.json"

    def test_only_production_gates_it(self):
        # staging / any non-"production" value keeps the endpoints on.
        for env in ("staging", "test", "dev", ""):
            assert _resolve_schema_url(env, "/docs") == "/docs"
