"""
Unit Tests for Consensus Orchestrator

Tests the ConsensusOrchestrator and reviewer classes for multi-agent
content review and consensus-based workflows.

Truth Protocol Compliance:
- Rule #8: Test Coverage ≥90%
- Rule #9: Document All
- Rule #10: No-Skip Rule
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.consensus_orchestrator import (
    AgentReview,
    BrandIntelligenceReviewer,
    ConsensusOrchestrator,
    ConsensusVote,
    ContentDraft,
    HumanDecision,
    ReviewDecision,
    SecurityComplianceReviewer,
    SEOMarketingReviewer,
    WorkflowState,
)


# =============================================================================
# ReviewDecision Enum Tests
# =============================================================================


class TestReviewDecision:
    """Tests for ReviewDecision enum."""

    def test_decision_values(self):
        """Test review decision values."""
        assert ReviewDecision.APPROVED.value == "approved"
        assert ReviewDecision.MINOR_ISSUE.value == "minor_issue"
        assert ReviewDecision.MAJOR_ISSUE.value == "major_issue"


# =============================================================================
# HumanDecision Enum Tests
# =============================================================================


class TestHumanDecision:
    """Tests for HumanDecision enum."""

    def test_decision_values(self):
        """Test human decision values."""
        assert HumanDecision.APPROVED.value == "approved"
        assert HumanDecision.REJECTED.value == "rejected"
        assert HumanDecision.PENDING.value == "pending"
        assert HumanDecision.TIMEOUT.value == "timeout"


# =============================================================================
# AgentReview Model Tests
# =============================================================================


class TestAgentReview:
    """Tests for AgentReview model."""

    def test_create_review(self):
        """Test creating an agent review."""
        review = AgentReview(
            agent_name="Brand Agent",
            decision=ReviewDecision.APPROVED,
            confidence=0.95,
            feedback="Content looks great!"
        )

        assert review.agent_name == "Brand Agent"
        assert review.decision == ReviewDecision.APPROVED
        assert review.confidence == 0.95
        assert review.issues_found == []
        assert review.suggestions == []

    def test_review_with_issues(self):
        """Test review with issues and suggestions."""
        review = AgentReview(
            agent_name="SEO Agent",
            decision=ReviewDecision.MINOR_ISSUE,
            confidence=0.8,
            feedback="Some SEO issues found",
            issues_found=["Missing meta keywords", "Title too long"],
            suggestions=["Add target keywords", "Shorten title"]
        )

        assert len(review.issues_found) == 2
        assert len(review.suggestions) == 2

    def test_review_has_timestamp(self):
        """Test that review has timestamp."""
        review = AgentReview(
            agent_name="Test",
            decision=ReviewDecision.APPROVED,
            confidence=0.9,
            feedback="OK"
        )

        assert isinstance(review.review_timestamp, datetime)


# =============================================================================
# ConsensusVote Model Tests
# =============================================================================


class TestConsensusVote:
    """Tests for ConsensusVote model."""

    def test_create_vote(self):
        """Test creating a consensus vote."""
        vote = ConsensusVote(
            total_reviewers=3,
            approved_count=2,
            minor_issue_count=1,
            major_issue_count=0,
            requires_redraft=False,
            consensus_feedback="Content approved by majority"
        )

        assert vote.total_reviewers == 3
        assert vote.approved_count == 2
        assert vote.requires_redraft is False

    def test_vote_requires_redraft(self):
        """Test vote that requires redraft."""
        vote = ConsensusVote(
            total_reviewers=3,
            approved_count=0,
            minor_issue_count=1,
            major_issue_count=2,
            requires_redraft=True,
            consensus_feedback="Multiple major issues found"
        )

        assert vote.requires_redraft is True


# =============================================================================
# ContentDraft Model Tests
# =============================================================================


class TestContentDraft:
    """Tests for ContentDraft model."""

    def test_create_draft(self):
        """Test creating a content draft."""
        draft = ContentDraft(
            title="Test Article",
            content="This is the content",
            meta_description="Description here",
            word_count=500,
            keywords=["test", "article"]
        )

        assert draft.title == "Test Article"
        assert draft.version == 1
        assert draft.draft_id is not None
        assert len(draft.keywords) == 2

    def test_draft_versioning(self):
        """Test draft version defaults and updates."""
        draft = ContentDraft(
            title="V1",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        assert draft.version == 1
        assert draft.feedback_applied is None


# =============================================================================
# WorkflowState Model Tests
# =============================================================================


class TestWorkflowState:
    """Tests for WorkflowState model."""

    def test_create_workflow(self):
        """Test creating a workflow state."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        workflow = WorkflowState(
            topic="Test Topic",
            current_draft=draft
        )

        assert workflow.workflow_id is not None
        assert workflow.topic == "Test Topic"
        assert workflow.human_decision == HumanDecision.PENDING
        assert workflow.iteration_count == 0
        assert workflow.approval_token is not None
        assert workflow.rejection_token is not None

    def test_workflow_tokens_different(self):
        """Test that approval and rejection tokens are different."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        workflow = WorkflowState(topic="Test", current_draft=draft)

        assert workflow.approval_token != workflow.rejection_token


# =============================================================================
# BrandIntelligenceReviewer Tests
# =============================================================================


class TestBrandIntelligenceReviewer:
    """Tests for BrandIntelligenceReviewer."""

    @pytest.fixture
    def brand_config(self):
        """Create brand config for testing."""
        return {
            "brand_keywords": ["luxury", "exclusive", "premium"],
            "values": ["luxury", "quality"],
            "min_word_count": 600
        }

    @pytest.fixture
    def reviewer(self, brand_config):
        """Create reviewer instance."""
        mock_client = MagicMock()
        return BrandIntelligenceReviewer(brand_config, mcp_client=mock_client)

    @pytest.mark.asyncio
    async def test_fallback_review_approved(self, reviewer):
        """Test fallback review approves good content."""
        draft = ContentDraft(
            title="Luxury Collection Launch",
            content="Discover our exclusive luxury collection featuring premium materials.",
            meta_description="Exclusive collection",
            word_count=700,
            keywords=["luxury"]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.APPROVED
        assert "Brand Intelligence Agent" in review.agent_name

    @pytest.mark.asyncio
    async def test_fallback_review_missing_keywords(self, reviewer):
        """Test fallback review detects missing keywords."""
        draft = ContentDraft(
            title="Product Launch",
            content="This is a regular product announcement.",
            meta_description="Product info",
            word_count=700,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.MINOR_ISSUE
        assert any("brand" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_inappropriate_tone(self, reviewer):
        """Test fallback review detects inappropriate tone."""
        draft = ContentDraft(
            title="Cheap Sale",
            content="Get our cheap discount items at basic prices.",
            meta_description="Discount sale",
            word_count=700,
            keywords=["luxury"]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("tone" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_too_short(self, reviewer):
        """Test fallback review detects short content."""
        draft = ContentDraft(
            title="Short Post",
            content="This is luxury content but too short.",
            meta_description="Short",
            word_count=100,
            keywords=["luxury"]
        )

        review = reviewer._fallback_review(draft)

        assert any("short" in issue.lower() for issue in review.issues_found)


# =============================================================================
# SEOMarketingReviewer Tests
# =============================================================================


class TestSEOMarketingReviewer:
    """Tests for SEOMarketingReviewer."""

    @pytest.fixture
    def reviewer(self):
        """Create reviewer instance."""
        mock_client = MagicMock()
        return SEOMarketingReviewer(mcp_client=mock_client)

    @pytest.mark.asyncio
    async def test_fallback_review_approved(self, reviewer):
        """Test fallback review approves good SEO content."""
        draft = ContentDraft(
            title="Short SEO Title",
            content="Learn more about our products and discover the best options.",
            meta_description="This is a well-crafted meta description of appropriate length for SEO.",
            word_count=500,
            keywords=["products", "options"]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.APPROVED

    @pytest.mark.asyncio
    async def test_fallback_review_meta_too_short(self, reviewer):
        """Test fallback review detects short meta description."""
        draft = ContentDraft(
            title="Test Title",
            content="Some content here",
            meta_description="Too short",
            word_count=500,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert any("meta description" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_meta_too_long(self, reviewer):
        """Test fallback review detects long meta description."""
        draft = ContentDraft(
            title="Test Title",
            content="Some content here",
            meta_description="x" * 200,  # Too long
            word_count=500,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("meta description" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_missing_keywords(self, reviewer):
        """Test fallback review detects missing keywords."""
        draft = ContentDraft(
            title="Test Title",
            content="Some generic content",
            meta_description="This is a meta description of proper length for testing purposes.",
            word_count=500,
            keywords=["specific", "keyword"]
        )

        review = reviewer._fallback_review(draft)

        assert any("keyword" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_title_too_long(self, reviewer):
        """Test fallback review detects long title."""
        draft = ContentDraft(
            title="This is an extremely long title that will definitely be truncated in search engine results pages",
            content="Some content here",
            meta_description="This is a meta description of proper length for testing purposes.",
            word_count=500,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("title" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_no_cta(self, reviewer):
        """Test fallback review detects missing CTA."""
        draft = ContentDraft(
            title="Short Title",
            content="This content has no call to action whatsoever.",
            meta_description="This is a meta description of proper length for testing purposes.",
            word_count=500,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert any("call-to-action" in issue.lower() or "cta" in issue.lower() for issue in review.issues_found)


# =============================================================================
# SecurityComplianceReviewer Tests
# =============================================================================


class TestSecurityComplianceReviewer:
    """Tests for SecurityComplianceReviewer."""

    @pytest.fixture
    def reviewer(self):
        """Create reviewer instance."""
        mock_client = MagicMock()
        return SecurityComplianceReviewer(mcp_client=mock_client)

    @pytest.mark.asyncio
    async def test_fallback_review_approved(self, reviewer):
        """Test fallback review approves safe content."""
        draft = ContentDraft(
            title="Safe Content",
            content="This is perfectly safe content with no issues.",
            meta_description="Safe meta",
            word_count=500,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.APPROVED

    @pytest.mark.asyncio
    async def test_fallback_review_sensitive_data(self, reviewer):
        """Test fallback review detects sensitive data."""
        draft = ContentDraft(
            title="Test",
            content="Use password: admin123 and api key ABC123",
            meta_description="Test meta",
            word_count=100,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("sensitive" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_unsubstantiated_claims(self, reviewer):
        """Test fallback review detects unsubstantiated claims."""
        draft = ContentDraft(
            title="Amazing Product",
            content="This product is 100% guaranteed to work and is scientifically proven.",
            meta_description="Amazing product",
            word_count=100,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert any("claim" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_medical_advice(self, reviewer):
        """Test fallback review detects unqualified medical advice."""
        draft = ContentDraft(
            title="Health Tips",
            content="This product can help with medical diagnosis of conditions.",
            meta_description="Health tips",
            word_count=100,
            keywords=[]
        )

        review = reviewer._fallback_review(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("regulated" in issue.lower() or "medical" in issue.lower() for issue in review.issues_found)


# =============================================================================
# ConsensusOrchestrator Tests
# =============================================================================


class TestConsensusOrchestrator:
    """Tests for ConsensusOrchestrator."""

    @pytest.fixture
    def mock_content_generator(self):
        """Create mock content generator."""
        generator = MagicMock()
        generator.generate_blog_post = AsyncMock(return_value={
            "title": "Test Blog Post",
            "content": "This is the test content for the blog post.",
            "meta_description": "Test description",
            "word_count": 500
        })
        return generator

    @pytest.fixture
    def orchestrator(self, mock_content_generator):
        """Create orchestrator instance."""
        brand_config = {
            "brand_keywords": ["luxury", "premium"],
            "values": ["quality"],
            "min_word_count": 500
        }
        return ConsensusOrchestrator(mock_content_generator, brand_config)

    @pytest.mark.asyncio
    async def test_generate_initial_draft(self, orchestrator):
        """Test generating initial draft."""
        draft = await orchestrator.generate_initial_draft(
            topic="Test Topic",
            keywords=["test", "keyword"],
            tone="professional",
            length=800
        )

        assert draft.title == "Test Blog Post"
        assert draft.version == 1
        assert draft.keywords == ["test", "keyword"]

    @pytest.mark.asyncio
    async def test_review_draft(self, orchestrator):
        """Test reviewing a draft."""
        draft = ContentDraft(
            title="Test Article",
            content="This is luxury content with premium quality. Learn more about our products.",
            meta_description="This is a meta description of appropriate length for SEO purposes.",
            word_count=600,
            keywords=["luxury"]
        )

        vote = await orchestrator.review_draft(draft)

        assert vote.total_reviewers == 3
        assert vote.approved_count + vote.minor_issue_count + vote.major_issue_count == 3

    @pytest.mark.asyncio
    async def test_review_draft_consensus_calculation(self, orchestrator):
        """Test consensus calculation."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta" * 20,  # Appropriate length
            word_count=600,
            keywords=[]
        )

        vote = await orchestrator.review_draft(draft)

        # Requires redraft if 2+ major issues
        expected_redraft = vote.major_issue_count >= 2
        assert vote.requires_redraft == expected_redraft

    @pytest.mark.asyncio
    async def test_redraft_content(self, orchestrator):
        """Test redrafting content."""
        original = ContentDraft(
            title="Original",
            content="Original content",
            meta_description="Original meta description for testing",
            word_count=500,
            keywords=[]
        )

        new_draft = await orchestrator.redraft_content(
            original,
            "Please improve SEO and add keywords"
        )

        assert new_draft.version == 2
        assert new_draft.feedback_applied is not None

    @pytest.mark.asyncio
    async def test_submit_human_decision_approve(self, orchestrator):
        """Test submitting human approval."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        updated = await orchestrator.submit_human_decision(
            workflow.workflow_id,
            workflow.approval_token,
            feedback="Looks good!"
        )

        assert updated.human_decision == HumanDecision.APPROVED
        assert updated.human_feedback == "Looks good!"

    @pytest.mark.asyncio
    async def test_submit_human_decision_reject(self, orchestrator):
        """Test submitting human rejection."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        updated = await orchestrator.submit_human_decision(
            workflow.workflow_id,
            workflow.rejection_token
        )

        assert updated.human_decision == HumanDecision.REJECTED

    @pytest.mark.asyncio
    async def test_submit_human_decision_invalid_token(self, orchestrator):
        """Test submitting with invalid token."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        with pytest.raises(ValueError, match="Invalid decision token"):
            await orchestrator.submit_human_decision(
                workflow.workflow_id,
                "invalid-token"
            )

    @pytest.mark.asyncio
    async def test_submit_human_decision_workflow_not_found(self, orchestrator):
        """Test submitting decision for nonexistent workflow."""
        with pytest.raises(ValueError, match="Workflow not found"):
            await orchestrator.submit_human_decision(
                "nonexistent-id",
                "some-token"
            )

    def test_get_workflow(self, orchestrator):
        """Test getting a workflow."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        retrieved = orchestrator.get_workflow(workflow.workflow_id)

        assert retrieved is not None
        assert retrieved.workflow_id == workflow.workflow_id

    def test_get_workflow_not_found(self, orchestrator):
        """Test getting nonexistent workflow."""
        retrieved = orchestrator.get_workflow("nonexistent")
        assert retrieved is None

    def test_get_approval_urls(self, orchestrator):
        """Test getting approval URLs."""
        draft = ContentDraft(
            title="Test",
            content="Content",
            meta_description="Meta",
            word_count=100
        )

        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        urls = orchestrator.get_approval_urls(workflow.workflow_id)

        assert "approve_url" in urls
        assert "reject_url" in urls
        assert workflow.approval_token in urls["approve_url"]
        assert workflow.rejection_token in urls["reject_url"]

    def test_get_approval_urls_not_found(self, orchestrator):
        """Test getting URLs for nonexistent workflow."""
        with pytest.raises(ValueError, match="Workflow not found"):
            orchestrator.get_approval_urls("nonexistent")

    def test_combine_feedback_approved(self, orchestrator):
        """Test combining feedback when approved."""
        reviews = [
            AgentReview(
                agent_name="Agent1",
                decision=ReviewDecision.APPROVED,
                confidence=0.9,
                feedback="Looks good"
            ),
            AgentReview(
                agent_name="Agent2",
                decision=ReviewDecision.APPROVED,
                confidence=0.95,
                feedback="Perfect"
            )
        ]

        feedback = orchestrator._combine_feedback(reviews, requires_redraft=False)

        assert "approved" in feedback.lower()

    def test_combine_feedback_redraft(self, orchestrator):
        """Test combining feedback when redraft needed."""
        reviews = [
            AgentReview(
                agent_name="Agent1",
                decision=ReviewDecision.MAJOR_ISSUE,
                confidence=0.8,
                feedback="Major problems found"
            ),
            AgentReview(
                agent_name="Agent2",
                decision=ReviewDecision.MAJOR_ISSUE,
                confidence=0.85,
                feedback="Needs significant changes"
            )
        ]

        feedback = orchestrator._combine_feedback(reviews, requires_redraft=True)

        assert "issues" in feedback.lower()
        assert "Major problems" in feedback
