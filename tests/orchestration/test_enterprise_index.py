"""
Tests for Enterprise Index
===========================

Tests multi-provider enterprise code search following TEST_STRATEGY.md patterns.

Coverage:
- Multi-provider parallel search
- Provider resilience (failures handled gracefully)
- Result sorting by score
- Cache functionality
"""

from unittest.mock import AsyncMock, patch

import pytest

from orchestration.enterprise_index import (
    CodeSearchResult,
    EnterpriseIndex,
    EnterpriseIndexConfig,
    GitHubEnterpriseProvider,
    GitLabProvider,
    SearchLanguage,
    create_enterprise_index,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enterprise_index_parallel_search(mock_api_keys):
    """Test parallel search across all providers."""
    # Configure with GitHub and GitLab
    config = EnterpriseIndexConfig(
        github_enterprise_url="https://github.test.com",
        github_enterprise_token="test_gh_token",
        gitlab_url="https://gitlab.test.com",
        gitlab_token="test_gl_token",
    )

    index = EnterpriseIndex(config)

    # Mock provider search methods
    gh_results = [
        CodeSearchResult(
            repository="org/repo1",
            file_path="auth.py",
            language="python",
            code_snippet="def authenticate():",
            url="https://github.test.com/org/repo1/auth.py",
            score=0.95,
            provider="github_enterprise",
        ),
        CodeSearchResult(
            repository="org/repo2",
            file_path="middleware/auth.py",
            language="python",
            code_snippet="class AuthMiddleware:",
            url="https://github.test.com/org/repo2/middleware/auth.py",
            score=0.85,
            provider="github_enterprise",
        ),
    ]

    gl_results = [
        CodeSearchResult(
            repository="project/service",
            file_path="src/auth.py",
            language="python",
            code_snippet="async def verify_token():",
            url="https://gitlab.test.com/project/service",
            score=0.90,
            provider="gitlab",
        ),
    ]

    with (
        patch.object(
            GitHubEnterpriseProvider, "search_code", new_callable=AsyncMock, return_value=gh_results
        ),
        patch.object(
            GitLabProvider, "search_code", new_callable=AsyncMock, return_value=gl_results
        ),
    ):
        await index.initialize()

        results = await index.search_code(
            query="authentication middleware",
            language=SearchLanguage.PYTHON,
            max_results_per_provider=5,
        )

    # Should get results from both providers
    assert len(results) == 3

    # Results should be sorted by score (descending)
    assert results[0].score >= results[1].score >= results[2].score
    assert results[0].score == 0.95
    assert results[1].score == 0.90
    assert results[2].score == 0.85

    # Should have results from both providers
    providers = {r.provider for r in results}
    assert "github_enterprise" in providers
    assert "gitlab" in providers


@pytest.mark.integration
@pytest.mark.asyncio
async def test_enterprise_index_resilience(mock_api_keys):
    """Test resilience when one provider fails."""
    config = EnterpriseIndexConfig(
        github_enterprise_url="https://github.test.com",
        github_enterprise_token="test_gh_token",
        gitlab_url="https://gitlab.test.com",
        gitlab_token="test_gl_token",
    )

    index = EnterpriseIndex(config)

    gl_results = [
        CodeSearchResult(
            repository="project/service",
            file_path="src/handler.py",
            language="python",
            code_snippet="def handle_request():",
            url="https://gitlab.test.com/project/service",
            score=0.90,
            provider="gitlab",
        ),
    ]

    # Mock GitHub to fail, GitLab to succeed
    with (
        patch.object(
            GitHubEnterpriseProvider,
            "search_code",
            new_callable=AsyncMock,
            side_effect=Exception("GitHub API error"),
        ),
        patch.object(
            GitLabProvider, "search_code", new_callable=AsyncMock, return_value=gl_results
        ),
    ):
        await index.initialize()

        results = await index.search_code("test")

    # Should still get GitLab results despite GitHub failure
    assert len(results) == 1
    assert results[0].provider == "gitlab"
    assert all(r.provider != "github_enterprise" for r in results)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enterprise_index_no_providers():
    """Test behavior when no providers are configured."""
    config = EnterpriseIndexConfig()  # No credentials
    index = EnterpriseIndex(config)

    await index.initialize()

    results = await index.search_code("test query")

    # Should return empty list with warning
    assert results == []
    assert len(index.providers) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_github_provider_search(mock_api_keys, mock_github_search_response):
    """Test GitHub Enterprise provider search."""
    config = EnterpriseIndexConfig(
        github_enterprise_url="https://github.test.com",
        github_enterprise_token="test_token",
    )

    provider = GitHubEnterpriseProvider(config)

    # Mock HTTP client - must return awaitable
    # Note: response.json() and response.raise_for_status() are synchronous in httpx
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.json = Mock(return_value=mock_github_search_response)
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    provider._client = mock_client

    results = await provider.search_code(
        query="authentication",
        language=SearchLanguage.PYTHON,
        max_results=10,
    )

    assert len(results) > 0
    assert all(r.provider == "github_enterprise" for r in results)
    assert results[0].repository == "org/repo1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_github_provider_cache():
    """Test GitHub provider caching mechanism."""
    config = EnterpriseIndexConfig(
        github_enterprise_url="https://github.test.com",
        github_enterprise_token="test_token",
        cache_ttl_seconds=3600,
    )

    provider = GitHubEnterpriseProvider(config)

    # Mock HTTP client
    # Note: response.json() and response.raise_for_status() are synchronous in httpx
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.json = Mock(
        return_value={
            "items": [
                {
                    "repository": {
                        "full_name": "org/repo",
                        "html_url": "https://github.test.com/org/repo",
                    },
                    "path": "test.py",
                    "language": "Python",
                    "html_url": "https://github.test.com/org/repo/blob/main/test.py",
                    "score": 0.95,
                    "text_matches": [{"fragment": "def test():"}],
                }
            ]
        }
    )
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    provider._client = mock_client

    # First call should hit API
    results1 = await provider.search_code("test")
    assert len(results1) == 1
    assert mock_client.get.call_count == 1

    # Second call should use cache
    results2 = await provider.search_code("test")
    assert len(results2) == 1
    assert mock_client.get.call_count == 1  # No additional API call
    assert results1[0].repository == results2[0].repository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gitlab_provider_search(mock_api_keys):
    """Test GitLab provider search."""
    config = EnterpriseIndexConfig(
        gitlab_url="https://gitlab.test.com",
        gitlab_token="test_token",
    )

    provider = GitLabProvider(config)

    # Mock HTTP client
    # Note: response.json() and response.raise_for_status() are synchronous in httpx
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.json = Mock(
        return_value=[
            {
                "project_id": "123",
                "path": "src/auth.py",
                "ref": "main",
                "data": "def authenticate():\n    pass",
            }
        ]
    )
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    provider._client = mock_client

    # Test without language filter (GitLab's language filter has issues)
    results = await provider.search_code(
        query="authentication",
        language=None,
    )

    assert len(results) == 1
    assert results[0].provider == "gitlab"
    assert results[0].repository == "123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_find_similar_implementations(mock_api_keys):
    """Test finding similar implementations."""
    config = EnterpriseIndexConfig(
        github_enterprise_url="https://github.test.com",
        github_enterprise_token="test_token",
    )

    index = EnterpriseIndex(config)

    mock_results = [
        CodeSearchResult(
            repository="org/repo",
            file_path="similar.py",
            language="python",
            code_snippet="def authenticate():",
            url="https://github.test.com/org/repo/similar.py",
            score=0.90,
            provider="github_enterprise",
        ),
    ]

    with patch.object(
        GitHubEnterpriseProvider, "search_code", new_callable=AsyncMock, return_value=mock_results
    ):
        await index.initialize()

        code_snippet = """
        def authenticate(username, password):
            # Verify credentials
            return verify_credentials(username, password)
        """

        results = await index.find_similar_implementations(
            code_snippet,
            language=SearchLanguage.PYTHON,
        )

    assert len(results) > 0
    assert all(r.language == "python" for r in results)


@pytest.mark.unit
def test_create_enterprise_index_from_env(monkeypatch):
    """Test factory function creates index from environment variables."""
    monkeypatch.setenv("GITHUB_ENTERPRISE_URL", "https://github.test.com")
    monkeypatch.setenv("GITHUB_ENTERPRISE_TOKEN", "test_gh_token")
    monkeypatch.setenv("GITLAB_TOKEN", "test_gl_token")

    index = create_enterprise_index()

    assert index.config.github_enterprise_url == "https://github.test.com"
    assert index.config.github_enterprise_token == "test_gh_token"
    assert index.config.gitlab_token == "test_gl_token"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_provider_initialization(mock_api_keys):
    """Test that only configured providers are initialized."""
    # Only configure GitHub
    config = EnterpriseIndexConfig(
        github_enterprise_url="https://github.test.com",
        github_enterprise_token="test_token",
    )

    index = EnterpriseIndex(config)

    with patch.object(GitHubEnterpriseProvider, "initialize", new_callable=AsyncMock):
        await index.initialize()

    # Should have only GitHub provider
    assert len(index.providers) == 1
    assert isinstance(index.providers[0], GitHubEnterpriseProvider)


@pytest.mark.unit
def test_extract_keywords():
    """Test keyword extraction from code snippets."""
    index = EnterpriseIndex()

    code = """
    def authenticate(user):
        pass

    class UserManager:
        async def verify_token(self):
            pass
    """

    keywords = index._extract_keywords(code)

    assert "authenticate" in keywords
    assert "UserManager" in keywords
    assert "verify_token" in keywords
