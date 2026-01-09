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

from .analytics_agent import AnalyticsAgent

# Enhanced Super Agent base and modules
from .base_super_agent import (
    EnhancedSuperAgent,  # Types; Data classes; Modules; Base
    LearningRecord,
    LLMProvider,
    LLMRoundTableInterface,
    MLCapabilitiesModule,
    MLPrediction,
    PromptEngineeringModule,
    PromptTechniqueResult,
    RoundTableEntry,
    RoundTableResult,
    SelfLearningModule,
    SuperAgentType,
    TaskCategory,
)

# Coding Doctor Agent (Meta-agent for codebase health)
from .coding_doctor_agent import (
    CodeIssue,
    CodingDoctorAgent,
    FileReview,
    HealthCheckType,
    HealthReport,
    IssueCategory,
    SeverityLevel,
    create_coding_doctor,
)

# 6 SuperAgents
from .collection_content_agent import CollectionContentAgent
from .commerce_agent import CommerceAgent
from .creative_agent import CreativeAgent, VisualTaskType

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
from .marketing_agent import MarketingAgent
from .operations_agent import OperationsAgent
from .support_agent import SupportAgent
from .tripo_agent import (
    COLLECTION_PROMPTS,
    GARMENT_TEMPLATES,
    ModelFormat,
    ModelStyle,
    TripoAssetAgent,
    TripoConfig,
    TripoTask,
    TripoTaskStatus,
)
from .tripo_agent import SKYYROSE_BRAND_DNA as TRIPO_BRAND_DNA
from .tripo_agent import GenerationResult as TripoGenerationResult

# Visual Generation Router (primary source for brand DNA and generation types)
from .visual_generation_router import (
    SKYYROSE_BRAND_DNA,
    AspectRatio,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    GoogleImagenClient,
    GoogleVeoClient,
    HuggingFaceFluxClient,
    ImageQuality,
    VisualGenerationRouter,
    VisualProvider,
    create_visual_router,
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
    # 6 SuperAgents + Coding Doctor
    "CollectionContentAgent",
    "CommerceAgent",
    "CreativeAgent",
    "VisualTaskType",
    "MarketingAgent",
    "SupportAgent",
    "OperationsAgent",
    "AnalyticsAgent",
    # Coding Doctor Agent
    "CodingDoctorAgent",
    "create_coding_doctor",
    "HealthCheckType",
    "HealthReport",
    "FileReview",
    "CodeIssue",
    "IssueCategory",
    "SeverityLevel",
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
    "TripoGenerationResult",
    "ModelFormat",
    "ModelStyle",
    "TripoTaskStatus",
    "TRIPO_BRAND_DNA",
    "COLLECTION_PROMPTS",
    "GARMENT_TEMPLATES",
    # Visual Generation (primary exports)
    "VisualProvider",
    "GenerationType",
    "AspectRatio",
    "ImageQuality",
    "GenerationRequest",
    "GenerationResult",
    "SKYYROSE_BRAND_DNA",
    "GoogleImagenClient",
    "GoogleVeoClient",
    "HuggingFaceFluxClient",
    "VisualGenerationRouter",
    "create_visual_router",
    # WordPress Asset Agent
    "WordPressAssetAgent",
    "WordPressAssetConfig",
    "MediaUploadResult",
    "ProductAssetResult",
    "GalleryResult",
    "Model3DUploadResult",
]
