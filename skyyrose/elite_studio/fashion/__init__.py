"""
Fashion Intelligence Core — SkyyRose Elite Studio

Deep fashion domain knowledge with SkyyRose brand DNA baked into every layer.
Covers garment knowledge, trend signals, photography standards, color theory,
editorial direction, material rendering accuracy, and QA rules.

"Luxury Grows from Concrete."
"""

from __future__ import annotations

from .colorway import ColorAdvisor, ColorPalette
from .context import FashionContext, FashionContextBuilder
from .editorial import EditorialDirector, StylingRule
from .knowledge import FashionKnowledgeBase, FabricProperties, GarmentType
from .materials import MaterialsExpert, RenderingSpec
from .photography import PhotographyDirector, PhotographyStandard
from .qa_rules import FashionQA, QARule
from .sizing import SizingAdvisor, SizingGuideline
from .trends import TrendAdvisor, TrendSignal
from .design import (
    DesignBrief,
    DesignConcept,
    DesignIdeationAgent,
    MockupGenerator,
    MockupResult,
    CollectionPlanner,
    CollectionPlan,
    TechPackGenerator,
    TechPack,
    MoodboardComposer,
    Moodboard,
)

__all__ = [
    # Context (primary entry point)
    "FashionContext",
    "FashionContextBuilder",
    # Knowledge
    "FashionKnowledgeBase",
    "GarmentType",
    "FabricProperties",
    # Trends
    "TrendAdvisor",
    "TrendSignal",
    # Photography
    "PhotographyDirector",
    "PhotographyStandard",
    # Color
    "ColorAdvisor",
    "ColorPalette",
    # Editorial
    "EditorialDirector",
    "StylingRule",
    # Materials
    "MaterialsExpert",
    "RenderingSpec",
    # Sizing
    "SizingAdvisor",
    "SizingGuideline",
    # QA
    "FashionQA",
    "QARule",
    # Design tools
    "DesignBrief",
    "DesignConcept",
    "DesignIdeationAgent",
    "MockupGenerator",
    "MockupResult",
    "CollectionPlanner",
    "CollectionPlan",
    "TechPackGenerator",
    "TechPack",
    "MoodboardComposer",
    "Moodboard",
]
