"""
Tests for agents module
=======================

Agent instantiation and workflow tests.
"""

from agents import (
    COLLECTION_PROMPTS,
    GARMENT_TEMPLATES,
    FashnConfig,
    FashnTryOnAgent,
    GarmentCategory,
    ModelFormat,
    TripoAssetAgent,
    TripoConfig,
    TryOnMode,
    WordPressAssetAgent,
)
from base import AgentCapability


class TestFashnAgent:
    """Test FASHN virtual try-on agent."""

    def test_instantiate(self):
        """Should instantiate agent."""
        agent = FashnTryOnAgent()

        assert agent.name == "fashn_tryon"
        assert AgentCapability.VIRTUAL_TRYON in agent.get_capabilities()

    def test_config_from_env(self):
        """Should create config from environment."""
        config = FashnConfig.from_env()

        assert config.base_url == "https://api.fashn.ai/v1"
        assert config.timeout == 120.0

    def test_garment_categories(self):
        """Should have garment categories."""
        assert GarmentCategory.TOPS.value == "tops"
        assert GarmentCategory.BOTTOMS.value == "bottoms"
        assert GarmentCategory.DRESSES.value == "dresses"

    def test_tryon_modes(self):
        """Should have try-on modes."""
        assert TryOnMode.QUALITY.value == "quality"
        assert TryOnMode.BALANCED.value == "balanced"
        assert TryOnMode.FAST.value == "fast"


class TestTripoAgent:
    """Test Tripo3D asset generation agent."""

    def test_instantiate(self):
        """Should instantiate agent."""
        agent = TripoAssetAgent()

        assert agent.name == "tripo_asset"
        assert AgentCapability.THREE_D_GENERATION in agent.get_capabilities()

    def test_config_from_env(self):
        """Should create config from environment."""
        config = TripoConfig.from_env()

        assert config.base_url == "https://api.tripo3d.ai/v2"
        assert config.timeout == 300.0

    def test_model_formats(self):
        """Should have model formats."""
        assert ModelFormat.GLB.value == "glb"
        assert ModelFormat.FBX.value == "fbx"
        assert ModelFormat.USDZ.value == "usdz"

    def test_collection_prompts(self):
        """Should have collection prompts."""
        assert "BLACK_ROSE" in COLLECTION_PROMPTS
        assert "LOVE_HURTS" in COLLECTION_PROMPTS
        assert "SIGNATURE" in COLLECTION_PROMPTS

        black_rose = COLLECTION_PROMPTS["BLACK_ROSE"]
        assert "style" in black_rose
        assert "colors" in black_rose
        assert "mood" in black_rose

    def test_garment_templates(self):
        """Should have garment templates."""
        assert "hoodie" in GARMENT_TEMPLATES
        assert "bomber" in GARMENT_TEMPLATES
        assert "tee" in GARMENT_TEMPLATES

        assert "luxury" in GARMENT_TEMPLATES["hoodie"].lower()

    def test_build_prompt(self):
        """Should build brand-aware prompts."""
        agent = TripoAssetAgent()

        prompt = agent._build_prompt(
            product_name="Heart aRose Bomber",
            collection="BLACK_ROSE",
            garment_type="bomber",
            additional_details="Rose gold zipper",
        )

        assert "Heart aRose Bomber" in prompt
        assert "dark elegance" in prompt  # From collection
        assert "premium bomber jacket" in prompt  # From template
        assert "Rose gold zipper" in prompt


class TestWordPressAssetAgent:
    """Test WordPress asset agent."""

    def test_instantiate(self):
        """Should instantiate agent."""
        agent = WordPressAssetAgent()

        assert agent.name == "wordpress_asset"
        assert AgentCapability.WORDPRESS_MANAGEMENT in agent.get_capabilities()
        assert AgentCapability.PRODUCT_MANAGEMENT in agent.get_capabilities()


class TestAgentCapabilities:
    """Test agent capabilities."""

    def test_all_agents_have_capabilities(self):
        """All agents should declare capabilities."""
        agents = [
            FashnTryOnAgent(),
            TripoAssetAgent(),
            WordPressAssetAgent(),
        ]

        for agent in agents:
            caps = agent.get_capabilities()
            assert len(caps) > 0, f"{agent.name} has no capabilities"

    def test_unique_agent_names(self):
        """Agents should have unique names."""
        agents = [
            FashnTryOnAgent(),
            TripoAssetAgent(),
            WordPressAssetAgent(),
        ]

        names = [a.name for a in agents]
        assert len(names) == len(set(names)), "Duplicate agent names"
