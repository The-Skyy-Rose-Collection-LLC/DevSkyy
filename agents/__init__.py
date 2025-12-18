"""
DevSkyy Agents Module
=====================

6 SuperAgents with 17 prompt engineering techniques, ML capabilities,
self-learning modules, and LLM Round Table integration.

SuperAgents:
- CommerceAgent: E-commerce, products, orders, inventory, pricing
- CreativeAgent: 3D assets, images, virtual try-on, videos
- MarketingAgent: Content, campaigns, SEO, social media
- SupportAgent: Customer service, tickets, FAQs
- OperationsAgent: WordPress, deployment, monitoring
- AnalyticsAgent: Reports, forecasting, insights

Specialized Agents:
- FashnTryOnAgent: Virtual try-on using FASHN API
- TripoAssetAgent: 3D model generation using Tripo3D API
- WordPressAssetAgent: WordPress media upload and management

All agents extend EnhancedSuperAgent and include:
- 17 prompt engineering techniques
- ML capabilities per agent type
- Self-learning optimization
- LLM Round Table competition
"""

# Enhanced Super Agent base and modules
from .base_super_agent import (
    # Types
    SuperAgentType,
    TaskCategory,
    LLMProvider,
    # Data classes
    PromptTechniqueResult,
    MLPrediction,
    LearningRecord,
    RoundTableEntry,
    RoundTableResult,
    # Modules
    PromptEngineeringModule,
    MLCapabilitiesModule,
    SelfLearningModule,
    LLMRoundTableInterface,
    # Base
    EnhancedSuperAgent,
)

# 6 SuperAgents
from .commerce_agent import CommerceAgent
from .creative_agent import CreativeAgent, VisualProvider as CreativeVisualProvider, VisualTaskType
from .marketing_agent import MarketingAgent
from .support_agent import SupportAgent
from .operations_agent import OperationsAgent
from .analytics_agent import AnalyticsAgent

# Visual Generation
from .visual_generation import (
    VisualProvider,
    GenerationType,
    AspectRatio,
    ImageQuality,
    GenerationRequest,
    GenerationResult,
    SKYYROSE_BRAND_DNA,
    GoogleImagenClient,
    GoogleVeoClient,
    HuggingFaceFluxClient,
    VisualGenerationRouter,
    create_visual_router,
)

# Specialized agents
from .fashn_agent import (
    FashnConfig,
    FashnTask,
    FashnTaskStatus,
    FashnTryOnAgent,
    GarmentCategory,
    TryOnMode,
    TryOnResult,
)
from .tripo_agent import (
    COLLECTION_PROMPTS,
    GARMENT_TEMPLATES,
    SKYYROSE_BRAND_DNA,
    GenerationResult,
    ModelFormat,
    ModelStyle,
    TripoAssetAgent,
    TripoConfig,
    TripoTask,
    TripoTaskStatus,
)
from .wordpress_asset_agent import (
    GalleryResult,
    MediaUploadResult,
    Model3DUploadResult,
    ProductAssetResult,
    WordPressAssetAgent,
    WordPressAssetConfig,
)

__all__ = [
    # Enhanced Super Agent - Types
    "SuperAgentType",
    "TaskCategory",
    "LLMProvider",
    # Enhanced Super Agent - Data classes
    "PromptTechniqueResult",
    "MLPrediction",
    "LearningRecord",
    "RoundTableEntry",
    "RoundTableResult",
    # Enhanced Super Agent - Modules
    "PromptEngineeringModule",
    "MLCapabilitiesModule",
    "SelfLearningModule",
    "LLMRoundTableInterface",
    # Enhanced Super Agent - Base
    "EnhancedSuperAgent",
    # 6 SuperAgents
    "CommerceAgent",
    "CreativeAgent",
    "VisualProvider",
    "VisualTaskType",
    "MarketingAgent",
    "SupportAgent",
    "OperationsAgent",
    "AnalyticsAgent",
    # FASHN Agent
    "FashnTryOnAgent",
    "FashnConfig",
    "FashnTask",
    "TryOnResult",
    "GarmentCategory",
    "TryOnMode",
    "FashnTaskStatus",
    # Tripo Agent
    "TripoAssetAgent",
    "TripoConfig",
    "TripoTask",
    "GenerationResult",
    "ModelFormat",
    "ModelStyle",
    "TripoTaskStatus",
    "SKYYROSE_BRAND_DNA",
    "COLLECTION_PROMPTS",
    "GARMENT_TEMPLATES",
    # WordPress Asset Agent
    "WordPressAssetAgent",
    "WordPressAssetConfig",
    "MediaUploadResult",
    "ProductAssetResult",
    "GalleryResult",
    "Model3DUploadResult",
]
