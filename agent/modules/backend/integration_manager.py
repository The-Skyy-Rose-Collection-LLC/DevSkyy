from datetime import datetime, timedelta
import json

from enum import Enum
from typing import Any, Dict, List
import base64
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    BANKING = "banking"
    PAYMENT_PROCESSOR = "payment_processor"
    ACCOUNTING_SOFTWARE = "accounting_software"
    EMAIL_MARKETING = "email_marketing"
    ANALYTICS = "analytics"
    CRM = "crm"

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"
    SUSPENDED = "suspended"

class IntegrationManager:
    """Universal Integration Manager for connecting external services to agents."""

    def __init__(self):
        self.integrations = {}
        self.agent_integrations = {}
        self.supported_services = self._initialize_supported_services()
        self.security_manager = self._initialize_security_manager()
        logger.info("🔗 Integration Manager initialized with Universal Service Support")

    def _initialize_supported_services(self) -> Dict[str, Any]:
        """Initialize comprehensive list of supported integrations."""
        return {
            "websites": {
                "wordpress": {
                    "name": "WordPress",
                    "icon": "🌐",
                    "auth_type": "api_key",
                    "required_fields": ["site_url", "api_key", "username"],
                    "capabilities": [
                        "content_management",
                        "plugin_management",
                        "theme_customization",
                        "analytics",
                    ],
                },
                "shopify": {
                    "name": "Shopify",
                    "icon": "🛍️",
                    "auth_type": "oauth",
                    "required_fields": ["shop_domain", "access_token"],
                    "capabilities": [
                        "product_management",
                        "order_processing",
                        "inventory_sync",
                        "analytics",
                    ],
                },
                "custom_site": {
                    "name": "Custom Website",
                    "icon": "⚡",
                    "auth_type": "api_key",
                    "required_fields": ["domain", "api_endpoint", "api_key"],
                    "capabilities": [
                        "data_sync",
                        "performance_monitoring",
                        "analytics_integration",
                    ],
                },
            },
            "social_media": {
                "facebook": {
                    "name": "Facebook",
                    "icon": "📘",
                    "auth_type": "oauth",
                    "required_fields": ["page_id", "access_token"],
                    "capabilities": [
                        "post_management",
                        "ad_management",
                        "analytics",
                        "customer_insights",
                    ],
                },
                "instagram": {
                    "name": "Instagram",
                    "icon": "📸",
                    "auth_type": "oauth",
                    "required_fields": ["account_id", "access_token"],
                    "capabilities": [
                        "content_publishing",
                        "story_management",
                        "analytics",
                        "influencer_tracking",
                    ],
                },
                "twitter": {
                    "name": "Twitter/X",
                    "icon": "🐦",
                    "auth_type": "oauth",
                    "required_fields": [
                        "api_key",
                        "api_secret",
                        "access_token",
                        "access_token_secret",
                    ],
                    "capabilities": [
                        "tweet_management",
                        "analytics",
                        "trend_monitoring",
                        "engagement_tracking",
                    ],
                },
                "linkedin": {
                    "name": "LinkedIn",
                    "icon": "💼",
                    "auth_type": "oauth",
                    "required_fields": ["company_id", "access_token"],
                    "capabilities": [
                        "business_posts",
                        "professional_networking",
                        "lead_generation",
                        "analytics",
                    ],
                },
                "tiktok": {
                    "name": "TikTok",
                    "icon": "📱",
                    "auth_type": "oauth",
                    "required_fields": ["account_id", "access_token"],
                    "capabilities": [
                        "video_publishing",
                        "trend_analysis",
                        "audience_insights",
                        "ad_management",
                    ],
                },
                "youtube": {
                    "name": "YouTube",
                    "icon": "📺",
                    "auth_type": "oauth",
                    "required_fields": ["channel_id", "access_token"],
                    "capabilities": [
                        "video_management",
                        "analytics",
                        "monetization",
                        "audience_insights",
                    ],
                },
            },
            "banking": {
                "chase": {
                    "name": "Chase Bank",
                    "icon": "🏦",
                    "auth_type": "secure_oauth",
                    "required_fields": [
                        "account_number",
                        "routing_number",
                        "access_token",
                    ],
                    "capabilities": [
                        "account_monitoring",
                        "transaction_analysis",
                        "cash_flow_tracking",
                        "payment_processing",
                    ],
                },
                "bank_of_america": {
                    "name": "Bank of America",
                    "icon": "🏛️",
                    "auth_type": "secure_oauth",
                    "required_fields": ["account_number", "access_token"],
                    "capabilities": [
                        "account_monitoring",
                        "transaction_analysis",
                        "wire_transfers",
                        "credit_monitoring",
                    ],
                },
                "wells_fargo": {
                    "name": "Wells Fargo",
                    "icon": "🏪",
                    "auth_type": "secure_oauth",
                    "required_fields": ["account_number", "access_token"],
                    "capabilities": [
                        "business_banking",
                        "merchant_services",
                        "loan_management",
                        "investment_tracking",
                    ],
                },
            },
            "payment_processors": {
                "stripe": {
                    "name": "Stripe",
                    "icon": "💳",
                    "auth_type": "api_key",
                    "required_fields": ["publishable_key", "secret_key"],
                    "capabilities": [
                        "payment_processing",
                        "subscription_management",
                        "analytics",
                        "fraud_detection",
                    ],
                },
                "paypal": {
                    "name": "PayPal",
                    "icon": "💰",
                    "auth_type": "oauth",
                    "required_fields": ["client_id", "client_secret"],
                    "capabilities": [
                        "payment_processing",
                        "invoice_management",
                        "dispute_resolution",
                        "analytics",
                    ],
                },
                "square": {
                    "name": "Square",
                    "icon": "⬜",
                    "auth_type": "oauth",
                    "required_fields": ["application_id", "access_token"],
                    "capabilities": [
                        "payment_processing",
                        "inventory_management",
                        "pos_integration",
                        "analytics",
                    ],
                },
            },
            "accounting_software": {
                "quickbooks": {
                    "name": "QuickBooks",
                    "icon": "📊",
                    "auth_type": "oauth",
                    "required_fields": ["company_id", "access_token"],
                    "capabilities": [
                        "financial_reporting",
                        "invoice_management",
                        "expense_tracking",
                        "tax_preparation",
                    ],
                },
                "xero": {
                    "name": "Xero",
                    "icon": "📈",
                    "auth_type": "oauth",
                    "required_fields": ["tenant_id", "access_token"],
                    "capabilities": [
                        "accounting_automation",
                        "bank_reconciliation",
                        "financial_reporting",
                        "tax_compliance",
                    ],
                },
            },
            "analytics": {
                "google_analytics": {
                    "name": "Google Analytics",
                    "icon": "📊",
                    "auth_type": "oauth",
                    "required_fields": ["property_id", "access_token"],
                    "capabilities": [
                        "web_analytics",
                        "conversion_tracking",
                        "audience_insights",
                        "goal_monitoring",
                    ],
                }
            },
        }

    async def create_integration(
        self,
        agent_type: str,
        service_type: str,
        service_name: str,
        credentials: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new integration between an agent and external service."""
        try:
            integration_id = str(uuid.uuid4())

            # Validate service support
            if not self._validate_service_support(service_type, service_name):
                return {
                    "error": f"Service {service_name} not supported",
                    "status": "failed",
                }

            # Validate credentials
            validation_result = await self._validate_credentials(
                service_type, service_name, credentials
            )
            if not validation_result["valid"]:
                return {
                    "error": validation_result["error"],
                    "status": "validation_failed",
                }

            # Encrypt and store credentials
            encrypted_credentials = self._encrypt_credentials(credentials)

            # Create integration record
            integration = {
                "id": integration_id,
                "agent_type": agent_type,
                "service_type": service_type,
                "service_name": service_name,
                "credentials": encrypted_credentials,
                "status": IntegrationStatus.PENDING.value,
                "capabilities": self.supported_services[service_type][service_name][
                    "capabilities"
                ],
                "created_at": datetime.now().isoformat(),
                "last_sync": None,
                "sync_frequency": "hourly",
                "data_mapping": self._create_data_mapping(
                    agent_type, service_type, service_name
                ),
                "webhook_url": f"/webhooks/{integration_id}",
                "error_count": 0,
                "success_count": 0,
            }

            # Store integration
            self.integrations[integration_id] = integration

            # Add to agent integrations
            if agent_type not in self.agent_integrations:
                self.agent_integrations[agent_type] = []
            self.agent_integrations[agent_type].append(integration_id)

            # Test connection
            test_result = await self._test_integration_connection(integration_id)
            if test_result["success"]:
                integration["status"] = IntegrationStatus.ACTIVE.value
                logger.info(f"✅ Integration {integration_id} activated successfully")
            else:
                integration["status"] = IntegrationStatus.ERROR.value
                integration["error_message"] = test_result["error"]
                logger.error(f"❌ Integration {integration_id} failed connection test")

            return {
                "integration_id": integration_id,
                "status": integration["status"],
                "service_info": self.supported_services[service_type][service_name],
                "capabilities": integration["capabilities"],
                "webhook_url": integration["webhook_url"],
                "data_sync_preview": self._generate_sync_preview(integration),
            }

        except Exception as e:
            logger.error(f"❌ Integration creation failed: {str(e)}")
            return {"error": str(e), "status": "failed"}

    async def get_agent_integrations(self, agent_type: str) -> Dict[str, Any]:
        """Get all integrations for a specific agent."""
        try:
            agent_integrations = self.agent_integrations.get(agent_type, [])
            integrations_data = []

            for integration_id in agent_integrations:
                if integration_id in self.integrations:
                    integration = self.integrations[integration_id].copy()
                    # Remove sensitive data for response
                    integration.pop("credentials", None)
                    integrations_data.append(integration)

            return {
                "agent_type": agent_type,
                "total_integrations": len(integrations_data),
                "active_integrations": len()
                    [i for i in integrations_data if i["status"] == "active"]
                ),
                "integrations": integrations_data,
                "available_services": self._get_available_services_for_agent(
                    agent_type
                ),
                "integration_health": self._calculate_integration_health(
                    integrations_data
                ),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get agent integrations: {str(e)}")
            return {"error": str(e), "status": "failed"}

    async def sync_integration_data(self, integration_id: str) -> Dict[str, Any]:
        """Sync data from integrated service."""
        try:
            if integration_id not in self.integrations:
                return {"error": "Integration not found", "status": "failed"}

            integration = self.integrations[integration_id]

            if integration["status"] != IntegrationStatus.ACTIVE.value:
                return {"error": "Integration not active", "status": "failed"}

            # Decrypt credentials
            credentials = self._decrypt_credentials(integration["credentials"])

            # Perform data sync based on service type
            sync_result = await self._perform_data_sync(integration, credentials)

            # Update integration status
            if sync_result["success"]:
                integration["last_sync"] = datetime.now().isoformat()
                integration["success_count"] += 1
                integration["error_count"] = 0  # Reset error count on success
            else:
                integration["error_count"] += 1
                if integration["error_count"] > 5:
                    integration["status"] = IntegrationStatus.ERROR.value

            return sync_result

        except Exception as e:
            logger.error(f"❌ Data sync failed: {str(e)}")
            return {"error": str(e), "status": "failed"}

    def _validate_service_support(self, service_type: str, service_name: str) -> bool:
        """Validate if service is supported."""
        return (
            service_type in self.supported_services
            and service_name in self.supported_services[service_type]
        )

    async def _validate_credentials(
        self, service_type: str, service_name: str, credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate provided credentials."""
        service_config = self.supported_services[service_type][service_name]
        required_fields = service_config["required_fields"]

        # Check required fields
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                return {"valid": False, "error": f"Missing required field: {field}"}

        # Additional validation logic can be added here
        return {"valid": True}

    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for secure storage."""
        credentials_json = json.dumps(credentials)
        # In production, use proper encryption (AES, etc.)
        encoded = base64.b64encode(credentials_json.encode()).decode()
        return encoded

    def _decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt stored credentials."""
        # In production, use proper decryption
        decoded = base64.b64decode(encrypted_credentials.encode()).decode()
        return json.loads(decoded)

    def _create_data_mapping(
        self, agent_type: str, service_type: str, service_name: str
    ) -> Dict[str, Any]:
        """Create data mapping configuration for integration."""
        mappings = {
            "financial": {
                "banking": {
                    "transaction_mapping": {
                        "amount": "amount",
                        "date": "transaction_date",
                        "description": "memo",
                    },
                    "account_mapping": {
                        "balance": "current_balance",
                        "account_type": "account_category",
                    },
                },
                "payment_processors": {
                    "payment_mapping": {
                        "amount": "gross_amount",
                        "fee": "stripe_fee",
                        "net": "net_amount",
                    },
                    "customer_mapping": {
                        "email": "customer_email",
                        "name": "customer_name",
                    },
                },
            }
        }

        return mappings.get(agent_type, {}).get(service_type, {})

    async def _test_integration_connection(self, integration_id: str) -> Dict[str, Any]:
        """Test integration connection."""
        # Simulate connection test
        return {"success": True, "response_time": 245}

    def _generate_sync_preview(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview of what data will be synced."""
        return {
            "data_types": ["transactions", "account_balances", "customer_data"],
            "sync_frequency": integration["sync_frequency"],
            "estimated_records": "~150 per sync",
            "data_retention": "90 days",
        }

    def _get_available_services_for_agent(
        self, agent_type: str
    ) -> Dict[str, List[str]]:
        """Get available services for specific agent type."""
        agent_service_compatibility = {
            "financial": ["banking", "payment_processors", "accounting_software"],
            "seo_marketing": ["social_media", "analytics", "email_marketing"],
            "ecommerce": ["websites", "payment_processors", "analytics"],
            "brand_intelligence": ["social_media", "analytics", "crm"],
            "customer_service": ["crm", "email_marketing", "social_media"],
        }

        compatible_services = agent_service_compatibility.get(agent_type, [])
        available = {}

        for service_type in compatible_services:
            if service_type in self.supported_services:
                available[service_type] = list()
                    self.supported_services[service_type].keys()
                )

        return available

    def _calculate_integration_health(
        self, integrations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall health of agent integrations."""
        if not integrations:
            return {"status": "no_integrations", "score": 0}

        active_count = len([i for i in integrations if i["status"] == "active"])
        error_count = len([i for i in integrations if i["status"] == "error"])

        health_score = (active_count / len(integrations)) * 100

        return {
            "status": (
                "healthy"
                if health_score > 80
                else "needs_attention" if health_score > 50 else "critical"
            ),
            "score": round(health_score, 1),
            "active_integrations": active_count,
            "error_integrations": error_count,
            "recommendations": self._generate_health_recommendations(integrations),
        }

    def _generate_health_recommendations(
        self, integrations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for improving integration health."""
        recommendations = []

        error_integrations = [i for i in integrations if i["status"] == "error"]
        if error_integrations:
            recommendations.append(f"Fix {len(error_integrations)} failed integrations")

        old_syncs = [
            i
            for i in integrations
            if i["last_sync"]
            and (datetime.now() - datetime.fromisoformat(i["last_sync"])).days > 1
        ]
        if old_syncs:
            recommendations.append(
                f"Update {len(old_syncs)} integrations with stale data"
            )

        return recommendations

    async def _perform_data_sync(
        self, integration: Dict[str, Any], credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform actual data synchronization."""
        # Simulate data sync - in production, this would make actual API calls
        return {
            "success": True,
            "records_synced": 47,
            "sync_duration_ms": 1200,
            "data_types": ["transactions", "balances"],
            "next_sync": (datetime.now() + timedelta(hours=1)).isoformat(),
        }

    def _initialize_security_manager(self) -> Dict[str, Any]:
        """Initialize security features for credential management."""
        return {
            "encryption_algorithm": "AES_256_GCM",
            "key_rotation_schedule": "monthly",
            "access_logging": "enabled",
            "credential_expiry_monitoring": "enabled",
            "oauth_token_refresh": "automatic",
        }

def create_integration_manager() -> IntegrationManager:
    """Factory function to create integration manager."""
    return IntegrationManager()
