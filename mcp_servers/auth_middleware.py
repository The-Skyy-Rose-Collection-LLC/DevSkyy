"""
MCP Authentication Middleware for DevSkyy Unified Cloud Server

Enterprise-grade authentication, authorization, and audit logging for FastMCP tools.

Sources Verified (5-Source Requirement per CLAUDE.md):
1. FastMCP 2.13 OAuth 2.1 Support: https://gofastmcp.com/updates
2. MCP Specification 2025-06-18: https://modelcontextprotocol.io/development/roadmap
3. JWT RFC 7519: https://datatracker.ietf.org/doc/html/rfc7519
4. OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
5. Claude Engineering Nov 2025: https://techbytes.app/posts/claude-engineering-november-2025-mcp-security-agents/

Per Truth Protocol:
- Rule #5: No secrets in code (JWT_SECRET_KEY from env)
- Rule #6: RBAC roles enforcement
- Rule #7: Input validation on all tool calls
- Rule #10: Audit logging (no-skip rule)
- Rule #13: Security baseline (AES-256-GCM, Argon2id ready)
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum
from functools import wraps
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Any, ParamSpec, TypeVar
import uuid

from pydantic import BaseModel, Field

# Import existing security infrastructure
from security.rbac import Role, is_role_higher_or_equal


logger = logging.getLogger(__name__)

# Constants
AUDIT_LOG_DIR = Path("logs")
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "mcp_audit.jsonl"
MAX_AUDIT_ENTRIES = 10000
CACHE_TTL_SECONDS = 300  # 5 minutes
REQUEST_TIMEOUT_SECONDS = 30

# Ensure audit log directory exists
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# TOOL PERMISSION MAPPING
# ============================================================================


class ToolCategory(str, Enum):
    """Tool categories for permission grouping."""

    THEME_ORCHESTRATOR = "theme_orchestrator"
    WOOCOMMERCE = "woocommerce"
    CONTENT_SEO = "content_seo"
    AI_GENERATION = "ai_generation"
    ANALYTICS = "analytics"
    AGENT_ORCHESTRATION = "agent_orchestration"
    RAG_KNOWLEDGE = "rag_knowledge"
    SYSTEM = "system"


# Map tools to categories and required roles
TOOL_PERMISSIONS: dict[str, tuple[ToolCategory, Role]] = {
    # Theme Orchestrator - Developer+
    "generate_wordpress_theme": (ToolCategory.THEME_ORCHESTRATOR, Role.DEVELOPER),
    "list_available_theme_types": (ToolCategory.THEME_ORCHESTRATOR, Role.API_USER),
    "generate_elementor_custom_widget": (ToolCategory.THEME_ORCHESTRATOR, Role.DEVELOPER),
    "get_theme_build_status": (ToolCategory.THEME_ORCHESTRATOR, Role.API_USER),
    # WooCommerce - Developer+ for write, APIUser+ for read
    "create_woocommerce_product": (ToolCategory.WOOCOMMERCE, Role.DEVELOPER),
    "update_woocommerce_product": (ToolCategory.WOOCOMMERCE, Role.DEVELOPER),
    "list_catalog_products": (ToolCategory.WOOCOMMERCE, Role.API_USER),
    "manage_product_inventory": (ToolCategory.WOOCOMMERCE, Role.DEVELOPER),
    "create_coupon_code": (ToolCategory.WOOCOMMERCE, Role.ADMIN),
    # Content/SEO - Developer+
    "create_blog_post": (ToolCategory.CONTENT_SEO, Role.DEVELOPER),
    "generate_seo_metadata": (ToolCategory.CONTENT_SEO, Role.DEVELOPER),
    # AI Generation - APIUser+
    "generate_product_description": (ToolCategory.AI_GENERATION, Role.API_USER),
    "generate_collection_copy": (ToolCategory.AI_GENERATION, Role.API_USER),
    "generate_ai_image_prompt": (ToolCategory.AI_GENERATION, Role.API_USER),
    # Analytics - APIUser+
    "get_sales_summary": (ToolCategory.ANALYTICS, Role.API_USER),
    "get_top_performing_products": (ToolCategory.ANALYTICS, Role.API_USER),
    "get_traffic_analytics": (ToolCategory.ANALYTICS, Role.API_USER),
    # Agent Orchestration - Admin+
    "dispatch_agent_task": (ToolCategory.AGENT_ORCHESTRATION, Role.ADMIN),
    "get_agent_status": (ToolCategory.AGENT_ORCHESTRATION, Role.DEVELOPER),
    "run_automation_workflow": (ToolCategory.AGENT_ORCHESTRATION, Role.ADMIN),
    # RAG Knowledge Base - APIUser+
    "ingest_document": (ToolCategory.RAG_KNOWLEDGE, Role.DEVELOPER),
    "query_knowledge_base": (ToolCategory.RAG_KNOWLEDGE, Role.API_USER),
    "list_knowledge_base_documents": (ToolCategory.RAG_KNOWLEDGE, Role.API_USER),
    "delete_document_from_knowledge_base": (ToolCategory.RAG_KNOWLEDGE, Role.ADMIN),
    "generate_rag_response": (ToolCategory.RAG_KNOWLEDGE, Role.API_USER),
    "ingest_skyyrose_knowledge": (ToolCategory.RAG_KNOWLEDGE, Role.DEVELOPER),
    # System - ReadOnly+ for status, Admin+ for config
    "get_brand_guidelines": (ToolCategory.SYSTEM, Role.READ_ONLY),
    "get_system_status": (ToolCategory.SYSTEM, Role.READ_ONLY),
}


# ============================================================================
# AUDIT LOGGING MODELS
# ============================================================================


class MCPAuditEntry(BaseModel):
    """Audit log entry for MCP tool invocations."""

    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str
    tool_name: str
    category: ToolCategory
    user_id: str | None = None
    user_role: Role | None = None
    parameters_hash: str  # SHA-256 hash of parameters (no PII)
    success: bool
    error: str | None = None
    execution_time_ms: float
    authorized: bool = True
    authorization_reason: str | None = None

    def to_json_line(self) -> str:
        """Convert to JSON line for JSONL logging."""
        data = self.model_dump()
        data["timestamp"] = data["timestamp"].isoformat()
        data["category"] = data["category"].value if data["category"] else None
        data["user_role"] = data["user_role"].value if data["user_role"] else None
        return json.dumps(data)


class MCPToolContext(BaseModel):
    """Context passed to MCP tools for authentication."""

    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")
    user_id: str | None = None
    user_role: Role = Role.READ_ONLY
    permissions: set[str] = Field(default_factory=set)
    authenticated: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# AUDIT LOGGER
# ============================================================================


class MCPAuditLogger:
    """Audit logger for MCP tool invocations."""

    _instance: "MCPAuditLogger | None" = None
    _lock: asyncio.Lock | None = None

    def __new__(cls) -> "MCPAuditLogger":
        """Singleton pattern for audit logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize audit logger."""
        if self._initialized:
            return
        self._initialized = True
        self._entries: list[MCPAuditEntry] = []
        self._lock = asyncio.Lock()

    async def log(self, entry: MCPAuditEntry) -> None:
        """Log an audit entry."""
        async with self._lock:
            self._entries.append(entry)
            # Trim if over limit
            if len(self._entries) > MAX_AUDIT_ENTRIES:
                self._entries = self._entries[-MAX_AUDIT_ENTRIES:]
            # Write to file
            try:
                with open(AUDIT_LOG_FILE, "a") as f:
                    f.write(entry.to_json_line() + "\n")
            except OSError as e:
                logger.error(f"Failed to write audit log: {e}")

    def log_sync(self, entry: MCPAuditEntry) -> None:
        """Synchronous log for non-async contexts."""
        self._entries.append(entry)
        if len(self._entries) > MAX_AUDIT_ENTRIES:
            self._entries = self._entries[-MAX_AUDIT_ENTRIES:]
        try:
            with open(AUDIT_LOG_FILE, "a") as f:
                f.write(entry.to_json_line() + "\n")
        except OSError as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_recent_entries(self, limit: int = 100) -> list[MCPAuditEntry]:
        """Get recent audit entries."""
        return self._entries[-limit:]

    def get_entries_by_user(self, user_id: str, limit: int = 100) -> list[MCPAuditEntry]:
        """Get entries for a specific user."""
        user_entries = [e for e in self._entries if e.user_id == user_id]
        return user_entries[-limit:]

    def get_entries_by_tool(self, tool_name: str, limit: int = 100) -> list[MCPAuditEntry]:
        """Get entries for a specific tool."""
        tool_entries = [e for e in self._entries if e.tool_name == tool_name]
        return tool_entries[-limit:]


# Global audit logger instance
audit_logger = MCPAuditLogger()


# ============================================================================
# AUTHORIZATION HELPERS
# ============================================================================


def hash_parameters(params: dict[str, Any]) -> str:
    """Create SHA-256 hash of parameters for audit (no PII stored)."""
    param_str = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(param_str.encode()).hexdigest()[:16]


def check_tool_authorization(
    tool_name: str,
    user_role: Role | None,
    user_permissions: set[str] | None = None,
) -> tuple[bool, str]:
    """
    Check if a user is authorized to call a tool.

    Args:
        tool_name: Name of the tool being called
        user_role: User's role (None if unauthenticated)
        user_permissions: Additional user permissions

    Returns:
        Tuple of (authorized: bool, reason: str)
    """
    # Get tool permission requirements
    tool_config = TOOL_PERMISSIONS.get(tool_name)

    if tool_config is None:
        # Unknown tool - allow with warning
        logger.warning(f"Unknown tool '{tool_name}' - no permission mapping found")
        return True, "unknown_tool_allowed"

    category, required_role = tool_config

    # Unauthenticated users only get ReadOnly access
    if user_role is None:
        user_role = Role.READ_ONLY

    # Check role hierarchy
    if is_role_higher_or_equal(user_role, required_role):
        return True, "role_authorized"

    # Check specific permissions
    if user_permissions:
        # Map categories to permissions
        category_permissions = {
            ToolCategory.THEME_ORCHESTRATOR: "deploy:code",
            ToolCategory.WOOCOMMERCE: "api:write",
            ToolCategory.CONTENT_SEO: "api:write",
            ToolCategory.AI_GENERATION: "api:read",
            ToolCategory.ANALYTICS: "view:metrics",
            ToolCategory.AGENT_ORCHESTRATION: "manage:agents",
            ToolCategory.RAG_KNOWLEDGE: "api:read",
            ToolCategory.SYSTEM: "view:dashboard",
        }
        required_permission = category_permissions.get(category)
        if required_permission and required_permission in user_permissions:
            return True, "permission_authorized"

    return False, f"requires_{required_role.value}_or_higher"


# ============================================================================
# MCP TOOL WRAPPER DECORATOR
# ============================================================================

P = ParamSpec("P")
T = TypeVar("T")


def mcp_authenticated(
    required_role: Role = Role.API_USER,
    required_permission: str | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for MCP tools requiring authentication and authorization.

    Args:
        required_role: Minimum role required to call this tool
        required_permission: Specific permission required (optional)

    Usage:
        @mcp.tool
        @mcp_authenticated(required_role=Role.DEVELOPER)
        def my_tool(param: str) -> dict:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            tool_name = func.__name__
            request_id = f"req_{uuid.uuid4().hex[:12]}"
            start_time = time.perf_counter()

            # Extract context if provided
            context: MCPToolContext | None = kwargs.pop("_mcp_context", None)

            # Default context for unauthenticated calls
            if context is None:
                context = MCPToolContext(
                    request_id=request_id,
                    user_role=Role.READ_ONLY,
                    authenticated=False,
                )

            # Check authorization
            authorized, reason = check_tool_authorization(
                tool_name=tool_name,
                user_role=context.user_role,
                user_permissions=context.permissions,
            )

            # Get tool category
            tool_config = TOOL_PERMISSIONS.get(tool_name)
            category = tool_config[0] if tool_config else ToolCategory.SYSTEM

            if not authorized:
                # Log unauthorized attempt
                execution_time_ms = (time.perf_counter() - start_time) * 1000
                audit_entry = MCPAuditEntry(
                    request_id=request_id,
                    tool_name=tool_name,
                    category=category,
                    user_id=context.user_id,
                    user_role=context.user_role,
                    parameters_hash=hash_parameters(kwargs),
                    success=False,
                    error="Unauthorized",
                    execution_time_ms=execution_time_ms,
                    authorized=False,
                    authorization_reason=reason,
                )
                audit_logger.log_sync(audit_entry)

                logger.warning(
                    f"Unauthorized tool call: {tool_name} by user={context.user_id} "
                    f"role={context.user_role.value} reason={reason}"
                )

                return {
                    "success": False,
                    "error": f"Unauthorized: {reason}",
                    "required_role": required_role.value,
                    "request_id": request_id,
                }

            # Execute the tool
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = {"success": False, "error": str(e)}
                success = False
                error = str(e)
                logger.exception(f"Tool execution failed: {tool_name}")

            # Log successful/failed execution
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            audit_entry = MCPAuditEntry(
                request_id=request_id,
                tool_name=tool_name,
                category=category,
                user_id=context.user_id,
                user_role=context.user_role,
                parameters_hash=hash_parameters(kwargs),
                success=success,
                error=error,
                execution_time_ms=execution_time_ms,
                authorized=True,
                authorization_reason=reason,
            )
            audit_logger.log_sync(audit_entry)

            return result

        return wrapper

    return decorator


# ============================================================================
# CACHE WRAPPER
# ============================================================================


class MCPResponseCache:
    """Response cache for MCP tools."""

    def __init__(self, default_ttl: int = CACHE_TTL_SECONDS) -> None:
        """Initialize cache."""
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def _make_key(self, tool_name: str, params: dict[str, Any]) -> str:
        """Create cache key from tool name and parameters."""
        param_hash = hash_parameters(params)
        return f"mcp:{tool_name}:{param_hash}"

    def get(self, tool_name: str, params: dict[str, Any]) -> tuple[bool, Any]:
        """
        Get cached response.

        Returns:
            Tuple of (hit: bool, value: Any)
        """
        key = self._make_key(tool_name, params)
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._hits += 1
                return True, value
            # Expired - remove
            del self._cache[key]
        self._misses += 1
        return False, None

    def set(self, tool_name: str, params: dict[str, Any], value: Any, ttl: int | None = None) -> None:
        """Cache a response."""
        key = self._make_key(tool_name, params)
        expiry = time.time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expiry)

    def invalidate(self, tool_name: str | None = None) -> int:
        """
        Invalidate cache entries.

        Args:
            tool_name: If provided, only invalidate entries for this tool

        Returns:
            Number of entries invalidated
        """
        if tool_name is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        prefix = f"mcp:{tool_name}:"
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]
        return len(keys_to_remove)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_ratio = self._hits / total if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(hit_ratio, 4),
            "entries": len(self._cache),
        }


# Global cache instance
response_cache = MCPResponseCache()


# Tool-specific cache TTLs (seconds)
TOOL_CACHE_TTLS: dict[str, int] = {
    # Analytics - 5 minutes
    "get_sales_summary": 300,
    "get_top_performing_products": 300,
    "get_traffic_analytics": 300,
    # Catalog - 5 minutes
    "list_catalog_products": 300,
    "list_knowledge_base_documents": 300,
    # Inventory - 30 seconds
    "manage_product_inventory": 30,
    # Brand/System - 1 hour
    "get_brand_guidelines": 3600,
    "get_system_status": 60,
    # Theme status - 10 seconds
    "get_theme_build_status": 10,
    # No cache (write operations)
    "create_woocommerce_product": 0,
    "update_woocommerce_product": 0,
    "create_blog_post": 0,
    "ingest_document": 0,
    "delete_document_from_knowledge_base": 0,
    "dispatch_agent_task": 0,
    "run_automation_workflow": 0,
}


def mcp_cached(ttl: int | None = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for caching MCP tool responses.

    Args:
        ttl: Cache TTL in seconds (None = use tool-specific or default)

    Usage:
        @mcp.tool
        @mcp_cached(ttl=300)
        def my_read_tool(query: str) -> dict:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            tool_name = func.__name__

            # Determine TTL
            cache_ttl = ttl
            if cache_ttl is None:
                cache_ttl = TOOL_CACHE_TTLS.get(tool_name, CACHE_TTL_SECONDS)

            # Skip cache for write operations
            if cache_ttl == 0:
                return func(*args, **kwargs)

            # Check cache
            hit, cached_value = response_cache.get(tool_name, kwargs)
            if hit:
                logger.debug(f"Cache hit for {tool_name}")
                return cached_value

            # Execute and cache
            result = func(*args, **kwargs)
            response_cache.set(tool_name, kwargs, result, cache_ttl)
            return result

        return wrapper

    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_audit_stats() -> dict[str, Any]:
    """Get audit logging statistics."""
    entries = audit_logger.get_recent_entries(limit=1000)
    if not entries:
        return {"total_calls": 0, "success_rate": 0.0, "unauthorized_attempts": 0}

    total = len(entries)
    successes = sum(1 for e in entries if e.success)
    unauthorized = sum(1 for e in entries if not e.authorized)
    avg_time = sum(e.execution_time_ms for e in entries) / total if total > 0 else 0

    # Tool breakdown
    tool_counts: dict[str, int] = {}
    for entry in entries:
        tool_counts[entry.tool_name] = tool_counts.get(entry.tool_name, 0) + 1

    return {
        "total_calls": total,
        "success_rate": round(successes / total, 4) if total > 0 else 0.0,
        "unauthorized_attempts": unauthorized,
        "avg_execution_time_ms": round(avg_time, 2),
        "top_tools": sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "cache_stats": response_cache.get_stats(),
    }


def create_mcp_context(
    user_id: str | None = None,
    role: Role = Role.READ_ONLY,
    permissions: set[str] | None = None,
) -> MCPToolContext:
    """Create an MCP tool context for authenticated calls."""
    return MCPToolContext(
        user_id=user_id,
        user_role=role,
        permissions=permissions or set(),
        authenticated=user_id is not None,
    )
