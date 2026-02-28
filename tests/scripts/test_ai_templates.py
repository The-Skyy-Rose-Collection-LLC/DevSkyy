"""Tests for AI Space templates."""
from scripts.ai_config import AIConfig


def test_render_trainer_template_contains_dataset():
    """Rendered template includes the configured dataset name."""
    from scripts.ai_templates import render_trainer_app
    config = AIConfig(dataset="damBruh/skyyrose-lora-dataset-v5")
    rendered = render_trainer_app(config)
    assert "damBruh/skyyrose-lora-dataset-v5" in rendered
    assert "gradio" in rendered.lower()


def test_render_trainer_template_respects_steps():
    """Rendered template uses configured step count."""
    from scripts.ai_templates import render_trainer_app
    config = AIConfig(steps=500)
    rendered = render_trainer_app(config)
    assert "--max_train_steps=500" in rendered


def test_render_trainer_template_respects_resolution():
    """Rendered template uses configured resolution."""
    from scripts.ai_templates import render_trainer_app
    config = AIConfig(resolution=512)
    rendered = render_trainer_app(config)
    assert "--resolution=512" in rendered


def test_render_requirements():
    """render_requirements() returns valid requirements.txt content."""
    from scripts.ai_templates import render_requirements
    reqs = render_requirements()
    assert "gradio" in reqs
    assert "huggingface_hub" in reqs
    assert "torch" in reqs
