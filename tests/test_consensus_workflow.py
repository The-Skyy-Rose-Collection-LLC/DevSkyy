"""
Consensus Workflow Tests

WHY: Validate consensus orchestration, multi-agent review, and human approval flow
HOW: Test complete workflow with mocked agents and database
IMPACT: Ensures consensus system works correctly before production

pytest -m consensus -v
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.consensus_orchestrator import (
    BrandIntelligenceReviewer,
    ConsensusOrchestrator,
    ContentDraft,
    HumanDecision,
    ReviewDecision,
    SecurityComplianceReviewer,
    SEOMarketingReviewer,
)


@pytest.fixture
def mock_content_generator():
    """Mock content generator"""
    generator = MagicMock()
    generator.generate_blog_post = AsyncMock(
        return_value={
            "title": "Test Article Title",
            "content": "This is test content with luxury keywords and premium quality.",
            "meta_description": "Test meta description about luxury products.",
            "word_count": 850,
            "keywords": ["luxury", "premium"],
        }
    )
    return generator


@pytest.fixture
def brand_config():
    """Brand configuration for testing"""
    return {
        "name": "Skyy Rose",
        "brand_keywords": ["luxury", "premium", "exclusive"],
        "values": ["luxury", "quality", "innovation"],
    }


@pytest.fixture
def orchestrator(mock_content_generator, brand_config):
    """Create orchestrator instance"""
    return ConsensusOrchestrator(content_generator=mock_content_generator, brand_config=brand_config)


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_generate_initial_draft(orchestrator):
    """Test initial draft generation"""
    draft = await orchestrator.generate_initial_draft(
        topic="Luxury Fashion Trends", keywords=["luxury", "fashion"], tone="luxury", length=800
    )

    assert draft.version == 1
    assert draft.title == "Test Article Title"
    assert draft.word_count == 850
    assert len(draft.keywords) == 2


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_brand_intelligence_reviewer_approval():
    """Test brand reviewer approves good content"""
    brand_config = {
        "brand_keywords": ["luxury", "premium"],
        "values": ["luxury"],
    }
    reviewer = BrandIntelligenceReviewer(brand_config)

    draft = ContentDraft(
        title="Luxury Fashion Guide",
        content="This luxury article discusses premium fashion with exclusive designs." * 50,
        meta_description="Luxury fashion guide",
        word_count=850,
        keywords=["luxury", "premium"],
    )

    review = await reviewer.review_content(draft)

    assert review.agent_name == "Brand Intelligence Agent"
    assert review.decision == ReviewDecision.APPROVED
    assert review.confidence > 0


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_brand_intelligence_reviewer_rejects_short_content():
    """Test brand reviewer flags short content"""
    brand_config = {
        "brand_keywords": ["luxury"],
        "values": ["luxury"],
    }
    reviewer = BrandIntelligenceReviewer(brand_config)

    draft = ContentDraft(
        title="Test", content="Short content without keywords.", meta_description="Test", word_count=400, keywords=[]
    )

    review = await reviewer.review_content(draft)

    assert review.decision in [ReviewDecision.MINOR_ISSUE, ReviewDecision.MAJOR_ISSUE]
    assert len(review.issues_found) > 0


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_seo_marketing_reviewer_validates_meta():
    """Test SEO reviewer checks meta description length"""
    reviewer = SEOMarketingReviewer()

    # Meta too long
    draft = ContentDraft(
        title="Good Title",
        content="Content with proper keywords and call-to-action. Shop now!",
        meta_description="This is a very long meta description that exceeds the recommended 160 character limit for search engine results pages and will be truncated in SERPs.",
        word_count=800,
        keywords=["keyword"],
    )

    review = await reviewer.review_content(draft)

    assert review.agent_name == "SEO Marketing Agent"
    assert review.decision == ReviewDecision.MAJOR_ISSUE
    assert any("Meta description too long" in issue for issue in review.issues_found)


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_seo_marketing_reviewer_checks_cta():
    """Test SEO reviewer checks for call-to-action"""
    reviewer = SEOMarketingReviewer()

    draft = ContentDraft(
        title="Article Title",
        content="Article content without any call to action.",
        meta_description="Good meta description length",
        word_count=800,
        keywords=[],
    )

    review = await reviewer.review_content(draft)

    assert any("call-to-action" in issue.lower() for issue in review.issues_found)


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_security_reviewer_flags_sensitive_data():
    """Test security reviewer flags potential sensitive data"""
    reviewer = SecurityComplianceReviewer()

    draft = ContentDraft(
        title="Security Test",
        content="Here is my password and API key information.",
        meta_description="Test",
        word_count=800,
        keywords=[],
    )

    review = await reviewer.review_content(draft)

    assert review.agent_name == "Security & Compliance Agent"
    assert review.decision == ReviewDecision.MAJOR_ISSUE
    assert any("sensitive" in issue.lower() for issue in review.issues_found)


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_security_reviewer_flags_missing_disclaimers():
    """Test security reviewer requires disclaimers for regulated content"""
    reviewer = SecurityComplianceReviewer()

    draft = ContentDraft(
        title="Medical Advice Article",
        content="This medical diagnosis information is guaranteed to cure your condition.",
        meta_description="Medical advice",
        word_count=800,
        keywords=[],
    )

    review = await reviewer.review_content(draft)

    assert review.decision in [ReviewDecision.MINOR_ISSUE, ReviewDecision.MAJOR_ISSUE]
    assert any("disclaimer" in issue.lower() for issue in review.issues_found)


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_consensus_vote_approval():
    """Test consensus calculation with all approvals"""
    draft = ContentDraft(
        title="Test Article",
        content="Good content" * 100,
        meta_description="Good description",
        word_count=800,
        keywords=["test"],
    )

    orchestrator = ConsensusOrchestrator(
        content_generator=MagicMock(), brand_config={"brand_keywords": ["test"], "values": ["quality"]}
    )

    # All reviewers approve
    with (
        patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
        patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
        patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
    ):

        from services.consensus_orchestrator import AgentReview

        mock_brand.return_value = AgentReview(
            agent_name="Brand", decision=ReviewDecision.APPROVED, confidence=0.9, feedback="Good"
        )
        mock_seo.return_value = AgentReview(
            agent_name="SEO", decision=ReviewDecision.APPROVED, confidence=0.9, feedback="Good"
        )
        mock_security.return_value = AgentReview(
            agent_name="Security", decision=ReviewDecision.APPROVED, confidence=0.9, feedback="Good"
        )

        consensus = await orchestrator.review_draft(draft)

        assert consensus.total_reviewers == 3
        assert consensus.approved_count == 3
        assert consensus.major_issue_count == 0
        assert consensus.requires_redraft is False


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_consensus_vote_requires_redraft():
    """Test consensus calculation requiring redraft (2+ major issues)"""
    draft = ContentDraft(title="Test", content="Bad content", meta_description="Bad", word_count=100, keywords=[])

    orchestrator = ConsensusOrchestrator(
        content_generator=MagicMock(), brand_config={"brand_keywords": [], "values": []}
    )

    with (
        patch.object(BrandIntelligenceReviewer, "review_content", new_callable=AsyncMock) as mock_brand,
        patch.object(SEOMarketingReviewer, "review_content", new_callable=AsyncMock) as mock_seo,
        patch.object(SecurityComplianceReviewer, "review_content", new_callable=AsyncMock) as mock_security,
    ):

        from services.consensus_orchestrator import AgentReview

        mock_brand.return_value = AgentReview(
            agent_name="Brand",
            decision=ReviewDecision.MAJOR_ISSUE,
            confidence=0.9,
            feedback="Major issues",
            issues_found=["Issue 1"],
        )
        mock_seo.return_value = AgentReview(
            agent_name="SEO",
            decision=ReviewDecision.MAJOR_ISSUE,
            confidence=0.9,
            feedback="Major issues",
            issues_found=["Issue 2"],
        )
        mock_security.return_value = AgentReview(
            agent_name="Security", decision=ReviewDecision.APPROVED, confidence=0.9, feedback="OK"
        )

        consensus = await orchestrator.review_draft(draft)

        assert consensus.major_issue_count == 2
        assert consensus.requires_redraft is True


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_complete_workflow_with_approval(orchestrator):
    """Test complete consensus workflow ending in human approval"""
    workflow = await orchestrator.execute_consensus_workflow(
        topic="Test Article", keywords=["test"], tone="professional", length=800
    )

    assert workflow.workflow_id is not None
    assert workflow.topic == "Test Article"
    assert workflow.current_draft is not None
    assert workflow.iteration_count >= 0
    assert workflow.iteration_count <= orchestrator.MAX_REDRAFT_ITERATIONS
    assert len(workflow.review_history) > 0
    assert workflow.human_decision == HumanDecision.PENDING
    assert workflow.approval_token is not None
    assert workflow.rejection_token is not None


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_human_approval_decision(orchestrator):
    """Test submitting human approval decision"""
    workflow = await orchestrator.execute_consensus_workflow(
        topic="Test", keywords=[], tone="professional", length=800
    )

    # Approve workflow
    updated_workflow = await orchestrator.submit_human_decision(
        workflow_id=workflow.workflow_id, decision_token=workflow.approval_token, feedback="Looks good!"
    )

    assert updated_workflow.human_decision == HumanDecision.APPROVED
    assert updated_workflow.human_feedback == "Looks good!"


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_human_rejection_decision(orchestrator):
    """Test submitting human rejection decision"""
    workflow = await orchestrator.execute_consensus_workflow(
        topic="Test", keywords=[], tone="professional", length=800
    )

    # Reject workflow
    updated_workflow = await orchestrator.submit_human_decision(
        workflow_id=workflow.workflow_id, decision_token=workflow.rejection_token, feedback="Needs more work"
    )

    assert updated_workflow.human_decision == HumanDecision.REJECTED
    assert updated_workflow.human_feedback == "Needs more work"


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_invalid_decision_token(orchestrator):
    """Test invalid decision token raises error"""
    workflow = await orchestrator.execute_consensus_workflow(
        topic="Test", keywords=[], tone="professional", length=800
    )

    with pytest.raises(ValueError, match="Invalid decision token"):
        await orchestrator.submit_human_decision(
            workflow_id=workflow.workflow_id, decision_token="invalid-token", feedback=None
        )


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_max_redraft_iterations(mock_content_generator, brand_config):
    """Test workflow stops after max redraft iterations"""
    orchestrator = ConsensusOrchestrator(content_generator=mock_content_generator, brand_config=brand_config)

    # Force all reviews to require redraft
    with patch.object(orchestrator, "review_draft", new_callable=AsyncMock) as mock_review:
        from services.consensus_orchestrator import AgentReview, ConsensusVote

        mock_review.return_value = ConsensusVote(
            total_reviewers=3,
            approved_count=0,
            minor_issue_count=1,
            major_issue_count=2,
            requires_redraft=True,
            consensus_feedback="Needs redraft",
            reviews=[
                AgentReview(agent_name="Agent1", decision=ReviewDecision.MAJOR_ISSUE, confidence=0.9, feedback="Issue")
            ],
        )

        workflow = await orchestrator.execute_consensus_workflow(
            topic="Test", keywords=[], tone="professional", length=800
        )

        assert workflow.iteration_count == orchestrator.MAX_REDRAFT_ITERATIONS


@pytest.mark.consensus
def test_approval_urls_generation(orchestrator):
    """Test approval URL generation"""
    # Create a workflow
    from services.consensus_orchestrator import ContentDraft, WorkflowState

    draft = ContentDraft(title="Test", content="Test", meta_description="Test", word_count=100, keywords=[])

    workflow = WorkflowState(topic="Test", current_draft=draft)

    orchestrator.workflows[workflow.workflow_id] = workflow

    urls = orchestrator.get_approval_urls(workflow.workflow_id, "http://localhost:8000")

    assert "approve_url" in urls
    assert "reject_url" in urls
    assert workflow.approval_token in urls["approve_url"]
    assert workflow.rejection_token in urls["reject_url"]
    assert "http://localhost:8000" in urls["approve_url"]


@pytest.mark.consensus
def test_workflow_not_found(orchestrator):
    """Test get_workflow with invalid ID returns None"""
    workflow = orchestrator.get_workflow("nonexistent-id")
    assert workflow is None


@pytest.mark.consensus
@pytest.mark.asyncio
async def test_redraft_incorporates_feedback(orchestrator):
    """Test redraft incorporates feedback from previous iteration"""
    original_draft = ContentDraft(
        version=1,
        title="Original Title",
        content="Original content",
        meta_description="Original meta",
        word_count=500,
        keywords=["test"],
    )

    feedback = "Please add more details and improve SEO."

    new_draft = await orchestrator.redraft_content(original_draft, feedback)

    assert new_draft.version == 2
    assert new_draft.feedback_applied == feedback
    assert new_draft.title == original_draft.title  # Title stays same
    assert new_draft.word_count > original_draft.word_count  # Content expanded
