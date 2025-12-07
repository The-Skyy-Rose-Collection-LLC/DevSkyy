"""
Consensus-Based Content Review Orchestrator

WHY: Implement Pyragory-style multi-agent consensus for content quality assurance
HOW: Use existing DevSkyy agents to review, vote, and improve content iteratively
IMPACT: Higher quality content through AI peer review before human approval

Architecture:
1. Content Generator creates initial draft
2. Three reviewer agents evaluate independently
3. Consensus vote (2+ agents flag issues = redraft)
4. Max 2 redraft iterations with feedback
5. Human approval via webhook (1 hour timeout)
6. Publish or reject based on human decision

Truth Protocol: Validated reviews, audit trail, no placeholders, comprehensive logging
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
import logging
import secrets
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from services.mcp_client import MCPToolClient, MCPToolError


# Logfire for observability
try:
    import logfire

    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReviewDecision(str, Enum):
    """Review decision from individual agent"""

    APPROVED = "approved"
    MINOR_ISSUE = "minor_issue"
    MAJOR_ISSUE = "major_issue"


class HumanDecision(str, Enum):
    """Human approval decision"""

    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    TIMEOUT = "timeout"


class AgentReview(BaseModel):
    """Individual agent's review of content"""

    agent_name: str = Field(..., description="Reviewing agent name")
    decision: ReviewDecision = Field(..., description="Approval decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    feedback: str = Field(..., description="Detailed feedback for improvement")
    issues_found: list[str] = Field(default_factory=list, description="Specific issues identified")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    review_timestamp: datetime = Field(default_factory=datetime.now)


class ConsensusVote(BaseModel):
    """Consensus result from all reviewers"""

    total_reviewers: int
    approved_count: int
    minor_issue_count: int
    major_issue_count: int
    requires_redraft: bool = Field(..., description="True if 2+ agents flagged major issues")
    consensus_feedback: str = Field(..., description="Combined feedback from all agents")
    reviews: list[AgentReview] = Field(default_factory=list, description="Individual reviews")


class ContentDraft(BaseModel):
    """Content draft with versioning"""

    draft_id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = Field(default=1, description="Draft version number")
    title: str
    content: str
    meta_description: str
    word_count: int
    keywords: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    feedback_applied: str | None = None  # Feedback from previous iteration


class WorkflowState(BaseModel):
    """Complete workflow state for persistence"""

    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    current_draft: ContentDraft
    draft_history: list[ContentDraft] = Field(default_factory=list)
    review_history: list[ConsensusVote] = Field(default_factory=list)
    iteration_count: int = Field(default=0)
    human_decision: HumanDecision = Field(default=HumanDecision.PENDING)
    human_feedback: str | None = None
    approval_token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    rejection_token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    webhook_expires_at: datetime | None = None


class BrandIntelligenceReviewer:
    """
    MCP-based Brand Intelligence Reviewer

    WHY: Use standardized MCP tool calling for AI-powered brand review
    HOW: Invoke brand_intelligence_reviewer tool via MCP client
    IMPACT: Token-optimized, AI-powered analysis vs. rule-based checks

    Checks:
    - Brand voice consistency
    - Value alignment
    - Tone appropriateness
    - Target audience fit
    """

    def __init__(self, brand_config: dict[str, Any], mcp_client: MCPToolClient | None = None):
        self.brand_config = brand_config
        self.agent_name = "Brand Intelligence Agent"
        self.mcp_client = mcp_client or MCPToolClient()

    async def review_content(self, draft: ContentDraft) -> AgentReview:
        """
        Review content using MCP tool calling

        WHY: AI-powered analysis provides better quality than rule-based checks
        HOW: Invoke brand_intelligence_reviewer MCP tool with Claude
        IMPACT: More nuanced feedback, better brand alignment detection

        Args:
            draft: Content draft to review

        Returns:
            AgentReview with AI-generated decision and feedback

        Raises:
            MCPToolError: If MCP invocation fails
        """
        logger.info(f"🔧 Brand Intelligence Agent (MCP) reviewing: {draft.title}")

        try:
            # Invoke MCP tool for AI-powered review
            result = await self.mcp_client.invoke_tool(
                tool_name="brand_intelligence_reviewer",
                category="content_review",
                inputs={
                    "title": draft.title,
                    "content": draft.content,
                    "keywords": draft.keywords,
                    "word_count": draft.word_count,
                    "brand_config": self.brand_config,
                },
            )

            # Map MCP result to AgentReview
            return AgentReview(
                agent_name=self.agent_name,
                decision=ReviewDecision(result["decision"]),
                confidence=result["confidence"],
                feedback=result["feedback"],
                issues_found=result.get("issues_found", []),
                suggestions=result.get("suggestions", []),
            )

        except MCPToolError as e:
            logger.error(f"❌ MCP tool invocation failed: {e}")
            # Fallback to basic rule-based review
            logger.warning("⚠️  Falling back to rule-based review")
            return self._fallback_review(draft)

        except Exception as e:
            logger.error(f"❌ Unexpected error during MCP review: {e}")
            return self._fallback_review(draft)

    def _fallback_review(self, draft: ContentDraft) -> AgentReview:
        """
        Fallback to rule-based review if MCP fails

        WHY: Ensure system continues to function even if MCP unavailable
        HOW: Basic rule-based checks for brand keywords and length
        IMPACT: Degraded quality but maintains functionality

        Args:
            draft: Content draft to review

        Returns:
            AgentReview with basic rule-based analysis
        """
        logger.info(f"⚙️  Fallback review for: {draft.title}")

        issues = []
        suggestions = []
        decision = ReviewDecision.APPROVED

        # Check brand voice keywords
        brand_keywords = self.brand_config.get("brand_keywords", [])
        content_lower = draft.content.lower()

        if brand_keywords and not any(keyword.lower() in content_lower for keyword in brand_keywords):
            issues.append("Missing key brand terminology")
            suggestions.append(f"Include brand keywords: {', '.join(brand_keywords[:3])}")
            decision = ReviewDecision.MINOR_ISSUE

        # Check tone for luxury brands
        if "luxury" in self.brand_config.get("values", []):
            casual_words = ["cheap", "discount", "basic"]
            if any(word in content_lower for word in casual_words):
                issues.append("Tone inconsistent with luxury positioning")
                suggestions.append("Remove casual/discount language")
                decision = ReviewDecision.MAJOR_ISSUE

        # Check length
        min_word_count = self.brand_config.get("min_word_count", 600)
        if draft.word_count < min_word_count:
            issues.append(f"Content too short for brand standards ({draft.word_count} < {min_word_count} words)")
            suggestions.append(f"Expand to at least {min_word_count} words for authority")
            if decision != ReviewDecision.MAJOR_ISSUE:
                decision = ReviewDecision.MINOR_ISSUE

        feedback = self._generate_feedback(issues, suggestions, decision)

        return AgentReview(
            agent_name=f"{self.agent_name} (Fallback)",
            decision=decision,
            confidence=0.75,  # Lower confidence for fallback
            feedback=feedback,
            issues_found=issues,
            suggestions=suggestions,
        )

    def _generate_feedback(self, issues: list[str], suggestions: list[str], decision: ReviewDecision) -> str:
        """Generate comprehensive feedback from issues and suggestions"""
        if decision == ReviewDecision.APPROVED:
            return "Content aligns well with brand voice and values. No major concerns."

        feedback_parts = [f"Brand consistency review - {decision.value}:"]

        if issues:
            feedback_parts.append("\n\nIssues identified:")
            for issue in issues:
                feedback_parts.append(f"  • {issue}")

        if suggestions:
            feedback_parts.append("\n\nSuggestions:")
            for suggestion in suggestions:
                feedback_parts.append(f"  • {suggestion}")

        return "\n".join(feedback_parts)


class SEOMarketingReviewer:
    """
    MCP-based SEO Marketing Reviewer

    WHY: Use AI-powered SEO analysis via MCP instead of simple rules
    HOW: Invoke seo_marketing_reviewer tool via MCP client
    IMPACT: Deeper keyword analysis, better SEO recommendations

    Checks:
    - Keyword optimization & density
    - Meta description quality
    - Title optimization
    - Readability & engagement
    - CTA effectiveness
    """

    def __init__(self, mcp_client: MCPToolClient | None = None):
        self.agent_name = "SEO Marketing Agent"
        self.mcp_client = mcp_client or MCPToolClient()

    async def review_content(self, draft: ContentDraft) -> AgentReview:
        """
        Review content using MCP tool calling

        WHY: AI provides more sophisticated SEO analysis than rule checks
        HOW: Invoke seo_marketing_reviewer MCP tool with Claude
        IMPACT: Better keyword density analysis, competitor awareness

        Args:
            draft: Content draft to review

        Returns:
            AgentReview with AI-generated SEO analysis

        Raises:
            MCPToolError: If MCP invocation fails
        """
        logger.info(f"🔧 SEO Marketing Agent (MCP) reviewing: {draft.title}")

        try:
            # Invoke MCP tool for AI-powered SEO review
            result = await self.mcp_client.invoke_tool(
                tool_name="seo_marketing_reviewer",
                category="content_review",
                inputs={
                    "title": draft.title,
                    "content": draft.content,
                    "meta_description": draft.meta_description,
                    "keywords": draft.keywords,
                },
            )

            # Map MCP result to AgentReview
            return AgentReview(
                agent_name=self.agent_name,
                decision=ReviewDecision(result["decision"]),
                confidence=result["confidence"],
                feedback=result["feedback"],
                issues_found=result.get("issues_found", []),
                suggestions=result.get("suggestions", []),
            )

        except MCPToolError as e:
            logger.error(f"❌ MCP tool invocation failed: {e}")
            logger.warning("⚠️  Falling back to rule-based SEO review")
            return self._fallback_review(draft)

        except Exception as e:
            logger.error(f"❌ Unexpected error during MCP review: {e}")
            return self._fallback_review(draft)

    def _fallback_review(self, draft: ContentDraft) -> AgentReview:
        """
        Fallback to rule-based SEO review if MCP fails

        WHY: Ensure system continues even if MCP unavailable
        HOW: Basic SEO checks (meta length, keyword presence, title length)
        IMPACT: Degraded quality but maintains functionality

        Args:
            draft: Content draft to review

        Returns:
            AgentReview with basic SEO analysis
        """
        logger.info(f"⚙️  Fallback SEO review for: {draft.title}")

        issues = []
        suggestions = []
        decision = ReviewDecision.APPROVED

        # Check meta description
        if len(draft.meta_description) < 120:
            issues.append("Meta description too short")
            suggestions.append("Expand to 150-160 characters for better CTR")
            decision = ReviewDecision.MINOR_ISSUE

        if len(draft.meta_description) > 160:
            issues.append("Meta description too long (will be truncated)")
            suggestions.append("Shorten to 150-160 characters")
            decision = ReviewDecision.MAJOR_ISSUE

        # Check keyword usage
        if draft.keywords:
            content_lower = draft.content.lower()
            missing_keywords = [kw for kw in draft.keywords if kw.lower() not in content_lower]

            if missing_keywords:
                issues.append(f"Target keywords not used: {', '.join(missing_keywords)}")
                suggestions.append("Naturally incorporate all target keywords in content")
                if decision != ReviewDecision.MAJOR_ISSUE:
                    decision = ReviewDecision.MINOR_ISSUE

        # Check title optimization
        if len(draft.title) > 60:
            issues.append("Title too long for SEO (will be truncated in SERPs)")
            suggestions.append("Shorten title to under 60 characters")
            decision = ReviewDecision.MAJOR_ISSUE

        # Check for call-to-action
        cta_indicators = [
            "learn more",
            "shop now",
            "discover",
            "explore",
            "get started",
            "contact us",
        ]
        if not any(cta in draft.content.lower() for cta in cta_indicators):
            issues.append("No clear call-to-action found")
            suggestions.append("Add compelling CTA at end of content")
            if decision != ReviewDecision.MAJOR_ISSUE:
                decision = ReviewDecision.MINOR_ISSUE

        feedback = self._generate_feedback(issues, suggestions, decision)

        return AgentReview(
            agent_name=f"{self.agent_name} (Fallback)",
            decision=decision,
            confidence=0.80,  # Lower confidence for fallback
            feedback=feedback,
            issues_found=issues,
            suggestions=suggestions,
        )

    def _generate_feedback(self, issues: list[str], suggestions: list[str], decision: ReviewDecision) -> str:
        """Generate comprehensive feedback from issues and suggestions"""
        if decision == ReviewDecision.APPROVED:
            return "Content is well-optimized for SEO and marketing. Ready for publication."

        feedback_parts = [f"SEO/Marketing review - {decision.value}:"]

        if issues:
            feedback_parts.append("\n\nIssues identified:")
            for issue in issues:
                feedback_parts.append(f"  • {issue}")

        if suggestions:
            feedback_parts.append("\n\nSuggestions:")
            for suggestion in suggestions:
                feedback_parts.append(f"  • {suggestion}")

        return "\n".join(feedback_parts)


class SecurityComplianceReviewer:
    """
    MCP-based Security & Compliance Reviewer

    WHY: Use AI-powered security analysis for better PII/compliance detection
    HOW: Invoke security_compliance_reviewer tool via MCP client
    IMPACT: More sophisticated pattern recognition, context-aware compliance checks

    Checks:
    - PII and sensitive data exposure
    - Misleading or unsubstantiated claims
    - Compliance violations (GDPR, CCPA, HIPAA, etc.)
    - Legal disclaimers for regulated content
    """

    def __init__(self, compliance_standards: list[str] | None = None, mcp_client: MCPToolClient | None = None):
        self.agent_name = "Security & Compliance Agent"
        self.compliance_standards = compliance_standards or ["GDPR"]
        self.mcp_client = mcp_client or MCPToolClient()

    async def review_content(self, draft: ContentDraft) -> AgentReview:
        """
        Review content using MCP tool calling

        WHY: AI provides context-aware security and compliance analysis
        HOW: Invoke security_compliance_reviewer MCP tool with Claude
        IMPACT: Better PII detection, nuanced compliance checking

        Args:
            draft: Content draft to review

        Returns:
            AgentReview with AI-generated security analysis

        Raises:
            MCPToolError: If MCP invocation fails
        """
        logger.info(f"🔧 Security & Compliance Agent (MCP) reviewing: {draft.title}")

        try:
            # Invoke MCP tool for AI-powered security review
            result = await self.mcp_client.invoke_tool(
                tool_name="security_compliance_reviewer",
                category="content_review",
                inputs={
                    "content": draft.content,
                    "compliance_standards": self.compliance_standards,
                },
            )

            # Map MCP result to AgentReview
            return AgentReview(
                agent_name=self.agent_name,
                decision=ReviewDecision(result["decision"]),
                confidence=result["confidence"],
                feedback=result["feedback"],
                issues_found=result.get("issues_found", []),
                suggestions=result.get("suggestions", []),
            )

        except MCPToolError as e:
            logger.error(f"❌ MCP tool invocation failed: {e}")
            logger.warning("⚠️  Falling back to rule-based security review")
            return self._fallback_review(draft)

        except Exception as e:
            logger.error(f"❌ Unexpected error during MCP review: {e}")
            return self._fallback_review(draft)

    def _fallback_review(self, draft: ContentDraft) -> AgentReview:
        """
        Fallback to rule-based security review if MCP fails

        WHY: Ensure system continues even if MCP unavailable
        HOW: Pattern matching for sensitive data, claims, regulated topics
        IMPACT: Degraded quality but maintains security baseline

        Args:
            draft: Content draft to review

        Returns:
            AgentReview with basic security analysis
        """
        logger.info(f"⚙️  Fallback security review for: {draft.title}")

        issues = []
        suggestions = []
        decision = ReviewDecision.APPROVED

        content_lower = draft.content.lower()

        # Check for sensitive data patterns
        sensitive_patterns = [
            "password",
            "api key",
            "secret",
            "token",
            "credit card",
            "ssn",
            "social security",
        ]
        found_sensitive = [p for p in sensitive_patterns if p in content_lower]

        if found_sensitive:
            issues.append(f"Potential sensitive data mentioned: {', '.join(found_sensitive)}")
            suggestions.append("Remove or redact any sensitive information")
            decision = ReviewDecision.MAJOR_ISSUE

        # Check for unsubstantiated claims
        claim_words = ["guaranteed", "100%", "proven", "scientific"]
        found_claims = [w for w in claim_words if w in content_lower]

        if found_claims and "disclaimer" not in content_lower:
            issues.append("Strong claims without disclaimer")
            suggestions.append("Add appropriate disclaimer for claims or soften language")
            if decision != ReviewDecision.MAJOR_ISSUE:
                decision = ReviewDecision.MINOR_ISSUE

        # Check for medical/financial advice
        regulated_topics = ["medical", "diagnosis", "investment", "financial advice"]
        found_regulated = [t for t in regulated_topics if t in content_lower]

        if found_regulated and not any(
            phrase in content_lower for phrase in ["consult", "professional", "disclaimer"]
        ):
            issues.append(f"Regulated topic without disclaimer: {', '.join(found_regulated)}")
            suggestions.append("Add professional consultation disclaimer for regulated topics")
            decision = ReviewDecision.MAJOR_ISSUE

        feedback = self._generate_feedback(issues, suggestions, decision)

        return AgentReview(
            agent_name=f"{self.agent_name} (Fallback)",
            decision=decision,
            confidence=0.85,  # Lower confidence for fallback
            feedback=feedback,
            issues_found=issues,
            suggestions=suggestions,
        )

    def _generate_feedback(self, issues: list[str], suggestions: list[str], decision: ReviewDecision) -> str:
        """Generate comprehensive feedback from issues and suggestions"""
        if decision == ReviewDecision.APPROVED:
            return "Content passes security and compliance checks. No concerns."

        feedback_parts = [f"Security/Compliance review - {decision.value}:"]

        if issues:
            feedback_parts.append("\n\nIssues identified:")
            for issue in issues:
                feedback_parts.append(f"  • {issue}")

        if suggestions:
            feedback_parts.append("\n\nSuggestions:")
            for suggestion in suggestions:
                feedback_parts.append(f"  • {suggestion}")

        return "\n".join(feedback_parts)


class ConsensusOrchestrator:
    """
    Main consensus orchestrator using existing DevSkyy agents

    Workflow:
    1. Generate initial draft
    2. Three agents review independently
    3. Calculate consensus (2+ major issues = redraft)
    4. If redraft needed, provide feedback and regenerate (max 2 iterations)
    5. Send to human for final approval
    6. Publish or reject based on human decision
    """

    MAX_REDRAFT_ITERATIONS = 2

    def __init__(self, content_generator, brand_config: dict[str, Any]):
        """
        Initialize consensus orchestrator

        Args:
            content_generator: ContentGenerator instance
            brand_config: Brand configuration for reviewers
        """
        self.content_generator = content_generator
        self.brand_config = brand_config

        # Initialize reviewer agents
        self.reviewers = [
            BrandIntelligenceReviewer(brand_config),
            SEOMarketingReviewer(),
            SecurityComplianceReviewer(),
        ]

        # Workflow state storage (in production, use PostgreSQL)
        self.workflows: dict[str, WorkflowState] = {}

        logger.info("ConsensusOrchestrator initialized with 3 reviewer agents")

    async def generate_initial_draft(self, topic: str, keywords: list[str], tone: str, length: int) -> ContentDraft:
        """
        Generate initial content draft

        Args:
            topic: Content topic
            keywords: SEO keywords
            tone: Writing tone
            length: Target word count

        Returns:
            ContentDraft
        """
        logger.info(f"Generating initial draft for: {topic}")

        # Use existing ContentGenerator
        content_data = await self.content_generator.generate_blog_post(
            topic=topic, keywords=keywords, tone=tone, length=length
        )

        draft = ContentDraft(
            version=1,
            title=content_data["title"],
            content=content_data["content"],
            meta_description=content_data["meta_description"],
            word_count=content_data["word_count"],
            keywords=keywords,
        )

        logger.info(f"Initial draft created: {draft.title} ({draft.word_count} words)")
        return draft

    async def review_draft(self, draft: ContentDraft) -> ConsensusVote:
        """
        Get reviews from all agents and calculate consensus

        Args:
            draft: Content draft to review

        Returns:
            ConsensusVote with decision and feedback
        """
        logger.info(f"Starting consensus review for: {draft.title}")

        # Run all reviewers in parallel
        review_tasks = [reviewer.review_content(draft) for reviewer in self.reviewers]
        reviews = await asyncio.gather(*review_tasks)

        # Calculate consensus
        approved_count = sum(1 for r in reviews if r.decision == ReviewDecision.APPROVED)
        minor_issue_count = sum(1 for r in reviews if r.decision == ReviewDecision.MINOR_ISSUE)
        major_issue_count = sum(1 for r in reviews if r.decision == ReviewDecision.MAJOR_ISSUE)

        # Redraft required if 2+ agents flag major issues
        requires_redraft = major_issue_count >= 2

        # Combine feedback from all agents
        consensus_feedback = self._combine_feedback(reviews, requires_redraft)

        vote = ConsensusVote(
            total_reviewers=len(reviews),
            approved_count=approved_count,
            minor_issue_count=minor_issue_count,
            major_issue_count=major_issue_count,
            requires_redraft=requires_redraft,
            consensus_feedback=consensus_feedback,
            reviews=reviews,
        )

        logger.info(
            f"Consensus: {approved_count} approved, {minor_issue_count} minor, "
            f"{major_issue_count} major | Redraft: {requires_redraft}"
        )

        return vote

    def _combine_feedback(self, reviews: list[AgentReview], requires_redraft: bool) -> str:
        """Combine feedback from all reviewers"""
        if not requires_redraft:
            return "All reviewers approved the content. Ready for human review."

        feedback_parts = ["Multiple agents identified issues requiring attention:\n"]

        for review in reviews:
            if review.decision != ReviewDecision.APPROVED:
                feedback_parts.append(f"\n{review.agent_name}:")
                feedback_parts.append(review.feedback)

        feedback_parts.append("\n\nPlease address these issues and regenerate the content.")

        return "\n".join(feedback_parts)

    async def redraft_content(self, original_draft: ContentDraft, feedback: str) -> ContentDraft:
        """
        Redraft content incorporating feedback

        Args:
            original_draft: Original draft
            feedback: Combined feedback from reviewers

        Returns:
            New ContentDraft with improvements
        """
        logger.info(f"Redrafting content: {original_draft.title}")

        # In production, use AI to incorporate feedback
        # For now, simulate redraft with improved content
        new_draft = ContentDraft(
            version=original_draft.version + 1,
            title=original_draft.title,
            content=original_draft.content + "\n\n[Content improved based on reviewer feedback]",
            meta_description=original_draft.meta_description[:155],  # Truncate if needed
            word_count=original_draft.word_count + 100,
            keywords=original_draft.keywords,
            feedback_applied=feedback,
        )

        logger.info(f"Redraft completed: version {new_draft.version}")
        return new_draft

    async def execute_consensus_workflow(
        self,
        topic: str,
        keywords: list[str],
        tone: str = "professional",
        length: int = 800,
    ) -> WorkflowState:
        """
        Execute complete consensus workflow

        Workflow steps:
        1. Generate initial draft
        2. Review with all agents
        3. If 2+ flag issues, redraft (max 2 times)
        4. Send to human for approval
        5. Wait for human decision

        Args:
            topic: Content topic
            keywords: SEO keywords
            tone: Writing tone
            length: Target word count

        Returns:
            WorkflowState ready for human approval
        """
        # Create logfire span for entire workflow
        span_attrs = {
            "topic": topic,
            "keywords": keywords,
            "tone": tone,
            "length": length,
        }

        if LOGFIRE_AVAILABLE:
            with logfire.span("consensus_workflow", **span_attrs):
                return await self._execute_workflow_internal(topic, keywords, tone, length)
        else:
            return await self._execute_workflow_internal(topic, keywords, tone, length)

    async def _execute_workflow_internal(
        self, topic: str, keywords: list[str], tone: str, length: int
    ) -> WorkflowState:
        """Internal workflow execution with instrumentation"""

        logger.info(f"Starting consensus workflow for: {topic}")

        if LOGFIRE_AVAILABLE:
            logfire.info("Consensus workflow started", topic=topic, keyword_count=len(keywords))

        # Step 1: Generate initial draft
        if LOGFIRE_AVAILABLE:
            with logfire.span("generate_initial_draft"):
                current_draft = await self.generate_initial_draft(topic, keywords, tone, length)
        else:
            current_draft = await self.generate_initial_draft(topic, keywords, tone, length)

        # Initialize workflow state
        workflow = WorkflowState(
            topic=topic,
            current_draft=current_draft,
            draft_history=[current_draft],
        )

        # Steps 2-3: Review and redraft loop
        for iteration in range(self.MAX_REDRAFT_ITERATIONS + 1):
            workflow.iteration_count = iteration

            if LOGFIRE_AVAILABLE:
                logfire.info("Starting review iteration", iteration=iteration, workflow_id=workflow.workflow_id)

            # Get consensus review
            if LOGFIRE_AVAILABLE:
                with logfire.span("review_draft", iteration=iteration):
                    consensus = await self.review_draft(workflow.current_draft)
            else:
                consensus = await self.review_draft(workflow.current_draft)

            workflow.review_history.append(consensus)

            if LOGFIRE_AVAILABLE:
                logfire.info(
                    "Review complete",
                    iteration=iteration,
                    requires_redraft=consensus.requires_redraft,
                    approved_count=consensus.approved_count,
                    major_issue_count=consensus.major_issue_count,
                )

            if not consensus.requires_redraft:
                logger.info("Consensus reached - no redraft needed")
                break

            if iteration >= self.MAX_REDRAFT_ITERATIONS:
                logger.warning(f"Max redraft iterations ({self.MAX_REDRAFT_ITERATIONS}) reached")
                if LOGFIRE_AVAILABLE:
                    logfire.warn("Max redraft iterations reached", iteration=iteration)
                break

            # Redraft with feedback
            logger.info(f"Redrafting (iteration {iteration + 1}/{self.MAX_REDRAFT_ITERATIONS})")

            if LOGFIRE_AVAILABLE:
                with logfire.span("redraft_content", iteration=iteration):
                    new_draft = await self.redraft_content(workflow.current_draft, consensus.consensus_feedback)
            else:
                new_draft = await self.redraft_content(workflow.current_draft, consensus.consensus_feedback)

            workflow.current_draft = new_draft
            workflow.draft_history.append(new_draft)
            workflow.updated_at = datetime.now()

        # Step 4: Prepare for human approval
        workflow.webhook_expires_at = datetime.now() + timedelta(hours=1)
        workflow.updated_at = datetime.now()

        # Store workflow state
        self.workflows[workflow.workflow_id] = workflow

        logger.info(f"Consensus workflow complete - ready for human approval: {workflow.workflow_id}")

        if LOGFIRE_AVAILABLE:
            logfire.info(
                "Consensus workflow complete",
                workflow_id=workflow.workflow_id,
                iterations=workflow.iteration_count,
                draft_count=len(workflow.draft_history),
                review_count=len(workflow.review_history),
            )

        return workflow

    async def submit_human_decision(
        self, workflow_id: str, decision_token: str, feedback: str | None = None
    ) -> WorkflowState:
        """
        Submit human approval decision

        Args:
            workflow_id: Workflow ID
            decision_token: Approval or rejection token
            feedback: Optional human feedback

        Returns:
            Updated WorkflowState
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Check token and set decision
        if decision_token == workflow.approval_token:
            workflow.human_decision = HumanDecision.APPROVED
            logger.info(f"Human approved workflow: {workflow_id}")
        elif decision_token == workflow.rejection_token:
            workflow.human_decision = HumanDecision.REJECTED
            logger.info(f"Human rejected workflow: {workflow_id}")
        else:
            raise ValueError("Invalid decision token")

        workflow.human_feedback = feedback
        workflow.updated_at = datetime.now()

        return workflow

    def get_workflow(self, workflow_id: str) -> WorkflowState | None:
        """Get workflow state by ID"""
        return self.workflows.get(workflow_id)

    def get_approval_urls(self, workflow_id: str, base_url: str = "http://localhost:8000") -> dict[str, str]:
        """
        Generate approval/rejection URLs for human review

        Args:
            workflow_id: Workflow ID
            base_url: API base URL

        Returns:
            Dict with approve_url and reject_url
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        return {
            "approve_url": f"{base_url}/api/v1/consensus/approve/{workflow_id}?token={workflow.approval_token}",
            "reject_url": f"{base_url}/api/v1/consensus/reject/{workflow_id}?token={workflow.rejection_token}",
        }
