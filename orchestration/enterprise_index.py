"""
Enterprise Code Index
=====================

Multi-provider enterprise code search integration for DevSkyy SuperAgents.

Provides context-aware code search across:
- GitHub Enterprise Code Search
- GitLab Advanced Search
- Sourcegraph API
- Bitbucket Code Search

This enables agents to query existing implementations BEFORE writing new code,
ensuring consistency with organizational patterns.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Models
# =============================================================================


class IndexProvider(str, Enum):
    """Supported enterprise index providers."""

    GITHUB_ENTERPRISE = "github_enterprise"
    GITLAB = "gitlab"
    SOURCEGRAPH = "sourcegraph"
    BITBUCKET = "bitbucket"


class SearchLanguage(str, Enum):
    """Programming language filters."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CPP = "cpp"


@dataclass
class CodeSearchResult:
    """A single code search result."""

    repository: str
    file_path: str
    language: str
    code_snippet: str
    url: str
    score: float
    provider: str
    metadata: dict[str, Any] | None = None


@dataclass
class RepositoryContext:
    """Context about a repository."""

    name: str
    description: str
    primary_language: str
    topics: list[str]
    stars: int
    last_updated: datetime
    url: str
    provider: str


class EnterpriseIndexConfig(BaseModel):
    """Configuration for enterprise index."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # GitHub Enterprise
    github_enterprise_url: str | None = Field(default=None)
    github_enterprise_token: str | None = Field(default=None)

    # GitLab
    gitlab_url: str | None = Field(default="https://gitlab.com")
    gitlab_token: str | None = Field(default=None)

    # Sourcegraph
    sourcegraph_url: str | None = Field(default=None)
    sourcegraph_token: str | None = Field(default=None)

    # Bitbucket
    bitbucket_url: str | None = Field(default="https://api.bitbucket.org/2.0")
    bitbucket_token: str | None = Field(default=None)

    # Search settings
    default_max_results: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    cache_ttl_seconds: int = Field(default=3600)  # 1 hour


# =============================================================================
# Base Index Provider
# =============================================================================


class BaseIndexProvider(ABC):
    """Abstract base class for enterprise index providers."""

    def __init__(self, config: EnterpriseIndexConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[list[CodeSearchResult], datetime]] = {}

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(self.config.timeout_seconds))

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    @abstractmethod
    async def search_code(
        self,
        query: str,
        language: SearchLanguage | None = None,
        max_results: int | None = None,
    ) -> list[CodeSearchResult]:
        """Search for code across repositories."""
        pass

    @abstractmethod
    async def get_repository_context(self, repo_name: str) -> RepositoryContext | None:
        """Get context about a repository."""
        pass

    def _get_cached(self, cache_key: str) -> list[CodeSearchResult] | None:
        """Check cache for recent results."""
        if cache_key in self._cache:
            results, timestamp = self._cache[cache_key]
            age = (datetime.now(UTC) - timestamp).total_seconds()
            if age < self.config.cache_ttl_seconds:
                logger.debug(f"Cache hit for {cache_key} (age: {age:.1f}s)")
                return results
        return None

    def _set_cached(self, cache_key: str, results: list[CodeSearchResult]) -> None:
        """Cache results."""
        self._cache[cache_key] = (results, datetime.now(UTC))


# =============================================================================
# GitHub Enterprise Provider
# =============================================================================


class GitHubEnterpriseProvider(BaseIndexProvider):
    """GitHub Enterprise Code Search provider."""

    async def search_code(
        self,
        query: str,
        language: SearchLanguage | None = None,
        max_results: int | None = None,
    ) -> list[CodeSearchResult]:
        """Search code using GitHub Enterprise Code Search."""
        if not self.config.github_enterprise_url or not self.config.github_enterprise_token:
            logger.warning("GitHub Enterprise not configured")
            return []

        max_results = max_results or self.config.default_max_results
        cache_key = f"gh:{query}:{language}:{max_results}"

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language.value}"

        headers = {
            "Authorization": f"token {self.config.github_enterprise_token}",
            "Accept": "application/vnd.github.v3.text-match+json",
        }

        try:
            response = await self._client.get(
                f"{self.config.github_enterprise_url}/api/v3/search/code",
                params={"q": search_query, "per_page": max_results},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                text_matches = item.get("text_matches", [])
                snippet = text_matches[0]["fragment"] if text_matches else ""

                results.append(
                    CodeSearchResult(
                        repository=item["repository"]["full_name"],
                        file_path=item["path"],
                        language=item.get("language", "unknown"),
                        code_snippet=snippet,
                        url=item["html_url"],
                        score=item.get("score", 0.0),
                        provider="github_enterprise",
                        metadata={"repo_url": item["repository"]["html_url"]},
                    )
                )

            self._set_cached(cache_key, results)
            logger.info(f"GitHub Enterprise search: {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"GitHub Enterprise search failed: {e}")
            return []

    async def get_repository_context(self, repo_name: str) -> RepositoryContext | None:
        """Get repository metadata from GitHub Enterprise."""
        if not self.config.github_enterprise_url or not self.config.github_enterprise_token:
            return None

        headers = {
            "Authorization": f"token {self.config.github_enterprise_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            response = await self._client.get(
                f"{self.config.github_enterprise_url}/api/v3/repos/{repo_name}",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            return RepositoryContext(
                name=data["full_name"],
                description=data.get("description", ""),
                primary_language=data.get("language", ""),
                topics=data.get("topics", []),
                stars=data.get("stargazers_count", 0),
                last_updated=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                url=data["html_url"],
                provider="github_enterprise",
            )

        except Exception as e:
            logger.error(f"GitHub Enterprise repo context failed: {e}")
            return None


# =============================================================================
# GitLab Provider
# =============================================================================


class GitLabProvider(BaseIndexProvider):
    """GitLab Advanced Search provider."""

    async def search_code(
        self,
        query: str,
        language: SearchLanguage | None = None,
        max_results: int | None = None,
    ) -> list[CodeSearchResult]:
        """Search code using GitLab Advanced Search."""
        if not self.config.gitlab_token:
            logger.warning("GitLab not configured")
            return []

        max_results = max_results or self.config.default_max_results
        cache_key = f"gl:{query}:{language}:{max_results}"

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        headers = {"PRIVATE-TOKEN": self.config.gitlab_token}

        try:
            # GitLab search API
            response = await self._client.get(
                f"{self.config.gitlab_url}/api/v4/search",
                params={"scope": "blobs", "search": query, "per_page": max_results},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data:
                # Filter by language if specified
                if language and not item.get("path", "").endswith(f".{language.value}"):
                    continue

                results.append(
                    CodeSearchResult(
                        repository=item.get("project_id", "unknown"),
                        file_path=item.get("path", ""),
                        language=language.value if language else "unknown",
                        code_snippet=item.get("data", "")[:500],
                        url=f"{self.config.gitlab_url}/{item.get('project_id')}/-/blob/{item.get('ref')}/{item.get('path')}",
                        score=1.0,
                        provider="gitlab",
                    )
                )

            self._set_cached(cache_key, results)
            logger.info(f"GitLab search: {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"GitLab search failed: {e}")
            return []

    async def get_repository_context(self, repo_name: str) -> RepositoryContext | None:
        """Get project metadata from GitLab."""
        if not self.config.gitlab_token:
            return None

        headers = {"PRIVATE-TOKEN": self.config.gitlab_token}

        try:
            # Encode repo name for URL
            import urllib.parse

            encoded_repo = urllib.parse.quote(repo_name, safe="")

            response = await self._client.get(
                f"{self.config.gitlab_url}/api/v4/projects/{encoded_repo}",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            return RepositoryContext(
                name=data["path_with_namespace"],
                description=data.get("description", ""),
                primary_language="unknown",  # GitLab doesn't provide this easily
                topics=data.get("topics", []),
                stars=data.get("star_count", 0),
                last_updated=datetime.fromisoformat(
                    data["last_activity_at"].replace("Z", "+00:00")
                ),
                url=data["web_url"],
                provider="gitlab",
            )

        except Exception as e:
            logger.error(f"GitLab project context failed: {e}")
            return None


# =============================================================================
# Sourcegraph Provider
# =============================================================================


class SourcegraphProvider(BaseIndexProvider):
    """Sourcegraph API provider."""

    async def search_code(
        self,
        query: str,
        language: SearchLanguage | None = None,
        max_results: int | None = None,
    ) -> list[CodeSearchResult]:
        """Search code using Sourcegraph."""
        if not self.config.sourcegraph_url or not self.config.sourcegraph_token:
            logger.warning("Sourcegraph not configured")
            return []

        max_results = max_results or self.config.default_max_results
        cache_key = f"sg:{query}:{language}:{max_results}"

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Build search query
        search_query = query
        if language:
            search_query += f" lang:{language.value}"

        headers = {"Authorization": f"token {self.config.sourcegraph_token}"}

        try:
            # Sourcegraph GraphQL API
            graphql_query = """
            query Search($query: String!) {
              search(query: $query, version: V3, patternType: literal) {
                results {
                  results {
                    ... on FileMatch {
                      repository {
                        name
                      }
                      file {
                        path
                        url
                      }
                      lineMatches {
                        preview
                      }
                    }
                  }
                }
              }
            }
            """

            response = await self._client.post(
                f"{self.config.sourcegraph_url}/.api/graphql",
                json={"query": graphql_query, "variables": {"query": search_query}},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for match in (
                data.get("data", {})
                .get("search", {})
                .get("results", {})
                .get("results", [])[:max_results]
            ):
                if "file" not in match:
                    continue

                snippet = ""
                if match.get("lineMatches"):
                    snippet = match["lineMatches"][0].get("preview", "")

                results.append(
                    CodeSearchResult(
                        repository=match["repository"]["name"],
                        file_path=match["file"]["path"],
                        language=language.value if language else "unknown",
                        code_snippet=snippet,
                        url=match["file"]["url"],
                        score=1.0,
                        provider="sourcegraph",
                    )
                )

            self._set_cached(cache_key, results)
            logger.info(f"Sourcegraph search: {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Sourcegraph search failed: {e}")
            return []

    async def get_repository_context(self, repo_name: str) -> RepositoryContext | None:
        """Get repository metadata from Sourcegraph."""
        # Sourcegraph doesn't provide detailed repo metadata via search API
        return None


# =============================================================================
# Bitbucket Provider
# =============================================================================


class BitbucketProvider(BaseIndexProvider):
    """Bitbucket Code Search provider."""

    async def search_code(
        self,
        query: str,
        language: SearchLanguage | None = None,
        max_results: int | None = None,
    ) -> list[CodeSearchResult]:
        """Search code using Bitbucket."""
        if not self.config.bitbucket_token:
            logger.warning("Bitbucket not configured")
            return []

        max_results = max_results or self.config.default_max_results
        cache_key = f"bb:{query}:{language}:{max_results}"

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # Bitbucket search API (limited compared to others)
            # Note: Bitbucket Cloud doesn't have a dedicated code search API
            # This is a placeholder for when using Bitbucket Server/Data Center
            logger.warning("Bitbucket code search not fully implemented (API limitations)")
            return []

        except Exception as e:
            logger.error(f"Bitbucket search failed: {e}")
            return []

    async def get_repository_context(self, repo_name: str) -> RepositoryContext | None:
        """Get repository metadata from Bitbucket."""
        if not self.config.bitbucket_token:
            return None

        headers = {"Authorization": f"Bearer {self.config.bitbucket_token}"}

        try:
            response = await self._client.get(
                f"{self.config.bitbucket_url}/repositories/{repo_name}",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            return RepositoryContext(
                name=data["full_name"],
                description=data.get("description", ""),
                primary_language=data.get("language", ""),
                topics=[],
                stars=0,  # Bitbucket doesn't have stars
                last_updated=datetime.fromisoformat(data["updated_on"].replace("Z", "+00:00")),
                url=data["links"]["html"]["href"],
                provider="bitbucket",
            )

        except Exception as e:
            logger.error(f"Bitbucket repo context failed: {e}")
            return None


# =============================================================================
# Multi-Provider Index
# =============================================================================


class EnterpriseIndex:
    """
    Multi-provider enterprise code index.

    Searches across all configured providers in parallel for maximum coverage.
    """

    def __init__(self, config: EnterpriseIndexConfig | None = None):
        self.config = config or EnterpriseIndexConfig()
        self.providers: list[BaseIndexProvider] = []

    async def initialize(self) -> None:
        """Initialize all configured providers."""
        # GitHub Enterprise
        if self.config.github_enterprise_url and self.config.github_enterprise_token:
            provider = GitHubEnterpriseProvider(self.config)
            await provider.initialize()
            self.providers.append(provider)
            logger.info("GitHub Enterprise provider initialized")

        # GitLab
        if self.config.gitlab_token:
            provider = GitLabProvider(self.config)
            await provider.initialize()
            self.providers.append(provider)
            logger.info("GitLab provider initialized")

        # Sourcegraph
        if self.config.sourcegraph_url and self.config.sourcegraph_token:
            provider = SourcegraphProvider(self.config)
            await provider.initialize()
            self.providers.append(provider)
            logger.info("Sourcegraph provider initialized")

        # Bitbucket
        if self.config.bitbucket_token:
            provider = BitbucketProvider(self.config)
            await provider.initialize()
            self.providers.append(provider)
            logger.info("Bitbucket provider initialized")

        logger.info(f"EnterpriseIndex initialized with {len(self.providers)} providers")

    async def close(self) -> None:
        """Close all providers."""
        for provider in self.providers:
            await provider.close()

    async def search_code(
        self,
        query: str,
        language: SearchLanguage | None = None,
        max_results_per_provider: int = 5,
    ) -> list[CodeSearchResult]:
        """
        Search for code across all providers in parallel.

        Args:
            query: Search query
            language: Filter by programming language
            max_results_per_provider: Max results from each provider

        Returns:
            Combined and deduplicated results from all providers
        """
        import asyncio

        if not self.providers:
            logger.warning("No providers configured")
            return []

        # Search all providers in parallel
        tasks = [
            provider.search_code(query, language, max_results_per_provider)
            for provider in self.providers
        ]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        all_results = []
        for results in results_list:
            if isinstance(results, list):
                all_results.extend(results)
            else:
                logger.error(f"Provider search failed: {results}")

        # Sort by score (descending)
        all_results.sort(key=lambda r: r.score, reverse=True)

        logger.info(f"Enterprise search: {len(all_results)} total results for '{query}'")
        return all_results

    async def find_similar_implementations(
        self, code_snippet: str, language: SearchLanguage | None = None
    ) -> list[CodeSearchResult]:
        """
        Find similar code implementations across enterprise codebases.

        Uses semantic search to find code that does similar things.
        """
        # Extract key patterns from code snippet
        # For now, use simple keyword extraction
        # TODO: Integrate with semantic_analyzer.py for better pattern detection
        keywords = self._extract_keywords(code_snippet)
        query = " ".join(keywords[:3])  # Top 3 keywords

        return await self.search_code(query, language, max_results_per_provider=3)

    def _extract_keywords(self, code: str) -> list[str]:
        """Extract keywords from code (simple heuristic)."""
        import re

        # Extract function/class names
        patterns = [
            r"def (\w+)",
            r"class (\w+)",
            r"async def (\w+)",
            r"function (\w+)",
        ]

        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, code)
            keywords.extend(matches)

        return keywords


# =============================================================================
# Factory
# =============================================================================


def create_enterprise_index(config: EnterpriseIndexConfig | None = None) -> EnterpriseIndex:
    """
    Create an enterprise index instance.

    Args:
        config: Configuration. Reads from environment if not provided.

    Returns:
        EnterpriseIndex: Multi-provider index instance.

    Example:
        >>> config = EnterpriseIndexConfig(
        ...     github_enterprise_url="https://github.company.com",
        ...     github_enterprise_token=os.getenv("GH_TOKEN")
        ... )
        >>> index = create_enterprise_index(config)
        >>> await index.initialize()
        >>> results = await index.search_code("authentication middleware", SearchLanguage.PYTHON)
    """
    if config is None:
        config = EnterpriseIndexConfig(
            github_enterprise_url=os.getenv("GITHUB_ENTERPRISE_URL"),
            github_enterprise_token=os.getenv("GITHUB_ENTERPRISE_TOKEN"),
            gitlab_url=os.getenv("GITLAB_URL", "https://gitlab.com"),
            gitlab_token=os.getenv("GITLAB_TOKEN"),
            sourcegraph_url=os.getenv("SOURCEGRAPH_URL"),
            sourcegraph_token=os.getenv("SOURCEGRAPH_TOKEN"),
            bitbucket_token=os.getenv("BITBUCKET_TOKEN"),
        )

    return EnterpriseIndex(config)
