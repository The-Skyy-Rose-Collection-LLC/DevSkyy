"""
Excel Handler Agent
===================

Spreadsheet generation and analysis using openpyxl for creation
and pandas for analysis. Includes formula recalculation via LibreOffice.

Adapted from claude-agent-sdk-demos/excel-demo.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import structlog
from claude_agent_sdk import AgentDefinition
from pydantic import BaseModel, Field

from agents.claude_sdk.base import ClaudeSDKBaseAgent, SDKAgentConfig

logger = structlog.get_logger(__name__)


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------


class ExcelOperation(StrEnum):
    CREATE = "create"
    ANALYZE = "analyze"


class ExcelRequest(BaseModel):
    """Input model for Excel API endpoint."""

    operation: ExcelOperation = Field(..., description="Create or analyze")
    description: str = Field(
        ...,
        description="Natural language description of what to create/analyze",
        min_length=5,
        max_length=2000,
    )
    input_file: str | None = Field(
        default=None,
        description="Path to existing Excel file (for analyze operation)",
    )
    output_filename: str | None = Field(
        default=None,
        description="Desired output filename (auto-generated if not provided)",
    )


class ExcelResult(BaseModel):
    """Output model for Excel API endpoint."""

    operation: ExcelOperation
    output_path: str | None = None
    analysis: str | None = None
    formula_check: dict[str, Any] | None = None
    response: str


# ------------------------------------------------------------------
# Recalc utility (ported from excel-demo recalc.py)
# ------------------------------------------------------------------

RECALC_SCRIPT = Path(__file__).parent / "utils" / "recalc.py"


def recalc_formulas(filepath: str, timeout: int = 30) -> dict[str, Any]:
    """Recalculate Excel formulas using LibreOffice.

    Args:
        filepath: Path to Excel file.
        timeout: Max seconds for recalculation.

    Returns:
        Dict with status, total_errors, error_summary, total_formulas.
    """
    if not RECALC_SCRIPT.exists():
        return {"error": "recalc.py not found"}

    try:
        result = subprocess.run(
            ["python3", str(RECALC_SCRIPT), filepath, str(timeout)],
            capture_output=True,
            text=True,
            timeout=timeout + 10,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr or "Recalculation failed"}
    except subprocess.TimeoutExpired:
        return {"error": "Recalculation timed out"}
    except Exception as e:
        return {"error": str(e)}


# ------------------------------------------------------------------
# Agent
# ------------------------------------------------------------------


class ExcelHandlerAgent(ClaudeSDKBaseAgent):
    """Spreadsheet creation and analysis agent.

    Uses openpyxl for creation (preserving formulas) and pandas for
    analysis. Supports formula recalculation via LibreOffice when available.

    Output directory: ``data/spreadsheets/``
    """

    SYSTEM_PROMPT = """You are a spreadsheet specialist for the DevSkyy platform.

You create and analyze Excel spreadsheets using openpyxl and pandas.

CRITICAL RULES:
1. Always use Excel FORMULAS, never hardcode calculated values
2. Use professional formatting with headers, borders, and number formats
3. Save files to data/spreadsheets/
4. For SkyyRose data: use brand colors (#B76E79 rose gold, #0A0A0A dark, #D4AF37 gold)

When CREATING spreadsheets:
- Use openpyxl for formulas and formatting
- Include proper headers, data validation, and formatting
- Use Excel formulas (=SUM, =AVERAGE, etc.) not Python calculations
- Save to data/spreadsheets/{filename}.xlsx

When ANALYZING spreadsheets:
- Use pandas for data analysis
- Provide statistical summaries, trends, and insights
- Generate visualizations if requested
- Reference specific cells and ranges in your analysis

Financial model standards:
- Blue text (#0000FF) for hardcoded inputs
- Black text for formulas
- Yellow background (#FFFF00) for key assumptions
- Currency: $#,##0 format
- Percentages: 0.0% format
- Years as text strings, not numbers
"""

    def __init__(self, config: SDKAgentConfig | None = None) -> None:
        cfg = config or SDKAgentConfig(output_dir=Path("data/spreadsheets"))
        super().__init__(cfg)

    def _build_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    def _build_allowed_tools(self) -> list[str]:
        return ["Read", "Write", "Bash", "Glob"]

    def _build_agents(self) -> dict[str, AgentDefinition]:
        return {}

    async def handle(self, request: ExcelRequest) -> ExcelResult:
        """Create or analyze a spreadsheet.

        Args:
            request: Excel operation request.

        Returns:
            ExcelResult with output path and/or analysis.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.config.output_dir / f"excel_{ts}"
        session_dir.mkdir(parents=True, exist_ok=True)

        if request.operation == ExcelOperation.CREATE:
            filename = request.output_filename or f"report_{ts}.xlsx"
            prompt = (
                f"Create an Excel spreadsheet and save it to "
                f"data/spreadsheets/{filename}.\n\n"
                f"Requirements:\n{request.description}"
            )
        else:
            if not request.input_file:
                return ExcelResult(
                    operation=request.operation,
                    response="Error: input_file required for analyze operation",
                )
            prompt = (
                f"Analyze the Excel file at: {request.input_file}\n\n"
                f"Analysis requested:\n{request.description}"
            )

        logger.info(
            "excel_operation_started",
            operation=request.operation,
            session_dir=str(session_dir),
        )

        response = await self.run(prompt, session_dir=session_dir)

        # For create operations, try to find and recalc the output file
        output_path = None
        formula_check = None

        if request.operation == ExcelOperation.CREATE:
            xlsx_files = list(self.config.output_dir.glob("*.xlsx"))
            if xlsx_files:
                latest = max(xlsx_files, key=lambda f: f.stat().st_mtime)
                output_path = str(latest)
                formula_check = recalc_formulas(output_path)

        return ExcelResult(
            operation=request.operation,
            output_path=output_path,
            analysis=response if request.operation == ExcelOperation.ANALYZE else None,
            formula_check=formula_check,
            response=response,
        )
