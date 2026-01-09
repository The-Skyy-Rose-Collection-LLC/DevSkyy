"""
Unit tests for Gemini native image generation prompt optimizer.

Tests all 5 prompt optimization patterns:
1. Tree of Thoughts for Complex Visuals
2. Negative Prompting Engine
3. Collection-Aware Prompt Templates
4. Thinking Mode Constructor
5. Google Search Grounding Optimizer
"""

from agents.visual_generation.prompt_optimizer import (
    CameraAngle,
    CollectionPromptBuilder,
    GeminiNegativePromptEngine,
    GeminiPromptOptimizer,
    GeminiTreeOfThoughtsVisual,
    GoogleSearchGroundingOptimizer,
    LightingSetup,
    ThinkingModeConstructor,
    VisualUseCase,
)
from orchestration.brand_context import Collection

# =============================================================================
# Pattern 1: Tree of Thoughts Tests
# =============================================================================


def test_tree_of_thoughts_creates_three_directions():
    """Tree of Thoughts should explore 3 creative directions."""
    prompt = GeminiTreeOfThoughtsVisual.create_prompt(
        product_type="hoodie",
        collection=Collection.BLACK_ROSE,
        focus_areas=["fabric texture", "rose gold details"],
    )

    assert "Direction 1" in prompt
    assert "Direction 2" in prompt
    assert "Direction 3" in prompt
    assert "Evaluation:" in prompt
    assert "Synthesized Final Image:" in prompt


def test_tree_of_thoughts_includes_focus_areas():
    """Tree of Thoughts should incorporate specified focus areas."""
    focus_areas = ["embroidered roses", "metallic hardware"]
    prompt = GeminiTreeOfThoughtsVisual.create_prompt(
        product_type="hoodie",
        collection=Collection.BLACK_ROSE,
        focus_areas=focus_areas,
    )

    assert "embroidered roses, metallic hardware" in prompt


def test_tree_of_thoughts_black_rose_has_gothic_direction():
    """BLACK_ROSE collection should include gothic romance direction."""
    prompt = GeminiTreeOfThoughtsVisual.create_prompt(
        product_type="hoodie",
        collection=Collection.BLACK_ROSE,
    )

    assert "gothic" in prompt.lower() or "romance" in prompt.lower()


def test_tree_of_thoughts_signature_has_minimalist_direction():
    """SIGNATURE collection should include minimalist direction."""
    prompt = GeminiTreeOfThoughtsVisual.create_prompt(
        product_type="t-shirt",
        collection=Collection.SIGNATURE,
    )

    assert "minimalism" in prompt.lower() or "clean" in prompt.lower()


def test_tree_of_thoughts_love_hurts_has_emotional_direction():
    """LOVE_HURTS collection should include emotional expression direction."""
    prompt = GeminiTreeOfThoughtsVisual.create_prompt(
        product_type="hoodie",
        collection=Collection.LOVE_HURTS,
    )

    assert "emotional" in prompt.lower() or "vulnerable" in prompt.lower()


# =============================================================================
# Pattern 2: Negative Prompting Engine Tests
# =============================================================================


def test_get_base_negatives_returns_list():
    """Base negatives should return list of quality negatives."""
    negatives = GeminiNegativePromptEngine.get_base_negatives()

    assert isinstance(negatives, list)
    assert len(negatives) > 0
    assert any("quality" in neg.lower() for neg in negatives)


def test_get_collection_negatives_black_rose():
    """BLACK_ROSE negatives should avoid bright colors."""
    negatives = GeminiNegativePromptEngine.get_collection_negatives(Collection.BLACK_ROSE)

    assert isinstance(negatives, list)
    assert any("bright" in neg.lower() for neg in negatives)


def test_get_collection_negatives_signature():
    """SIGNATURE negatives should avoid trendy fast fashion."""
    negatives = GeminiNegativePromptEngine.get_collection_negatives(Collection.SIGNATURE)

    assert isinstance(negatives, list)
    assert any("trendy" in neg.lower() or "fast fashion" in neg.lower() for neg in negatives)


def test_get_collection_negatives_love_hurts():
    """LOVE_HURTS negatives should avoid emotionless clinical mood."""
    negatives = GeminiNegativePromptEngine.get_collection_negatives(Collection.LOVE_HURTS)

    assert isinstance(negatives, list)
    assert any("emotionless" in neg.lower() for neg in negatives)


def test_build_negative_prompt_combines_base_and_collection():
    """Negative prompt should combine base + collection negatives."""
    negative_prompt = GeminiNegativePromptEngine.build_negative_prompt(Collection.BLACK_ROSE)

    # Should include base negatives
    assert "quality" in negative_prompt.lower() or "blurry" in negative_prompt.lower()

    # Should include collection negatives
    assert "bright" in negative_prompt.lower()


def test_build_negative_prompt_without_collection():
    """Negative prompt without collection should only include base negatives."""
    negative_prompt = GeminiNegativePromptEngine.build_negative_prompt()

    assert isinstance(negative_prompt, str)
    assert "quality" in negative_prompt.lower() or "blurry" in negative_prompt.lower()


# =============================================================================
# Pattern 3: Collection-Aware Prompt Templates Tests
# =============================================================================


def test_collection_prompt_builder_product_photography():
    """Product photography template should use lighting and camera specs."""
    prompt = CollectionPromptBuilder.build_prompt(
        product_name="SkyyRose BLACK ROSE hoodie",
        collection=Collection.BLACK_ROSE,
        use_case=VisualUseCase.PRODUCT_PHOTOGRAPHY,
    )

    # Should include product name
    assert "SkyyRose BLACK ROSE hoodie" in prompt or "hoodie" in prompt

    # Should include lighting specifications
    assert "lighting" in prompt.lower()

    # Should include camera angle
    assert "angle" in prompt.lower() or "shot" in prompt.lower()


def test_collection_prompt_builder_black_rose_has_dramatic_lighting():
    """BLACK_ROSE should use dramatic chiaroscuro lighting."""
    prompt = CollectionPromptBuilder.build_prompt(
        product_name="test product",
        collection=Collection.BLACK_ROSE,
        use_case=VisualUseCase.PRODUCT_PHOTOGRAPHY,
    )

    assert "dramatic" in prompt.lower() or "chiaroscuro" in prompt.lower()


def test_collection_prompt_builder_signature_has_clean_studio():
    """SIGNATURE should use clean studio lighting."""
    prompt = CollectionPromptBuilder.build_prompt(
        product_name="test product",
        collection=Collection.SIGNATURE,
        use_case=VisualUseCase.PRODUCT_PHOTOGRAPHY,
    )

    assert "studio" in prompt.lower() or "clean" in prompt.lower()


def test_collection_prompt_builder_love_hurts_has_warm_lighting():
    """LOVE_HURTS should use warm, emotionally lit setup."""
    prompt = CollectionPromptBuilder.build_prompt(
        product_name="test product",
        collection=Collection.LOVE_HURTS,
        use_case=VisualUseCase.PRODUCT_PHOTOGRAPHY,
    )

    assert "warm" in prompt.lower() or "emotional" in prompt.lower()


def test_collection_prompt_builder_custom_overrides():
    """Custom overrides should replace template variables."""
    prompt = CollectionPromptBuilder.build_prompt(
        product_name="test product",
        collection=Collection.BLACK_ROSE,
        use_case=VisualUseCase.PRODUCT_PHOTOGRAPHY,
        custom_overrides={
            "camera_angle": "custom wide-angle",
            "lighting_setup": "custom natural light",
        },
    )

    assert "custom wide-angle" in prompt or "custom natural light" in prompt


# =============================================================================
# Pattern 4: Thinking Mode Constructor Tests
# =============================================================================


def test_thinking_mode_creates_step_by_step_prompt():
    """Thinking mode should create step-by-step reasoning prompt."""
    prompt = ThinkingModeConstructor.create_thinking_prompt(
        concept="AI model wearing BLACK ROSE collection",
        collection=Collection.BLACK_ROSE,
    )

    assert "Step 1" in prompt
    assert "Step 2" in prompt
    assert "Step 3" in prompt
    assert "Step 4" in prompt
    assert "Step 5" in prompt


def test_thinking_mode_includes_brand_dna():
    """Thinking mode should integrate brand DNA strategy."""
    prompt = ThinkingModeConstructor.create_thinking_prompt(
        concept="luxury streetwear photoshoot",
        collection=Collection.BLACK_ROSE,
    )

    assert "Brand DNA" in prompt or "brand" in prompt.lower()


def test_thinking_mode_without_collection():
    """Thinking mode should work without collection specified."""
    prompt = ThinkingModeConstructor.create_thinking_prompt(
        concept="product photography",
    )

    assert "Step 1" in prompt
    assert isinstance(prompt, str)


# =============================================================================
# Pattern 5: Google Search Grounding Optimizer Tests
# =============================================================================


def test_search_grounding_includes_trend_keywords():
    """Search grounding should incorporate trend keywords."""
    prompt = GoogleSearchGroundingOptimizer.create_grounded_prompt(
        product_type="hoodie",
        trend_keywords=["Y2K", "streetwear", "oversized"],
    )

    assert "Y2K" in prompt
    assert "streetwear" in prompt
    assert "oversized" in prompt


def test_search_grounding_includes_location_context():
    """Search grounding should include location context."""
    prompt = GoogleSearchGroundingOptimizer.create_grounded_prompt(
        product_type="hoodie",
        location_context="Oakland, CA",
    )

    assert "Oakland, CA" in prompt or "Oakland" in prompt


def test_search_grounding_instructs_google_search():
    """Search grounding should instruct using Google Search."""
    prompt = GoogleSearchGroundingOptimizer.create_grounded_prompt(
        product_type="hoodie",
        trend_keywords=["streetwear"],
    )

    assert "Google Search" in prompt or "Search" in prompt


# =============================================================================
# Main Optimizer Class Tests
# =============================================================================


def test_optimizer_init():
    """Optimizer should initialize with brand injector."""
    optimizer = GeminiPromptOptimizer()

    assert optimizer.brand_injector is not None


def test_optimizer_tree_of_thoughts_returns_dict():
    """Tree of Thoughts optimization should return dict with prompt and negative."""
    optimizer = GeminiPromptOptimizer()

    result = optimizer.optimize_for_tree_of_thoughts(
        product_type="hoodie",
        collection=Collection.BLACK_ROSE,
    )

    assert isinstance(result, dict)
    assert "prompt" in result
    assert "negative_prompt" in result
    assert isinstance(result["prompt"], str)
    assert isinstance(result["negative_prompt"], str)


def test_optimizer_product_photography_returns_dict():
    """Product photography optimization should return dict with prompt and negative."""
    optimizer = GeminiPromptOptimizer()

    result = optimizer.optimize_for_product_photography(
        product_name="SkyyRose SIGNATURE t-shirt",
        collection=Collection.SIGNATURE,
    )

    assert isinstance(result, dict)
    assert "prompt" in result
    assert "negative_prompt" in result


def test_optimizer_thinking_mode_returns_dict():
    """Thinking mode optimization should return dict with prompt and negative."""
    optimizer = GeminiPromptOptimizer()

    result = optimizer.optimize_for_thinking_mode(
        concept="luxury fashion editorial",
        collection=Collection.BLACK_ROSE,
    )

    assert isinstance(result, dict)
    assert "prompt" in result
    assert "negative_prompt" in result


def test_optimizer_search_grounding_returns_dict():
    """Search grounding optimization should return dict with prompt and negative."""
    optimizer = GeminiPromptOptimizer()

    result = optimizer.optimize_for_search_grounding(
        product_type="hoodie",
        trend_keywords=["streetwear"],
        collection=Collection.BLACK_ROSE,
    )

    assert isinstance(result, dict)
    assert "prompt" in result
    assert "negative_prompt" in result


def test_optimizer_negative_prompts_include_collection_specifics():
    """Negative prompts should include collection-specific negatives."""
    optimizer = GeminiPromptOptimizer()

    # BLACK_ROSE should avoid bright colors
    result_br = optimizer.optimize_for_product_photography(
        product_name="test",
        collection=Collection.BLACK_ROSE,
    )
    assert "bright" in result_br["negative_prompt"].lower()

    # SIGNATURE should avoid trendy
    result_sig = optimizer.optimize_for_product_photography(
        product_name="test",
        collection=Collection.SIGNATURE,
    )
    assert "trendy" in result_sig["negative_prompt"].lower()


# =============================================================================
# Enum Tests
# =============================================================================


def test_visual_use_case_enum():
    """VisualUseCase enum should have all expected values."""
    assert VisualUseCase.PRODUCT_PHOTOGRAPHY.value == "product_photography"
    assert VisualUseCase.CAMPAIGN_IMAGERY.value == "campaign_imagery"
    assert VisualUseCase.AI_MODEL_GENERATION.value == "ai_model_generation"


def test_camera_angle_enum():
    """CameraAngle enum should have all expected values."""
    assert "eye level" in CameraAngle.STRAIGHT_ON.value.lower()
    assert "low" in CameraAngle.LOW_ANGLE.value.lower()
    assert "overhead" in CameraAngle.HIGH_ANGLE.value.lower()


def test_lighting_setup_enum():
    """LightingSetup enum should have all expected values."""
    assert "softbox" in LightingSetup.THREE_POINT_SOFTBOX.value.lower()
    assert "chiaroscuro" in LightingSetup.DRAMATIC_CHIAROSCURO.value.lower()
    assert "golden hour" in LightingSetup.GOLDEN_HOUR.value.lower()
