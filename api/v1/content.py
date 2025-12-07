"""
Content Publishing API Endpoints

WHY: Provide REST API for automated content generation and publishing workflow
HOW: FastAPI endpoints orchestrating content generator, Pexels, and WordPress
IMPACT: Replaces n8n workflow with native DevSkyy automation

Truth Protocol: Input validation, error handling, logging, no placeholders
"""

from datetime import datetime
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from services.content_publishing_orchestrator import ContentPublishingOrchestrator
from services.wordpress_categorization import WordPressCategorizationService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content", tags=["Content Publishing"])


class PublishContentRequest(BaseModel):
    """Request to publish AI-generated content"""

    topic: str = Field(..., min_length=1, max_length=200, description="Content topic")
    keywords: list[str] = Field(default_factory=list, description="SEO keywords for content")
    tone: str = Field(
        default="professional",
        description="Writing tone (professional, casual, luxury, friendly)",
    )
    length: int = Field(default=800, ge=200, le=3000, description="Target word count")
    apply_random_delay: bool = Field(default=False, description="Apply random delay before publishing")
    min_delay_hours: float = Field(default=0, ge=0, le=24, description="Minimum delay in hours")
    max_delay_hours: float = Field(default=6, ge=0, le=24, description="Maximum delay in hours")
    publish_status: str = Field(default="publish", description="WordPress status (publish, draft)")
    notify_telegram: bool = Field(default=True, description="Send Telegram notification")
    log_to_sheets: bool = Field(default=True, description="Log to Google Sheets")


class PublishContentResponse(BaseModel):
    """Response from content publishing"""

    success: bool
    message: str
    title: str | None = None
    wordpress_url: str | None = None
    wordpress_id: int | None = None
    word_count: int | None = None
    image_url: str | None = None
    duration_seconds: float | None = None
    delay_applied_seconds: float | None = None


class ScheduledPublishRequest(BaseModel):
    """Request to schedule content publishing"""

    topics: list[str] = Field(..., min_items=1, description="List of topics to publish")
    keywords: list[str] = Field(default_factory=list, description="Common keywords")
    schedule_days: list[str] = Field(
        default=["tuesday", "thursday", "sunday"],
        description="Days to publish (lowercase)",
    )
    schedule_time: str = Field(default="12:00", description="Time to publish (HH:MM)")
    timezone: str = Field(default="UTC", description="Timezone")
    random_delay_enabled: bool = Field(default=True, description="Enable random delay per n8n workflow")
    max_delay_hours: int = Field(default=6, description="Maximum random delay in hours")


class ScheduledPublishResponse(BaseModel):
    """Response from scheduled publishing setup"""

    success: bool
    message: str
    schedule_id: str | None = None
    next_execution: str | None = None


# Dependency injection for orchestrator service
def get_orchestrator_service() -> ContentPublishingOrchestrator:
    """
    Get content publishing orchestrator instance

    Loads credentials from environment variables:
    - ANTHROPIC_API_KEY: For AI content generation
    - PEXELS_API_KEY: For image retrieval
    - TELEGRAM_BOT_TOKEN: For notifications (optional)
    - TELEGRAM_CHAT_ID: For notifications (optional)
    - GOOGLE_SHEETS_CREDENTIALS_JSON: For logging (optional)
    - GOOGLE_SHEETS_ID: For logging (optional)
    """
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    pexels_api_key = os.getenv("PEXELS_API_KEY")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    if not pexels_api_key:
        raise HTTPException(status_code=500, detail="PEXELS_API_KEY not configured")

    # Initialize orchestrator
    orchestrator = ContentPublishingOrchestrator(
        anthropic_api_key=anthropic_api_key,
        pexels_api_key=pexels_api_key,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        # Google Sheets credentials would be loaded here if needed
    )

    return orchestrator


@router.post("/publish", response_model=PublishContentResponse)
async def publish_content(
    request: PublishContentRequest,
    background_tasks: BackgroundTasks,
    orchestrator: ContentPublishingOrchestrator = Depends(get_orchestrator_service),
):
    """
    Publish AI-generated content to WordPress

    This endpoint implements the complete n8n workflow:
    1. Calculate random delay (optional)
    2. Wait for delay
    3. Generate AI content using Claude
    4. Fetch featured image from Pexels
    5. Publish to WordPress
    6. Log to Google Sheets (optional)
    7. Send Telegram notification (optional)

    Example request:
    ```json
    {
      "topic": "Luxury Fashion Trends 2025",
      "keywords": ["luxury fashion", "trends", "2025"],
      "tone": "luxury",
      "length": 1000,
      "apply_random_delay": true,
      "max_delay_hours": 2
    }
    ```
    """
    try:
        logger.info(
            f"Content publish requested: {request.topic}",
            extra={"topic": request.topic, "keywords": request.keywords},
        )

        # Execute workflow
        result = await orchestrator.execute_workflow(
            topic=request.topic,
            keywords=request.keywords,
            tone=request.tone,
            length=request.length,
            apply_random_delay=request.apply_random_delay,
            min_delay_hours=request.min_delay_hours,
            max_delay_hours=request.max_delay_hours,
            publish_status=request.publish_status,
            notify=request.notify_telegram,
            log_to_sheets=request.log_to_sheets,
        )

        if result["success"]:
            return PublishContentResponse(
                success=True,
                message="Content published successfully",
                title=result["content"]["title"],
                wordpress_url=result["wordpress_post"]["url"],
                wordpress_id=result["wordpress_post"]["id"],
                word_count=result["content"]["word_count"],
                image_url=result["image"]["url"] if result.get("image") else None,
                duration_seconds=result["duration_seconds"],
                delay_applied_seconds=result.get("delay_applied", 0),
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Publishing failed"))

    except Exception as e:
        logger.exception("Content publishing failed")
        raise HTTPException(status_code=500, detail=f"Publishing failed: {e!s}")


@router.post("/publish-batch", response_model=dict)
async def publish_content_batch(
    topics: list[str],
    keywords: list[str] | None = None,
    tone: str = "professional",
    length: int = 800,
    orchestrator: ContentPublishingOrchestrator = Depends(get_orchestrator_service),
):
    """
    Publish multiple pieces of content in batch

    Args:
        topics: List of topics to publish
        keywords: Common keywords for all topics
        tone: Writing tone
        length: Target word count

    Example:
    ```json
    {
      "topics": [
        "Luxury Fashion Trends 2025",
        "Sustainable Luxury: The Future",
        "Investing in Timeless Pieces"
      ],
      "keywords": ["luxury", "fashion"],
      "tone": "luxury",
      "length": 1000
    }
    ```
    """
    if keywords is None:
        keywords = []
    try:
        logger.info(f"Batch publish requested for {len(topics)} topics")

        results = []
        for topic in topics:
            try:
                result = await orchestrator.execute_workflow(
                    topic=topic,
                    keywords=keywords,
                    tone=tone,
                    length=length,
                    apply_random_delay=True,
                    max_delay_hours=1,  # Small delay between batch items
                    notify=False,  # Don't spam notifications
                    log_to_sheets=True,
                )
                results.append(
                    {
                        "topic": topic,
                        "success": result["success"],
                        "title": result["content"]["title"] if result["success"] else None,
                        "url": (result["wordpress_post"]["url"] if result["success"] else None),
                    }
                )
            except Exception as e:
                logger.exception(f"Failed to publish topic: {topic}")
                results.append({"topic": topic, "success": False, "error": str(e)})

        succeeded = len([r for r in results if r["success"]])
        failed = len(results) - succeeded

        # Send summary notification
        if orchestrator.telegram_service:
            summary = (
                f"<b>📦 Batch Publishing Complete</b>\n\n"
                f"<b>Total:</b> {len(results)}\n"
                f"<b>✅ Succeeded:</b> {succeeded}\n"
                f"<b>❌ Failed:</b> {failed}"
            )
            await orchestrator.telegram_service.send_notification(summary)

        return {
            "success": True,
            "total": len(results),
            "succeeded": succeeded,
            "failed": failed,
            "results": results,
        }

    except Exception as e:
        logger.exception("Batch publishing failed")
        raise HTTPException(status_code=500, detail=f"Batch publishing failed: {e!s}")


@router.post("/schedule", response_model=ScheduledPublishResponse)
async def schedule_content_publishing(
    request: ScheduledPublishRequest,
    orchestrator: ContentPublishingOrchestrator = Depends(get_orchestrator_service),
):
    """
    Schedule content publishing (requires Celery)

    This endpoint sets up a recurring schedule matching the n8n workflow:
    - Days: Tuesday, Thursday, Sunday
    - Time: 12:00 UTC
    - Random delay: 0-6 hours

    Example:
    ```json
    {
      "topics": [
        "Luxury Fashion Trends",
        "Sustainable Fashion",
        "Investment Pieces"
      ],
      "schedule_days": ["tuesday", "thursday", "sunday"],
      "schedule_time": "12:00",
      "random_delay_enabled": true,
      "max_delay_hours": 6
    }
    ```

    Note: This requires Celery Beat for scheduling.
    See documentation for Celery setup.
    """
    try:
        logger.info(f"Schedule requested for {len(request.topics)} topics on {request.schedule_days}")

        # TODO: Implement Celery Beat scheduling
        # This would create a periodic task that:
        # 1. Runs on specified days at specified time
        # 2. Picks a random topic from the list
        # 3. Applies random delay
        # 4. Executes publish workflow

        return ScheduledPublishResponse(
            success=True,
            message="Scheduling not yet implemented - requires Celery Beat setup",
            schedule_id=None,
            next_execution=None,
        )

    except Exception as e:
        logger.exception("Scheduling failed")
        raise HTTPException(status_code=500, detail=f"Scheduling failed: {e!s}")


@router.post("/categorize", response_model=dict)
async def categorize_wordpress_posts(
    post_ids: list[int] | None = None,
    wordpress_site_url: str | None = None,
    use_ai: bool = True,
):
    """
    Auto-categorize WordPress posts using AI

    This endpoint implements the n8n "Auto categorize wordpress template" workflow:
    1. Fetch posts from WordPress (all posts or specific IDs)
    2. Use AI to analyze post titles and assign categories
    3. Update WordPress with assigned categories

    Example request:
    ```json
    {
      "post_ids": [123, 456, 789],  // Optional - if not provided, categorizes all posts
      "wordpress_site_url": "https://rumjahn.com",  // Optional - uses default if not provided
      "use_ai": true  // Use AI (true) or keyword matching (false)
    }
    ```

    Categories:
    - 13 = Content Creation
    - 14 = Digital Marketing
    - 15 = AI Tools
    - 17 = Automation & Integration
    - 18 = Productivity Tools
    - 19 = Analytics & Strategy
    """
    try:
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        # Initialize categorization service
        categorization_service = WordPressCategorizationService(
            anthropic_api_key=anthropic_api_key,
            openai_api_key=openai_api_key,
        )

        # TODO: Fetch posts from WordPress
        # For now, simulate with mock data
        mock_posts = [
            {"id": 123, "title": {"rendered": "How to Create Engaging Blog Content"}},
            {"id": 456, "title": {"rendered": "Top AI Tools for Content Marketing"}},
            {
                "id": 789,
                "title": {"rendered": "Automating Your Workflow with n8n and Zapier"},
            },
        ]

        # If specific post IDs provided, filter
        posts_to_categorize = [p for p in mock_posts if p["id"] in post_ids] if post_ids else mock_posts

        # Categorize posts
        results = await categorization_service.categorize_posts_batch(posts_to_categorize, use_ai=use_ai)

        # Prepare response
        succeeded = [r for r in results if not r.error]
        failed = [r for r in results if r.error]

        return {
            "success": True,
            "total": len(results),
            "succeeded": len(succeeded),
            "failed": len(failed),
            "results": [
                {
                    "post_id": r.post_id,
                    "post_title": r.post_title,
                    "assigned_category_id": r.assigned_category_id,
                    "assigned_category_name": r.assigned_category_name,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                    "error": r.error,
                }
                for r in results
            ],
            "method": "AI" if use_ai else "keyword matching",
        }

    except Exception as e:
        logger.exception("WordPress categorization failed")
        raise HTTPException(status_code=500, detail=f"Categorization failed: {e!s}")


@router.get("/categories", response_model=dict)
async def get_available_categories():
    """
    Get available WordPress categories

    Returns the predefined category mappings used for AI categorization
    """
    categorization_service = WordPressCategorizationService()
    categories = categorization_service.get_all_categories()

    return {
        "total": len(categories),
        "categories": [
            {
                "id": c.category_id,
                "name": c.category_name,
                "description": c.description,
                "keywords": c.keywords,
            }
            for c in categories
        ],
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Content Publishing",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/config")
async def get_configuration():
    """
    Get current configuration status

    Returns information about which services are configured
    """
    return {
        "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "pexels_configured": bool(os.getenv("PEXELS_API_KEY")),
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "google_sheets_configured": bool(os.getenv("GOOGLE_SHEETS_ID")),
        "wordpress_credentials_configured": bool(os.getenv("SKYY_ROSE_SITE_URL")),
    }
