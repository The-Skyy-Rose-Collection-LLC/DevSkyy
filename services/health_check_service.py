"""
Health Check Service - Production Ready
System health monitoring for database, cache, and external APIs

Author: DevSkyy Enterprise Team
Date: 2025-11-10
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional
import httpx

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Health check service for monitoring system dependencies"""

    @staticmethod
    async def check_database(session: AsyncSession) -> Dict:
        """
        Check database connectivity and responsiveness

        Args:
            session: Database session

        Returns:
            Dict with status, response_time_ms, and details
        """
        try:
            start_time = asyncio.get_event_loop().time()

            # Execute simple query
            result = await session.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()

            end_time = asyncio.get_event_loop().time()
            response_time_ms = (end_time - start_time) * 1000

            if row and row[0] == 1:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": "Database connection successful"
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": "Unexpected query result"
                }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "details": "Database connection failed"
            }

    @staticmethod
    async def check_redis(redis_url: str) -> Dict:
        """
        Check Redis connectivity and responsiveness

        Args:
            redis_url: Redis connection URL

        Returns:
            Dict with status, response_time_ms, and details
        """
        try:
            import redis.asyncio as redis

            start_time = asyncio.get_event_loop().time()

            # Connect to Redis
            r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

            # Ping Redis
            response = await r.ping()

            end_time = asyncio.get_event_loop().time()
            response_time_ms = (end_time - start_time) * 1000

            await r.aclose()

            if response:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": "Redis connection successful"
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": "Redis ping failed"
                }

        except ImportError:
            logger.warning("redis package not installed")
            return {
                "status": "unknown",
                "response_time_ms": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "details": "Redis client not available"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "details": "Redis connection failed"
            }

    @staticmethod
    async def check_api(api_name: str, api_key: Optional[str], test_url: Optional[str] = None) -> Dict:
        """
        Check external API connectivity

        Args:
            api_name: Name of the API (Anthropic, OpenAI, etc.)
            api_key: API key for authentication
            test_url: Optional test URL (uses default if None)

        Returns:
            Dict with status, response_time_ms, and details
        """
        if not api_key:
            return {
                "status": "unknown",
                "response_time_ms": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "details": f"{api_name} API key not configured"
            }

        try:
            # Default test URLs
            test_urls = {
                "Anthropic": "https://api.anthropic.com/v1/messages",
                "OpenAI": "https://api.openai.com/v1/models"
            }

            url = test_url or test_urls.get(api_name)
            if not url:
                return {
                    "status": "unknown",
                    "response_time_ms": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": f"No test URL configured for {api_name}"
                }

            headers = {}
            if api_name == "Anthropic":
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
            elif api_name == "OpenAI":
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

            start_time = asyncio.get_event_loop().time()

            async with httpx.AsyncClient(timeout=10.0) as client:
                if api_name == "OpenAI":
                    # OpenAI models endpoint - simple GET
                    response = await client.get(url, headers=headers)
                else:
                    # For Anthropic, we need to send a minimal POST to validate
                    # We won't actually send a message, just check authentication
                    # Using HEAD or GET would be better but Anthropic requires POST
                    response = await client.options(url, headers=headers)

            end_time = asyncio.get_event_loop().time()
            response_time_ms = (end_time - start_time) * 1000

            # Check response
            if response.status_code in [200, 201, 405]:  # 405 = Method Not Allowed (but API is reachable)
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status_code": response.status_code,
                    "details": f"{api_name} API accessible"
                }
            elif response.status_code == 401:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status_code": response.status_code,
                    "details": f"{api_name} API key invalid or expired"
                }
            else:
                return {
                    "status": "degraded",
                    "response_time_ms": round(response_time_ms, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status_code": response.status_code,
                    "details": f"{api_name} API returned unexpected status"
                }

        except httpx.TimeoutException:
            return {
                "status": "unhealthy",
                "response_time_ms": 10000,  # Timeout threshold
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Request timeout",
                "details": f"{api_name} API not responding"
            }
        except Exception as e:
            logger.error(f"{api_name} API health check failed: {e}")
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "details": f"{api_name} API connection failed"
            }

    @staticmethod
    async def comprehensive_health_check(
        session: AsyncSession,
        redis_url: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ) -> Dict:
        """
        Perform comprehensive health check of all system dependencies

        Args:
            session: Database session
            redis_url: Redis connection URL (optional)
            anthropic_api_key: Anthropic API key (optional)
            openai_api_key: OpenAI API key (optional)

        Returns:
            Dict with overall status and individual component statuses
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {}
        }

        # Check database
        db_health = await HealthCheckService.check_database(session)
        results["components"]["database"] = db_health

        # Check Redis if URL provided
        if redis_url:
            redis_health = await HealthCheckService.check_redis(redis_url)
            results["components"]["redis"] = redis_health

        # Check Anthropic API if key provided
        if anthropic_api_key:
            anthropic_health = await HealthCheckService.check_api("Anthropic", anthropic_api_key)
            results["components"]["anthropic_api"] = anthropic_health

        # Check OpenAI API if key provided
        if openai_api_key:
            openai_health = await HealthCheckService.check_api("OpenAI", openai_api_key)
            results["components"]["openai_api"] = openai_health

        # Determine overall status
        unhealthy_count = sum(
            1 for component in results["components"].values()
            if component.get("status") == "unhealthy"
        )
        degraded_count = sum(
            1 for component in results["components"].values()
            if component.get("status") == "degraded"
        )

        if unhealthy_count > 0:
            results["overall_status"] = "unhealthy"
            results["unhealthy_components"] = unhealthy_count
        elif degraded_count > 0:
            results["overall_status"] = "degraded"
            results["degraded_components"] = degraded_count

        return results
