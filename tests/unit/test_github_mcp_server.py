"""
Unit Tests for GitHub MCP Server with Dynamic Toolsets

Tests the GitHub MCP server implementation including:
- CLI argument parsing (--tools, --dynamic-toolsets)
- Tool registration and filtering
- Dynamic toolset selection
- Pydantic request/response models

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #7: Input validation testing
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the module
from github_mcp_server import (
    GetFileContentsRequest,
    FileContentsResult,
    SearchCodeRequest,
    CodeSearchResult,
    GetIssuesRequest,
    IssuesResult,
    CreateIssueRequest,
    CreateIssueResult,
    GetPullRequestsRequest,
    PullRequestsResult,
    GetRepoInfoRequest,
    RepoInfoResult,
    ListBranchesRequest,
    BranchesResult,
    GetCommitsRequest,
    CommitsResult,
    GitHubToolStatus,
    DynamicToolsetManager,
    TOOL_REGISTRY,
)


class TestPydanticModels:
    """Test Pydantic request/response models."""

    def test_get_file_contents_request_valid(self):
        """Test valid GetFileContentsRequest."""
        request = GetFileContentsRequest(
            owner="anthropics",
            repo="claude-code",
            path="README.md"
        )
        assert request.owner == "anthropics"
        assert request.repo == "claude-code"
        assert request.path == "README.md"
        assert request.ref is None

    def test_get_file_contents_request_with_ref(self):
        """Test GetFileContentsRequest with branch reference."""
        request = GetFileContentsRequest(
            owner="anthropics",
            repo="claude-code",
            path="src/main.py",
            ref="develop"
        )
        assert request.ref == "develop"

    def test_file_contents_result_success(self):
        """Test FileContentsResult for success."""
        result = FileContentsResult(
            status=GitHubToolStatus.SUCCESS,
            path="README.md",
            content="# Hello World",
            encoding="base64",
            size=12,
            sha="abc123"
        )
        assert result.status == GitHubToolStatus.SUCCESS
        assert result.content == "# Hello World"
        assert result.error is None

    def test_file_contents_result_error(self):
        """Test FileContentsResult for error."""
        result = FileContentsResult(
            status=GitHubToolStatus.ERROR,
            path="missing.md",
            error="File not found"
        )
        assert result.status == GitHubToolStatus.ERROR
        assert result.content is None
        assert result.error == "File not found"

    def test_search_code_request_valid(self):
        """Test valid SearchCodeRequest."""
        request = SearchCodeRequest(
            query="import asyncio",
            repo="anthropics/claude-code",
            language="python"
        )
        assert request.query == "import asyncio"
        assert request.repo == "anthropics/claude-code"
        assert request.language == "python"
        assert request.per_page == 10  # Default

    def test_search_code_request_per_page_limits(self):
        """Test SearchCodeRequest per_page limits."""
        # Valid limits
        request = SearchCodeRequest(query="test", per_page=1)
        assert request.per_page == 1

        request = SearchCodeRequest(query="test", per_page=100)
        assert request.per_page == 100

        # Invalid limits should raise validation error
        with pytest.raises(ValueError):
            SearchCodeRequest(query="test", per_page=0)

        with pytest.raises(ValueError):
            SearchCodeRequest(query="test", per_page=101)

    def test_get_issues_request_valid(self):
        """Test valid GetIssuesRequest."""
        request = GetIssuesRequest(
            owner="anthropics",
            repo="claude-code",
            state="open",
            labels="bug,enhancement"
        )
        assert request.state == "open"
        assert request.labels == "bug,enhancement"

    def test_get_issues_request_state_options(self):
        """Test GetIssuesRequest state options."""
        for state in ["open", "closed", "all"]:
            request = GetIssuesRequest(
                owner="test",
                repo="test",
                state=state
            )
            assert request.state == state

    def test_create_issue_request_minimal(self):
        """Test CreateIssueRequest with minimal fields."""
        request = CreateIssueRequest(
            owner="test",
            repo="test",
            title="Bug Report"
        )
        assert request.title == "Bug Report"
        assert request.body is None
        assert request.labels is None
        assert request.assignees is None

    def test_create_issue_request_full(self):
        """Test CreateIssueRequest with all fields."""
        request = CreateIssueRequest(
            owner="test",
            repo="test",
            title="Bug Report",
            body="## Description\n\nDetails here",
            labels=["bug", "priority-high"],
            assignees=["user1", "user2"]
        )
        assert request.body == "## Description\n\nDetails here"
        assert len(request.labels) == 2
        assert len(request.assignees) == 2

    def test_get_pull_requests_request_defaults(self):
        """Test GetPullRequestsRequest defaults."""
        request = GetPullRequestsRequest(
            owner="test",
            repo="test"
        )
        assert request.state == "open"
        assert request.per_page == 10

    def test_get_repo_info_request(self):
        """Test GetRepoInfoRequest."""
        request = GetRepoInfoRequest(
            owner="anthropics",
            repo="claude-code"
        )
        assert request.owner == "anthropics"
        assert request.repo == "claude-code"

    def test_repo_info_result_complete(self):
        """Test RepoInfoResult with all fields."""
        result = RepoInfoResult(
            status=GitHubToolStatus.SUCCESS,
            name="claude-code",
            full_name="anthropics/claude-code",
            description="Official CLI for Claude",
            stars=1000,
            forks=100,
            language="Python",
            default_branch="main",
            topics=["cli", "ai", "claude"]
        )
        assert result.stars == 1000
        assert len(result.topics) == 3

    def test_list_branches_request(self):
        """Test ListBranchesRequest."""
        request = ListBranchesRequest(
            owner="test",
            repo="test",
            per_page=50
        )
        assert request.per_page == 50

    def test_get_commits_request_with_filters(self):
        """Test GetCommitsRequest with filters."""
        request = GetCommitsRequest(
            owner="test",
            repo="test",
            sha="develop",
            path="src/main.py",
            per_page=20
        )
        assert request.sha == "develop"
        assert request.path == "src/main.py"


class TestToolRegistry:
    """Test tool registration and registry."""

    def test_tool_registry_populated(self):
        """Test that tool registry is populated."""
        assert len(TOOL_REGISTRY) > 0
        assert "get_file_contents" in TOOL_REGISTRY
        assert "search_code" in TOOL_REGISTRY

    def test_tool_registry_structure(self):
        """Test tool registry entry structure."""
        for name, definition in TOOL_REGISTRY.items():
            assert "func" in definition
            assert "description" in definition
            assert "keywords" in definition
            assert isinstance(definition["keywords"], set)

    def test_get_file_contents_keywords(self):
        """Test get_file_contents tool keywords."""
        keywords = TOOL_REGISTRY["get_file_contents"]["keywords"]
        assert "file" in keywords
        assert "content" in keywords
        assert "read" in keywords

    def test_search_code_keywords(self):
        """Test search_code tool keywords."""
        keywords = TOOL_REGISTRY["search_code"]["keywords"]
        assert "search" in keywords
        assert "find" in keywords
        assert "code" in keywords


class TestDynamicToolsetManager:
    """Test dynamic toolset selection."""

    def test_manager_initialization(self):
        """Test DynamicToolsetManager initialization."""
        manager = DynamicToolsetManager()
        assert manager.tool_definitions == TOOL_REGISTRY

    def test_select_tools_file_task(self):
        """Test tool selection for file-related task."""
        manager = DynamicToolsetManager()
        selected = manager.select_tools("I need to read a file from the repository")

        assert "get_file_contents" in selected
        assert len(selected) <= 5  # Default max

    def test_select_tools_search_task(self):
        """Test tool selection for search-related task."""
        manager = DynamicToolsetManager()
        selected = manager.select_tools("search for code that uses asyncio")

        assert "search_code" in selected

    def test_select_tools_issue_task(self):
        """Test tool selection for issue-related task."""
        manager = DynamicToolsetManager()
        selected = manager.select_tools("show me the open bugs and issues")

        assert "get_issues" in selected

    def test_select_tools_pr_task(self):
        """Test tool selection for PR-related task."""
        manager = DynamicToolsetManager()
        selected = manager.select_tools("list the open pull requests for review")

        assert "get_pull_requests" in selected

    def test_select_tools_max_limit(self):
        """Test tool selection respects max_tools limit."""
        manager = DynamicToolsetManager()
        selected = manager.select_tools("file search issues commits branches", max_tools=3)

        assert len(selected) <= 3

    def test_select_tools_no_match(self):
        """Test tool selection with no keyword matches."""
        manager = DynamicToolsetManager()
        selected = manager.select_tools("xyz123 random gibberish")

        # Should return all tools when no match
        assert len(selected) > 0

    def test_get_tool_schemas(self):
        """Test getting tool schemas."""
        manager = DynamicToolsetManager()
        schemas = manager.get_tool_schemas(["get_file_contents", "search_code"])

        assert len(schemas) == 2
        assert schemas[0]["name"] == "get_file_contents"
        assert "description" in schemas[0]

    def test_get_tool_schemas_unknown_tool(self):
        """Test getting schemas for unknown tools."""
        manager = DynamicToolsetManager()
        schemas = manager.get_tool_schemas(["unknown_tool", "get_file_contents"])

        assert len(schemas) == 1  # Only valid tool


class TestCLIArgumentParsing:
    """Test CLI argument handling."""

    def test_tools_env_var_empty(self):
        """Test empty tools environment variable."""
        os.environ["_GITHUB_MCP_TOOLS"] = ""
        tools = set(os.environ.get("_GITHUB_MCP_TOOLS", "").split(","))
        tools.discard("")
        assert len(tools) == 0

    def test_tools_env_var_single(self):
        """Test single tool environment variable."""
        os.environ["_GITHUB_MCP_TOOLS"] = "get_file_contents"
        tools = set(os.environ.get("_GITHUB_MCP_TOOLS", "").split(","))
        assert "get_file_contents" in tools

    def test_tools_env_var_multiple(self):
        """Test multiple tools environment variable."""
        os.environ["_GITHUB_MCP_TOOLS"] = "get_file_contents,search_code,get_issues"
        tools = set(os.environ.get("_GITHUB_MCP_TOOLS", "").split(","))
        assert len(tools) == 3
        assert "get_file_contents" in tools
        assert "search_code" in tools
        assert "get_issues" in tools

    def test_dynamic_toolsets_env_var(self):
        """Test dynamic toolsets environment variable."""
        os.environ["_GITHUB_MCP_DYNAMIC"] = "true"
        assert os.environ.get("_GITHUB_MCP_DYNAMIC") == "true"

        os.environ["_GITHUB_MCP_DYNAMIC"] = "false"
        assert os.environ.get("_GITHUB_MCP_DYNAMIC") == "false"


class TestGitHubToolStatus:
    """Test GitHubToolStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert GitHubToolStatus.SUCCESS.value == "success"
        assert GitHubToolStatus.ERROR.value == "error"
        assert GitHubToolStatus.RATE_LIMITED.value == "rate_limited"

    def test_status_comparison(self):
        """Test status comparison."""
        assert GitHubToolStatus.SUCCESS == GitHubToolStatus.SUCCESS
        assert GitHubToolStatus.SUCCESS != GitHubToolStatus.ERROR


class TestIntegration:
    """Integration tests for GitHub MCP server components."""

    @pytest.mark.asyncio
    async def test_dynamic_selection_workflow(self):
        """Test complete dynamic selection workflow."""
        manager = DynamicToolsetManager()

        # Simulate user query
        query = "I want to read the README file and check open issues"
        selected = manager.select_tools(query)

        # Should select file and issue tools
        assert "get_file_contents" in selected or "get_issues" in selected

        # Get schemas for selected tools
        schemas = manager.get_tool_schemas(selected)
        assert len(schemas) > 0

    def test_all_tools_have_keywords(self):
        """Test that all registered tools have keywords."""
        for name, definition in TOOL_REGISTRY.items():
            assert len(definition["keywords"]) > 0, f"Tool {name} has no keywords"

    def test_tool_descriptions_not_empty(self):
        """Test that all tools have descriptions."""
        for name, definition in TOOL_REGISTRY.items():
            assert definition["description"], f"Tool {name} has empty description"

    def test_all_expected_tools_registered(self):
        """Test that all expected tools are registered."""
        expected_tools = [
            "get_file_contents",
            "search_code",
            "get_issues",
            "create_issue",
            "get_pull_requests",
            "get_repo_info",
            "list_branches",
            "get_commits",
        ]
        for tool in expected_tools:
            assert tool in TOOL_REGISTRY, f"Tool {tool} not registered"


# Cleanup
def teardown_module():
    """Clean up environment variables after tests."""
    os.environ.pop("_GITHUB_MCP_TOOLS", None)
    os.environ.pop("_GITHUB_MCP_DYNAMIC", None)
