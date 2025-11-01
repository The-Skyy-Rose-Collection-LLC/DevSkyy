from datetime import datetime, timedelta
from infrastructure.elasticsearch_manager import elasticsearch_manager
from infrastructure.redis_manager import redis_manager
import json
import os
import re
import time

from dataclasses import asdict, dataclass
from enum import Enum
from fashion.intelligence_engine import fashion_intelligence
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
import aiohttp
import asyncio
import hashlib
import logging
import yaml

"""
Automated API Discovery & Evaluation Framework
Enterprise-grade API discovery, evaluation, and management system for fashion e-commerce
Integrates with existing Redis, Elasticsearch, and Fashion Intelligence systems
"""

logger = logging.getLogger(__name__)

class APICategory(Enum):
    """API categories for fashion e-commerce"""

    FASHION_TRENDS = "fashion_trends"
    INVENTORY_MANAGEMENT = "inventory_management"
    PRODUCT_CATALOG = "product_catalog"
    CUSTOMER_ANALYTICS = "customer_analytics"
    PAYMENT_PROCESSING = "payment_processing"
    CONTENT_GENERATION = "content_generation"
    DESIGN_AUTOMATION = "design_automation"
    CLOUD_INFRASTRUCTURE = "cloud_infrastructure"
    DEVOPS_AUTOMATION = "devops_automation"
    BUSINESS_INTELLIGENCE = "business_intelligence"

class AuthenticationType(Enum):
    """API authentication types"""

    api_key = os.getenv("API_KEY", "")
    OAUTH2 = "oauth2"
    JWT = "jwt"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM = "custom"

class APIStatus(Enum):
    """API operational status"""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    BETA = "beta"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"

@dataclass
class APIEndpoint:
    """API endpoint information"""

    api_id: str
    name: str
    description: str
    base_url: str
    version: str
    category: APICategory
    provider: str
    authentication: AuthenticationType
    rate_limits: Dict[str, int]
    pricing: Dict[str, Any]
    features: List[str]
    supported_formats: List[str]
    documentation_url: str
    status: APIStatus
    reliability_score: float
    performance_score: float
    cost_score: float
    feature_score: float
    overall_score: float
    last_evaluated: datetime
    fashion_relevance: float
    sustainability_support: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["category"] = self.category.value
        data["authentication"] = self.authentication.value
        data["status"] = self.status.value
        data["last_evaluated"] = self.last_evaluated.isoformat()
        return data

@dataclass
class APIEvaluationCriteria:
    """API evaluation criteria and weights"""

    reliability_weight: float = 0.3
    performance_weight: float = 0.25
    cost_weight: float = 0.2
    features_weight: float = 0.15
    fashion_relevance_weight: float = 0.1

    def normalize_weights(self):
        """Normalize weights to sum to 1.0"""
        total = (
            self.reliability_weight
            + self.performance_weight
            + self.cost_weight
            + self.features_weight
            + self.fashion_relevance_weight
        )

        self.reliability_weight /= total
        self.performance_weight /= total
        self.cost_weight /= total
        self.features_weight /= total
        self.fashion_relevance_weight /= total

class APIDiscoveryEngine:
    """Automated API discovery and evaluation engine"""

    def __init__(self):
        self.discovered_apis: Dict[str, APIEndpoint] = {}
        self.api_registry: Dict[str, Dict[str, Any]] = {}
        self.evaluation_criteria = APIEvaluationCriteria()
        self.discovery_sources = self._initialize_discovery_sources()
        self.fashion_api_patterns = self._initialize_fashion_patterns()

        # Performance tracking
        self.discovery_metrics = {
            "total_apis_discovered": 0,
            "apis_by_category": {},
            "evaluation_success_rate": 0.0,
            "last_discovery_run": None,
            "discovery_duration": 0.0,
        }

        logger.info("API Discovery Engine initialized")

    def _initialize_discovery_sources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize API discovery sources"""
        return {
            "rapidapi": {
                "base_url": "https://rapidapi.com/api/v1",
                "search_endpoint": "/search",
                "categories": ["fashion", "ecommerce", "retail", "trends"],
                "requires_auth": True,
            },
            "programmableweb": {
                "base_url": "https://www.programmableweb.com/api",
                "search_endpoint": "/search",
                "categories": ["fashion", "retail", "commerce"],
                "requires_auth": False,
            },
            "apis_guru": {
                "base_url": "https://api.apis.guru/v2",
                "list_endpoint": "/list.json",
                "categories": ["all"],
                "requires_auth": False,
            },
            "fashion_specific": {
                "sources": [
                    "https://api.shopify.com",
                    "https://api.woocommerce.com",
                    "https://api.magento.com",
                    "https://developers.pinterest.com",
                    "https://developers.instagram.com",
                    "https://api.stripe.com",
                    "https://api.square.com",
                ]
            },
        }

    def _initialize_fashion_patterns(self) -> Dict[str, List[str]]:
        """Initialize fashion-specific API patterns"""
        return {
            "fashion_keywords": [
                "fashion",
                "style",
                "trend",
                "apparel",
                "clothing",
                "outfit",
                "wardrobe",
                "designer",
                "brand",
                "collection",
                "runway",
                "seasonal",
                "color",
                "fabric",
                "textile",
                "sustainable",
            ],
            "ecommerce_keywords": [
                "ecommerce",
                "retail",
                "shop",
                "store",
                "cart",
                "checkout",
                "payment",
                "inventory",
                "product",
                "catalog",
                "order",
                "customer",
                "analytics",
                "recommendation",
                "personalization",
            ],
            "business_keywords": [
                "revenue",
                "profit",
                "sales",
                "conversion",
                "roi",
                "kpi",
                "dashboard",
                "report",
                "analytics",
                "intelligence",
                "forecast",
            ],
        }

    async def discover_apis(
        self, categories: List[APICategory] = None, force_refresh: bool = False
    ) -> Dict[str, List[APIEndpoint]]:
        """Discover APIs across multiple sources"""

        start_time = time.time()
        categories = categories or list(APICategory)

        logger.info(
            f"Starting API discovery for categories: {[c.value for c in categories]}"
        )

        discovered_apis = {}

        # Check cache first
        if not force_refresh:
            cached_results = await self._get_cached_discovery_results(categories)
            if cached_results:
                logger.info("Using cached API discovery results")
                return cached_results

        # Discover from each source
        for source_name, source_config in self.discovery_sources.items():
            try:
                if source_name == "fashion_specific":
                    apis = await self._discover_fashion_specific_apis(source_config)
                else:
                    apis = await self._discover_from_source(
                        source_name, source_config, categories
                    )

                for api in apis:
                    category_key = api.category.value
                    if category_key not in discovered_apis:
                        discovered_apis[category_key] = []
                    discovered_apis[category_key].append(api)

                logger.info(f"Discovered {len(apis)} APIs from {source_name}")

            except Exception as e:
                logger.error(f"Error discovering APIs from {source_name}: {e}")

        # Evaluate and score all discovered APIs
        for category_apis in discovered_apis.values():
            for api in category_apis:
                await self._evaluate_api(api)
                self.discovered_apis[api.api_id] = api

        # Cache results
        await self._cache_discovery_results(discovered_apis)

        # Update metrics
        discovery_duration = time.time() - start_time
        self.discovery_metrics.update(
            {
                "total_apis_discovered": sum()
                    len(apis) for apis in discovered_apis.values()
                ),
                "apis_by_category": {
                    cat: len(apis) for cat, apis in discovered_apis.items()
                },
                "last_discovery_run": datetime.now().isoformat(),
                "discovery_duration": discovery_duration,
            }
        )

        logger.info(f"API discovery completed in {discovery_duration:.2f}s")
        return discovered_apis

    async def _discover_from_source(
        self,
        source_name: str,
        source_config: Dict[str, Any],
        categories: List[APICategory],
    ) -> List[APIEndpoint]:
        """Discover APIs from a specific source"""

        discovered_apis = []

        if source_name == "rapidapi":
            discovered_apis = await self._discover_rapidapi(source_config, categories)
        elif source_name == "apis_guru":
            discovered_apis = await self._discover_apis_guru(source_config, categories)
        elif source_name == "programmableweb":
            discovered_apis = await self._discover_programmableweb(
                source_config, categories
            )

        return discovered_apis

    async def _discover_rapidapi(
        self, config: Dict[str, Any], categories: List[APICategory]
    ) -> List[APIEndpoint]:
        """Discover APIs from RapidAPI"""

        apis = []

        # Search for fashion and ecommerce APIs
        search_terms = ["fashion", "ecommerce", "retail", "trends", "style"]

        async with aiohttp.ClientSession() as session:
            for term in search_terms:
                try:
                    url = f"{config['base_url']}{config['search_endpoint']}"
                    params = {"query": term, "category": "ecommerce", "limit": 50}

                    # Note: In production, you'd use actual RapidAPI credentials
                    headers = {
                        "X-RapidAPI-Key": "your-rapidapi-key",
                        "X-RapidAPI-Host": "rapidapi.com",
                    }

                    async with session.get(
                        url, params=params, headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            for api_data in data.get("results", []):
                                api = self._parse_rapidapi_result(api_data)
                                if api and self._is_fashion_relevant(api):
                                    apis.append(api)

                except Exception as e:
                    logger.error(f"Error searching RapidAPI for '{term}': {e}")

        return apis

    async def _discover_apis_guru(
        self, config: Dict[str, Any], categories: List[APICategory]
    ) -> List[APIEndpoint]:
        """Discover APIs from APIs.guru"""

        apis = []

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{config['base_url']}{config['list_endpoint']}"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()

                        for provider, provider_apis in data.items():
                            for api_name, api_versions in provider_apis.items():
                                # Get the latest version
                                latest_version = max(api_versions.keys())
                                api_info = api_versions[latest_version]

                                api = self._parse_apis_guru_result(
                                    provider, api_name, api_info
                                )
                                if api and self._is_fashion_relevant(api):
                                    apis.append(api)

            except Exception as e:
                logger.error(f"Error discovering from APIs.guru: {e}")

        return apis

    async def _discover_fashion_specific_apis(
        self, config: Dict[str, Any]
    ) -> List[APIEndpoint]:
        """Discover fashion-specific APIs from known sources"""

        apis = []

        # Predefined fashion and ecommerce APIs
        fashion_apis = [
            {
                "name": "Shopify Admin API",
                "description": "Complete ecommerce platform API for fashion retailers",
                "base_url": "https://your-shop.myshopify.com/admin/api/2023-10",
                "category": APICategory.PRODUCT_CATALOG,
                "provider": "Shopify",
                "authentication": AuthenticationType.API_KEY,
                "features": [
                    "products",
                    "inventory",
                    "orders",
                    "customers",
                    "analytics",
                ],
                "fashion_relevance": 0.95,
            },
            {
                "name": "WooCommerce REST API",
                "description": "WordPress ecommerce API for fashion stores",
                "base_url": "https://your-site.com/wp-json/wc/v3",
                "category": APICategory.PRODUCT_CATALOG,
                "provider": "WooCommerce",
                "authentication": AuthenticationType.OAUTH2,
                "features": ["products", "orders", "customers", "coupons"],
                "fashion_relevance": 0.90,
            },
            {
                "name": "Pinterest API",
                "description": "Visual discovery platform API for fashion inspiration",
                "base_url": "https://api.pinterest.com/v5",
                "category": APICategory.FASHION_TRENDS,
                "provider": "Pinterest",
                "authentication": AuthenticationType.OAUTH2,
                "features": ["boards", "pins", "trends", "analytics"],
                "fashion_relevance": 0.85,
            },
            {
                "name": "Instagram Basic Display API",
                "description": "Social media API for fashion brand content",
                "base_url": "https://graph.instagram.com",
                "category": APICategory.CONTENT_GENERATION,
                "provider": "Meta",
                "authentication": AuthenticationType.OAUTH2,
                "features": ["media", "user_profile", "insights"],
                "fashion_relevance": 0.80,
            },
            {
                "name": "Stripe API",
                "description": "Payment processing API for fashion e-commerce",
                "base_url": "https://api.stripe.com/v1",
                "category": APICategory.PAYMENT_PROCESSING,
                "provider": "Stripe",
                "authentication": AuthenticationType.API_KEY,
                "features": ["payments", "subscriptions", "invoices", "analytics"],
                "fashion_relevance": 0.75,
            },
            {
                "name": "OpenAI API",
                "description": "AI-powered content generation for fashion descriptions",
                "base_url": "https://api.openai.com/v1",
                "category": APICategory.CONTENT_GENERATION,
                "provider": "OpenAI",
                "authentication": AuthenticationType.BEARER_TOKEN,
                "features": ["text_generation", "image_generation", "embeddings"],
                "fashion_relevance": 0.70,
            },
            {
                "name": "AWS API Gateway",
                "description": "Cloud infrastructure API for scalable fashion platforms",
                "base_url": "https://apigateway.us-east-1.amazonaws.com",
                "category": APICategory.CLOUD_INFRASTRUCTURE,
                "provider": "Amazon Web Services",
                "authentication": AuthenticationType.CUSTOM,
                "features": ["api_management", "scaling", "monitoring", "security"],
                "fashion_relevance": 0.60,
            },
        ]

        for api_data in fashion_apis:
            api = APIEndpoint(
                api_id=hashlib.sha256(
                    f"{api_data['provider']}_{api_data['name']}".encode()
                ).hexdigest(),
                name=api_data["name"],
                description=api_data["description"],
                base_url=api_data["base_url"],
                version="latest",
                category=api_data["category"],
                provider=api_data["provider"],
                authentication=api_data["authentication"],
                rate_limits={"requests_per_minute": 1000},  # Default
                pricing={"tier": "freemium"},  # Default
                features=api_data["features"],
                supported_formats=["json"],
                documentation_url=f"https://docs.{api_data['provider'].lower().replace(' ', '')}.com",
                status=APIStatus.ACTIVE,
                reliability_score=0.0,  # Will be calculated
                performance_score=0.0,  # Will be calculated
                cost_score=0.0,  # Will be calculated
                feature_score=0.0,  # Will be calculated
                overall_score=0.0,  # Will be calculated
                last_evaluated=datetime.now(),
                fashion_relevance=api_data["fashion_relevance"],
                sustainability_support=False,  # Will be determined during evaluation
            )
            apis.append(api)

        return apis

    def _parse_rapidapi_result(self, api_data: Dict[str, Any]) -> Optional[APIEndpoint]:
        """Parse RapidAPI search result"""
        try:
            return APIEndpoint(
                api_id=api_data.get("id", ""),
                name=api_data.get("name", ""),
                description=api_data.get("description", ""),
                base_url=api_data.get("baseUrl", ""),
                version=api_data.get("version", "v1"),
                category=self._determine_category(api_data),
                provider=api_data.get("provider", {}).get("name", ""),
                authentication=self._determine_auth_type(api_data),
                rate_limits=api_data.get("rateLimits", {}),
                pricing=api_data.get("pricing", {}),
                features=api_data.get("features", []),
                supported_formats=api_data.get("formats", ["json"]),
                documentation_url=api_data.get("documentationUrl", ""),
                status=APIStatus.ACTIVE,
                reliability_score=0.0,
                performance_score=0.0,
                cost_score=0.0,
                feature_score=0.0,
                overall_score=0.0,
                last_evaluated=datetime.now(),
                fashion_relevance=0.0,
                sustainability_support=False,
            )
        except Exception as e:
            logger.error(f"Error parsing RapidAPI result: {e}")
            return None

    def _parse_apis_guru_result(
        self, provider: str, api_name: str, api_info: Dict[str, Any]
    ) -> Optional[APIEndpoint]:
        """Parse APIs.guru result"""
        try:
            swagger_url = api_info.get("swaggerUrl", "")

            return APIEndpoint(
                api_id=hashlib.sha256(f"{provider}_{api_name}".encode()).hexdigest(),
                name=api_info.get("info", {}).get("title", api_name),
                description=api_info.get("info", {}).get("description", ""),
                base_url=(
                    swagger_url.replace("/swagger.json", "") if swagger_url else ""
                ),
                version=api_info.get("info", {}).get("version", "v1"),
                category=self._determine_category_from_text(
                    api_info.get("info", {}).get("description", "")
                ),
                provider=provider,
                authentication=AuthenticationType.API_KEY,  # Default assumption
                rate_limits={},
                pricing={},
                features=[],
                supported_formats=["json"],
                documentation_url=swagger_url,
                status=APIStatus.ACTIVE,
                reliability_score=0.0,
                performance_score=0.0,
                cost_score=0.0,
                feature_score=0.0,
                overall_score=0.0,
                last_evaluated=datetime.now(),
                fashion_relevance=0.0,
                sustainability_support=False,
            )
        except Exception as e:
            logger.error(f"Error parsing APIs.guru result: {e}")
            return None

    def _determine_category(self, api_data: Dict[str, Any]) -> APICategory:
        """Determine API category from data"""
        name = api_data.get("name", "").lower()
        description = api_data.get("description", "").lower()
        tags = [tag.lower() for tag in api_data.get("tags", [])]

        text = f"{name} {description} {' '.join(tags)}"

        return self._determine_category_from_text(text)

    def _determine_category_from_text(self, text: str) -> APICategory:
        """Determine API category from text content"""
        text_lower = text.lower()

        # Fashion and trends
        if any(
            keyword in text_lower
            for keyword in self.fashion_api_patterns["fashion_keywords"]
        ):
            return APICategory.FASHION_TRENDS

        # E-commerce and retail
        if any(
            keyword in text_lower for keyword in ["inventory", "stock", "warehouse"]
        ):
            return APICategory.INVENTORY_MANAGEMENT

        if any(keyword in text_lower for keyword in ["product", "catalog", "item"]):
            return APICategory.PRODUCT_CATALOG

        if any(
            keyword in text_lower for keyword in ["customer", "analytics", "behavior"]
        ):
            return APICategory.CUSTOMER_ANALYTICS

        if any(
            keyword in text_lower for keyword in ["payment", "billing", "transaction"]
        ):
            return APICategory.PAYMENT_PROCESSING

        # Content and design
        if any(
            keyword in text_lower for keyword in ["image", "video", "content", "media"]
        ):
            return APICategory.CONTENT_GENERATION

        if any(
            keyword in text_lower for keyword in ["design", "css", "theme", "template"]
        ):
            return APICategory.DESIGN_AUTOMATION

        # Infrastructure
        if any(keyword in text_lower for keyword in ["cloud", "aws", "azure", "gcp"]):
            return APICategory.CLOUD_INFRASTRUCTURE

        if any(
            keyword in text_lower for keyword in ["deploy", "ci/cd", "devops", "git"]
        ):
            return APICategory.DEVOPS_AUTOMATION

        # Business intelligence
        if any(
            keyword in text_lower
            for keyword in self.fashion_api_patterns["business_keywords"]
        ):
            return APICategory.BUSINESS_INTELLIGENCE

        # Default to product catalog for e-commerce
        return APICategory.PRODUCT_CATALOG

    def _determine_auth_type(self, api_data: Dict[str, Any]) -> AuthenticationType:
        """Determine authentication type from API data"""
        auth_info = api_data.get("authentication", {})

        if "oauth" in str(auth_info).lower():
            return AuthenticationType.OAUTH2
        elif "jwt" in str(auth_info).lower():
            return AuthenticationType.JWT
        elif "bearer" in str(auth_info).lower():
            return AuthenticationType.BEARER_TOKEN
        elif "basic" in str(auth_info).lower():
            return AuthenticationType.BASIC_AUTH
        else:
            return AuthenticationType.API_KEY

    def _is_fashion_relevant(self, api: APIEndpoint) -> bool:
        """Check if API is relevant to fashion e-commerce"""
        text = f"{api.name} {api.description} {' '.join(api.features)}".lower()

        # Check for fashion keywords
        fashion_keywords = (
            self.fashion_api_patterns["fashion_keywords"]
            + self.fashion_api_patterns["ecommerce_keywords"]
            + self.fashion_api_patterns["business_keywords"]
        )

        relevance_count = sum(1 for keyword in fashion_keywords if keyword in text)

        # Consider relevant if it has at least 2 fashion-related keywords
        # or if it's in a relevant category
        return relevance_count >= 2 or api.category in [
            APICategory.FASHION_TRENDS,
            APICategory.INVENTORY_MANAGEMENT,
            APICategory.PRODUCT_CATALOG,
            APICategory.CUSTOMER_ANALYTICS,
        ]

    async def _evaluate_api(self, api: APIEndpoint):
        """Evaluate API and calculate scores"""

        # Reliability score (based on provider reputation and status)
        reliability_score = await self._calculate_reliability_score(api)

        # Performance score (based on response times and uptime)
        performance_score = await self._calculate_performance_score(api)

        # Cost score (based on pricing model)
        cost_score = await self._calculate_cost_score(api)

        # Feature score (based on available features)
        feature_score = await self._calculate_feature_score(api)

        # Fashion relevance score
        fashion_relevance = await self._calculate_fashion_relevance(api)

        # Calculate overall score
        criteria = self.evaluation_criteria
        overall_score = (
            reliability_score * criteria.reliability_weight
            + performance_score * criteria.performance_weight
            + cost_score * criteria.cost_weight
            + feature_score * criteria.features_weight
            + fashion_relevance * criteria.fashion_relevance_weight
        )

        # Update API scores
        api.reliability_score = reliability_score
        api.performance_score = performance_score
        api.cost_score = cost_score
        api.feature_score = feature_score
        api.fashion_relevance = fashion_relevance
        api.overall_score = overall_score
        api.last_evaluated = datetime.now()

        # Check sustainability support
        api.sustainability_support = await self._check_sustainability_support(api)

    async def _calculate_reliability_score(self, api: APIEndpoint) -> float:
        """Calculate API reliability score"""

        # Base score from provider reputation
        provider_scores = {
            "shopify": 0.95,
            "stripe": 0.95,
            "amazon web services": 0.90,
            "google": 0.90,
            "microsoft": 0.85,
            "meta": 0.80,
            "pinterest": 0.75,
            "woocommerce": 0.70,
        }

        base_score = provider_scores.get(api.provider.lower(), 0.60)

        # Adjust based on status
        status_multipliers = {
            APIStatus.ACTIVE: 1.0,
            APIStatus.BETA: 0.8,
            APIStatus.DEPRECATED: 0.4,
            APIStatus.MAINTENANCE: 0.6,
            APIStatus.UNAVAILABLE: 0.0,
        }

        return base_score * status_multipliers.get(api.status, 0.5)

    async def _calculate_performance_score(self, api: APIEndpoint) -> float:
        """Calculate API performance score"""

        # Simulate performance testing (in production, you'd do actual tests)
        try:
            start_time = time.time()

            # Mock API health check
            async with aiohttp.ClientSession() as session:
                try:
                    # Try to access API documentation or health endpoint
                    async with session.get(
                        api.documentation_url, timeout=5
                    ) as response:
                        response_time = time.time() - start_time

                        if response.status == 200:
                            # Good response time scoring
                            if response_time < 0.5:
                                return 1.0
                            elif response_time < 1.0:
                                return 0.8
                            elif response_time < 2.0:
                                return 0.6
                            else:
                                return 0.4
                        else:
                            return 0.3

                except asyncio.TimeoutError:
                    return 0.2
                except Exception:
                    return 0.1

        except Exception:
            # Default score if we can't test
            return 0.5

    async def _calculate_cost_score(self, api: APIEndpoint) -> float:
        """Calculate API cost score (higher score = better value)"""

        pricing = api.pricing

        # Free tier gets highest score
        if pricing.get("tier") == "free" or pricing.get("free_tier", False):
            return 1.0

        # Freemium gets high score
        if pricing.get("tier") == "freemium":
            return 0.9

        # Pay-per-use gets good score
        if pricing.get("model") == "pay_per_use":
            return 0.7

        # Subscription models
        if pricing.get("model") == "subscription":
            monthly_cost = pricing.get("monthly_cost", 100)
            if monthly_cost < 50:
                return 0.8
            elif monthly_cost < 200:
                return 0.6
            else:
                return 0.4

        # Default for unknown pricing
        return 0.5

    async def _calculate_feature_score(self, api: APIEndpoint) -> float:
        """Calculate API feature score"""

        features = api.features
        feature_count = len(features)

        # Base score from feature count
        if feature_count >= 10:
            base_score = 1.0
        elif feature_count >= 5:
            base_score = 0.8
        elif feature_count >= 3:
            base_score = 0.6
        else:
            base_score = 0.4

        # Bonus for fashion-specific features
        fashion_features = [
            "trends",
            "style",
            "recommendation",
            "personalization",
            "analytics",
        ]
        fashion_bonus = sum()
            0.1
            for feature in features
            if any(ff in feature.lower() for ff in fashion_features)
        )

        return min(base_score + fashion_bonus, 1.0)

    async def _calculate_fashion_relevance(self, api: APIEndpoint) -> float:
        """Calculate fashion industry relevance score"""

        # Use fashion intelligence engine for context analysis
        context_text = f"{api.name} {api.description} {' '.join(api.features)}"
        fashion_context = await fashion_intelligence.analyze_fashion_context(
            context_text
        )

        return fashion_context.get("fashion_relevance_score", 0.0)

    async def _check_sustainability_support(self, api: APIEndpoint) -> bool:
        """Check if API supports sustainability features"""

        sustainability_keywords = [
            "sustainable",
            "sustainability",
            "eco",
            "green",
            "carbon",
            "circular",
            "ethical",
            "responsible",
            "environmental",
        ]

        text = f"{api.name} {api.description} {' '.join(api.features)}".lower()

        return any(keyword in text for keyword in sustainability_keywords)

    async def _get_cached_discovery_results(
        self, categories: List[APICategory]
    ) -> Optional[Dict[str, List[APIEndpoint]]]:
        """Get cached API discovery results"""

        cache_key = f"api_discovery:{':'.join(sorted(c.value for c in categories))}"

        try:
            cached_data = await redis_manager.get(cache_key, prefix="api_cache")
            if cached_data:
                # Convert back to APIEndpoint objects
                results = {}
                for category, api_list in cached_data.items():
                    results[category] = [
                        APIEndpoint(**api_data) for api_data in api_list
                    ]
                return results
        except Exception as e:
            logger.error(f"Error getting cached discovery results: {e}")

        return None

    async def _cache_discovery_results(self, results: Dict[str, List[APIEndpoint]]):
        """Cache API discovery results"""

        cache_key = f"api_discovery:{':'.join(sorted(results.keys()))}"

        try:
            # Convert to serializable format
            cache_data = {}
            for category, api_list in results.items():
                cache_data[category] = [api.to_dict() for api in api_list]

            # Cache for 24 hours
            await redis_manager.set(
                cache_key, cache_data, ttl=86400, prefix="api_cache"
            )

        except Exception as e:
            logger.error(f"Error caching discovery results: {e}")

    async def get_recommended_apis(
        self, category: APICategory, limit: int = 5, min_score: float = 0.6
    ) -> List[APIEndpoint]:
        """Get recommended APIs for a category"""

        # Filter APIs by category and minimum score
        category_apis = [
            api
            for api in self.discovered_apis.values()
            if api.category == category and api.overall_score >= min_score
        ]

        # Sort by overall score
        category_apis.sort(key=lambda x: x.overall_score, reverse=True)

        return category_apis[:limit]

    async def get_discovery_metrics(self) -> Dict[str, Any]:
        """Get API discovery metrics"""

        return {
            "discovery_metrics": self.discovery_metrics,
            "total_apis_in_registry": len(self.discovered_apis),
            "apis_by_category": {
                category.value: len()
                    [
                        api
                        for api in self.discovered_apis.values()
                        if api.category == category
                    ]
                )
                for category in APICategory
            },
            "top_providers": self._get_top_providers(),
            "authentication_distribution": self._get_auth_distribution(),
            "average_scores": self._get_average_scores(),
        }

    def _get_top_providers(self) -> List[Dict[str, Any]]:
        """Get top API providers by count and average score"""

        provider_stats = {}

        for api in self.discovered_apis.values():
            if api.provider not in provider_stats:
                provider_stats[api.provider] = {"count": 0, "total_score": 0.0}

            provider_stats[api.provider]["count"] += 1
            provider_stats[api.provider]["total_score"] += api.overall_score

        # Calculate average scores and sort
        top_providers = []
        for provider, stats in provider_stats.items():
            avg_score = stats["total_score"] / stats["count"]
            top_providers.append(
                {
                    "provider": provider,
                    "api_count": stats["count"],
                    "average_score": avg_score,
                }
            )

        return sorted(top_providers, key=lambda x: x["average_score"], reverse=True)[
            :10
        ]

    def _get_auth_distribution(self) -> Dict[str, int]:
        """Get authentication type distribution"""

        auth_counts = {}
        for api in self.discovered_apis.values():
            auth_type = api.authentication.value
            auth_counts[auth_type] = auth_counts.get(auth_type, 0) + 1

        return auth_counts

    def _get_average_scores(self) -> Dict[str, float]:
        """Get average scores across all APIs"""

        if not self.discovered_apis:
            return {}

        total_apis = len(self.discovered_apis)

        return {
            "reliability": sum()
                api.reliability_score for api in self.discovered_apis.values()
            )
            / total_apis,
            "performance": sum()
                api.performance_score for api in self.discovered_apis.values()
            )
            / total_apis,
            "cost": sum(api.cost_score for api in self.discovered_apis.values())
            / total_apis,
            "features": sum(api.feature_score for api in self.discovered_apis.values())
            / total_apis,
            "fashion_relevance": sum()
                api.fashion_relevance for api in self.discovered_apis.values()
            )
            / total_apis,
            "overall": sum(api.overall_score for api in self.discovered_apis.values())
            / total_apis,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check for API discovery engine"""

        try:
            metrics = await self.get_discovery_metrics()

            return {
                "status": "healthy",
                "discovery_engine": "operational",
                "total_apis_discovered": metrics["total_apis_in_registry"],
                "discovery_sources": len(self.discovery_sources),
                "last_discovery_run": self.discovery_metrics.get("last_discovery_run"),
                "cache_status": "operational",
                "fashion_intelligence_integration": "active",
                "metrics": metrics,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# Global API discovery engine instance
api_discovery_engine = APIDiscoveryEngine()
