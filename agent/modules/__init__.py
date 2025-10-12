"""
DevSkyy Agent Modules Package

This package contains all the specialized AI agents for comprehensive
website management, optimization, and monitoring.
"""

__version__ = "2.0.0"
__author__ = "DevSkyy Enhanced Platform"

from .fixer import fix_code
from .scanner import scan_site

# Import all agent classes with graceful fallback for missing dependencies
try:
    from .customer_service_agent import CustomerServiceAgent
except ImportError:
    CustomerServiceAgent = None  # type: ignore

try:
    from .design_automation_agent import DesignAutomationAgent
except ImportError:
    DesignAutomationAgent = None  # type: ignore

try:
    from .email_sms_automation_agent import EmailSMSAutomationAgent
except ImportError:
    EmailSMSAutomationAgent = None  # type: ignore

try:
    from .financial_agent import FinancialAgent
except ImportError:
    FinancialAgent = None  # type: ignore

try:
    from .social_media_automation_agent import SocialMediaAutomationAgent
except ImportError:
    SocialMediaAutomationAgent = None  # type: ignore

try:
    from .performance_agent import PerformanceAgent
except ImportError:
    PerformanceAgent = None  # type: ignore

try:
    from .security_agent import SecurityAgent
except ImportError:
    SecurityAgent = None  # type: ignore

try:
    from .inventory_agent import InventoryAgent
except ImportError:
    InventoryAgent = None  # type: ignore

try:
    from .web_development_agent import WebDevelopmentAgent
except ImportError:
    WebDevelopmentAgent = None  # type: ignore

try:
    from .wordpress_agent import WordPressAgent
except ImportError:
    WordPressAgent = None  # type: ignore

try:
    from .site_communication_agent import SiteCommunicationAgent
except ImportError:
    SiteCommunicationAgent = None  # type: ignore

try:
    from .brand_intelligence_agent import BrandIntelligenceAgent
except ImportError:
    BrandIntelligenceAgent = None  # type: ignore

try:
    from .seo_marketing_agent import SEOMarketingAgent
except ImportError:
    SEOMarketingAgent = None  # type: ignore

try:
    from .ecommerce_agent import EcommerceAgent
except ImportError:
    EcommerceAgent = None  # type: ignore

# Additional agents available in the codebase
try:
    from .advanced_code_generation_agent import AdvancedCodeGenerationAgent
except ImportError:
    AdvancedCodeGenerationAgent = None  # type: ignore

try:
    from .continuous_learning_background_agent import ContinuousLearningBackgroundAgent
except ImportError:
    ContinuousLearningBackgroundAgent = None  # type: ignore

try:
    from .enhanced_brand_intelligence_agent import EnhancedBrandIntelligenceAgent
except ImportError:
    EnhancedBrandIntelligenceAgent = None  # type: ignore

try:
    from .fashion_computer_vision_agent import FashionComputerVisionAgent
except ImportError:
    FashionComputerVisionAgent = None  # type: ignore

try:
    from .marketing_content_generation_agent import MarketingContentGenerationAgent
except ImportError:
    MarketingContentGenerationAgent = None  # type: ignore

try:
    from .meta_social_automation_agent import MetaSocialAutomationAgent
except ImportError:
    MetaSocialAutomationAgent = None  # type: ignore

try:
    from .universal_self_healing_agent import UniversalSelfHealingAgent
except ImportError:
    UniversalSelfHealingAgent = None  # type: ignore

try:
    from .voice_audio_content_agent import VoiceAudioContentAgent
except ImportError:
    VoiceAudioContentAgent = None  # type: ignore

try:
    from .wordpress_divi_elementor_agent import WordPressDiviElementorAgent
except ImportError:
    WordPressDiviElementorAgent = None  # type: ignore

try:
    from .wordpress_fullstack_theme_builder_agent import WordPressFullStackThemeBuilderAgent
except ImportError:
    WordPressFullStackThemeBuilderAgent = None  # type: ignore

__all__ = [
    "scan_site",
    "fix_code",
    # Core agents as requested in requirements
    "CustomerServiceAgent",
    "DesignAutomationAgent",
    "EmailSMSAutomationAgent",
    "FinancialAgent",
    "SocialMediaAutomationAgent",
    "PerformanceAgent",
    "SecurityAgent",
    "InventoryAgent",
    "WebDevelopmentAgent",
    "WordPressAgent",
    "SiteCommunicationAgent",
    "BrandIntelligenceAgent",
    "SEOMarketingAgent",
    "EcommerceAgent",
    # Additional agents
    "AdvancedCodeGenerationAgent",
    "ContinuousLearningBackgroundAgent",
    "EnhancedBrandIntelligenceAgent",
    "FashionComputerVisionAgent",
    "MarketingContentGenerationAgent",
    "MetaSocialAutomationAgent",
    "UniversalSelfHealingAgent",
    "VoiceAudioContentAgent",
    "WordPressDiviElementorAgent",
    "WordPressFullStackThemeBuilderAgent",
]
