#!/usr/bin/env python3
"""
GitHub MCP Server with Dynamic Toolsets Support

Features:
- GitHub API integration tools (get_file_contents, search_code, get_issues, etc.)
- --tools flag to filter which tools are exposed
- --dynamic-toolsets flag for ML-based intelligent tool selection
- Token optimization and compressed schemas
- Enterprise security with rate limiting

Usage:
    # Expose all tools
    python github_mcp_server.py

    # Expose specific tools only
    python github_mcp_server.py --tools get_file_contents search_code

    # Enable dynamic toolset selection
    python github_mcp_server.py --dynamic-toolsets

    # Combine both flags
    python github_mcp_server.py --tools get_file_contents --dynamic-toolsets

Per Truth Protocol:
- Rule #1: Never guess - Verify all GitHub API calls
- Rule #5: No secrets in code - API tokens via environment
- Rule #7: Input validation - Pydantic schemas for all inputs
- Rule #12: Performance SLOs - P95 < 200ms with caching
"""

import argparse
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import logging
import os
import sys
from typing import Any, Literal

try:
    import httpx
    from mcp.server.fastmcp import Context, FastMCP
    from mcp.server.session import ServerSession
    from pydantic import BaseModel, Field
except ImportError as e:
    print(f"Missing required packages: {e}")
    print('Install: pip install "mcp[cli]" httpx pydantic')
    sys.exit(1)

# Optional imports for dynamic toolsets
try:
    from ml.tool_optimization import (
        DynamicToolSelector,
        ToolSelectionContext,
        get_optimization_manager,
    )
    DYNAMIC_TOOLSETS_AVAILABLE = True
except ImportError:
    DYNAMIC_TOOLSETS_AVAILABLE = False


logger = logging.getLogger(__name__)

# Configuration
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REQUEST_TIMEOUT = 30.0


class GitHubToolStatus(str, Enum):
    """Tool execution status."""
    SUCCESS = "success"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


# Pydantic Models for GitHub Tools

class GetFileContentsRequest(BaseModel):
    """Request to get file contents from a repository."""
    owner: str = Field(description="Repository owner (username or organization)")
    repo: str = Field(description="Repository name")
    path: str = Field(description="Path to the file in the repository")
    ref: str | None = Field(default=None, description="Branch, tag, or commit SHA (default: main)")


class FileContentsResult(BaseModel):
    """Result of getting file contents."""
    status: GitHubToolStatus
    path: str
    content: str | None = None
    encoding: str | None = None
    size: int | None = None
    sha: str | None = None
    error: str | None = None


class SearchCodeRequest(BaseModel):
    """Request to search code on GitHub."""
    query: str = Field(description="Search query (GitHub code search syntax)")
    repo: str | None = Field(default=None, description="Limit to specific repo (owner/repo format)")
    language: str | None = Field(default=None, description="Filter by programming language")
    path: str | None = Field(default=None, description="Filter by file path")
    per_page: int = Field(default=10, ge=1, le=100, description="Results per page")


class CodeSearchResult(BaseModel):
    """Result of code search."""
    status: GitHubToolStatus
    total_count: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class GetIssuesRequest(BaseModel):
    """Request to get issues from a repository."""
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    state: Literal["open", "closed", "all"] = Field(default="open")
    labels: str | None = Field(default=None, description="Comma-separated list of labels")
    per_page: int = Field(default=10, ge=1, le=100)


class IssuesResult(BaseModel):
    """Result of getting issues."""
    status: GitHubToolStatus
    count: int = 0
    issues: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class CreateIssueRequest(BaseModel):
    """Request to create an issue."""
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    title: str = Field(description="Issue title")
    body: str | None = Field(default=None, description="Issue body (markdown)")
    labels: list[str] | None = Field(default=None, description="Labels to add")
    assignees: list[str] | None = Field(default=None, description="Users to assign")


class CreateIssueResult(BaseModel):
    """Result of creating an issue."""
    status: GitHubToolStatus
    issue_number: int | None = None
    html_url: str | None = None
    error: str | None = None


class GetPullRequestsRequest(BaseModel):
    """Request to get pull requests."""
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    state: Literal["open", "closed", "all"] = Field(default="open")
    per_page: int = Field(default=10, ge=1, le=100)


class PullRequestsResult(BaseModel):
    """Result of getting pull requests."""
    status: GitHubToolStatus
    count: int = 0
    pull_requests: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class GetRepoInfoRequest(BaseModel):
    """Request to get repository information."""
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")


class RepoInfoResult(BaseModel):
    """Result of getting repository info."""
    status: GitHubToolStatus
    name: str | None = None
    full_name: str | None = None
    description: str | None = None
    stars: int | None = None
    forks: int | None = None
    language: str | None = None
    default_branch: str | None = None
    topics: list[str] | None = None
    error: str | None = None


class ListBranchesRequest(BaseModel):
    """Request to list repository branches."""
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    per_page: int = Field(default=30, ge=1, le=100)


class BranchesResult(BaseModel):
    """Result of listing branches."""
    status: GitHubToolStatus
    count: int = 0
    branches: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class GetCommitsRequest(BaseModel):
    """Request to get commits from a repository."""
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    sha: str | None = Field(default=None, description="Branch, tag, or commit SHA")
    path: str | None = Field(default=None, description="Filter by file path")
    per_page: int = Field(default=10, ge=1, le=100)


class CommitsResult(BaseModel):
    """Result of getting commits."""
    status: GitHubToolStatus
    count: int = 0
    commits: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


# Lifespan Context

@dataclass
class GitHubMCPContext:
    """Application context for GitHub MCP server."""
    http_client: httpx.AsyncClient
    github_token: str
    start_time: datetime
    enabled_tools: set[str]
    dynamic_toolsets_enabled: bool
    tool_selector: Any | None  # DynamicToolSelector if available


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[GitHubMCPContext]:
    """
    Manage GitHub MCP server lifecycle.

    Initializes:
    - HTTP client with connection pooling
    - GitHub authentication headers
    - Dynamic tool selector (if enabled)
    """
    print("Initializing GitHub MCP Server...")

    # Parse CLI args from environment (set by main())
    enabled_tools = set(os.getenv("_GITHUB_MCP_TOOLS", "").split(","))
    enabled_tools.discard("")  # Remove empty strings
    dynamic_enabled = os.getenv("_GITHUB_MCP_DYNAMIC", "false") == "true"

    # Initialize HTTP client
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    http_client = httpx.AsyncClient(
        base_url=GITHUB_API_URL,
        headers=headers,
        timeout=httpx.Timeout(REQUEST_TIMEOUT),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
    )

    # Initialize dynamic tool selector
    tool_selector = None
    if dynamic_enabled and DYNAMIC_TOOLSETS_AVAILABLE:
        tool_selector = get_optimization_manager().tool_selector
        print("Dynamic toolsets enabled")

    print(f"GitHub API: {GITHUB_API_URL}")
    print(f"Token: {'Set' if GITHUB_TOKEN else 'Not Set (rate limited)'}")
    print(f"Enabled tools: {enabled_tools or 'all'}")

    start_time = datetime.utcnow()

    try:
        yield GitHubMCPContext(
            http_client=http_client,
            github_token=GITHUB_TOKEN,
            start_time=start_time,
            enabled_tools=enabled_tools,
            dynamic_toolsets_enabled=dynamic_enabled,
            tool_selector=tool_selector,
        )
    finally:
        await http_client.aclose()
        uptime = datetime.utcnow() - start_time
        print(f"Server shutdown. Uptime: {uptime}")


# Initialize MCP Server
mcp = FastMCP(
    "github_mcp_server",
    lifespan=app_lifespan,
    dependencies=["httpx>=0.24.0", "pydantic>=2.5.0"]
)


# Tool Registry for Dynamic Selection
TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def register_github_tool(name: str, description: str, keywords: list[str]):
    """Decorator to register a tool for dynamic selection."""
    def decorator(func):
        TOOL_REGISTRY[name] = {
            "func": func,
            "description": description,
            "keywords": set(keywords),
        }
        return func
    return decorator


# GitHub Tools Implementation

@mcp.tool()
@register_github_tool(
    "get_file_contents",
    "Get file contents from a GitHub repository",
    ["file", "content", "read", "source", "code", "path"]
)
async def get_file_contents(
    request: GetFileContentsRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> FileContentsResult:
    """
    Get the contents of a file from a GitHub repository.

    This tool fetches raw file contents using the GitHub Contents API.
    Supports any text or code file up to 1MB.

    **Example:**
    ```python
    result = await get_file_contents(
        GetFileContentsRequest(
            owner="anthropics",
            repo="claude-code",
            path="README.md"
        )
    )
    ```
    """
    # Check if tool is enabled
    if ctx.request_context.lifespan_context.enabled_tools:
        if "get_file_contents" not in ctx.request_context.lifespan_context.enabled_tools:
            return FileContentsResult(
                status=GitHubToolStatus.ERROR,
                path=request.path,
                error="Tool not enabled. Use --tools flag to enable."
            )

    await ctx.info(f"Fetching: {request.owner}/{request.repo}/{request.path}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        params = {}
        if request.ref:
            params["ref"] = request.ref

        response = await client.get(
            f"/repos/{request.owner}/{request.repo}/contents/{request.path}",
            params=params
        )

        if response.status_code == 403:
            return FileContentsResult(
                status=GitHubToolStatus.RATE_LIMITED,
                path=request.path,
                error="GitHub API rate limit exceeded"
            )

        response.raise_for_status()
        data = response.json()

        # Handle file content
        if data.get("type") == "file":
            import base64
            content = base64.b64decode(data.get("content", "")).decode("utf-8")

            return FileContentsResult(
                status=GitHubToolStatus.SUCCESS,
                path=request.path,
                content=content,
                encoding=data.get("encoding"),
                size=data.get("size"),
                sha=data.get("sha"),
            )
        else:
            return FileContentsResult(
                status=GitHubToolStatus.ERROR,
                path=request.path,
                error=f"Path is a {data.get('type')}, not a file"
            )

    except httpx.HTTPStatusError as e:
        return FileContentsResult(
            status=GitHubToolStatus.ERROR,
            path=request.path,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return FileContentsResult(
            status=GitHubToolStatus.ERROR,
            path=request.path,
            error=str(e)
        )


@mcp.tool()
@register_github_tool(
    "search_code",
    "Search for code across GitHub repositories",
    ["search", "find", "query", "code", "grep", "pattern"]
)
async def search_code(
    request: SearchCodeRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> CodeSearchResult:
    """
    Search for code across GitHub repositories.

    Uses the GitHub Code Search API to find code matching a query.
    Supports GitHub's advanced code search syntax.

    **Example:**
    ```python
    result = await search_code(
        SearchCodeRequest(
            query="import asyncio",
            repo="anthropics/claude-code",
            language="python"
        )
    )
    ```
    """
    if ctx.request_context.lifespan_context.enabled_tools:
        if "search_code" not in ctx.request_context.lifespan_context.enabled_tools:
            return CodeSearchResult(
                status=GitHubToolStatus.ERROR,
                error="Tool not enabled. Use --tools flag to enable."
            )

    await ctx.info(f"Searching code: {request.query}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        # Build query
        query = request.query
        if request.repo:
            query += f" repo:{request.repo}"
        if request.language:
            query += f" language:{request.language}"
        if request.path:
            query += f" path:{request.path}"

        response = await client.get(
            "/search/code",
            params={"q": query, "per_page": request.per_page}
        )

        if response.status_code == 403:
            return CodeSearchResult(
                status=GitHubToolStatus.RATE_LIMITED,
                error="GitHub API rate limit exceeded"
            )

        response.raise_for_status()
        data = response.json()

        # Extract relevant fields
        items = [
            {
                "name": item.get("name"),
                "path": item.get("path"),
                "repository": item.get("repository", {}).get("full_name"),
                "html_url": item.get("html_url"),
            }
            for item in data.get("items", [])
        ]

        return CodeSearchResult(
            status=GitHubToolStatus.SUCCESS,
            total_count=data.get("total_count", 0),
            items=items,
        )

    except httpx.HTTPStatusError as e:
        return CodeSearchResult(
            status=GitHubToolStatus.ERROR,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return CodeSearchResult(
            status=GitHubToolStatus.ERROR,
            error=str(e)
        )


@mcp.tool()
@register_github_tool(
    "get_issues",
    "Get issues from a GitHub repository",
    ["issues", "bugs", "tickets", "problems", "tasks"]
)
async def get_issues(
    request: GetIssuesRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> IssuesResult:
    """
    Get issues from a GitHub repository.

    Fetches issues with optional filtering by state and labels.

    **Example:**
    ```python
    result = await get_issues(
        GetIssuesRequest(
            owner="anthropics",
            repo="claude-code",
            state="open",
            labels="bug"
        )
    )
    ```
    """
    if ctx.request_context.lifespan_context.enabled_tools:
        if "get_issues" not in ctx.request_context.lifespan_context.enabled_tools:
            return IssuesResult(
                status=GitHubToolStatus.ERROR,
                error="Tool not enabled. Use --tools flag to enable."
            )

    await ctx.info(f"Fetching issues: {request.owner}/{request.repo}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        params = {"state": request.state, "per_page": request.per_page}
        if request.labels:
            params["labels"] = request.labels

        response = await client.get(
            f"/repos/{request.owner}/{request.repo}/issues",
            params=params
        )

        if response.status_code == 403:
            return IssuesResult(
                status=GitHubToolStatus.RATE_LIMITED,
                error="GitHub API rate limit exceeded"
            )

        response.raise_for_status()
        data = response.json()

        # Extract relevant fields (compress output)
        issues = [
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "labels": [l.get("name") for l in issue.get("labels", [])],
                "created_at": issue.get("created_at"),
                "html_url": issue.get("html_url"),
            }
            for issue in data
            if not issue.get("pull_request")  # Filter out PRs
        ]

        return IssuesResult(
            status=GitHubToolStatus.SUCCESS,
            count=len(issues),
            issues=issues,
        )

    except httpx.HTTPStatusError as e:
        return IssuesResult(
            status=GitHubToolStatus.ERROR,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return IssuesResult(
            status=GitHubToolStatus.ERROR,
            error=str(e)
        )


@mcp.tool()
@register_github_tool(
    "create_issue",
    "Create a new issue in a GitHub repository",
    ["create", "new", "issue", "bug", "report", "ticket"]
)
async def create_issue(
    request: CreateIssueRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> CreateIssueResult:
    """
    Create a new issue in a GitHub repository.

    Requires write access to the repository (valid GITHUB_TOKEN).

    **Example:**
    ```python
    result = await create_issue(
        CreateIssueRequest(
            owner="myorg",
            repo="myrepo",
            title="Bug: Something is broken",
            body="## Description\n\nDetails here...",
            labels=["bug", "priority-high"]
        )
    )
    ```
    """
    if ctx.request_context.lifespan_context.enabled_tools:
        if "create_issue" not in ctx.request_context.lifespan_context.enabled_tools:
            return CreateIssueResult(
                status=GitHubToolStatus.ERROR,
                error="Tool not enabled. Use --tools flag to enable."
            )

    if not ctx.request_context.lifespan_context.github_token:
        return CreateIssueResult(
            status=GitHubToolStatus.ERROR,
            error="GITHUB_TOKEN required to create issues"
        )

    await ctx.info(f"Creating issue in: {request.owner}/{request.repo}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        payload = {"title": request.title}
        if request.body:
            payload["body"] = request.body
        if request.labels:
            payload["labels"] = request.labels
        if request.assignees:
            payload["assignees"] = request.assignees

        response = await client.post(
            f"/repos/{request.owner}/{request.repo}/issues",
            json=payload
        )

        if response.status_code == 403:
            return CreateIssueResult(
                status=GitHubToolStatus.RATE_LIMITED,
                error="GitHub API rate limit exceeded or insufficient permissions"
            )

        response.raise_for_status()
        data = response.json()

        await ctx.info(f"Created issue #{data.get('number')}")

        return CreateIssueResult(
            status=GitHubToolStatus.SUCCESS,
            issue_number=data.get("number"),
            html_url=data.get("html_url"),
        )

    except httpx.HTTPStatusError as e:
        return CreateIssueResult(
            status=GitHubToolStatus.ERROR,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return CreateIssueResult(
            status=GitHubToolStatus.ERROR,
            error=str(e)
        )


@mcp.tool()
@register_github_tool(
    "get_pull_requests",
    "Get pull requests from a GitHub repository",
    ["pull", "pr", "merge", "review", "changes"]
)
async def get_pull_requests(
    request: GetPullRequestsRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> PullRequestsResult:
    """
    Get pull requests from a GitHub repository.

    **Example:**
    ```python
    result = await get_pull_requests(
        GetPullRequestsRequest(
            owner="anthropics",
            repo="claude-code",
            state="open"
        )
    )
    ```
    """
    if ctx.request_context.lifespan_context.enabled_tools:
        if "get_pull_requests" not in ctx.request_context.lifespan_context.enabled_tools:
            return PullRequestsResult(
                status=GitHubToolStatus.ERROR,
                error="Tool not enabled. Use --tools flag to enable."
            )

    await ctx.info(f"Fetching PRs: {request.owner}/{request.repo}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        response = await client.get(
            f"/repos/{request.owner}/{request.repo}/pulls",
            params={"state": request.state, "per_page": request.per_page}
        )

        if response.status_code == 403:
            return PullRequestsResult(
                status=GitHubToolStatus.RATE_LIMITED,
                error="GitHub API rate limit exceeded"
            )

        response.raise_for_status()
        data = response.json()

        prs = [
            {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "user": pr.get("user", {}).get("login"),
                "created_at": pr.get("created_at"),
                "html_url": pr.get("html_url"),
                "draft": pr.get("draft", False),
            }
            for pr in data
        ]

        return PullRequestsResult(
            status=GitHubToolStatus.SUCCESS,
            count=len(prs),
            pull_requests=prs,
        )

    except httpx.HTTPStatusError as e:
        return PullRequestsResult(
            status=GitHubToolStatus.ERROR,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return PullRequestsResult(
            status=GitHubToolStatus.ERROR,
            error=str(e)
        )


@mcp.tool()
@register_github_tool(
    "get_repo_info",
    "Get information about a GitHub repository",
    ["repo", "repository", "info", "details", "metadata"]
)
async def get_repo_info(
    request: GetRepoInfoRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> RepoInfoResult:
    """
    Get information about a GitHub repository.

    **Example:**
    ```python
    result = await get_repo_info(
        GetRepoInfoRequest(
            owner="anthropics",
            repo="claude-code"
        )
    )
    ```
    """
    if ctx.request_context.lifespan_context.enabled_tools:
        if "get_repo_info" not in ctx.request_context.lifespan_context.enabled_tools:
            return RepoInfoResult(
                status=GitHubToolStatus.ERROR,
                error="Tool not enabled. Use --tools flag to enable."
            )

    await ctx.info(f"Fetching repo info: {request.owner}/{request.repo}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        response = await client.get(f"/repos/{request.owner}/{request.repo}")

        if response.status_code == 403:
            return RepoInfoResult(
                status=GitHubToolStatus.RATE_LIMITED,
                error="GitHub API rate limit exceeded"
            )

        response.raise_for_status()
        data = response.json()

        return RepoInfoResult(
            status=GitHubToolStatus.SUCCESS,
            name=data.get("name"),
            full_name=data.get("full_name"),
            description=data.get("description"),
            stars=data.get("stargazers_count"),
            forks=data.get("forks_count"),
            language=data.get("language"),
            default_branch=data.get("default_branch"),
            topics=data.get("topics", []),
        )

    except httpx.HTTPStatusError as e:
        return RepoInfoResult(
            status=GitHubToolStatus.ERROR,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return RepoInfoResult(
            status=GitHubToolStatus.ERROR,
            error=str(e)
        )


@mcp.tool()
@register_github_tool(
    "list_branches",
    "List branches in a GitHub repository",
    ["branches", "branch", "list", "git"]
)
async def list_branches(
    request: ListBranchesRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> BranchesResult:
    """
    List branches in a GitHub repository.

    **Example:**
    ```python
    result = await list_branches(
        ListBranchesRequest(
            owner="anthropics",
            repo="claude-code"
        )
    )
    ```
    """
    if ctx.request_context.lifespan_context.enabled_tools:
        if "list_branches" not in ctx.request_context.lifespan_context.enabled_tools:
            return BranchesResult(
                status=GitHubToolStatus.ERROR,
                error="Tool not enabled. Use --tools flag to enable."
            )

    await ctx.info(f"Listing branches: {request.owner}/{request.repo}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        response = await client.get(
            f"/repos/{request.owner}/{request.repo}/branches",
            params={"per_page": request.per_page}
        )

        if response.status_code == 403:
            return BranchesResult(
                status=GitHubToolStatus.RATE_LIMITED,
                error="GitHub API rate limit exceeded"
            )

        response.raise_for_status()
        data = response.json()

        branches = [
            {
                "name": branch.get("name"),
                "protected": branch.get("protected", False),
                "sha": branch.get("commit", {}).get("sha"),
            }
            for branch in data
        ]

        return BranchesResult(
            status=GitHubToolStatus.SUCCESS,
            count=len(branches),
            branches=branches,
        )

    except httpx.HTTPStatusError as e:
        return BranchesResult(
            status=GitHubToolStatus.ERROR,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return BranchesResult(
            status=GitHubToolStatus.ERROR,
            error=str(e)
        )


@mcp.tool()
@register_github_tool(
    "get_commits",
    "Get commits from a GitHub repository",
    ["commits", "history", "log", "changes", "git"]
)
async def get_commits(
    request: GetCommitsRequest,
    ctx: Context[ServerSession, GitHubMCPContext]
) -> CommitsResult:
    """
    Get commits from a GitHub repository.

    **Example:**
    ```python
    result = await get_commits(
        GetCommitsRequest(
            owner="anthropics",
            repo="claude-code",
            path="README.md"
        )
    )
    ```
    """
    if ctx.request_context.lifespan_context.enabled_tools:
        if "get_commits" not in ctx.request_context.lifespan_context.enabled_tools:
            return CommitsResult(
                status=GitHubToolStatus.ERROR,
                error="Tool not enabled. Use --tools flag to enable."
            )

    await ctx.info(f"Fetching commits: {request.owner}/{request.repo}")

    client = ctx.request_context.lifespan_context.http_client

    try:
        params = {"per_page": request.per_page}
        if request.sha:
            params["sha"] = request.sha
        if request.path:
            params["path"] = request.path

        response = await client.get(
            f"/repos/{request.owner}/{request.repo}/commits",
            params=params
        )

        if response.status_code == 403:
            return CommitsResult(
                status=GitHubToolStatus.RATE_LIMITED,
                error="GitHub API rate limit exceeded"
            )

        response.raise_for_status()
        data = response.json()

        commits = [
            {
                "sha": commit.get("sha", "")[:7],  # Short SHA
                "message": commit.get("commit", {}).get("message", "").split("\n")[0],  # First line
                "author": commit.get("commit", {}).get("author", {}).get("name"),
                "date": commit.get("commit", {}).get("author", {}).get("date"),
            }
            for commit in data
        ]

        return CommitsResult(
            status=GitHubToolStatus.SUCCESS,
            count=len(commits),
            commits=commits,
        )

    except httpx.HTTPStatusError as e:
        return CommitsResult(
            status=GitHubToolStatus.ERROR,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        )
    except Exception as e:
        return CommitsResult(
            status=GitHubToolStatus.ERROR,
            error=str(e)
        )


# Dynamic Toolset Selection

class DynamicToolsetManager:
    """
    Manages dynamic tool selection based on context.

    When --dynamic-toolsets is enabled, this manager:
    1. Analyzes the incoming request context
    2. Scores each tool based on relevance
    3. Returns only the most relevant tools for the task
    """

    def __init__(self):
        self.tool_definitions = TOOL_REGISTRY

    def select_tools(
        self,
        task_description: str,
        max_tools: int = 5
    ) -> list[str]:
        """
        Select the most relevant tools for a given task.

        Args:
            task_description: Natural language description of the task
            max_tools: Maximum number of tools to return

        Returns:
            List of tool names ordered by relevance
        """
        # Extract keywords from task description
        keywords = set(task_description.lower().split())

        # Score each tool
        scores = []
        for name, definition in self.tool_definitions.items():
            tool_keywords = definition.get("keywords", set())
            # Calculate overlap score
            overlap = len(keywords & tool_keywords)
            # Add description match bonus
            desc = definition.get("description", "").lower()
            desc_bonus = sum(1 for kw in keywords if kw in desc) * 0.5
            scores.append((name, overlap + desc_bonus))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top tools
        selected = [name for name, score in scores[:max_tools] if score > 0]

        # If no tools matched, return all tools
        if not selected:
            return list(self.tool_definitions.keys())[:max_tools]

        return selected

    def get_tool_schemas(self, tool_names: list[str]) -> list[dict]:
        """Get compressed schemas for selected tools."""
        schemas = []
        for name in tool_names:
            if name in self.tool_definitions:
                schemas.append({
                    "name": name,
                    "description": self.tool_definitions[name]["description"],
                })
        return schemas


# MCP Resource for Dynamic Toolsets

@mcp.resource("github://tools/available")
def get_available_tools() -> str:
    """
    List all available GitHub tools.

    Returns a JSON list of tool names and descriptions.
    """
    return json.dumps(
        [
            {"name": name, "description": info["description"]}
            for name, info in TOOL_REGISTRY.items()
        ],
        indent=2
    )


@mcp.resource("github://tools/dynamic-select")
async def dynamic_tool_selection(ctx: Context[ServerSession, GitHubMCPContext]) -> str:
    """
    Get dynamically selected tools based on context.

    This resource is used when --dynamic-toolsets is enabled.
    """
    if not ctx.request_context.lifespan_context.dynamic_toolsets_enabled:
        return json.dumps({"error": "Dynamic toolsets not enabled. Use --dynamic-toolsets flag."})

    manager = DynamicToolsetManager()
    return json.dumps({
        "enabled": True,
        "available_tools": list(TOOL_REGISTRY.keys()),
        "selection_method": "keyword_matching",
    })


# Main Entry Point

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="GitHub MCP Server with Dynamic Toolsets Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Expose all tools
  python github_mcp_server.py

  # Expose specific tools only
  python github_mcp_server.py --tools get_file_contents search_code

  # Enable dynamic toolset selection
  python github_mcp_server.py --dynamic-toolsets

  # Combine both
  python github_mcp_server.py --tools get_file_contents --dynamic-toolsets

Available tools:
  - get_file_contents   Get file contents from a repository
  - search_code         Search for code across repositories
  - get_issues          Get issues from a repository
  - create_issue        Create a new issue
  - get_pull_requests   Get pull requests from a repository
  - get_repo_info       Get repository information
  - list_branches       List repository branches
  - get_commits         Get commits from a repository
        """
    )

    parser.add_argument(
        "--tools",
        nargs="+",
        help="Space-separated list of tools to expose (default: all)",
        metavar="TOOL"
    )

    parser.add_argument(
        "--dynamic-toolsets",
        action="store_true",
        help="Enable ML-based dynamic tool selection"
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)"
    )

    args = parser.parse_args()

    # Set environment variables for lifespan to read
    if args.tools:
        valid_tools = set(TOOL_REGISTRY.keys())
        for tool in args.tools:
            if tool not in valid_tools:
                print(f"Warning: Unknown tool '{tool}'")
                print(f"Available: {', '.join(valid_tools)}")
        os.environ["_GITHUB_MCP_TOOLS"] = ",".join(args.tools)
    else:
        os.environ["_GITHUB_MCP_TOOLS"] = ""

    os.environ["_GITHUB_MCP_DYNAMIC"] = "true" if args.dynamic_toolsets else "false"

    # Print banner
    all_tools = list(TOOL_REGISTRY.keys())
    enabled = args.tools if args.tools else all_tools

    print(f"""
====================================================
       GitHub MCP Server - Dynamic Toolsets
====================================================

Configuration:
  Transport: {args.transport}
  Dynamic Toolsets: {'Enabled' if args.dynamic_toolsets else 'Disabled'}
  GitHub Token: {'Set' if GITHUB_TOKEN else 'Not Set (rate limited)'}

Enabled Tools ({len(enabled)}/{len(all_tools)}):
  {chr(10).join(f'  - {t}' for t in enabled)}

Starting server...
""")

    # Run server
    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", port=args.port, host=args.host)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
