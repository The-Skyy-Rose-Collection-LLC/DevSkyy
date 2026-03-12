"""
Claude Agent SDK Integration Package
=====================================

Deep integration of Claude Agent SDK into DevSkyy's agent hierarchy.

Layers:
    1. Standalone agents (research, email, excel, session)
    2. SDKCapabilityMixin — grants SDK execution to ANY agent
    3. SDKSubAgent — SubAgent powered by SDK with tool use
    4. DevSkyyHookSystem — SDK hooks → self-healing integration
    5. ToolProfile — domain-aware tool sets for SDK agents
    6. Tool bridge — reusable AgentDefinition builders

Any CoreAgent or SubAgent can inherit SDKCapabilityMixin to gain:
    _sdk_execute()   — full tool-use execution via SDK
    _sdk_delegate()  — multi-agent orchestration
    _sdk_session()   — stateful multi-turn conversations
"""

import logging as _logging

_logger = _logging.getLogger(__name__)

try:
    from .base import ClaudeSDKBaseAgent, SDKAgentConfig
except ImportError as _e:
    _logger.debug("ClaudeSDKBaseAgent unavailable: %s", _e)
    ClaudeSDKBaseAgent = None  # type: ignore[assignment,misc]
    SDKAgentConfig = None  # type: ignore[assignment,misc]

try:
    from .research import ResearchAgent, ResearchRequest, ResearchResult
except ImportError as _e:
    _logger.debug("ResearchAgent unavailable: %s", _e)
    ResearchAgent = None  # type: ignore[assignment,misc]

try:
    from .email_automation import EmailAutomationAgent, EmailTriageRequest, EmailTriageResult
except ImportError as _e:
    _logger.debug("EmailAutomationAgent unavailable: %s", _e)
    EmailAutomationAgent = None  # type: ignore[assignment,misc]

try:
    from .excel_handler import ExcelHandlerAgent, ExcelRequest, ExcelResult
except ImportError as _e:
    _logger.debug("ExcelHandlerAgent unavailable: %s", _e)
    ExcelHandlerAgent = None  # type: ignore[assignment,misc]

try:
    from .session import SessionConfig, SessionManager
except ImportError as _e:
    _logger.debug("SessionManager unavailable: %s", _e)
    SessionManager = None  # type: ignore[assignment,misc]

# --- Deep integration layer ---

try:
    from .hooks import DevSkyyHookSystem, HookMetrics
except ImportError as _e:
    _logger.debug("DevSkyyHookSystem unavailable: %s", _e)
    DevSkyyHookSystem = None  # type: ignore[assignment,misc]
    HookMetrics = None  # type: ignore[assignment,misc]

try:
    from .mixin import SDKCapabilityMixin, SDKExecutionResult
except ImportError as _e:
    _logger.debug("SDKCapabilityMixin unavailable: %s", _e)
    SDKCapabilityMixin = None  # type: ignore[assignment,misc]
    SDKExecutionResult = None  # type: ignore[assignment,misc]

try:
    from .sdk_sub_agent import SDKSubAgent
except ImportError as _e:
    _logger.debug("SDKSubAgent unavailable: %s", _e)
    SDKSubAgent = None  # type: ignore[assignment,misc]

try:
    from .tool_bridge import (
        ToolProfile,
        build_analyst_agent,
        build_code_agent,
        build_domain_agents,
        build_researcher_agent,
        build_writer_agent,
    )
except ImportError as _e:
    _logger.debug("ToolProfile unavailable: %s", _e)
    ToolProfile = None  # type: ignore[assignment,misc]

__all__ = [
    # Original standalone agents
    "ClaudeSDKBaseAgent",
    "SDKAgentConfig",
    "ResearchAgent",
    "ResearchRequest",
    "ResearchResult",
    "EmailAutomationAgent",
    "EmailTriageRequest",
    "EmailTriageResult",
    "ExcelHandlerAgent",
    "ExcelRequest",
    "ExcelResult",
    "SessionManager",
    "SessionConfig",
    # Deep integration layer
    "DevSkyyHookSystem",
    "HookMetrics",
    "SDKCapabilityMixin",
    "SDKExecutionResult",
    "SDKSubAgent",
    "ToolProfile",
    "build_researcher_agent",
    "build_analyst_agent",
    "build_writer_agent",
    "build_code_agent",
    "build_domain_agents",
]
