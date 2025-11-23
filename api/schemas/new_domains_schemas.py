"""
Pydantic Request/Response Models for New Business Domains
Comprehensive validation and serialization schemas

Author: DevSkyy Platform Team
Version: 1.0.0
Python: >=3.11
"""

from datetime import datetime
import re
from typing import Any

from pydantic import BaseModel, EmailStr, Field, validator
from pydantic.types import confloat, constr


# Import security validators
def validate_no_sql_injection(value: str) -> str:
    """Validate against SQL injection patterns"""
    if not isinstance(value, str):
        return value

    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, value.upper()):
            raise ValueError("Potential SQL injection detected")

    return value


def validate_no_xss(value: str) -> str:
    """Validate against XSS patterns"""
    if not isinstance(value, str):
        return value

    xss_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]

    for pattern in xss_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError("Potential XSS detected")

    return value


# ============================================================================
# SOCIAL MEDIA SCHEMAS
# ============================================================================


class SocialPostCreateRequest(BaseModel):
    """Create social media post"""

    content: constr(min_length=1, max_length=5000) = Field(..., description="Post content")
    platforms: list[str] = Field(..., description="Target platforms")
    media_urls: list[str] | None = Field(None, description="Media attachments")
    scheduled_for: datetime | None = Field(None, description="Schedule post")
    hashtags: list[str] | None = Field(None, description="Hashtags")
    mentions: list[str] | None = Field(None, description="User mentions")
    location: str | None = Field(None, max_length=200)
    ai_optimize: bool = Field(default=True, description="AI optimization")

    @validator("platforms")
    def validate_platforms(cls, v):
        valid = ["facebook", "instagram", "twitter", "linkedin", "tiktok", "pinterest"]
        for platform in v:
            if platform.lower() not in valid:
                raise ValueError(f"Invalid platform: {platform}")
        return [p.lower() for p in v]

    @validator("content")
    def validate_content(cls, v):
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        return v


class SocialPostAnalytics(BaseModel):
    """Post engagement analytics"""

    total_views: int = 0
    total_likes: int = 0
    total_shares: int = 0
    total_comments: int = 0
    engagement_rate: float = 0.0
    platform_breakdown: dict[str, dict[str, int]]
    best_performing_platform: str | None = None
    sentiment_score: float | None = None


class SocialPostCreateResponse(BaseModel):
    """Response from post creation"""

    success: bool
    post_id: str
    status: str
    platform_results: dict[str, dict[str, Any]]
    scheduled_for: datetime | None = None
    ai_optimizations: dict[str, str] | None = None
    analytics_url: str | None = None
    created_at: datetime
    error_message: str | None = None


class SocialScheduleRequest(BaseModel):
    """Schedule social media posts"""

    posts: list[SocialPostCreateRequest] = Field(..., min_items=1, max_items=50)
    optimization_strategy: str = Field(default="ai_optimal")
    timezone: str = Field(default="UTC")
    date_range_start: datetime
    date_range_end: datetime
    frequency: str = Field(default="daily")

    @validator("optimization_strategy")
    def validate_strategy(cls, v):
        valid = ["ai_optimal", "manual", "peak_hours", "consistent"]
        if v not in valid:
            raise ValueError(f"Invalid strategy. Valid: {valid}")
        return v


class SocialPlatformConnectRequest(BaseModel):
    """Connect social platform"""

    platform: str
    credentials: dict[str, str] = Field(..., description="Encrypted credentials")
    account_id: str | None = None
    permissions: list[str] = Field(default=["read", "write"])
    webhook_url: str | None = None


class SocialCampaignRequest(BaseModel):
    """Social media campaign"""

    name: constr(min_length=1, max_length=200)
    objective: str
    platforms: list[str]
    content_plan: list[dict[str, Any]]
    target_audience: dict[str, Any]
    budget: float | None = Field(None, gt=0)
    start_date: datetime
    end_date: datetime
    hashtags: list[str] = Field(default=[])
    tracking_urls: dict[str, str] | None = None
    ai_optimization: bool = Field(default=True)

    @validator("objective")
    def validate_objective(cls, v):
        valid = ["awareness", "engagement", "conversion", "traffic", "brand_building"]
        if v not in valid:
            raise ValueError(f"Invalid objective. Valid: {valid}")
        return v


# ============================================================================
# EMAIL MARKETING SCHEMAS
# ============================================================================


class EmailCampaignRequest(BaseModel):
    """Email campaign creation"""

    name: constr(min_length=1, max_length=200)
    subject_line: constr(min_length=1, max_length=150)
    from_name: constr(min_length=1, max_length=100)
    from_email: EmailStr
    reply_to: EmailStr | None = None
    template_id: str | None = None
    content_html: str | None = None
    content_text: str | None = None
    mailing_lists: list[str] = Field(..., min_items=1)
    segment_filters: dict[str, Any] | None = None
    personalization_fields: list[str] | None = None
    scheduled_for: datetime | None = None
    ab_test_config: dict[str, Any] | None = None
    tracking_enabled: bool = Field(default=True)
    utm_parameters: dict[str, str] | None = None

    @validator("content_html")
    def validate_html_content(cls, v):
        if v:
            dangerous_patterns = [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
            ]
            for pattern in dangerous_patterns:
                if re.search(pattern, v, re.IGNORECASE):
                    raise ValueError("Unsafe HTML content detected")
        return v


class EmailCampaignAnalytics(BaseModel):
    """Email campaign analytics"""

    sent: int
    delivered: int
    bounced: int
    opened: int
    clicked: int
    unsubscribed: int
    spam_reported: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    click_to_open_rate: float
    unsubscribe_rate: float
    bounce_rate: float
    spam_rate: float
    engagement_score: float
    top_clicked_links: list[dict]
    geographic_breakdown: dict | None = None
    device_breakdown: dict | None = None


class EmailCampaignResponse(BaseModel):
    """Campaign creation response"""

    success: bool
    campaign_id: str
    name: str
    status: str
    total_recipients: int
    scheduled_for: datetime | None = None
    estimated_send_time: str | None = None
    preview_url: str
    created_at: datetime
    error_message: str | None = None


class EmailSendRequest(BaseModel):
    """Transactional email send"""

    to_email: EmailStr
    to_name: str | None = Field(None, max_length=100)
    subject: constr(min_length=1, max_length=150)
    from_email: EmailStr | None = None
    from_name: str | None = None
    template_id: str | None = None
    template_variables: dict[str, Any] | None = None
    content_html: str | None = None
    content_text: str | None = None
    attachments: list[dict] | None = Field(None, max_items=10)
    tags: list[str] | None = None
    tracking_enabled: bool = Field(default=False)
    priority: str = Field(default="normal")

    @validator("attachments")
    def validate_attachments(cls, v):
        if v:
            max_size = 10 * 1024 * 1024  # 10MB total
            total_size = sum(att.get("size", 0) for att in v)
            if total_size > max_size:
                raise ValueError(f"Total attachments size exceeds {max_size} bytes")
        return v


class EmailTemplateRequest(BaseModel):
    """Email template creation"""

    name: constr(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    subject_template: constr(min_length=1, max_length=150)
    html_template: str
    text_template: str | None = None
    template_variables: list[str]
    category: str | None = None
    is_active: bool = Field(default=True)
    preview_data: dict[str, str] | None = None


class MailingListRequest(BaseModel):
    """Mailing list creation"""

    name: constr(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    default_from_name: str = Field(..., max_length=100)
    default_from_email: EmailStr
    subscription_type: str = Field(default="double_opt_in")
    tags: list[str] | None = None
    custom_fields: list[dict] | None = None

    @validator("subscription_type")
    def validate_subscription_type(cls, v):
        valid = ["single_opt_in", "double_opt_in", "imported"]
        if v not in valid:
            raise ValueError(f"Invalid type. Valid: {valid}")
        return v


class SubscriberAddRequest(BaseModel):
    """Add subscriber to list"""

    email: EmailStr
    list_ids: list[str] = Field(..., min_items=1)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    custom_fields: dict[str, Any] | None = None
    tags: list[str] | None = None
    source: str | None = None
    confirmed: bool = Field(default=False)
    send_welcome_email: bool = Field(default=True)


class EmailAutomationRequest(BaseModel):
    """Email automation workflow"""

    name: constr(min_length=1, max_length=200)
    trigger_type: str
    trigger_config: dict[str, Any]
    email_sequence: list[dict[str, Any]] = Field(..., min_items=1, max_items=20)
    target_lists: list[str] | None = None
    segment_filters: dict[str, Any] | None = None
    is_active: bool = Field(default=True)

    @validator("trigger_type")
    def validate_trigger(cls, v):
        valid = [
            "subscriber_joined",
            "abandoned_cart",
            "birthday",
            "purchase_completed",
            "inactive_subscriber",
            "custom",
        ]
        if v not in valid:
            raise ValueError(f"Invalid trigger. Valid: {valid}")
        return v

    @validator("email_sequence")
    def validate_sequence(cls, v):
        for step in v:
            if "delay" not in step or "email_config" not in step:
                raise ValueError("Each step must have 'delay' and 'email_config'")
        return v


# ============================================================================
# CUSTOMER SERVICE SCHEMAS
# ============================================================================


class SupportTicketCreateRequest(BaseModel):
    """Create support ticket"""

    customer_email: EmailStr
    customer_name: str | None = Field(None, max_length=100)
    subject: constr(min_length=1, max_length=200)
    description: constr(min_length=1, max_length=10000)
    category: str
    priority: str = Field(default="medium")
    channel: str = Field(default="web")
    product_id: str | None = None
    order_id: str | None = None
    attachments: list[str] | None = Field(None, max_items=5)
    metadata: dict[str, Any] | None = None
    ai_categorization: bool = Field(default=True)

    @validator("category")
    def validate_category(cls, v):
        valid = ["technical", "billing", "general", "product", "account", "feedback"]
        if v not in valid:
            raise ValueError(f"Invalid category. Valid: {valid}")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        valid = ["low", "medium", "high", "urgent"]
        if v not in valid:
            raise ValueError(f"Invalid priority. Valid: {valid}")
        return v

    @validator("description")
    def validate_description(cls, v):
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        return v


class TicketAIInsights(BaseModel):
    """AI-generated insights"""

    sentiment: str
    sentiment_score: float
    urgency_score: float
    complexity_score: float
    suggested_category: str
    suggested_priority: str
    similar_tickets: list[str]
    suggested_responses: list[str]
    knowledge_base_articles: list[str]


class SupportTicketCreateResponse(BaseModel):
    """Ticket creation response"""

    success: bool
    ticket_id: str
    ticket_number: str
    status: str
    priority: str
    assigned_to: str | None = None
    ai_suggestions: dict[str, Any] | None = None
    estimated_resolution_time: str | None = None
    created_at: datetime


class SupportTicketUpdateRequest(BaseModel):
    """Update support ticket"""

    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    internal_notes: str | None = Field(None, max_length=5000)

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid = ["new", "open", "in_progress", "resolved", "closed", "on_hold"]
            if v not in valid:
                raise ValueError(f"Invalid status. Valid: {valid}")
        return v


class TicketResponseAddRequest(BaseModel):
    """Add response to ticket"""

    content: constr(min_length=1, max_length=10000)
    is_internal: bool = Field(default=False)
    attachments: list[str] | None = Field(None, max_items=5)
    send_email: bool = Field(default=True)
    auto_close: bool = Field(default=False)

    @validator("content")
    def validate_content(cls, v):
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        return v


class LiveChatStartRequest(BaseModel):
    """Start live chat session"""

    customer_email: EmailStr | None = None
    customer_name: str | None = Field(None, max_length=100)
    initial_message: constr(min_length=1, max_length=1000)
    department: str | None = None
    language: str = Field(default="en")
    metadata: dict[str, Any] | None = None
    enable_ai_assist: bool = Field(default=True)

    @validator("initial_message")
    def validate_message(cls, v):
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        return v


class KnowledgeBaseArticleRequest(BaseModel):
    """Create KB article"""

    title: constr(min_length=1, max_length=200)
    content: constr(min_length=1, max_length=50000)
    category: str
    subcategory: str | None = None
    tags: list[str] = Field(default=[])
    keywords: list[str] = Field(default=[])
    related_articles: list[str] | None = None
    is_published: bool = Field(default=False)
    visibility: str = Field(default="public")
    author_id: str | None = None

    @validator("content")
    def validate_content(cls, v):
        v = validate_no_sql_injection(v)
        return v

    @validator("visibility")
    def validate_visibility(cls, v):
        valid = ["public", "internal", "private"]
        if v not in valid:
            raise ValueError(f"Invalid visibility. Valid: {valid}")
        return v


class SupportAIAssistRequest(BaseModel):
    """AI assistance request"""

    context_type: str
    customer_message: constr(min_length=1, max_length=10000)
    ticket_history: list[dict] | None = None
    customer_data: dict[str, Any] | None = None
    product_context: dict[str, Any] | None = None
    suggestion_type: str = Field(default="response")
    tone: str = Field(default="professional")

    @validator("context_type")
    def validate_context(cls, v):
        valid = ["ticket", "chat", "email"]
        if v not in valid:
            raise ValueError(f"Invalid context. Valid: {valid}")
        return v

    @validator("customer_message")
    def validate_message(cls, v):
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        return v


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================


class PaymentProcessRequest(BaseModel):
    """Process payment"""

    amount: confloat(gt=0)
    currency: constr(min_length=3, max_length=3) = Field(default="USD")
    payment_method: str
    payment_details: dict[str, Any]
    customer_id: str | None = None
    order_id: str | None = None
    description: constr(max_length=500)
    metadata: dict[str, Any] | None = None
    idempotency_key: str

    @validator("payment_method")
    def validate_method(cls, v):
        valid = ["card", "bank_transfer", "paypal", "stripe", "square", "crypto"]
        if v not in valid:
            raise ValueError(f"Invalid method. Valid: {valid}")
        return v

    @validator("payment_details")
    def validate_details(cls, v):
        if "encrypted" not in v or not v["encrypted"]:
            raise ValueError("Payment details must be encrypted")
        return v


class PaymentProcessResponse(BaseModel):
    """Payment processing response"""

    success: bool
    transaction_id: str
    status: str
    amount: float
    currency: str
    payment_method: str
    receipt_url: str | None = None
    requires_action: bool = False
    action_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    processed_at: datetime


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================


class NotificationSendRequest(BaseModel):
    """Send notification"""

    recipient_id: str | None = None
    recipient_email: EmailStr | None = None
    channels: list[str] = Field(..., min_items=1)
    notification_type: str
    title: constr(min_length=1, max_length=200)
    message: constr(min_length=1, max_length=5000)
    action_url: str | None = None
    priority: str = Field(default="normal")
    scheduled_for: datetime | None = None
    metadata: dict[str, Any] | None = None

    @validator("channels")
    def validate_channels(cls, v):
        valid = ["email", "sms", "push", "webhook", "slack", "discord"]
        for channel in v:
            if channel not in valid:
                raise ValueError(f"Invalid channel: {channel}")
        return v


class NotificationSendResponse(BaseModel):
    """Notification send response"""

    success: bool
    notification_id: str
    status: str
    channel_results: dict[str, dict[str, Any]]
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None


# ============================================================================
# FILE STORAGE SCHEMAS
# ============================================================================


class FileUploadRequest(BaseModel):
    """File upload"""

    file_name: str = Field(..., max_length=255)
    file_type: str
    file_size: int = Field(..., gt=0)
    category: str = Field(default="general")
    visibility: str = Field(default="private")
    metadata: dict[str, Any] | None = None

    @validator("file_size")
    def validate_size(cls, v):
        max_size = 100 * 1024 * 1024  # 100MB
        if v > max_size:
            raise ValueError(f"File size exceeds maximum {max_size} bytes")
        return v


class FileUploadResponse(BaseModel):
    """File upload response"""

    success: bool
    file_id: str
    file_name: str
    file_url: str
    cdn_url: str | None = None
    file_size: int
    content_type: str
    uploaded_at: datetime
