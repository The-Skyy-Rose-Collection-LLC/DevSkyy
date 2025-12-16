#!/usr/bin/env python3
"""
Vercel Deployment Verification Script
====================================

Verifies that the DevSkyy platform is properly deployed and accessible on Vercel.
Run this after deployment to ensure all endpoints are working correctly.
"""

import asyncio
import sys

import httpx


class DeploymentVerifier:
    def __init__(self, base_url: str = "https://devskyy.vercel.app"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def check_endpoint(self, path: str, expected_status: int = 200) -> dict:
        """Check a single endpoint"""
        url = f"{self.base_url}{path}"
        try:
            response = await self.client.get(url)
            return {
                "url": url,
                "status": response.status_code,
                "success": response.status_code == expected_status,
                "response_time": response.elapsed.total_seconds(),
                "headers": dict(response.headers),
                "content_length": len(response.content),
            }
        except Exception as e:
            return {
                "url": url,
                "status": 0,
                "success": False,
                "error": str(e),
                "response_time": 0,
                "headers": {},
                "content_length": 0,
            }

    async def verify_health_endpoints(self) -> list[dict]:
        """Verify all health check endpoints"""
        endpoints = ["/health", "/ready", "/live"]

        results = []
        for endpoint in endpoints:
            result = await self.check_endpoint(endpoint)
            results.append(result)

        return results

    async def verify_api_documentation(self) -> list[dict]:
        """Verify API documentation endpoints"""
        endpoints = ["/docs", "/redoc"]

        results = []
        for endpoint in endpoints:
            result = await self.check_endpoint(endpoint)
            results.append(result)

        return results

    async def verify_security_headers(self) -> dict:
        """Verify security headers are properly set"""
        result = await self.check_endpoint("/health")

        if not result["success"]:
            return {"success": False, "error": "Could not fetch headers"}

        headers = result["headers"]
        security_checks = {
            "cors": "access-control-allow-origin" in headers,
            "xss_protection": "x-xss-protection" in headers,
            "content_type_options": "x-content-type-options" in headers,
            "frame_options": "x-frame-options" in headers,
            "hsts": "strict-transport-security" in headers,
        }

        return {
            "success": all(security_checks.values()),
            "checks": security_checks,
            "headers": headers,
        }

    def print_results(self, results: list[dict], title: str):
        """Print formatted results"""
        print(f"\n🔍 {title}")
        print("=" * 50)

        for result in results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {result['url']}")
            print(f"   Status: {result['status']}")
            print(f"   Response Time: {result.get('response_time', 0):.3f}s")

            if not result["success"] and "error" in result:
                print(f"   Error: {result['error']}")
            print()

    async def run_verification(self):
        """Run complete deployment verification"""
        print("🚀 DevSkyy Vercel Deployment Verification")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)

        # Check health endpoints
        health_results = await self.verify_health_endpoints()
        self.print_results(health_results, "Health Check Endpoints")

        # Check documentation endpoints
        docs_results = await self.verify_api_documentation()
        self.print_results(docs_results, "API Documentation Endpoints")

        # Check security headers
        security_result = await self.verify_security_headers()
        print("\n🔒 Security Headers Verification")
        print("=" * 50)

        if security_result["success"]:
            print("✅ All security headers properly configured")
            for check, passed in security_result["checks"].items():
                icon = "✅" if passed else "❌"
                print(f"   {icon} {check.replace('_', ' ').title()}")
        else:
            print("❌ Security headers verification failed")
            if "error" in security_result:
                print(f"   Error: {security_result['error']}")

        # Summary
        all_results = health_results + docs_results
        total_checks = len(all_results) + 1  # +1 for security headers
        passed_checks = sum(1 for r in all_results if r["success"]) + (
            1 if security_result["success"] else 0
        )

        print("\n" + "=" * 60)
        print(f"📊 Verification Summary: {passed_checks}/{total_checks} checks passed")

        if passed_checks == total_checks:
            print("🎉 Deployment verification successful! All systems operational.")
            return 0
        else:
            print("⚠️  Some checks failed. Please review the issues above.")
            return 1


async def main():
    """Main verification function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://devskyy.vercel.app"

    async with DeploymentVerifier(base_url) as verifier:
        return await verifier.run_verification()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        sys.exit(1)
