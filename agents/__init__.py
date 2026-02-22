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
- SecurityOpsAgent: Vulnerability scanning, auto-remediation, compliance reporting

All agents extend EnhancedSuperAgent and include:
- 17 prompt engineering techniques
- ML capabilities per agent type
- Self-learning optimization
- LLM Round Table competition

Note: Imports are guarded with try/except so missing optional dependencies
(wordpress, adk, etc.) don't block the entire package from loading.
"""

import logging as _logging

_logger = _logging.getLogger(__name__)

# --- Guarded imports: missing deps log a warning instead of crashing ---

try:
    from .analytics_agent import AnalyticsAgent
except ImportError as _e:
    _logger.debug("AnalyticsAgent unavailable: %s", _e)
    AnalyticsAgent = None  # type: ignore[assignment,misc]

try:
    # Enhanced Super Agent base and modules
    from .base_super_agent import (
        EnhancedSuperAgent,
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
except ImportError as _e:
    _logger.debug("EnhancedSuperAgent unavailable: %s", _e)

try:
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
except ImportError as _e:
    _logger.debug("CodingDoctorAgent unavailable: %s", _e)

try:
    # 6 SuperAgents
    from .collection_content_agent import CollectionContentAgent
except ImportError as _e:
    _logger.debug("CollectionContentAgent unavailable: %s", _e)
    CollectionContentAgent = None  # type: ignore[assignment,misc]

try:
    from .commerce_agent import CommerceAgent
except ImportError as _e:
    _logger.debug("CommerceAgent unavailable: %s", _e)
    CommerceAgent = None  # type: ignore[assignment,misc]

try:
    from .creative_agent import CreativeAgent, VisualTaskType
except ImportError as _e:
    _logger.debug("CreativeAgent unavailable: %s", _e)

try:
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
except ImportError as _e:
    _logger.debug("FashnTryOnAgent unavailable: %s", _e)

try:
    from .marketing_agent import MarketingAgent
except ImportError as _e:
    _logger.debug("MarketingAgent unavailable: %s", _e)
    MarketingAgent = None  # type: ignore[assignment,misc]

try:
    from .operations_agent import OperationsAgent
except ImportError as _e:
    _logger.debug("OperationsAgent unavailable: %s", _e)
    OperationsAgent = None  # type: ignore[assignment,misc]

try:
    from .security_ops_agent import SecurityOpsAgent
except ImportError as _e:
    _logger.debug("SecurityOpsAgent unavailable: %s", _e)
    SecurityOpsAgent = None  # type: ignore[assignment,misc]

try:
    from .skyyrose_content_agent import (
        BrandDNA,
        ContentStatus,
        ContentType,
        GeneratedContent,
        SkyyRoseContentAgent,
    )
except ImportError as _e:
    _logger.debug("SkyyRoseContentAgent unavailable: %s", _e)

try:
    from .skyyrose_imagery_agent import (
        GeneratedImage,
        ImageryBatch,
        ImageryPurpose,
        ModelPose,
        SkyyRoseImageryAgent,
    )
except ImportError as _e:
    _logger.debug("SkyyRoseImageryAgent unavailable: %s", _e)

try:
    from .support_agent import SupportAgent
except ImportError as _e:
    _logger.debug("SupportAgent unavailable: %s", _e)
    SupportAgent = None  # type: ignore[assignment,misc]

try:
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
except ImportError as _e:
    _logger.debug("TripoAssetAgent unavailable: %s", _e)

try:
    # Visual Generation (primary source for brand DNA and generation types)
    from .visual_generation import (
        SKYYROSE_BRAND_DNA,
        AspectRatio,
        ConversationEditor,
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
except ImportError as _e:
    _logger.debug("VisualGeneration unavailable: %s", _e)

try:
    from .wordpress_asset_agent import (
        GalleryResult,
        MediaUploadResult,
        Model3DUploadResult,
        ProductAssetResult,
        WordPressAssetAgent,
        WordPressAssetConfig,
    )
except ImportError as _e:
    _logger.debug("WordPressAssetAgent unavailable: %s", _e)

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
    "SecurityOpsAgent",
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
    "ConversationEditor",
    # SkyyRose Imagery Agent
    "SkyyRoseImageryAgent",
    "ImageryPurpose",
    "ModelPose",
    "GeneratedImage",
    "ImageryBatch",
    # SkyyRose Content Agent
    "SkyyRoseContentAgent",
    "ContentType",
    "ContentStatus",
    "GeneratedContent",
    "BrandDNA",
    # WordPress Asset Agent
    "WordPressAssetAgent",
    "WordPressAssetConfig",
    "MediaUploadResult",
    "ProductAssetResult",
    "GalleryResult",
    "Model3DUploadResult",
]
