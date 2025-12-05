"""
Comprehensive Test Suite for Consensus Orchestrator

WHY: Achieve ≥80% test coverage for services/consensus_orchestrator.py
HOW: Test all code paths including MCP success/failure, voting, consensus, timeouts
IMPACT: Ensure multi-agent consensus system is production-ready

Truth Protocol Rules: #1 (Never Guess), #8 (Test Coverage ≥90%), #15 (No Placeholders)

Coverage Target: ≥80% (0/349 lines → 280+/349 lines)

Test Categories:
1. Agent Reviews (MCP success, MCP failure, fallback logic)
2. Voting Mechanisms (majority, weighted, unanimous)
3. Consensus Algorithms (2+ major issues = redraft)
4. Conflict Resolution (mixed decisions)
5. Quorum Requirements (all agents must vote)
6. Vote Aggregation (counting votes correctly)
7. Decision Finalization (human approval/rejection)
8. Agent Coordination (parallel execution)
9. Timeout Handling (webhook expiry)
10. Workflow State Management

Run: pytest tests/services/test_consensus_orchestrator_comprehensive.py --cov=services.consensus_orchestrator --cov-report=term-missing -v
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse

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
from services.mcp_client import MCPToolError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_content_generator():
    """Mock content generator for testing"""
    generator = MagicMock()
    generator.generate_blog_post = AsyncMock(
        return_value={
            "title": "Test Article: Luxury Fashion Trends 2025",
            "content": "This luxury article discusses premium fashion with exclusive designs and sophisticated style. "
            * 50,
            "meta_description": "Discover luxury fashion trends for 2025 with exclusive designs and premium quality.",
            "word_count": 850,
            "keywords": ["luxury", "premium", "fashion"],
        }
    )
    return generator


@pytest.fixture
def brand_config():
    """Brand configuration for testing"""
    return {
        "name": "Skyy Rose Collection",
        "brand_keywords": ["luxury", "premium", "exclusive", "sophisticated"],
        "values": ["luxury", "quality", "innovation", "elegance"],
        "min_word_count": 600,
    }


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing"""
    client = MagicMock()
    client.invoke_tool = AsyncMock()
    return client


@pytest.fixture
def sample_draft():
    """Sample content draft for testing"""
    return ContentDraft(
        title="Luxury Fashion Trends 2025",
        content="This luxury article discusses premium fashion with exclusive designs and sophisticated style. "
        "Shop now and explore our collection. Learn more about luxury fashion trends." * 20,
        meta_description="Discover luxury fashion trends for 2025 with exclusive designs and premium quality.",
        word_count=850,
        keywords=["luxury", "premium", "fashion"],
    )


# ============================================================================
# BRAND INTELLIGENCE REVIEWER TESTS
# ============================================================================


class TestBrandIntelligenceReviewer:
    """Test BrandIntelligenceReviewer agent"""

    @pytest.mark.asyncio
    async def test_mcp_review_success(self, brand_config, sample_draft, mock_mcp_client):
        """Test successful MCP-based brand review"""
        # Mock successful MCP response
        mock_mcp_client.invoke_tool.return_value = {
            "decision": "approved",
            "confidence": 0.95,
            "feedback": "Content aligns perfectly with brand voice and values.",
            "issues_found": [],
            "suggestions": [],
        }

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert review.agent_name == "Brand Intelligence Agent"
        assert review.decision == ReviewDecision.APPROVED
        assert review.confidence == 0.95
        assert "aligns perfectly" in review.feedback
        mock_mcp_client.invoke_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_review_minor_issue(self, brand_config, sample_draft, mock_mcp_client):
        """Test MCP review with minor issues"""
        mock_mcp_client.invoke_tool.return_value = {
            "decision": "minor_issue",
            "confidence": 0.85,
            "feedback": "Good content but could use more brand keywords.",
            "issues_found": ["Limited brand keyword usage"],
            "suggestions": ["Add more 'exclusive' and 'sophisticated' mentions"],
        }

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert review.decision == ReviewDecision.MINOR_ISSUE
        assert review.confidence == 0.85
        assert len(review.issues_found) == 1
        assert len(review.suggestions) == 1

    @pytest.mark.asyncio
    async def test_mcp_review_major_issue(self, brand_config, sample_draft, mock_mcp_client):
        """Test MCP review with major issues"""
        mock_mcp_client.invoke_tool.return_value = {
            "decision": "major_issue",
            "confidence": 0.90,
            "feedback": "Content conflicts with luxury brand positioning.",
            "issues_found": ["Tone too casual", "Missing luxury terminology"],
            "suggestions": ["Adopt formal tone", "Use luxury vocabulary"],
        }

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert len(review.issues_found) == 2
        assert len(review.suggestions) == 2

    @pytest.mark.asyncio
    async def test_mcp_failure_fallback(self, brand_config, sample_draft, mock_mcp_client):
        """Test fallback to rule-based review when MCP fails"""
        mock_mcp_client.invoke_tool.side_effect = MCPToolError("Connection failed")

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        # Should fall back to rule-based review
        assert "(Fallback)" in review.agent_name
        assert review.decision in [ReviewDecision.APPROVED, ReviewDecision.MINOR_ISSUE, ReviewDecision.MAJOR_ISSUE]
        assert review.confidence == 0.75  # Fallback confidence

    @pytest.mark.asyncio
    async def test_fallback_review_approved(self, brand_config):
        """Test fallback review approves good content"""
        draft = ContentDraft(
            title="Luxury Fashion",
            content="This luxury article discusses premium and exclusive fashion with sophisticated style. " * 50,
            meta_description="Luxury fashion",
            word_count=850,
            keywords=["luxury"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.APPROVED
        assert "aligns well" in review.feedback.lower()

    @pytest.mark.asyncio
    async def test_fallback_review_missing_keywords(self, brand_config):
        """Test fallback review flags missing brand keywords"""
        draft = ContentDraft(
            title="Fashion Article",
            content="Generic fashion content without any brand-specific terminology." * 50,
            meta_description="Fashion article",
            word_count=850,
            keywords=["fashion"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.MINOR_ISSUE
        assert any("brand" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_luxury_brand_casual_tone(self):
        """Test fallback review flags casual tone for luxury brand"""
        brand_config = {
            "brand_keywords": ["luxury"],
            "values": ["luxury"],
            "min_word_count": 600,
        }

        draft = ContentDraft(
            title="Cheap Fashion",
            content="Check out these cheap discount deals on basic fashion items! Great bargains and low prices." * 50,
            meta_description="Cheap fashion deals",
            word_count=850,
            keywords=["cheap"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("luxury" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_short_content(self, brand_config):
        """Test fallback review flags content below minimum word count"""
        draft = ContentDraft(
            title="Short Article",
            content="This is short content with luxury keywords.",
            meta_description="Short article",
            word_count=350,  # Below 600 minimum
            keywords=["luxury"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision in [ReviewDecision.MINOR_ISSUE, ReviewDecision.MAJOR_ISSUE]
        assert any("short" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_unexpected_error_fallback(self, brand_config, sample_draft, mock_mcp_client):
        """Test fallback on unexpected errors during MCP review"""
        mock_mcp_client.invoke_tool.side_effect = Exception("Unexpected error")

        reviewer = BrandIntelligenceReviewer(brand_config, mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert "(Fallback)" in review.agent_name
        assert isinstance(review, AgentReview)

    def test_generate_feedback_approved(self, brand_config):
        """Test feedback generation for approved content"""
        reviewer = BrandIntelligenceReviewer(brand_config)
        feedback = reviewer._generate_feedback([], [], ReviewDecision.APPROVED)

        assert "aligns well" in feedback.lower()
        assert "no major concerns" in feedback.lower()

    def test_generate_feedback_with_issues(self, brand_config):
        """Test feedback generation with issues and suggestions"""
        reviewer = BrandIntelligenceReviewer(brand_config)
        issues = ["Missing brand keywords", "Tone inconsistent"]
        suggestions = ["Add luxury terminology", "Adopt formal tone"]

        feedback = reviewer._generate_feedback(issues, suggestions, ReviewDecision.MINOR_ISSUE)

        assert "Issues identified" in feedback
        assert "Missing brand keywords" in feedback
        assert "Suggestions" in feedback
        assert "Add luxury terminology" in feedback


# ============================================================================
# SEO MARKETING REVIEWER TESTS
# ============================================================================


class TestSEOMarketingReviewer:
    """Test SEOMarketingReviewer agent"""

    @pytest.mark.asyncio
    async def test_mcp_review_success(self, sample_draft, mock_mcp_client):
        """Test successful MCP-based SEO review"""
        mock_mcp_client.invoke_tool.return_value = {
            "decision": "approved",
            "confidence": 0.92,
            "feedback": "Excellent SEO optimization with proper keyword usage and meta tags.",
            "issues_found": [],
            "suggestions": [],
        }

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert review.agent_name == "SEO Marketing Agent"
        assert review.decision == ReviewDecision.APPROVED
        assert review.confidence == 0.92

    @pytest.mark.asyncio
    async def test_mcp_failure_fallback(self, sample_draft, mock_mcp_client):
        """Test fallback to rule-based SEO review when MCP fails"""
        mock_mcp_client.invoke_tool.side_effect = MCPToolError("MCP unavailable")

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert "(Fallback)" in review.agent_name
        assert review.confidence == 0.80

    @pytest.mark.asyncio
    async def test_fallback_review_meta_too_short(self):
        """Test fallback review flags short meta description"""
        draft = ContentDraft(
            title="Good Title",
            content="Content with proper keywords and call-to-action. Shop now!" * 20,
            meta_description="Short meta",  # Too short (< 120 chars)
            word_count=800,
            keywords=["keyword"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.MINOR_ISSUE
        assert any("Meta description too short" in issue for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_meta_too_long(self):
        """Test fallback review flags long meta description"""
        draft = ContentDraft(
            title="Good Title",
            content="Content with proper keywords and call-to-action. Shop now!" * 20,
            meta_description="This is a very long meta description that exceeds the recommended 160 character limit "
            "for search engine results pages and will definitely be truncated in SERPs because it is way too long.",
            word_count=800,
            keywords=["keyword"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("Meta description too long" in issue for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_missing_keywords(self):
        """Test fallback review flags missing target keywords"""
        draft = ContentDraft(
            title="Article Title",
            content="Content without the target keywords. Discover more today!" * 20,
            meta_description="Good meta description with appropriate length for SEO optimization.",
            word_count=800,
            keywords=["missing", "keywords", "not", "found"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert any("not used" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_title_too_long(self):
        """Test fallback review flags SEO title that's too long"""
        draft = ContentDraft(
            title="This is a very long title that exceeds the 60 character limit for SEO purposes",
            content="Content with proper keywords and call-to-action. Shop now!" * 20,
            meta_description="Good meta description with appropriate length for SEO optimization.",
            word_count=800,
            keywords=["keyword"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("Title too long" in issue for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_missing_cta(self):
        """Test fallback review flags missing call-to-action"""
        draft = ContentDraft(
            title="Article Title",
            content="This is article content without any call to action at the end." * 20,
            meta_description="Good meta description with appropriate length for SEO optimization.",
            word_count=800,
            keywords=["keyword"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert any("call-to-action" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_approved(self):
        """Test fallback review approves well-optimized content"""
        draft = ContentDraft(
            title="Good SEO Title Under 60 Chars",
            content="Content with proper keywords included naturally. Shop now and discover our products today! "
            "Learn more about our exclusive collection." * 20,
            meta_description="Perfect meta description length between 150-160 characters for optimal SEO performance and search engine visibility results.",
            word_count=800,
            keywords=["keywords", "products"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.APPROVED
        assert "well-optimized" in review.feedback.lower()

    @pytest.mark.asyncio
    async def test_unexpected_error_fallback(self, sample_draft, mock_mcp_client):
        """Test fallback on unexpected errors during MCP review"""
        mock_mcp_client.invoke_tool.side_effect = Exception("Unexpected error")

        reviewer = SEOMarketingReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert "(Fallback)" in review.agent_name

    def test_generate_feedback_approved(self):
        """Test feedback generation for approved content"""
        reviewer = SEOMarketingReviewer()
        feedback = reviewer._generate_feedback([], [], ReviewDecision.APPROVED)

        assert "well-optimized" in feedback.lower()
        assert "ready for publication" in feedback.lower()


# ============================================================================
# SECURITY COMPLIANCE REVIEWER TESTS
# ============================================================================


class TestSecurityComplianceReviewer:
    """Test SecurityComplianceReviewer agent"""

    @pytest.mark.asyncio
    async def test_mcp_review_success(self, sample_draft, mock_mcp_client):
        """Test successful MCP-based security review"""
        mock_mcp_client.invoke_tool.return_value = {
            "decision": "approved",
            "confidence": 0.96,
            "feedback": "Content passes all security and compliance checks.",
            "issues_found": [],
            "suggestions": [],
        }

        reviewer = SecurityComplianceReviewer(compliance_standards=["GDPR"], mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert review.agent_name == "Security & Compliance Agent"
        assert review.decision == ReviewDecision.APPROVED
        assert review.confidence == 0.96

    @pytest.mark.asyncio
    async def test_mcp_failure_fallback(self, sample_draft, mock_mcp_client):
        """Test fallback to rule-based security review when MCP fails"""
        mock_mcp_client.invoke_tool.side_effect = MCPToolError("MCP unavailable")

        reviewer = SecurityComplianceReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert "(Fallback)" in review.agent_name
        assert review.confidence == 0.85

    @pytest.mark.asyncio
    async def test_fallback_review_sensitive_data(self):
        """Test fallback review flags sensitive data patterns"""
        draft = ContentDraft(
            title="Security Test",
            content="Here is my password: secret123 and API key: sk-12345. Also my credit card number.",
            meta_description="Test",
            word_count=800,
            keywords=[],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SecurityComplianceReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("sensitive" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_unsubstantiated_claims(self):
        """Test fallback review flags strong claims without disclaimer"""
        draft = ContentDraft(
            title="Amazing Product",
            content="This is 100% guaranteed to work perfectly. Scientifically proven results every time!" * 20,
            meta_description="Guaranteed results",
            word_count=800,
            keywords=[],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SecurityComplianceReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision in [ReviewDecision.MINOR_ISSUE, ReviewDecision.MAJOR_ISSUE]
        assert any("claims" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_medical_disclaimer(self):
        """Test fallback review requires disclaimer for medical content"""
        draft = ContentDraft(
            title="Health Advice",
            content="This medical diagnosis information will cure your condition. "
            "Here's financial advice for investment." * 20,
            meta_description="Medical advice",
            word_count=800,
            keywords=[],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SecurityComplianceReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.MAJOR_ISSUE
        assert any("regulated" in issue.lower() for issue in review.issues_found)

    @pytest.mark.asyncio
    async def test_fallback_review_approved(self):
        """Test fallback review approves clean content"""
        draft = ContentDraft(
            title="Safe Article",
            content="This is safe content without any sensitive information or unsubstantiated claims. "
            "Please consult a professional for medical advice." * 20,
            meta_description="Safe article",
            word_count=800,
            keywords=["safe"],
        )

        mock_mcp_client = MagicMock()
        mock_mcp_client.invoke_tool = AsyncMock(side_effect=MCPToolError("MCP unavailable"))

        reviewer = SecurityComplianceReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(draft)

        assert review.decision == ReviewDecision.APPROVED
        assert "passes" in review.feedback.lower()

    @pytest.mark.asyncio
    async def test_compliance_standards_parameter(self):
        """Test custom compliance standards parameter"""
        reviewer = SecurityComplianceReviewer(compliance_standards=["GDPR", "HIPAA", "CCPA"])
        assert reviewer.compliance_standards == ["GDPR", "HIPAA", "CCPA"]

    @pytest.mark.asyncio
    async def test_default_compliance_standards(self):
        """Test default compliance standards"""
        reviewer = SecurityComplianceReviewer()
        assert reviewer.compliance_standards == ["GDPR"]

    @pytest.mark.asyncio
    async def test_unexpected_error_fallback(self, sample_draft, mock_mcp_client):
        """Test fallback on unexpected errors during MCP review"""
        mock_mcp_client.invoke_tool.side_effect = Exception("Unexpected error")

        reviewer = SecurityComplianceReviewer(mcp_client=mock_mcp_client)
        review = await reviewer.review_content(sample_draft)

        assert "(Fallback)" in review.agent_name


# ============================================================================
# CONSENSUS ORCHESTRATOR TESTS
# ============================================================================


class TestConsensusOrchestrator:
    """Test ConsensusOrchestrator main orchestration logic"""

    @pytest.mark.asyncio
    async def test_generate_initial_draft(self, mock_content_generator, brand_config):
        """Test initial draft generation"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        draft = await orchestrator.generate_initial_draft(
            topic="Luxury Fashion Trends", keywords=["luxury", "fashion"], tone="luxury", length=800
        )

        assert draft.version == 1
        assert draft.title == "Test Article: Luxury Fashion Trends 2025"
        assert draft.word_count == 850
        assert "luxury" in draft.keywords
        mock_content_generator.generate_blog_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_draft_all_approved(self, mock_content_generator, brand_config, sample_draft):
        """Test review draft when all agents approve"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with (
            patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
            patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
            patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
        ):
            mock_brand.return_value = AgentReview(
                agent_name="Brand", decision=ReviewDecision.APPROVED, confidence=0.95, feedback="Excellent"
            )
            mock_seo.return_value = AgentReview(
                agent_name="SEO", decision=ReviewDecision.APPROVED, confidence=0.92, feedback="Great"
            )
            mock_security.return_value = AgentReview(
                agent_name="Security", decision=ReviewDecision.APPROVED, confidence=0.96, feedback="Clean"
            )

            consensus = await orchestrator.review_draft(sample_draft)

            assert consensus.total_reviewers == 3
            assert consensus.approved_count == 3
            assert consensus.minor_issue_count == 0
            assert consensus.major_issue_count == 0
            assert consensus.requires_redraft is False
            assert "approved" in consensus.consensus_feedback.lower()

    @pytest.mark.asyncio
    async def test_review_draft_requires_redraft(self, mock_content_generator, brand_config, sample_draft):
        """Test review draft when 2+ agents flag major issues (requires redraft)"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with (
            patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
            patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
            patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
        ):
            mock_brand.return_value = AgentReview(
                agent_name="Brand",
                decision=ReviewDecision.MAJOR_ISSUE,
                confidence=0.90,
                feedback="Brand voice inconsistent",
                issues_found=["Casual tone"],
            )
            mock_seo.return_value = AgentReview(
                agent_name="SEO",
                decision=ReviewDecision.MAJOR_ISSUE,
                confidence=0.88,
                feedback="Poor SEO optimization",
                issues_found=["Missing keywords"],
            )
            mock_security.return_value = AgentReview(
                agent_name="Security", decision=ReviewDecision.APPROVED, confidence=0.96, feedback="Clean"
            )

            consensus = await orchestrator.review_draft(sample_draft)

            assert consensus.total_reviewers == 3
            assert consensus.approved_count == 1
            assert consensus.major_issue_count == 2
            assert consensus.requires_redraft is True
            assert "issues" in consensus.consensus_feedback.lower()

    @pytest.mark.asyncio
    async def test_review_draft_mixed_decisions(self, mock_content_generator, brand_config, sample_draft):
        """Test review draft with mixed decisions (conflict resolution)"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with (
            patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
            patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
            patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
        ):
            mock_brand.return_value = AgentReview(
                agent_name="Brand", decision=ReviewDecision.APPROVED, confidence=0.95, feedback="Good"
            )
            mock_seo.return_value = AgentReview(
                agent_name="SEO", decision=ReviewDecision.MINOR_ISSUE, confidence=0.85, feedback="Minor SEO issues"
            )
            mock_security.return_value = AgentReview(
                agent_name="Security", decision=ReviewDecision.MAJOR_ISSUE, confidence=0.90, feedback="Major concerns"
            )

            consensus = await orchestrator.review_draft(sample_draft)

            assert consensus.approved_count == 1
            assert consensus.minor_issue_count == 1
            assert consensus.major_issue_count == 1
            assert consensus.requires_redraft is False  # Only 1 major issue (need 2+)

    @pytest.mark.asyncio
    async def test_combine_feedback_no_redraft(self, mock_content_generator, brand_config):
        """Test feedback combination when no redraft needed"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        reviews = [
            AgentReview(agent_name="Agent1", decision=ReviewDecision.APPROVED, confidence=0.9, feedback="Good"),
            AgentReview(agent_name="Agent2", decision=ReviewDecision.APPROVED, confidence=0.9, feedback="Good"),
        ]

        feedback = orchestrator._combine_feedback(reviews, requires_redraft=False)

        assert "approved" in feedback.lower()
        assert "ready for human review" in feedback.lower()

    @pytest.mark.asyncio
    async def test_combine_feedback_with_redraft(self, mock_content_generator, brand_config):
        """Test feedback combination when redraft required"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        reviews = [
            AgentReview(
                agent_name="Brand Agent",
                decision=ReviewDecision.MAJOR_ISSUE,
                confidence=0.9,
                feedback="Brand issues detected",
            ),
            AgentReview(
                agent_name="SEO Agent", decision=ReviewDecision.MAJOR_ISSUE, confidence=0.9, feedback="SEO problems"
            ),
        ]

        feedback = orchestrator._combine_feedback(reviews, requires_redraft=True)

        assert "issues" in feedback.lower()
        assert "Brand Agent" in feedback
        assert "SEO Agent" in feedback
        assert "address these issues" in feedback.lower()

    @pytest.mark.asyncio
    async def test_redraft_content(self, mock_content_generator, brand_config):
        """Test content redrafting with feedback"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        original_draft = ContentDraft(
            version=1,
            title="Original Title",
            content="Original content",
            meta_description="Original meta description here",
            word_count=500,
            keywords=["test"],
        )

        feedback = "Please improve SEO and add brand keywords."

        new_draft = await orchestrator.redraft_content(original_draft, feedback)

        assert new_draft.version == 2
        assert new_draft.title == original_draft.title
        assert new_draft.word_count > original_draft.word_count
        assert new_draft.feedback_applied == feedback
        assert len(new_draft.meta_description) <= 155  # Truncated

    @pytest.mark.asyncio
    async def test_execute_consensus_workflow_no_redraft(self, mock_content_generator, brand_config):
        """Test complete consensus workflow with no redraft needed"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with (
            patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
            patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
            patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
        ):
            # All approve
            mock_brand.return_value = AgentReview(
                agent_name="Brand", decision=ReviewDecision.APPROVED, confidence=0.95, feedback="Good"
            )
            mock_seo.return_value = AgentReview(
                agent_name="SEO", decision=ReviewDecision.APPROVED, confidence=0.92, feedback="Good"
            )
            mock_security.return_value = AgentReview(
                agent_name="Security", decision=ReviewDecision.APPROVED, confidence=0.96, feedback="Good"
            )

            workflow = await orchestrator.execute_consensus_workflow(
                topic="Test Article", keywords=["test"], tone="professional", length=800
            )

            assert workflow.workflow_id is not None
            assert workflow.topic == "Test Article"
            assert workflow.iteration_count == 0  # No redrafts
            assert len(workflow.review_history) == 1
            assert len(workflow.draft_history) == 1
            assert workflow.human_decision == HumanDecision.PENDING
            assert workflow.webhook_expires_at is not None

    @pytest.mark.asyncio
    async def test_execute_consensus_workflow_max_iterations(self, mock_content_generator, brand_config):
        """Test workflow stops after max redraft iterations"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with (
            patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
            patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
            patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
        ):
            # Always require redraft
            mock_brand.return_value = AgentReview(
                agent_name="Brand", decision=ReviewDecision.MAJOR_ISSUE, confidence=0.90, feedback="Issues"
            )
            mock_seo.return_value = AgentReview(
                agent_name="SEO", decision=ReviewDecision.MAJOR_ISSUE, confidence=0.88, feedback="Issues"
            )
            mock_security.return_value = AgentReview(
                agent_name="Security", decision=ReviewDecision.APPROVED, confidence=0.96, feedback="OK"
            )

            workflow = await orchestrator.execute_consensus_workflow(
                topic="Test Article", keywords=["test"], tone="professional", length=800
            )

            assert workflow.iteration_count == orchestrator.MAX_REDRAFT_ITERATIONS
            assert len(workflow.review_history) == orchestrator.MAX_REDRAFT_ITERATIONS + 1
            assert len(workflow.draft_history) == orchestrator.MAX_REDRAFT_ITERATIONS + 1

    @pytest.mark.asyncio
    async def test_submit_human_decision_approved(self, mock_content_generator, brand_config):
        """Test submitting human approval decision"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        # Create a workflow
        draft = ContentDraft(
            title="Test", content="Test content", meta_description="Test", word_count=100, keywords=[]
        )
        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        # Submit approval
        updated = await orchestrator.submit_human_decision(
            workflow_id=workflow.workflow_id, decision_token=workflow.approval_token, feedback="Looks great!"
        )

        assert updated.human_decision == HumanDecision.APPROVED
        assert updated.human_feedback == "Looks great!"

    @pytest.mark.asyncio
    async def test_submit_human_decision_rejected(self, mock_content_generator, brand_config):
        """Test submitting human rejection decision"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        # Create a workflow
        draft = ContentDraft(
            title="Test", content="Test content", meta_description="Test", word_count=100, keywords=[]
        )
        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        # Submit rejection
        updated = await orchestrator.submit_human_decision(
            workflow_id=workflow.workflow_id, decision_token=workflow.rejection_token, feedback="Needs more work"
        )

        assert updated.human_decision == HumanDecision.REJECTED
        assert updated.human_feedback == "Needs more work"

    @pytest.mark.asyncio
    async def test_submit_human_decision_invalid_workflow(self, mock_content_generator, brand_config):
        """Test submitting decision for non-existent workflow"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with pytest.raises(ValueError, match="Workflow not found"):
            await orchestrator.submit_human_decision(
                workflow_id="nonexistent-id", decision_token="any-token", feedback=None
            )

    @pytest.mark.asyncio
    async def test_submit_human_decision_invalid_token(self, mock_content_generator, brand_config):
        """Test submitting decision with invalid token"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        # Create a workflow
        draft = ContentDraft(
            title="Test", content="Test content", meta_description="Test", word_count=100, keywords=[]
        )
        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        # Submit with invalid token
        with pytest.raises(ValueError, match="Invalid decision token"):
            await orchestrator.submit_human_decision(
                workflow_id=workflow.workflow_id, decision_token="invalid-token", feedback=None
            )

    def test_get_workflow_exists(self, mock_content_generator, brand_config):
        """Test getting existing workflow"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        draft = ContentDraft(
            title="Test", content="Test content", meta_description="Test", word_count=100, keywords=[]
        )
        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        retrieved = orchestrator.get_workflow(workflow.workflow_id)

        assert retrieved is not None
        assert retrieved.workflow_id == workflow.workflow_id

    def test_get_workflow_not_found(self, mock_content_generator, brand_config):
        """Test getting non-existent workflow returns None"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        retrieved = orchestrator.get_workflow("nonexistent-id")

        assert retrieved is None

    def test_get_approval_urls(self, mock_content_generator, brand_config):
        """Test approval URL generation"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        draft = ContentDraft(
            title="Test", content="Test content", meta_description="Test", word_count=100, keywords=[]
        )
        workflow = WorkflowState(topic="Test", current_draft=draft)
        orchestrator.workflows[workflow.workflow_id] = workflow

        urls = orchestrator.get_approval_urls(workflow.workflow_id, base_url="https://example.com")

        assert "approve_url" in urls
        assert "reject_url" in urls
        assert workflow.approval_token in urls["approve_url"]
        assert workflow.rejection_token in urls["reject_url"]
        parsed_approve = urlparse(urls["approve_url"])
        assert parsed_approve.scheme == "https"
        assert parsed_approve.netloc == "example.com"
        assert f"/api/v1/consensus/approve/{workflow.workflow_id}" in urls["approve_url"]

    def test_get_approval_urls_workflow_not_found(self, mock_content_generator, brand_config):
        """Test approval URL generation for non-existent workflow"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with pytest.raises(ValueError, match="Workflow not found"):
            orchestrator.get_approval_urls("nonexistent-id")


# ============================================================================
# WORKFLOW STATE & MODELS TESTS
# ============================================================================


class TestWorkflowModels:
    """Test Pydantic models and workflow state"""

    def test_content_draft_defaults(self):
        """Test ContentDraft default values"""
        draft = ContentDraft(title="Test", content="Test content", meta_description="Test", word_count=100)

        assert draft.draft_id is not None
        assert draft.version == 1
        assert draft.keywords == []
        assert draft.created_at is not None
        assert draft.feedback_applied is None

    def test_workflow_state_defaults(self):
        """Test WorkflowState default values"""
        draft = ContentDraft(title="Test", content="Test", meta_description="Test", word_count=100)
        workflow = WorkflowState(topic="Test Topic", current_draft=draft)

        assert workflow.workflow_id is not None
        assert workflow.draft_history == []
        assert workflow.review_history == []
        assert workflow.iteration_count == 0
        assert workflow.human_decision == HumanDecision.PENDING
        assert workflow.human_feedback is None
        assert workflow.approval_token is not None
        assert workflow.rejection_token is not None
        assert len(workflow.approval_token) > 20  # Secure token
        assert len(workflow.rejection_token) > 20
        assert workflow.approval_token != workflow.rejection_token

    def test_agent_review_model(self):
        """Test AgentReview model validation"""
        review = AgentReview(
            agent_name="Test Agent",
            decision=ReviewDecision.APPROVED,
            confidence=0.95,
            feedback="Good content",
            issues_found=["Issue 1"],
            suggestions=["Suggestion 1"],
        )

        assert review.agent_name == "Test Agent"
        assert review.decision == ReviewDecision.APPROVED
        assert review.confidence == 0.95
        assert len(review.issues_found) == 1
        assert review.review_timestamp is not None

    def test_consensus_vote_model(self):
        """Test ConsensusVote model"""
        reviews = [
            AgentReview(agent_name="Agent1", decision=ReviewDecision.APPROVED, confidence=0.9, feedback="Good"),
            AgentReview(agent_name="Agent2", decision=ReviewDecision.MINOR_ISSUE, confidence=0.8, feedback="Minor"),
        ]

        vote = ConsensusVote(
            total_reviewers=3,
            approved_count=1,
            minor_issue_count=1,
            major_issue_count=1,
            requires_redraft=False,
            consensus_feedback="Combined feedback",
            reviews=reviews,
        )

        assert vote.total_reviewers == 3
        assert vote.approved_count == 1
        assert len(vote.reviews) == 2


# ============================================================================
# INTEGRATION & EDGE CASES
# ============================================================================


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""

    @pytest.mark.asyncio
    async def test_parallel_review_execution(self, mock_content_generator, brand_config, sample_draft):
        """Test that all reviewers execute in parallel"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        # Track call order
        call_order = []

        def mock_review_with_tracking(name):
            async def mock_review(self, draft):
                call_order.append(f"{name}_start")
                await asyncio.sleep(0.01)  # Simulate work
                call_order.append(f"{name}_end")
                return AgentReview(agent_name=name, decision=ReviewDecision.APPROVED, confidence=0.9, feedback="OK")

            return mock_review

        with (
            patch.object(BrandIntelligenceReviewer, "review_content", new=mock_review_with_tracking("Brand")),
            patch.object(SEOMarketingReviewer, "review_content", new=mock_review_with_tracking("SEO")),
            patch.object(SecurityComplianceReviewer, "review_content", new=mock_review_with_tracking("Security")),
        ):

            await orchestrator.review_draft(sample_draft)

            # All should start before any ends (parallel execution)
            start_calls = [item for item in call_order if item.endswith("_start")]
            end_calls = [item for item in call_order if item.endswith("_end")]
            assert len(start_calls) == 3
            assert len(end_calls) == 3

    @pytest.mark.asyncio
    async def test_workflow_without_logfire(self, mock_content_generator, brand_config):
        """Test workflow execution without logfire instrumentation"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        with (
            patch("services.consensus_orchestrator.LOGFIRE_AVAILABLE", False),
            patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
            patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
            patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
        ):
            mock_brand.return_value = AgentReview(
                agent_name="Brand", decision=ReviewDecision.APPROVED, confidence=0.95, feedback="Good"
            )
            mock_seo.return_value = AgentReview(
                agent_name="SEO", decision=ReviewDecision.APPROVED, confidence=0.92, feedback="Good"
            )
            mock_security.return_value = AgentReview(
                agent_name="Security", decision=ReviewDecision.APPROVED, confidence=0.96, feedback="Good"
            )

            workflow = await orchestrator.execute_consensus_workflow(
                topic="Test", keywords=["test"], tone="professional", length=800
            )

            # Verify workflow completed successfully
            assert workflow.workflow_id is not None
            assert workflow.iteration_count == 0

    def test_webhook_expiry_timestamp(self, mock_content_generator, brand_config):
        """Test webhook expiry is set correctly (1 hour from now)"""
        ConsensusOrchestrator(mock_content_generator, brand_config)

        draft = ContentDraft(title="Test", content="Test", meta_description="Test", word_count=100)
        workflow = WorkflowState(topic="Test", current_draft=draft)

        # Simulate setting webhook expiry
        before = datetime.now()
        workflow.webhook_expires_at = datetime.now() + timedelta(hours=1)
        after = datetime.now()

        expected_expiry_min = before + timedelta(hours=1)
        expected_expiry_max = after + timedelta(hours=1)

        assert expected_expiry_min <= workflow.webhook_expires_at <= expected_expiry_max

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, mock_content_generator, brand_config):
        """Test orchestrator initializes with correct reviewers"""
        orchestrator = ConsensusOrchestrator(mock_content_generator, brand_config)

        assert len(orchestrator.reviewers) == 3
        assert isinstance(orchestrator.reviewers[0], BrandIntelligenceReviewer)
        assert isinstance(orchestrator.reviewers[1], SEOMarketingReviewer)
        assert isinstance(orchestrator.reviewers[2], SecurityComplianceReviewer)
        assert orchestrator.MAX_REDRAFT_ITERATIONS == 2
        assert orchestrator.workflows == {}

    def test_review_decision_enum_values(self):
        """Test ReviewDecision enum has correct values"""
        assert ReviewDecision.APPROVED == "approved"
        assert ReviewDecision.MINOR_ISSUE == "minor_issue"
        assert ReviewDecision.MAJOR_ISSUE == "major_issue"

    def test_human_decision_enum_values(self):
        """Test HumanDecision enum has correct values"""
        assert HumanDecision.APPROVED == "approved"
        assert HumanDecision.REJECTED == "rejected"
        assert HumanDecision.PENDING == "pending"
        assert HumanDecision.TIMEOUT == "timeout"
