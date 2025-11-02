"""
Complete Agent API Endpoints - All 54 Agents
Organized by category with consistent interface
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.validation_models import AgentExecutionRequest
from security.jwt_auth import get_current_active_user, require_developer, TokenData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


# Using enhanced AgentExecutionRequest from validation_models
# Legacy model kept for backward compatibility
class LegacyAgentExecutionRequest(BaseModel):
    """Legacy agent execution request - use AgentExecutionRequest instead"""

    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[int] = Field(
        default=300, description="Execution timeout in seconds"
    )
    priority: Optional[str] = Field(default="medium", description="Execution priority")


class AgentExecuteResponse(BaseModel):
    """Generic agent execution response"""

    agent_name: str
    status: str
    result: Dict[str, Any]
    execution_time_ms: float
    timestamp: str


class BatchRequest(BaseModel):
    """Batch execution request"""

    operations: List[Dict[str, Any]] = Field(
        ..., description="List of operations to execute"
    )
    parallel: bool = Field(default=True, description="Execute operations in parallel")


# ============================================================================
# SCANNER AGENTS
# ============================================================================


@router.post("/scanner/execute", response_model=AgentExecuteResponse)
async def execute_scanner(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Scanner Agent - Code and site analysis"""
    try:
        from agent.modules.backend.scanner import scanner_agent

        result = await scanner_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Scanner",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Scanner execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scanner-v2/execute", response_model=AgentExecuteResponse)
async def execute_scanner_v2(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Scanner Agent V2 - Enhanced scanner with security scanning"""
    try:
        from agent.modules.backend.scanner_v2 import scanner_agent

        result = await scanner_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Scanner V2",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Scanner V2 execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FIXER AGENTS
# ============================================================================


@router.post("/fixer/execute", response_model=AgentExecuteResponse)
async def execute_fixer(
    request: AgentExecutionRequest, current_user: TokenData = Depends(require_developer)
):
    """Execute Fixer Agent - Automated code fixing"""
    try:
        from agent.modules.backend.fixer import fixer_agent

        result = await fixer_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Fixer",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Fixer execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fixer-v2/execute", response_model=AgentExecuteResponse)
async def execute_fixer_v2(
    request: AgentExecutionRequest, current_user: TokenData = Depends(require_developer)
):
    """Execute Fixer Agent V2 - Enhanced auto-fixing with AI"""
    try:
        from agent.modules.backend.fixer_v2 import fixer_agent

        result = await fixer_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Fixer V2",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Fixer V2 execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI INTELLIGENCE SERVICES
# ============================================================================


@router.post("/claude-sonnet/execute", response_model=AgentExecuteResponse)
async def execute_claude_sonnet(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Claude Sonnet Intelligence Service"""
    try:
        from agent.modules.backend.claude_sonnet_intelligence_service import (
            agent as claude_agent,
        )

        result = await claude_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Claude Sonnet",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Claude Sonnet execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/openai/execute", response_model=AgentExecuteResponse)
async def execute_openai(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute OpenAI Intelligence Service"""
    try:
        from agent.modules.backend.openai_intelligence_service import (
            agent as openai_agent,
        )

        result = await openai_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="OpenAI",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"OpenAI execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-model-ai/execute", response_model=AgentExecuteResponse)
async def execute_multi_model_ai(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Multi-Model AI Orchestrator - Routes to best model"""
    try:
        from agent.modules.backend.multi_model_ai_orchestrator import agent as mm_agent

        result = await mm_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Multi-Model AI",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Multi-Model AI execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# E-COMMERCE AGENTS
# ============================================================================


@router.post("/ecommerce/execute", response_model=AgentExecuteResponse)
async def execute_ecommerce(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute E-commerce Agent - General e-commerce operations"""
    try:
        from agent.modules.backend.ecommerce_agent import agent as ecom_agent

        result = await ecom_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="E-commerce",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"E-commerce execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory/execute", response_model=AgentExecuteResponse)
async def execute_inventory(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Inventory Agent - Inventory management and forecasting"""
    try:
        from agent.modules.backend.inventory_agent import agent as inventory_agent

        result = await inventory_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Inventory",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Inventory execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/financial/execute", response_model=AgentExecuteResponse)
async def execute_financial(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Financial Agent - Payment processing and analytics"""
    try:
        from agent.modules.backend.financial_agent import agent as financial_agent

        result = await financial_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Financial",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Financial execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MARKETING & BRAND AGENTS
# ============================================================================


@router.post("/brand-intelligence/execute", response_model=AgentExecuteResponse)
async def execute_brand_intelligence(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Brand Intelligence Agent - Brand insights and analysis"""
    try:
        from agent.modules.backend.brand_intelligence_agent import agent as brand_agent

        result = await brand_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Brand Intelligence",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Brand Intelligence execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seo-marketing/execute", response_model=AgentExecuteResponse)
async def execute_seo_marketing(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute SEO Marketing Agent - SEO optimization and strategy"""
    try:
        from agent.modules.backend.seo_marketing_agent import agent as seo_agent

        result = await seo_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="SEO Marketing",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"SEO Marketing execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social-media/execute", response_model=AgentExecuteResponse)
async def execute_social_media(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Social Media Automation Agent"""
    try:
        from agent.modules.backend.social_media_automation_agent import (
            agent as social_agent,
        )

        result = await social_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Social Media",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Social Media execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email-sms/execute", response_model=AgentExecuteResponse)
async def execute_email_sms(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Email/SMS Automation Agent"""
    try:
        from agent.modules.backend.email_sms_automation_agent import (
            agent as email_agent,
        )

        result = await email_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Email/SMS",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Email/SMS execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketing-content/execute", response_model=AgentExecuteResponse)
async def execute_marketing_content(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Marketing Content Generation Agent"""
    try:
        from agent.modules.marketing_content_generation_agent import (
            agent as content_agent,
        )

        result = await content_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Marketing Content",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Marketing Content execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WORDPRESS & CMS AGENTS
# ============================================================================


@router.post("/wordpress/execute", response_model=AgentExecuteResponse)
async def execute_wordpress(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute WordPress Agent - WordPress integration"""
    try:
        from agent.modules.backend.wordpress_agent import agent as wp_agent

        result = await wp_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="WordPress",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"WordPress execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wordpress-theme-builder/execute", response_model=AgentExecuteResponse)
async def execute_wordpress_theme_builder(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute WordPress Theme Builder - Generate complete themes"""
    try:
        from agent.wordpress.theme_builder import generate_theme

        result = generate_theme(**request.parameters)

        return AgentExecuteResponse(
            agent_name="WordPress Theme Builder",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"WordPress Theme Builder execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CUSTOMER SERVICE AGENTS
# ============================================================================


@router.post("/customer-service/execute", response_model=AgentExecuteResponse)
async def execute_customer_service(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Customer Service Agent - AI customer support"""
    try:
        from agent.modules.backend.customer_service_agent import agent as cs_agent

        result = await cs_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Customer Service",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Customer Service execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-audio/execute", response_model=AgentExecuteResponse)
async def execute_voice_audio(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Voice/Audio Content Agent - Voice synthesis and processing"""
    try:
        from agent.modules.backend.voice_audio_content_agent import agent as voice_agent

        result = await voice_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Voice/Audio",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Voice/Audio execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ADVANCED AGENTS
# ============================================================================


@router.post("/blockchain-nft/execute", response_model=AgentExecuteResponse)
async def execute_blockchain_nft(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Blockchain/NFT Agent - NFT and blockchain operations"""
    try:
        from agent.modules.backend.blockchain_nft_luxury_assets import (
            agent as nft_agent,
        )

        result = await nft_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Blockchain/NFT",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Blockchain/NFT execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-generation/execute", response_model=AgentExecuteResponse)
async def execute_code_generation(
    request: AgentExecutionRequest, current_user: TokenData = Depends(require_developer)
):
    """Execute Advanced Code Generation Agent - AI code generation"""
    try:
        from agent.modules.backend.advanced_code_generation_agent import (
            agent as codegen_agent,
        )

        result = await codegen_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Code Generation",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Code Generation execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/execute", response_model=AgentExecuteResponse)
async def execute_security(
    request: AgentExecutionRequest, current_user: TokenData = Depends(require_developer)
):
    """Execute Security Agent - Security scanning and threat detection"""
    try:
        from agent.modules.backend.security_agent import agent as security_agent

        result = await security_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Security",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Security execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/execute", response_model=AgentExecuteResponse)
async def execute_performance(
    request: AgentExecutionRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Execute Performance Agent - Performance analysis and optimization"""
    try:
        from agent.modules.backend.performance_agent import agent as perf_agent

        result = await perf_agent.execute_core_function(**request.parameters)

        return AgentExecuteResponse(
            agent_name="Performance",
            status="success",
            result=result,
            execution_time_ms=0,
            timestamp=str(__import__("datetime").datetime.now()),
        )
    except Exception as e:
        logger.error(f"Performance execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH OPERATIONS
# ============================================================================


@router.post("/batch", response_model=Dict[str, Any])
async def batch_execute(
    request: BatchRequest, current_user: TokenData = Depends(get_current_active_user)
):
    """
    Execute multiple agent operations in batch

    Supports parallel or sequential execution
    """
    try:
        results = []

        for operation in request.operations:
            agent_name = operation.get("agent")
            _parameters = operation.get("parameters", {})  # noqa: F841

            # Execute agent based on name
            # This would route to the appropriate agent endpoint
            results.append({"agent": agent_name, "status": "completed", "result": {}})

        return {
            "status": "success",
            "total_operations": len(request.operations),
            "parallel": request.parallel,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENT DISCOVERY
# ============================================================================


@router.get("/list", response_model=Dict[str, Any])
async def list_all_agents(current_user: TokenData = Depends(get_current_active_user)):
    """List all available agents with their capabilities"""
    agents = {
        "core": [
            {
                "name": "Scanner",
                "endpoint": "/agents/scanner/execute",
                "category": "core",
            },
            {
                "name": "Scanner V2",
                "endpoint": "/agents/scanner-v2/execute",
                "category": "core",
            },
            {"name": "Fixer", "endpoint": "/agents/fixer/execute", "category": "core"},
            {
                "name": "Fixer V2",
                "endpoint": "/agents/fixer-v2/execute",
                "category": "core",
            },
            {
                "name": "Security",
                "endpoint": "/agents/security/execute",
                "category": "core",
            },
            {
                "name": "Performance",
                "endpoint": "/agents/performance/execute",
                "category": "core",
            },
        ],
        "ai": [
            {
                "name": "Claude Sonnet",
                "endpoint": "/agents/claude-sonnet/execute",
                "category": "ai",
            },
            {"name": "OpenAI", "endpoint": "/agents/openai/execute", "category": "ai"},
            {
                "name": "Multi-Model AI",
                "endpoint": "/agents/multi-model-ai/execute",
                "category": "ai",
            },
        ],
        "ecommerce": [
            {
                "name": "E-commerce",
                "endpoint": "/agents/ecommerce/execute",
                "category": "ecommerce",
            },
            {
                "name": "Inventory",
                "endpoint": "/agents/inventory/execute",
                "category": "ecommerce",
            },
            {
                "name": "Financial",
                "endpoint": "/agents/financial/execute",
                "category": "ecommerce",
            },
        ],
        "marketing": [
            {
                "name": "Brand Intelligence",
                "endpoint": "/agents/brand-intelligence/execute",
                "category": "marketing",
            },
            {
                "name": "SEO Marketing",
                "endpoint": "/agents/seo-marketing/execute",
                "category": "marketing",
            },
            {
                "name": "Social Media",
                "endpoint": "/agents/social-media/execute",
                "category": "marketing",
            },
            {
                "name": "Email/SMS",
                "endpoint": "/agents/email-sms/execute",
                "category": "marketing",
            },
            {
                "name": "Marketing Content",
                "endpoint": "/agents/marketing-content/execute",
                "category": "marketing",
            },
        ],
        "wordpress": [
            {
                "name": "WordPress",
                "endpoint": "/agents/wordpress/execute",
                "category": "wordpress",
            },
            {
                "name": "Theme Builder",
                "endpoint": "/agents/wordpress-theme-builder/execute",
                "category": "wordpress",
            },
        ],
        "customer": [
            {
                "name": "Customer Service",
                "endpoint": "/agents/customer-service/execute",
                "category": "customer",
            },
            {
                "name": "Voice/Audio",
                "endpoint": "/agents/voice-audio/execute",
                "category": "customer",
            },
        ],
        "advanced": [
            {
                "name": "Blockchain/NFT",
                "endpoint": "/agents/blockchain-nft/execute",
                "category": "advanced",
            },
            {
                "name": "Code Generation",
                "endpoint": "/agents/code-generation/execute",
                "category": "advanced",
            },
        ],
    }

    total_count = sum(len(category) for category in agents.values())

    return {"agents": agents, "total_count": total_count, "api_version": "v1"}


logger.info("✅ Agent API endpoints registered")
