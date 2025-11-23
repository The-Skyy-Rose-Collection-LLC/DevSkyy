"""
Tests for ml/rlvr/agent_upgrade_system.py

Target: 60%+ coverage

Tests cover:
- Agent upgrade system initialization
- Upgrade deployment
- Upgrade verification
- Status tracking
"""

import uuid

import pytest

from ml.rlvr.agent_upgrade_system import AgentUpgradeSystem
from ml.rlvr.reward_verifier import VerificationMethod


class TestAgentUpgradeSystem:
    """Test AgentUpgradeSystem"""

    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """Test system initialization"""
        system = AgentUpgradeSystem(mock_session)

        assert system.session is not None
        assert len(system.upgrade_catalog) > 0
        assert "scanner" in system.upgrade_catalog

    @pytest.mark.asyncio
    async def test_upgrade_catalog_structure(self, mock_session):
        """Test upgrade catalog has correct structure"""
        system = AgentUpgradeSystem(mock_session)

        for agent_type, upgrade in system.upgrade_catalog.items():
            assert "name" in upgrade
            assert "description" in upgrade
            assert "verification_methods" in upgrade
            assert "expected_improvement" in upgrade

    @pytest.mark.asyncio
    async def test_deploy_upgrade(self, mock_session):
        """Test deploying an upgrade"""
        system = AgentUpgradeSystem(mock_session)
        user_id = uuid.uuid4()

        result = await system.deploy_upgrade(
            agent_type="scanner",
            user_id=user_id,
            enable_ab_test=False,
        )

        assert "upgrade_id" in result
        assert "agent_type" in result
        assert result["agent_type"] == "scanner"
        assert "status" in result

    @pytest.mark.asyncio
    async def test_deploy_upgrade_with_ab_test(self, mock_session):
        """Test deploying upgrade with A/B testing"""
        system = AgentUpgradeSystem(mock_session)
        user_id = uuid.uuid4()

        result = await system.deploy_upgrade(
            agent_type="scanner",
            user_id=user_id,
            enable_ab_test=True,
        )

        assert result["ab_test_enabled"] is True

    @pytest.mark.asyncio
    async def test_deploy_unknown_agent(self, mock_session):
        """Test deploying to unknown agent raises error"""
        system = AgentUpgradeSystem(mock_session)
        user_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Unknown agent type"):
            await system.deploy_upgrade(
                agent_type="nonexistent_agent",
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_deploy_all_upgrades(self, mock_session):
        """Test deploying upgrades to all agents"""
        system = AgentUpgradeSystem(mock_session)
        user_id = uuid.uuid4()

        result = await system.deploy_all_upgrades(user_id)

        assert "total_agents" in result
        assert "successful_deployments" in result
        assert "failed_deployments" in result
        assert "deployments" in result

        assert result["total_agents"] == len(system.upgrade_catalog)

    @pytest.mark.asyncio
    async def test_get_upgrade_status(self, mock_session):
        """Test getting upgrade status"""
        system = AgentUpgradeSystem(mock_session)
        user_id = uuid.uuid4()

        # Deploy upgrade
        deploy_result = await system.deploy_upgrade(
            agent_type="scanner",
            user_id=user_id,
        )

        upgrade_id = uuid.UUID(deploy_result["upgrade_id"])

        # Get status
        status = await system.get_upgrade_status(upgrade_id)

        assert status is not None
        assert "upgrade_id" in status
        assert "agent_type" in status

    @pytest.mark.asyncio
    async def test_get_all_upgrades_status(self, mock_session):
        """Test getting all upgrades status"""
        system = AgentUpgradeSystem(mock_session)
        user_id = uuid.uuid4()

        # Deploy some upgrades
        await system.deploy_upgrade("scanner", user_id)
        await system.deploy_upgrade("multi_model_orchestrator", user_id)

        # Get all statuses
        result = await system.get_all_upgrades_status()

        assert "total_upgrades" in result
        assert "completed_verifications" in result
        assert "in_progress" in result
        assert "upgrades" in result

    @pytest.mark.asyncio
    async def test_calculate_progress(self, mock_session):
        """Test progress calculation"""
        system = AgentUpgradeSystem(mock_session)

        upgrade_info = {
            "agent_type": "scanner",
            "verification_pending": [
                VerificationMethod.CODE_ANALYSIS,
                VerificationMethod.TEST_EXECUTION,
            ],
        }

        progress = system._calculate_progress(upgrade_info)

        # Should be 33% (1 of 3 verifications complete)
        assert 30 <= progress <= 40

    @pytest.mark.asyncio
    async def test_upgrade_catalog_expected_improvements(self, mock_session):
        """Test all upgrades have expected improvement values"""
        system = AgentUpgradeSystem(mock_session)

        for agent_type, upgrade in system.upgrade_catalog.items():
            improvement = upgrade["expected_improvement"]

            # Should be between 0 and 1 (0% to 100%)
            assert 0 < improvement < 1.0
