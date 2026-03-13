"""
Claude Agent SDK API Router
============================

REST endpoints for Claude Agent SDK integrations:
- POST /claude-sdk/research    — Trigger multi-agent research pipeline
- POST /claude-sdk/email       — Process/triage email via IMAP + AI
- POST /claude-sdk/excel       — Generate or analyze spreadsheets
- POST /claude-sdk/session     — Create/resume V2 stateful sessions
- POST /claude-sdk/dashboard   — Execute dashboard actions across domains
- GET  /claude-sdk/dashboard/health — Dashboard agent health status
- GET  /claude-sdk/dashboard/agents — List all registered agents
- POST /claude-sdk/dashboard/find   — Find agents by capability
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/claude-sdk", tags=["Claude Agent SDK"])

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Research endpoint
# ------------------------------------------------------------------


@router.post("/research")
async def trigger_research(
    topic: str,
    subtopics: list[str] | None = None,
    model: str = "haiku",
):
    """Trigger a multi-agent research pipeline.

    Spawns researcher, data-analyst, and report-writer subagents
    to produce a comprehensive PDF report with data visualizations.

    Args:
        topic: Research topic.
        subtopics: Optional specific subtopics to investigate.
        model: Claude model for subagents.

    Returns:
        Research result with session directory and report path.
    """
    try:
        from agents.claude_sdk.research import ResearchAgent, ResearchRequest

        agent = ResearchAgent()
        request = ResearchRequest(topic=topic, subtopics=subtopics, model=model)
        result = await agent.research(request)
        return result.model_dump()
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed. Run: pip install claude-agent-sdk",
        )
    except Exception as e:
        logger.exception("research_failed")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Email triage endpoint
# ------------------------------------------------------------------


@router.post("/email")
async def triage_email(
    mailbox: str = "INBOX",
    limit: int = 10,
    unread_only: bool = True,
):
    """Triage emails from IMAP with AI classification.

    Fetches emails, classifies priority/category, extracts action items,
    and drafts responses.

    Args:
        mailbox: IMAP mailbox to scan.
        limit: Max emails to process.
        unread_only: Only process unread emails.

    Returns:
        Triage results with classified emails and action items.
    """
    try:
        from agents.claude_sdk.email_automation import (
            EmailAutomationAgent,
            EmailTriageRequest,
        )

        agent = EmailAutomationAgent()
        request = EmailTriageRequest(mailbox=mailbox, limit=limit, unread_only=unread_only)
        result = await agent.triage(request)
        return result.model_dump()
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed. Run: pip install claude-agent-sdk",
        )
    except Exception as e:
        logger.exception("email_triage_failed")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Excel endpoint
# ------------------------------------------------------------------


@router.post("/excel")
async def handle_excel(
    operation: str,
    description: str,
    input_file: str | None = None,
    output_filename: str | None = None,
):
    """Create or analyze Excel spreadsheets with AI.

    Uses openpyxl for creation (with proper formulas) and pandas for
    analysis. Supports formula recalculation via LibreOffice.

    Args:
        operation: "create" or "analyze".
        description: Natural language description of what to do.
        input_file: Path to existing file (for analyze).
        output_filename: Desired output filename (for create).

    Returns:
        Excel result with output path and/or analysis.
    """
    try:
        from agents.claude_sdk.excel_handler import (
            ExcelHandlerAgent,
            ExcelOperation,
            ExcelRequest,
        )

        agent = ExcelHandlerAgent()
        request = ExcelRequest(
            operation=ExcelOperation(operation),
            description=description,
            input_file=input_file,
            output_filename=output_filename,
        )
        result = await agent.handle(request)
        return result.model_dump()
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed. Run: pip install claude-agent-sdk",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("excel_operation_failed")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Session endpoint
# ------------------------------------------------------------------


@router.post("/session")
async def manage_session(
    action: str = "create",
    prompt: str | None = None,
    session_id: str | None = None,
    model: str = "sonnet",
    system_prompt: str | None = None,
):
    """Create, resume, or execute one-shot V2 sessions.

    Args:
        action: "create", "resume", or "one-shot".
        prompt: Message to send (required for resume/one-shot).
        session_id: Session ID (required for resume).
        model: Claude model to use.
        system_prompt: Optional system prompt.

    Returns:
        Session response with session_id and response text.
    """
    try:
        from agents.claude_sdk.session import (
            OneShotRequest,
            SessionConfig,
            SessionCreateRequest,
            SessionManager,
            SessionResumeRequest,
        )

        manager = SessionManager()
        config = SessionConfig(model=model, system_prompt=system_prompt)

        if action == "create":
            request = SessionCreateRequest(config=config, initial_prompt=prompt)
            result = await manager.create_session(request)
        elif action == "resume":
            if not session_id or not prompt:
                raise HTTPException(
                    status_code=400,
                    detail="session_id and prompt required for resume",
                )
            request = SessionResumeRequest(session_id=session_id, prompt=prompt, config=config)
            result = await manager.resume_session(request)
        elif action == "one-shot":
            if not prompt:
                raise HTTPException(
                    status_code=400,
                    detail="prompt required for one-shot",
                )
            request = OneShotRequest(prompt=prompt, model=model)
            result = await manager.one_shot(request)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action: {action}. Use create, resume, or one-shot.",
            )

        return result.model_dump()

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed. Run: pip install claude-agent-sdk",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("session_operation_failed")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Dashboard orchestrator endpoints
# ------------------------------------------------------------------


@router.post("/dashboard")
async def execute_dashboard_actions(
    actions: list[dict],
    parallel: bool = True,
):
    """Execute actions across SDK domain agents.

    The dashboard orchestrator coordinates 27 SDK agents across
    15 domains (operations, commerce, content, analytics, imagery,
    creative, marketing, web_builder, immersive, customer_intelligence,
    influencer, supply_chain, brand_guardian, community, seo_discovery).

    Each action targets a domain + capability. Independent actions
    can run in parallel for faster dashboard updates.

    Args:
        actions: List of action dicts with domain, action, params.
        parallel: Execute independent actions in parallel.

    Returns:
        Aggregated results from all actions.
    """
    try:
        from agents.claude_sdk.dashboard import (
            DashboardAction,
            DashboardOrchestrator,
            DashboardRequest,
        )

        orchestrator = DashboardOrchestrator()
        parsed_actions = [DashboardAction(**a) for a in actions]
        request = DashboardRequest(actions=parsed_actions, parallel=parallel)
        result = await orchestrator.execute(request)
        return result.model_dump()

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed. Run: pip install claude-agent-sdk",
        )
    except Exception as e:
        logger.exception("dashboard_action_failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/health")
async def get_dashboard_health():
    """Get health status of all registered SDK dashboard agents.

    Returns the list of all 27 SDK agents across 15 domains with
    their availability, capabilities, and last-used timestamps.
    """
    try:
        from agents.claude_sdk.dashboard import DashboardOrchestrator

        orchestrator = DashboardOrchestrator()
        return orchestrator.get_health().model_dump()

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed.",
        )
    except Exception as e:
        logger.exception("dashboard_health_failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/agents")
async def list_dashboard_agents(
    domain: str | None = None,
):
    """List all registered SDK dashboard agents, optionally filtered by domain.

    Args:
        domain: Optional domain filter (operations, commerce, content,
                analytics, imagery, creative, marketing, web_builder,
                immersive, customer_intelligence, influencer,
                supply_chain, brand_guardian, community, seo_discovery).

    Returns:
        Agent list with capabilities and domain information.
    """
    try:
        from agents.claude_sdk.dashboard import DashboardOrchestrator

        orchestrator = DashboardOrchestrator()
        health = orchestrator.get_health()

        if domain:
            agents = [a for a in health.agents if a.domain == domain]
        else:
            agents = health.agents

        return {
            "total": len(agents),
            "domain_filter": domain,
            "agents": [a.model_dump() for a in agents],
            "available_domains": health.domains,
        }

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed.",
        )
    except Exception as e:
        logger.exception("dashboard_agents_list_failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard/find")
async def find_agents_by_capability(
    capability: str,
):
    """Find SDK agents that have a specific capability.

    Args:
        capability: Capability to search for (e.g., 'deploy_run',
                   'vton_render', 'brand_compliance').

    Returns:
        List of agent names with the requested capability.
    """
    try:
        from agents.claude_sdk.dashboard import DashboardOrchestrator

        orchestrator = DashboardOrchestrator()
        agents = orchestrator.find_agent(capability)
        return {
            "capability": capability,
            "agents": agents,
            "count": len(agents),
        }

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Claude Agent SDK not installed.",
        )
    except Exception as e:
        logger.exception("dashboard_find_failed")
        raise HTTPException(status_code=500, detail=str(e))
