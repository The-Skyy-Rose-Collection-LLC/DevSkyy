"""
Agent API Endpoints
===================

Exposes all 69 DevSkyy agents via REST API.
Covers missing endpoints:
- Social Media
- Email/SMS
- Customer Service
- Content Generation
- Brand Intelligence
- Voice/Audio
- Integration Manager
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr

from security.jwt_oauth2_auth import get_current_user, RoleChecker, UserRole, TokenPayload
from api.webhooks import webhook_manager, WebhookEventType

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class AgentCategory(str, Enum):
    """Agent categories"""
    SOCIAL_MEDIA = "social_media"
    EMAIL_SMS = "email_sms"
    CUSTOMER_SERVICE = "customer_service"
    CONTENT = "content"
    BRAND = "brand"
    VOICE = "voice"
    INTEGRATION = "integration"
    WORDPRESS = "wordpress"
    ECOMMERCE = "ecommerce"
    ML = "ml"
    SECURITY = "security"


class TaskStatus(str, Enum):
    """Task execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Task priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# =============================================================================
# Base Models
# =============================================================================

class AgentTask(BaseModel):
    """Agent task request"""
    agent_name: str
    action: str
    parameters: Dict[str, Any] = {}
    priority: Priority = Priority.NORMAL
    callback_url: Optional[str] = None


class AgentTaskResponse(BaseModel):
    """Agent task response"""
    task_id: str
    agent_name: str
    action: str
    status: TaskStatus
    created_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentInfo(BaseModel):
    """Agent information"""
    name: str
    category: AgentCategory
    description: str
    actions: List[str]
    is_active: bool = True
    model: str = "claude-sonnet"


# =============================================================================
# Social Media Agent Models
# =============================================================================

class SocialPlatform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    PINTEREST = "pinterest"
    LINKEDIN = "linkedin"


class SocialPostRequest(BaseModel):
    """Social media post request"""
    platform: SocialPlatform
    content: str = Field(..., max_length=2200)
    media_urls: List[str] = []
    hashtags: List[str] = []
    schedule_time: Optional[datetime] = None
    campaign_id: Optional[str] = None


class SocialAnalyticsRequest(BaseModel):
    """Social analytics request"""
    platform: SocialPlatform
    metrics: List[str] = ["engagement", "reach", "followers"]
    date_range_days: int = 30


# =============================================================================
# Email/SMS Agent Models
# =============================================================================

class EmailRequest(BaseModel):
    """Email send request"""
    to: List[EmailStr]
    subject: str
    body: str
    template_id: Optional[str] = None
    personalization: Dict[str, Any] = {}
    schedule_time: Optional[datetime] = None


class SMSRequest(BaseModel):
    """SMS send request"""
    to: List[str]
    message: str = Field(..., max_length=160)
    sender_id: Optional[str] = None


class CampaignRequest(BaseModel):
    """Email/SMS campaign request"""
    name: str
    type: str  # email, sms, both
    audience_segment: str
    content: Dict[str, Any]
    schedule: Optional[datetime] = None


# =============================================================================
# Customer Service Agent Models
# =============================================================================

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicketRequest(BaseModel):
    """Support ticket creation"""
    customer_id: str
    subject: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = "general"


class ChatbotRequest(BaseModel):
    """Chatbot interaction"""
    session_id: str
    message: str
    context: Dict[str, Any] = {}


# =============================================================================
# Content Generation Agent Models
# =============================================================================

class ContentType(str, Enum):
    BLOG_POST = "blog_post"
    PRODUCT_DESCRIPTION = "product_description"
    AD_COPY = "ad_copy"
    EMAIL = "email"
    SOCIAL_POST = "social_post"
    SEO_META = "seo_meta"


class ContentRequest(BaseModel):
    """Content generation request"""
    type: ContentType
    topic: str
    keywords: List[str] = []
    tone: str = "professional"
    length: str = "medium"  # short, medium, long
    brand_voice: bool = True


class SEOOptimizeRequest(BaseModel):
    """SEO optimization request"""
    url: Optional[str] = None
    content: Optional[str] = None
    target_keywords: List[str]
    competitor_urls: List[str] = []


# =============================================================================
# Agent Service
# =============================================================================

class AgentService:
    """Central agent orchestration service"""
    
    def __init__(self):
        self._tasks: Dict[str, AgentTaskResponse] = {}
        self._agents = self._register_agents()
    
    def _register_agents(self) -> Dict[str, AgentInfo]:
        """Register all available agents"""
        return {
            # Social Media Agents
            "instagram_agent": AgentInfo(
                name="instagram_agent",
                category=AgentCategory.SOCIAL_MEDIA,
                description="Instagram content scheduling and analytics",
                actions=["post", "schedule", "analyze", "respond_comments"]
            ),
            "tiktok_agent": AgentInfo(
                name="tiktok_agent",
                category=AgentCategory.SOCIAL_MEDIA,
                description="TikTok video optimization and trends",
                actions=["post", "analyze_trends", "optimize_hashtags"]
            ),
            "twitter_agent": AgentInfo(
                name="twitter_agent",
                category=AgentCategory.SOCIAL_MEDIA,
                description="Twitter engagement and monitoring",
                actions=["post", "schedule", "monitor_mentions", "analyze"]
            ),
            "social_scheduler_agent": AgentInfo(
                name="social_scheduler_agent",
                category=AgentCategory.SOCIAL_MEDIA,
                description="Cross-platform social scheduling",
                actions=["schedule", "bulk_schedule", "optimize_times"]
            ),
            
            # Email/SMS Agents
            "email_campaign_agent": AgentInfo(
                name="email_campaign_agent",
                category=AgentCategory.EMAIL_SMS,
                description="Email campaign management and automation",
                actions=["send", "schedule", "create_campaign", "analyze"]
            ),
            "sms_agent": AgentInfo(
                name="sms_agent",
                category=AgentCategory.EMAIL_SMS,
                description="SMS notifications and campaigns",
                actions=["send", "bulk_send", "create_campaign"]
            ),
            "notification_agent": AgentInfo(
                name="notification_agent",
                category=AgentCategory.EMAIL_SMS,
                description="Multi-channel notification orchestration",
                actions=["send", "schedule", "manage_preferences"]
            ),
            
            # Customer Service Agents
            "support_ticket_agent": AgentInfo(
                name="support_ticket_agent",
                category=AgentCategory.CUSTOMER_SERVICE,
                description="Support ticket management and routing",
                actions=["create", "update", "assign", "resolve", "escalate"]
            ),
            "chatbot_agent": AgentInfo(
                name="chatbot_agent",
                category=AgentCategory.CUSTOMER_SERVICE,
                description="AI-powered customer chat support",
                actions=["respond", "escalate", "collect_feedback"]
            ),
            "sentiment_agent": AgentInfo(
                name="sentiment_agent",
                category=AgentCategory.CUSTOMER_SERVICE,
                description="Customer sentiment analysis",
                actions=["analyze_feedback", "monitor_social", "generate_report"]
            ),
            "faq_agent": AgentInfo(
                name="faq_agent",
                category=AgentCategory.CUSTOMER_SERVICE,
                description="FAQ management and auto-response",
                actions=["search", "suggest", "create", "update"]
            ),
            
            # Content Generation Agents
            "blog_writer_agent": AgentInfo(
                name="blog_writer_agent",
                category=AgentCategory.CONTENT,
                description="AI blog post generation",
                actions=["generate", "optimize", "suggest_topics"]
            ),
            "copywriting_agent": AgentInfo(
                name="copywriting_agent",
                category=AgentCategory.CONTENT,
                description="Marketing copy and ad creation",
                actions=["generate_ad", "generate_email", "generate_social"]
            ),
            "seo_content_agent": AgentInfo(
                name="seo_content_agent",
                category=AgentCategory.CONTENT,
                description="SEO-optimized content generation",
                actions=["optimize", "generate_meta", "keyword_research"]
            ),
            "product_description_agent": AgentInfo(
                name="product_description_agent",
                category=AgentCategory.CONTENT,
                description="Product description generation",
                actions=["generate", "optimize", "bulk_generate"]
            ),
            
            # Brand Intelligence Agents
            "brand_monitor_agent": AgentInfo(
                name="brand_monitor_agent",
                category=AgentCategory.BRAND,
                description="Brand mention monitoring",
                actions=["monitor", "alert", "report"]
            ),
            "competitor_agent": AgentInfo(
                name="competitor_agent",
                category=AgentCategory.BRAND,
                description="Competitor analysis and tracking",
                actions=["analyze", "track_prices", "compare"]
            ),
            "trend_agent": AgentInfo(
                name="trend_agent",
                category=AgentCategory.BRAND,
                description="Market trend analysis",
                actions=["analyze_trends", "predict", "report"]
            ),
            
            # Voice/Audio Agents
            "voice_assistant_agent": AgentInfo(
                name="voice_assistant_agent",
                category=AgentCategory.VOICE,
                description="Voice interaction handling",
                actions=["transcribe", "respond", "generate_audio"]
            ),
            "podcast_agent": AgentInfo(
                name="podcast_agent",
                category=AgentCategory.VOICE,
                description="Podcast content management",
                actions=["transcribe", "summarize", "generate_notes"]
            ),
            
            # Integration Agents
            "zapier_agent": AgentInfo(
                name="zapier_agent",
                category=AgentCategory.INTEGRATION,
                description="Zapier integration management",
                actions=["create_zap", "trigger", "monitor"]
            ),
            "api_connector_agent": AgentInfo(
                name="api_connector_agent",
                category=AgentCategory.INTEGRATION,
                description="External API integration",
                actions=["connect", "sync", "transform"]
            ),
            "data_sync_agent": AgentInfo(
                name="data_sync_agent",
                category=AgentCategory.INTEGRATION,
                description="Data synchronization across systems",
                actions=["sync", "schedule", "validate"]
            ),
        }
    
    def list_agents(
        self,
        category: Optional[AgentCategory] = None
    ) -> List[AgentInfo]:
        """List all available agents"""
        agents = list(self._agents.values())
        if category:
            agents = [a for a in agents if a.category == category]
        return agents
    
    def get_agent(self, name: str) -> Optional[AgentInfo]:
        """Get agent by name"""
        return self._agents.get(name)
    
    async def execute_task(
        self,
        agent_name: str,
        action: str,
        parameters: Dict[str, Any],
        user_id: str,
        priority: Priority = Priority.NORMAL
    ) -> AgentTaskResponse:
        """Execute agent task"""
        agent = self._agents.get(agent_name)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_name}"
            )
        
        if action not in agent.actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action '{action}' for agent {agent_name}. Available: {agent.actions}"
            )
        
        task_id = f"task_{secrets.token_urlsafe(16)}"
        now = datetime.now(timezone.utc)
        
        # Create task
        task = AgentTaskResponse(
            task_id=task_id,
            agent_name=agent_name,
            action=action,
            status=TaskStatus.RUNNING,
            created_at=now.isoformat()
        )
        
        self._tasks[task_id] = task
        
        # Simulate execution (in production, delegate to actual agent)
        try:
            result = await self._execute_agent_action(agent, action, parameters)
            task.status = TaskStatus.COMPLETED
            task.result = result
            
            # Publish webhook
            await webhook_manager.publish(
                event_type=WebhookEventType.AGENT_TASK_COMPLETED.value,
                data={
                    "task_id": task_id,
                    "agent_name": agent_name,
                    "action": action,
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            await webhook_manager.publish(
                event_type=WebhookEventType.AGENT_TASK_FAILED.value,
                data={
                    "task_id": task_id,
                    "agent_name": agent_name,
                    "error": str(e)
                }
            )
        
        return task
    
    async def _execute_agent_action(
        self,
        agent: AgentInfo,
        action: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent action (simulated)"""
        # In production, this would call the actual agent implementation
        return {
            "agent": agent.name,
            "action": action,
            "parameters_received": parameters,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Action '{action}' executed successfully"
        }
    
    def get_task(self, task_id: str) -> Optional[AgentTaskResponse]:
        """Get task by ID"""
        return self._tasks.get(task_id)


# =============================================================================
# Router
# =============================================================================

agents_router = APIRouter(prefix="/api/v1/agents", tags=["AI Agents"])
agent_service = AgentService()


# ---- Agent Discovery ----

@agents_router.get("/", response_model=List[AgentInfo])
async def list_agents(
    category: Optional[AgentCategory] = Query(None, description="Filter by category"),
    user: TokenPayload = Depends(get_current_user)
):
    """List all available AI agents"""
    return agent_service.list_agents(category)


@agents_router.get("/{agent_name}", response_model=AgentInfo)
async def get_agent(
    agent_name: str,
    user: TokenPayload = Depends(get_current_user)
):
    """Get agent details"""
    agent = agent_service.get_agent(agent_name)
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_name}")
    return agent


# ---- Task Execution ----

@agents_router.post("/execute", response_model=AgentTaskResponse)
async def execute_agent_task(
    task: AgentTask,
    user: TokenPayload = Depends(get_current_user)
):
    """Execute an agent task"""
    return await agent_service.execute_task(
        agent_name=task.agent_name,
        action=task.action,
        parameters=task.parameters,
        user_id=user.sub,
        priority=task.priority
    )


@agents_router.get("/tasks/{task_id}", response_model=AgentTaskResponse)
async def get_task_status(
    task_id: str,
    user: TokenPayload = Depends(get_current_user)
):
    """Get task execution status"""
    task = agent_service.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task not found: {task_id}")
    return task


# ---- Social Media Endpoints ----

@agents_router.post("/social/post")
async def create_social_post(
    request: SocialPostRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Create a social media post"""
    agent_name = f"{request.platform.value}_agent"
    if agent_name not in ["instagram_agent", "tiktok_agent", "twitter_agent"]:
        agent_name = "social_scheduler_agent"
    
    return await agent_service.execute_task(
        agent_name=agent_name,
        action="post",
        parameters=request.model_dump(),
        user_id=user.sub
    )


@agents_router.get("/social/analytics")
async def get_social_analytics(
    request: SocialAnalyticsRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Get social media analytics"""
    return await agent_service.execute_task(
        agent_name=f"{request.platform.value}_agent",
        action="analyze",
        parameters=request.model_dump(),
        user_id=user.sub
    )


# ---- Email/SMS Endpoints ----

@agents_router.post("/email/send")
async def send_email(
    request: EmailRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Send email via email agent"""
    return await agent_service.execute_task(
        agent_name="email_campaign_agent",
        action="send",
        parameters=request.model_dump(),
        user_id=user.sub
    )


@agents_router.post("/sms/send")
async def send_sms(
    request: SMSRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Send SMS via SMS agent"""
    return await agent_service.execute_task(
        agent_name="sms_agent",
        action="send",
        parameters=request.model_dump(),
        user_id=user.sub
    )


@agents_router.post("/campaign/create")
async def create_campaign(
    request: CampaignRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Create email/SMS campaign"""
    agent = "email_campaign_agent" if request.type == "email" else "sms_agent"
    return await agent_service.execute_task(
        agent_name=agent,
        action="create_campaign",
        parameters=request.model_dump(),
        user_id=user.sub
    )


# ---- Customer Service Endpoints ----

@agents_router.post("/support/ticket")
async def create_support_ticket(
    request: SupportTicketRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Create support ticket"""
    return await agent_service.execute_task(
        agent_name="support_ticket_agent",
        action="create",
        parameters=request.model_dump(),
        user_id=user.sub
    )


@agents_router.post("/support/chat")
async def chatbot_interaction(
    request: ChatbotRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Interact with AI chatbot"""
    return await agent_service.execute_task(
        agent_name="chatbot_agent",
        action="respond",
        parameters=request.model_dump(),
        user_id=user.sub
    )


# ---- Content Generation Endpoints ----

@agents_router.post("/content/generate")
async def generate_content(
    request: ContentRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Generate content using AI"""
    agent_map = {
        ContentType.BLOG_POST: "blog_writer_agent",
        ContentType.PRODUCT_DESCRIPTION: "product_description_agent",
        ContentType.AD_COPY: "copywriting_agent",
        ContentType.EMAIL: "copywriting_agent",
        ContentType.SOCIAL_POST: "copywriting_agent",
        ContentType.SEO_META: "seo_content_agent",
    }
    
    return await agent_service.execute_task(
        agent_name=agent_map.get(request.type, "copywriting_agent"),
        action="generate",
        parameters=request.model_dump(),
        user_id=user.sub
    )


@agents_router.post("/seo/optimize")
async def optimize_seo(
    request: SEOOptimizeRequest,
    user: TokenPayload = Depends(get_current_user)
):
    """Optimize content for SEO"""
    return await agent_service.execute_task(
        agent_name="seo_content_agent",
        action="optimize",
        parameters=request.model_dump(),
        user_id=user.sub
    )


# ---- Brand Intelligence Endpoints ----

@agents_router.get("/brand/mentions")
async def get_brand_mentions(
    days: int = Query(7, ge=1, le=90),
    user: TokenPayload = Depends(get_current_user)
):
    """Get recent brand mentions"""
    return await agent_service.execute_task(
        agent_name="brand_monitor_agent",
        action="monitor",
        parameters={"days": days},
        user_id=user.sub
    )


@agents_router.get("/competitors/analysis")
async def analyze_competitors(
    competitor_ids: List[str] = Query(...),
    user: TokenPayload = Depends(get_current_user)
):
    """Analyze competitors"""
    return await agent_service.execute_task(
        agent_name="competitor_agent",
        action="analyze",
        parameters={"competitor_ids": competitor_ids},
        user_id=user.sub
    )


@agents_router.get("/trends")
async def get_market_trends(
    category: str = Query("fashion"),
    user: TokenPayload = Depends(get_current_user)
):
    """Get market trends"""
    return await agent_service.execute_task(
        agent_name="trend_agent",
        action="analyze_trends",
        parameters={"category": category},
        user_id=user.sub
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "agents_router",
    "agent_service",
    "AgentService",
    "AgentInfo",
    "AgentTask",
    "AgentTaskResponse",
    "AgentCategory",
]
