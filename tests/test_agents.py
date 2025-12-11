"""
Agent API Tests
===============

Tests for AI agent endpoints:
- Agent discovery
- Task execution
- Social media
- Email/SMS
- Customer service
- Content generation
- Brand intelligence
"""

import pytest

pytestmark = [pytest.mark.integration]


class TestAgentDiscovery:
    """Agent discovery tests"""

    @pytest.mark.asyncio
    async def test_list_all_agents(self, client, auth_headers):
        """Test listing all agents"""
        response = await client.get("/api/v1/agents/", headers=auth_headers)

        assert response.status_code == 200
        agents = response.json()

        assert isinstance(agents, list)
        assert len(agents) > 0

        # Check agent structure
        agent = agents[0]
        assert "name" in agent
        assert "category" in agent
        assert "description" in agent
        assert "actions" in agent

    @pytest.mark.asyncio
    async def test_filter_agents_by_category(self, client, auth_headers):
        """Test filtering agents by category"""
        response = await client.get(
            "/api/v1/agents/", headers=auth_headers, params={"category": "social_media"}
        )

        assert response.status_code == 200
        agents = response.json()

        for agent in agents:
            assert agent["category"] == "social_media"

    @pytest.mark.asyncio
    async def test_get_single_agent(self, client, auth_headers):
        """Test getting single agent details"""
        response = await client.get("/api/v1/agents/instagram_agent", headers=auth_headers)

        assert response.status_code == 200
        agent = response.json()

        assert agent["name"] == "instagram_agent"
        assert "post" in agent["actions"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, client, auth_headers):
        """Test getting nonexistent agent returns 404"""
        response = await client.get("/api/v1/agents/fake_agent_xyz", headers=auth_headers)

        assert response.status_code == 404


class TestTaskExecution:
    """Task execution tests"""

    @pytest.mark.asyncio
    async def test_execute_agent_task(self, client, auth_headers, agent_task):
        """Test executing an agent task"""
        response = await client.post(
            "/api/v1/agents/execute", headers=auth_headers, json=agent_task
        )

        assert response.status_code == 200
        task = response.json()

        assert "task_id" in task
        assert task["task_id"].startswith("task_")
        assert task["agent_name"] == agent_task["agent_name"]
        assert task["action"] == agent_task["action"]
        assert task["status"] in ["running", "completed"]

    @pytest.mark.asyncio
    async def test_execute_invalid_action(self, client, auth_headers):
        """Test executing invalid action returns error"""
        response = await client.post(
            "/api/v1/agents/execute",
            headers=auth_headers,
            json={
                "agent_name": "instagram_agent",
                "action": "invalid_action_xyz",
                "parameters": {},
            },
        )

        assert response.status_code == 400
        assert "Invalid action" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_task_status(self, client, auth_headers, agent_task):
        """Test getting task status"""
        # Execute task first
        exec_response = await client.post(
            "/api/v1/agents/execute", headers=auth_headers, json=agent_task
        )
        task_id = exec_response.json()["task_id"]

        # Get status
        status_response = await client.get(f"/api/v1/agents/tasks/{task_id}", headers=auth_headers)

        assert status_response.status_code == 200
        assert status_response.json()["task_id"] == task_id


class TestSocialMediaAgents:
    """Social media agent tests"""

    @pytest.mark.asyncio
    async def test_create_social_post(self, client, auth_headers):
        """Test creating social media post"""
        response = await client.post(
            "/api/v1/agents/social/post",
            headers=auth_headers,
            json={
                "platform": "instagram",
                "content": "Test post from DevSkyy 🌹",
                "hashtags": ["skyyrose", "luxury", "streetwear"],
                "media_urls": [],
            },
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "instagram_agent"
        assert task["action"] == "post"

    @pytest.mark.asyncio
    async def test_get_social_analytics(self, client, auth_headers):
        """Test getting social analytics"""
        response = await client.get(
            "/api/v1/agents/social/analytics",
            headers=auth_headers,
            params={
                "platform": "instagram",
                "metrics": ["engagement", "reach"],
                "date_range_days": 30,
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_schedule_social_post(self, client, auth_headers):
        """Test scheduling social post for future"""
        from datetime import datetime, timedelta

        future_time = datetime.now() + timedelta(hours=24)

        response = await client.post(
            "/api/v1/agents/social/post",
            headers=auth_headers,
            json={
                "platform": "twitter",
                "content": "Scheduled post test",
                "schedule_time": future_time.isoformat(),
            },
        )

        assert response.status_code == 200


class TestEmailSMSAgents:
    """Email and SMS agent tests"""

    @pytest.mark.asyncio
    async def test_send_email(self, client, auth_headers):
        """Test sending email"""
        response = await client.post(
            "/api/v1/agents/email/send",
            headers=auth_headers,
            json={
                "to": ["test@example.com"],
                "subject": "Test Email from DevSkyy",
                "body": "This is a test email.",
                "personalization": {"name": "Test User"},
            },
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "email_campaign_agent"

    @pytest.mark.asyncio
    async def test_send_sms(self, client, auth_headers):
        """Test sending SMS"""
        response = await client.post(
            "/api/v1/agents/sms/send",
            headers=auth_headers,
            json={"to": ["+15551234567"], "message": "Test SMS from DevSkyy"},
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "sms_agent"

    @pytest.mark.asyncio
    async def test_create_email_campaign(self, client, auth_headers):
        """Test creating email campaign"""
        response = await client.post(
            "/api/v1/agents/campaign/create",
            headers=auth_headers,
            json={
                "name": "Test Campaign",
                "type": "email",
                "audience_segment": "vip_customers",
                "content": {
                    "subject": "Special Offer",
                    "body": "Exclusive deal for VIP customers",
                },
            },
        )

        assert response.status_code == 200


class TestCustomerServiceAgents:
    """Customer service agent tests"""

    @pytest.mark.asyncio
    async def test_create_support_ticket(self, client, auth_headers):
        """Test creating support ticket"""
        response = await client.post(
            "/api/v1/agents/support/ticket",
            headers=auth_headers,
            json={
                "customer_id": "cust_001",
                "subject": "Order not received",
                "description": "I placed order #123 last week but haven't received it.",
                "priority": "high",
                "category": "shipping",
            },
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "support_ticket_agent"

    @pytest.mark.asyncio
    async def test_chatbot_interaction(self, client, auth_headers):
        """Test chatbot interaction"""
        response = await client.post(
            "/api/v1/agents/support/chat",
            headers=auth_headers,
            json={
                "session_id": "sess_001",
                "message": "What's the status of my order?",
                "context": {"customer_id": "cust_001"},
            },
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "chatbot_agent"


class TestContentAgents:
    """Content generation agent tests"""

    @pytest.mark.asyncio
    async def test_generate_blog_post(self, client, auth_headers):
        """Test generating blog post"""
        response = await client.post(
            "/api/v1/agents/content/generate",
            headers=auth_headers,
            json={
                "type": "blog_post",
                "topic": "Summer Fashion Trends 2025",
                "keywords": ["summer", "fashion", "luxury", "streetwear"],
                "tone": "professional",
                "length": "medium",
            },
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "blog_writer_agent"

    @pytest.mark.asyncio
    async def test_generate_product_description(self, client, auth_headers):
        """Test generating product description"""
        response = await client.post(
            "/api/v1/agents/content/generate",
            headers=auth_headers,
            json={
                "type": "product_description",
                "topic": "Rose Gold Luxury Hoodie",
                "keywords": ["luxury", "comfort", "streetwear"],
                "brand_voice": True,
            },
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "product_description_agent"

    @pytest.mark.asyncio
    async def test_generate_ad_copy(self, client, auth_headers):
        """Test generating ad copy"""
        response = await client.post(
            "/api/v1/agents/content/generate",
            headers=auth_headers,
            json={
                "type": "ad_copy",
                "topic": "BLACK ROSE Collection Launch",
                "keywords": ["exclusive", "limited", "luxury"],
                "length": "short",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_seo_optimization(self, client, auth_headers):
        """Test SEO optimization"""
        response = await client.post(
            "/api/v1/agents/seo/optimize",
            headers=auth_headers,
            json={
                "content": "Sample content to optimize for search engines.",
                "target_keywords": ["luxury streetwear", "rose gold fashion"],
                "competitor_urls": [],
            },
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "seo_content_agent"


class TestBrandIntelligence:
    """Brand intelligence agent tests"""

    @pytest.mark.asyncio
    async def test_get_brand_mentions(self, client, auth_headers):
        """Test getting brand mentions"""
        response = await client.get(
            "/api/v1/agents/brand/mentions", headers=auth_headers, params={"days": 7}
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "brand_monitor_agent"

    @pytest.mark.asyncio
    async def test_competitor_analysis(self, client, auth_headers):
        """Test competitor analysis"""
        response = await client.get(
            "/api/v1/agents/competitors/analysis",
            headers=auth_headers,
            params={"competitor_ids": ["comp_001", "comp_002"]},
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "competitor_agent"

    @pytest.mark.asyncio
    async def test_market_trends(self, client, auth_headers):
        """Test getting market trends"""
        response = await client.get(
            "/api/v1/agents/trends",
            headers=auth_headers,
            params={"category": "fashion"},
        )

        assert response.status_code == 200
        task = response.json()
        assert task["agent_name"] == "trend_agent"


class TestAgentAuthorization:
    """Agent authorization tests"""

    @pytest.mark.asyncio
    async def test_agents_require_auth(self, client):
        """Test agent endpoints require authentication"""
        response = await client.get("/api/v1/agents/")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_task_execution_requires_auth(self, client):
        """Test task execution requires authentication"""
        response = await client.post(
            "/api/v1/agents/execute",
            json={"agent_name": "instagram_agent", "action": "post", "parameters": {}},
        )

        assert response.status_code == 401


class TestAgentCategories:
    """Test all agent categories are accessible"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "category",
        [
            "social_media",
            "email_sms",
            "customer_service",
            "content",
            "brand",
            "integration",
        ],
    )
    async def test_category_has_agents(self, client, auth_headers, category):
        """Test each category has agents"""
        response = await client.get(
            "/api/v1/agents/", headers=auth_headers, params={"category": category}
        )

        assert response.status_code == 200
        agents = response.json()
        assert len(agents) > 0, f"Category {category} should have agents"
