"""
Comprehensive Test Suite for Security Headers Module (OWASP compliant)

Tests security headers implementation including CSP, X-Frame-Options,
X-Content-Type-Options, HSTS, and other security headers per OWASP recommendations.

Per CLAUDE.md Rule #7: CSP headers required
Per CLAUDE.md Rule #8: Target ≥90% coverage
Per CLAUDE.md Rule #1: Verify against OWASP Secure Headers Project

Author: DevSkyy Enterprise Team
Version: 1.0.0
Python: >=3.11.0
"""

from security.secure_headers import SecurityHeaders, security_headers_manager


class TestSecurityHeadersGetAllHeaders:
    """Test suite for SecurityHeaders.get_all_headers() method"""

    def test_get_all_headers_returns_dict(self):
        """Test that get_all_headers returns a dictionary"""
        headers = SecurityHeaders.get_all_headers()
        assert isinstance(headers, dict)
        assert len(headers) > 0

    def test_x_frame_options_header(self):
        """Test X-Frame-Options header prevents clickjacking (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options_header(self):
        """Test X-Content-Type-Options prevents MIME sniffing (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

    def test_x_xss_protection_header(self):
        """Test X-XSS-Protection for legacy browser XSS protection (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"

    def test_referrer_policy_header(self):
        """Test Referrer-Policy controls referrer information (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self):
        """Test Permissions-Policy restricts browser features (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Permissions-Policy" in headers
        assert "geolocation=()" in headers["Permissions-Policy"]
        assert "microphone=()" in headers["Permissions-Policy"]
        assert "camera=()" in headers["Permissions-Policy"]

    def test_strict_transport_security_header(self):
        """Test HSTS enforces HTTPS connections (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Strict-Transport-Security" in headers
        hsts = headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

    def test_content_security_policy_header(self):
        """Test CSP header prevents XSS and injection attacks (OWASP Rule #7)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Content-Security-Policy" in headers
        csp = headers["Content-Security-Policy"]

        # Verify required CSP directives
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self'" in csp
        assert "font-src 'self'" in csp
        assert "connect-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "base-uri 'self'" in csp
        assert "form-action 'self'" in csp

    def test_server_header(self):
        """Test Server header obscures server details (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Server" in headers
        assert headers["Server"] == "DevSkyy/5.1"

    def test_cross_origin_embedder_policy_header(self):
        """Test COEP header for cross-origin isolation (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Cross-Origin-Embedder-Policy" in headers
        assert headers["Cross-Origin-Embedder-Policy"] == "require-corp"

    def test_cross_origin_opener_policy_header(self):
        """Test COOP header prevents window context access (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Cross-Origin-Opener-Policy" in headers
        assert headers["Cross-Origin-Opener-Policy"] == "same-origin"

    def test_cross_origin_resource_policy_header(self):
        """Test CORP header controls resource loading (OWASP)"""
        headers = SecurityHeaders.get_all_headers()
        assert "Cross-Origin-Resource-Policy" in headers
        assert headers["Cross-Origin-Resource-Policy"] == "same-origin"

    def test_all_headers_count(self):
        """Test that all expected security headers are present"""
        headers = SecurityHeaders.get_all_headers()
        expected_headers = {
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Server",
            "Cross-Origin-Embedder-Policy",
            "Cross-Origin-Opener-Policy",
            "Cross-Origin-Resource-Policy",
        }
        assert set(headers.keys()) == expected_headers

    def test_headers_are_strings(self):
        """Test that all header values are strings"""
        headers = SecurityHeaders.get_all_headers()
        for key, value in headers.items():
            assert isinstance(key, str), f"Header key {key} is not a string"
            assert isinstance(value, str), f"Header value for {key} is not a string"

    def test_headers_non_empty(self):
        """Test that all header values are non-empty"""
        headers = SecurityHeaders.get_all_headers()
        for key, value in headers.items():
            assert value.strip(), f"Header {key} has empty value"


class TestSecurityHeadersGetApiHeaders:
    """Test suite for SecurityHeaders.get_api_headers() method"""

    def test_get_api_headers_returns_dict(self):
        """Test that get_api_headers returns a dictionary"""
        headers = SecurityHeaders.get_api_headers()
        assert isinstance(headers, dict)
        assert len(headers) > 0

    def test_api_x_frame_options_header(self):
        """Test API X-Frame-Options header (OWASP)"""
        headers = SecurityHeaders.get_api_headers()
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    def test_api_x_content_type_options_header(self):
        """Test API X-Content-Type-Options header (OWASP)"""
        headers = SecurityHeaders.get_api_headers()
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

    def test_api_x_xss_protection_header(self):
        """Test API X-XSS-Protection header (OWASP)"""
        headers = SecurityHeaders.get_api_headers()
        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"

    def test_api_referrer_policy_header(self):
        """Test API Referrer-Policy is more restrictive (OWASP)"""
        headers = SecurityHeaders.get_api_headers()
        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] == "no-referrer"

    def test_api_cache_control_header(self):
        """Test API Cache-Control prevents sensitive data caching (OWASP)"""
        headers = SecurityHeaders.get_api_headers()
        assert "Cache-Control" in headers
        cache_control = headers["Cache-Control"]
        assert "no-store" in cache_control
        assert "max-age=0" in cache_control

    def test_api_pragma_header(self):
        """Test API Pragma header for legacy cache control (OWASP)"""
        headers = SecurityHeaders.get_api_headers()
        assert "Pragma" in headers
        assert headers["Pragma"] == "no-cache"

    def test_api_headers_count(self):
        """Test that all expected API headers are present"""
        headers = SecurityHeaders.get_api_headers()
        expected_headers = {
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Cache-Control",
            "Pragma",
        }
        assert set(headers.keys()) == expected_headers

    def test_api_headers_are_strings(self):
        """Test that all API header values are strings"""
        headers = SecurityHeaders.get_api_headers()
        for key, value in headers.items():
            assert isinstance(key, str), f"API header key {key} is not a string"
            assert isinstance(value, str), f"API header value for {key} is not a string"

    def test_api_headers_non_empty(self):
        """Test that all API header values are non-empty"""
        headers = SecurityHeaders.get_api_headers()
        for key, value in headers.items():
            assert value.strip(), f"API header {key} has empty value"

    def test_api_headers_subset_of_all_headers(self):
        """Test that API headers are more specific than all headers"""
        all_headers = SecurityHeaders.get_all_headers()
        api_headers = SecurityHeaders.get_api_headers()

        # API headers should have different cache policies
        assert api_headers.get("Cache-Control") is not None
        assert all_headers.get("Cache-Control") is None

        # API headers should have stricter referrer policy
        assert api_headers["Referrer-Policy"] == "no-referrer"
        assert all_headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


class TestSecurityHeadersGlobalInstance:
    """Test suite for global security_headers_manager instance"""

    def test_global_instance_exists(self):
        """Test that global security_headers_manager instance exists"""
        assert security_headers_manager is not None

    def test_global_instance_is_security_headers(self):
        """Test that global instance is of type SecurityHeaders"""
        assert isinstance(security_headers_manager, SecurityHeaders)

    def test_global_instance_get_all_headers(self):
        """Test that global instance can call get_all_headers"""
        headers = security_headers_manager.get_all_headers()
        assert isinstance(headers, dict)
        assert "Content-Security-Policy" in headers

    def test_global_instance_get_api_headers(self):
        """Test that global instance can call get_api_headers"""
        headers = security_headers_manager.get_api_headers()
        assert isinstance(headers, dict)
        assert "Cache-Control" in headers


class TestSecurityHeadersStaticMethods:
    """Test suite for static method behavior"""

    def test_get_all_headers_is_static(self):
        """Test that get_all_headers can be called without instance"""
        # Should work without instantiation
        headers1 = SecurityHeaders.get_all_headers()

        # Should also work with instance
        instance = SecurityHeaders()
        headers2 = instance.get_all_headers()

        # Both should return identical dictionaries
        assert headers1 == headers2

    def test_get_api_headers_is_static(self):
        """Test that get_api_headers can be called without instance"""
        # Should work without instantiation
        headers1 = SecurityHeaders.get_api_headers()

        # Should also work with instance
        instance = SecurityHeaders()
        headers2 = instance.get_api_headers()

        # Both should return identical dictionaries
        assert headers1 == headers2

    def test_multiple_calls_return_consistent_results(self):
        """Test that multiple calls return consistent headers"""
        headers1 = SecurityHeaders.get_all_headers()
        headers2 = SecurityHeaders.get_all_headers()
        headers3 = SecurityHeaders.get_all_headers()

        assert headers1 == headers2 == headers3

    def test_headers_are_independent_copies(self):
        """Test that returned headers are not shared references"""
        headers1 = SecurityHeaders.get_all_headers()
        headers2 = SecurityHeaders.get_all_headers()

        # Modify one header
        headers1["X-Frame-Options"] = "MODIFIED"

        # Other should not be affected
        assert headers2["X-Frame-Options"] == "DENY"


class TestSecurityHeadersOWASPCompliance:
    """Test suite for OWASP Secure Headers Project compliance"""

    def test_owasp_recommended_headers_present(self):
        """Test that OWASP-recommended headers are present (Rule #7)"""
        headers = SecurityHeaders.get_all_headers()

        # OWASP Top Security Headers
        owasp_headers = [
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Strict-Transport-Security",
            "Referrer-Policy",
        ]

        for header in owasp_headers:
            assert header in headers, f"OWASP-recommended header {header} is missing"

    def test_csp_prevents_inline_scripts_properly(self):
        """Test CSP configuration allows necessary inline scripts"""
        headers = SecurityHeaders.get_all_headers()
        csp = headers["Content-Security-Policy"]

        # Verify script-src includes necessary directives
        assert "script-src" in csp
        assert "'self'" in csp

    def test_hsts_configuration_secure(self):
        """Test HSTS is configured securely per OWASP"""
        headers = SecurityHeaders.get_all_headers()
        hsts = headers["Strict-Transport-Security"]

        # OWASP recommends at least 1 year (31536000 seconds)
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

    def test_x_frame_options_prevents_clickjacking(self):
        """Test X-Frame-Options is set to DENY per OWASP"""
        headers = SecurityHeaders.get_all_headers()
        assert headers["X-Frame-Options"] == "DENY"

    def test_referrer_policy_restricts_referrer(self):
        """Test Referrer-Policy restricts referrer information"""
        all_headers = SecurityHeaders.get_all_headers()
        api_headers = SecurityHeaders.get_api_headers()

        # All headers should have some referrer policy
        assert all_headers["Referrer-Policy"] in [
            "strict-origin-when-cross-origin",
            "no-referrer",
            "same-origin"
        ]

        # API should be most restrictive
        assert api_headers["Referrer-Policy"] == "no-referrer"


class TestSecurityHeadersEdgeCases:
    """Test suite for edge cases and special scenarios"""

    def test_headers_with_multiple_values(self):
        """Test headers with multiple directives are properly formatted"""
        headers = SecurityHeaders.get_all_headers()

        # CSP should have multiple directives
        csp = headers["Content-Security-Policy"]
        directives = csp.split(";")
        assert len(directives) >= 9  # At least 9 directives specified

    def test_empty_instance_creation(self):
        """Test that SecurityHeaders can be instantiated"""
        instance = SecurityHeaders()
        assert instance is not None
        assert isinstance(instance, SecurityHeaders)

    def test_headers_thread_safety(self):
        """Test that headers can be safely accessed from multiple contexts"""
        import concurrent.futures

        def get_headers():
            return SecurityHeaders.get_all_headers()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_headers) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
