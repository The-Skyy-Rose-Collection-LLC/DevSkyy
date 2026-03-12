"""
Claude Agent SDK API Router
============================

REST endpoints for Claude Agent SDK integrations:
- POST /claude-sdk/research   — Trigger multi-agent research pipeline
- POST /claude-sdk/email      — Process/triage email via IMAP + AI
- POST /claude-sdk/excel      — Generate or analyze spreadsheets
- POST /claude-sdk/session    — Create/resume V2 stateful sessions
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
