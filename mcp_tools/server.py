"""FastMCP server instance, configuration constants, and logger."""

import os

try:
    from config import settings  # noqa: F401, E402 - must be first
except ImportError:
    settings = None  # Fallback for standalone mode

from mcp.server.fastmcp import FastMCP
from utils.logging_utils import configure_logging, get_logger

# ===========================
# Configuration
# ===========================

# Backend selection: 'devskyy' (default) or 'critical-fuchsia-ape'
MCP_BACKEND = os.getenv("MCP_BACKEND", "devskyy")

# Dynamic configuration based on backend
if MCP_BACKEND == "critical-fuchsia-ape":
    # FastMCP hosted endpoint
    API_BASE_URL = os.getenv("CRITICAL_FUCHSIA_APE_URL", "https://critical-fuchsia-ape.fastmcp.app")
    API_KEY = os.getenv("CRITICAL_FUCHSIA_APE_KEY", "")
else:
    # Local DevSkyy backend
    API_BASE_URL = os.getenv("DEVSKYY_API_URL", "http://localhost:8000")
    API_KEY = os.getenv("DEVSKYY_API_KEY", "")

CHARACTER_LIMIT = 25000  # Maximum response size
REQUEST_TIMEOUT = 60.0  # API request timeout in seconds

# ===========================
# Advanced Tool Use Configuration
# ===========================

# System prompt for tool discovery guidance
SYSTEM_PROMPT = """
DevSkyy Enterprise Platform v2.0 - 54 Specialized AI Agents

Available agent categories (use tool search to discover specific tools):
- E-Commerce: Product analysis, pricing optimization, inventory management
- ML/AI: Trend prediction, customer segmentation, demand forecasting
- 3D Integration: Tripo AI (text/image to 3D), FASHN AI (virtual try-on)
- Marketing: SEO, content generation, campaign management
- Integration: WooCommerce, WordPress, API orchestration
- Advanced: Theme generation, automation workflows
- Infrastructure: Code scanning, self-healing, monitoring

Use devskyy_list_agents for the complete agent directory.
Use devskyy_system_monitoring for platform health status.
"""

# PTC caller identifier for programmatic tool calling
PTC_CALLER = "code_execution_20250825"

# ===========================
# Logging
# ===========================

configure_logging(json_output=True)
logger = get_logger(__name__)

# ===========================
# Initialize MCP Server
# ===========================

mcp = FastMCP("devskyy_mcp_v2")
