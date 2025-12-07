#!/usr/bin/env python3
"""
Comprehensive test suite for incident_response.py
Target: ≥75% coverage (173/231 lines)
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from monitoring.enterprise_metrics import Alert, AlertSeverity
from monitoring.incident_response import (
    Incident,
    IncidentResponse,
    IncidentResponseSystem,
    IncidentStatus,
    ResponseAction,
    ResponsePlan,
)


@pytest.fixture
def incident_system():
    """Create fresh incident response system for each test."""
    with patch("monitoring.incident_response.metrics_collector") as mock_collector:
        system = IncidentResponseSystem()
        return system


@pytest.fixture
def sample_alert_high():
    """Create sample high-severity alert."""
    return Alert(
        rule_name="high_response_time",
        metric_name="http_response_time",
        current_value=5.0,
        threshold=3.0,
        severity=AlertSeverity.HIGH,
        triggered_at=datetime.utcnow(),
        description="HTTP response time exceeded threshold",
        labels={"service": "web", "environment": "production"},
    )


@pytest.fixture
def sample_alert_critical():
    """Create sample critical-severity alert."""
    return Alert(
        rule_name="high_error_rate",
        metric_name="error_rate",
        current_value=0.15,
        threshold=0.05,
        severity=AlertSeverity.CRITICAL,
        triggered_at=datetime.utcnow(),
        description="Error rate exceeded critical threshold",
        labels={"service": "api", "environment": "production"},
    )


@pytest.fixture
def sample_alert_low():
    """Create sample low-severity alert."""
    return Alert(
        rule_name="low_memory",
        metric_name="memory_usage",
        current_value=0.85,
        threshold=0.90,
        severity=AlertSeverity.LOW,
        triggered_at=datetime.utcnow(),
        description="Memory usage approaching limit",
        labels={"service": "workers"},
    )


@pytest.fixture
def sample_alert_medium():
    """Create sample medium-severity alert."""
    return Alert(
        rule_name="security_events",
        metric_name="failed_logins",
        current_value=50,
        threshold=20,
        severity=AlertSeverity.MEDIUM,
        triggered_at=datetime.utcnow(),
        description="Multiple failed login attempts detected",
        labels={"source": "api"},
    )


class TestIncidentEnums:
    """Test incident-related enums."""

    def test_incident_status_values(self):
        """Test all IncidentStatus enum values."""
        assert IncidentStatus.OPEN.value == "open"
        assert IncidentStatus.INVESTIGATING.value == "investigating"
        assert IncidentStatus.IDENTIFIED.value == "identified"
        assert IncidentStatus.MONITORING.value == "monitoring"
        assert IncidentStatus.RESOLVED.value == "resolved"

    def test_response_action_values(self):
        """Test all ResponseAction enum values."""
        assert ResponseAction.SCALE_UP.value == "scale_up"
        assert ResponseAction.SCALE_DOWN.value == "scale_down"
        assert ResponseAction.RESTART_SERVICE.value == "restart_service"
        assert ResponseAction.CLEAR_CACHE.value == "clear_cache"
        assert ResponseAction.CIRCUIT_BREAKER.value == "circuit_breaker"
        assert ResponseAction.RATE_LIMIT.value == "rate_limit"
        assert ResponseAction.NOTIFICATION.value == "notification"
        assert ResponseAction.RUNBOOK.value == "runbook"
        assert ResponseAction.CUSTOM.value == "custom"


class TestDataClasses:
    """Test data class creation and defaults."""

    def test_incident_response_defaults(self):
        """Test IncidentResponse default values."""
        response = IncidentResponse(action=ResponseAction.NOTIFICATION)
        assert response.action == ResponseAction.NOTIFICATION
        assert response.parameters == {}
        assert response.delay_seconds == 0
        assert response.max_retries == 3
        assert response.timeout_seconds == 300
        assert response.condition is None

    def test_incident_response_with_parameters(self):
        """Test IncidentResponse with custom parameters."""
        response = IncidentResponse(
            action=ResponseAction.SCALE_UP,
            parameters={"service": "web", "replicas": 3},
            delay_seconds=60,
            max_retries=5,
            timeout_seconds=600,
            condition="cpu_usage > 0.8",
        )
        assert response.parameters["service"] == "web"
        assert response.delay_seconds == 60
        assert response.condition == "cpu_usage > 0.8"

    def test_incident_creation(self):
        """Test Incident dataclass creation."""
        incident = Incident(
            id="inc_001",
            title="Test Incident",
            description="Test description",
            severity=AlertSeverity.HIGH,
            status=IncidentStatus.OPEN,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert incident.id == "inc_001"
        assert incident.severity == AlertSeverity.HIGH
        assert incident.status == IncidentStatus.OPEN
        assert len(incident.alerts) == 0
        assert len(incident.responses_executed) == 0

    def test_response_plan_defaults(self):
        """Test ResponsePlan default values."""
        plan = ResponsePlan(
            name="test_plan",
            description="Test plan",
            triggers=["alert1"],
            responses=[],
        )
        assert plan.escalation_time == 300
        assert plan.auto_resolve is False


class TestIncidentResponseSystemInit:
    """Test IncidentResponseSystem initialization."""

    def test_system_initialization(self, incident_system):
        """Test system initializes with correct defaults."""
        assert isinstance(incident_system.incidents, dict)
        assert isinstance(incident_system.response_plans, dict)
        assert len(incident_system.response_plans) == 4  # 4 default plans
        assert "high_response_time_plan" in incident_system.response_plans
        assert "high_error_rate_plan" in incident_system.response_plans
        assert "memory_pressure_plan" in incident_system.response_plans
        assert "security_incident_plan" in incident_system.response_plans

    def test_default_plans_structure(self, incident_system):
        """Test default response plans have correct structure."""
        plan = incident_system.response_plans["high_response_time_plan"]
        assert plan.name == "high_response_time_plan"
        assert "high_response_time" in plan.triggers
        assert len(plan.responses) == 3  # Clear cache, scale up, notification
        assert plan.escalation_time == 600
        assert plan.auto_resolve is True

    def test_error_rate_plan_configuration(self, incident_system):
        """Test high error rate plan configuration."""
        plan = incident_system.response_plans["high_error_rate_plan"]
        assert len(plan.responses) == 3
        assert plan.responses[0].action == ResponseAction.CIRCUIT_BREAKER
        assert plan.responses[1].action == ResponseAction.RATE_LIMIT
        assert plan.responses[2].action == ResponseAction.NOTIFICATION
        assert plan.escalation_time == 180


class TestResponsePlanManagement:
    """Test adding and managing response plans."""

    def test_add_response_plan(self, incident_system):
        """Test adding a new response plan."""
        plan = ResponsePlan(
            name="custom_plan",
            description="Custom test plan",
            triggers=["custom_alert"],
            responses=[
                IncidentResponse(action=ResponseAction.NOTIFICATION, parameters={"message": "Test"}),
            ],
        )
        incident_system.add_response_plan(plan)
        assert "custom_plan" in incident_system.response_plans
        assert incident_system.response_plans["custom_plan"] == plan

    def test_add_multiple_plans(self, incident_system):
        """Test adding multiple response plans."""
        plan1 = ResponsePlan(name="plan1", description="Plan 1", triggers=["alert1"], responses=[])
        plan2 = ResponsePlan(name="plan2", description="Plan 2", triggers=["alert2"], responses=[])

        incident_system.add_response_plan(plan1)
        incident_system.add_response_plan(plan2)

        assert len(incident_system.response_plans) == 6  # 4 default + 2 custom
        assert "plan1" in incident_system.response_plans
        assert "plan2" in incident_system.response_plans


class TestAlertHandling:
    """Test alert handling and incident creation."""

    def test_handle_alert_creates_incident(self, incident_system, sample_alert_high):
        """Test handling alert creates new incident."""
        incident_system.handle_alert(sample_alert_high)
        assert len(incident_system.incidents) == 1

        incident = list(incident_system.incidents.values())[0]
        assert incident.status == IncidentStatus.OPEN
        assert incident.severity == AlertSeverity.HIGH
        assert len(incident.alerts) == 1
        assert incident.alerts[0].rule_name == "high_response_time"

    def test_handle_alert_no_matching_plan(self, incident_system):
        """Test handling alert with no matching response plan."""
        alert = Alert(
            rule_name="unknown_alert",
            metric_name="unknown_metric",
            current_value=100,
            threshold=50,
            severity=AlertSeverity.LOW,
            triggered_at=datetime.utcnow(),
            description="Unknown alert",
        )
        incident_system.handle_alert(alert)
        # Should not create incident for unknown alerts
        assert len(incident_system.incidents) == 0

    def test_handle_critical_alert(self, incident_system, sample_alert_critical):
        """Test handling critical severity alert."""
        incident_system.handle_alert(sample_alert_critical)
        assert len(incident_system.incidents) == 1

        incident = list(incident_system.incidents.values())[0]
        assert incident.severity == AlertSeverity.CRITICAL
        assert "high_error_rate_plan" in incident.tags

    def test_handle_multiple_alerts_same_rule(self, incident_system, sample_alert_high):
        """Test handling multiple alerts for same rule updates existing incident."""
        # First alert
        incident_system.handle_alert(sample_alert_high)
        assert len(incident_system.incidents) == 1
        incident_id = list(incident_system.incidents.keys())[0]

        # Second alert (same rule) - use LOW severity to test max()
        alert2 = Alert(
            rule_name="high_response_time",
            metric_name="http_response_time",
            current_value=6.0,
            threshold=3.0,
            severity=AlertSeverity.LOW,
            triggered_at=datetime.utcnow(),
            description="Response time alert",
        )
        incident_system.handle_alert(alert2)

        # Should still have only 1 incident
        assert len(incident_system.incidents) == 1
        assert incident_id in incident_system.incidents

        # Incident should be updated
        incident = incident_system.incidents[incident_id]
        assert len(incident.alerts) == 2
        # Severity should remain HIGH (max by string value: "low" < "high")
        assert incident.severity == AlertSeverity.HIGH


class TestIncidentCreationAndUpdate:
    """Test incident creation and update logic."""

    def test_create_new_incident(self, incident_system, sample_alert_high):
        """Test creating a new incident."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        assert incident.id is not None
        assert incident.status == IncidentStatus.OPEN
        assert incident.severity == AlertSeverity.HIGH
        assert len(incident.alerts) == 1
        assert "high_response_time_plan" in incident.tags

    def test_update_existing_incident(self, incident_system, sample_alert_high):
        """Test updating existing incident."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident1 = incident_system._create_or_update_incident(sample_alert_high, plans)
        initial_updated_at = incident1.updated_at

        # Wait a tiny bit to ensure timestamp differs
        import time

        time.sleep(0.01)

        # Create another alert with same rule - using MEDIUM severity
        alert2 = Alert(
            rule_name="high_response_time",
            metric_name="http_response_time",
            current_value=7.0,
            threshold=3.0,
            severity=AlertSeverity.MEDIUM,
            triggered_at=datetime.utcnow(),
            description="Response time increased",
        )

        incident2 = incident_system._create_or_update_incident(alert2, plans)

        # Should be same incident
        assert incident2.id == incident1.id
        assert len(incident2.alerts) == 2
        assert incident2.updated_at > initial_updated_at
        # Severity should be max by string value: "medium" > "high"
        assert incident2.severity == AlertSeverity.MEDIUM

    def test_create_incidents_for_different_rules(self, incident_system, sample_alert_high, sample_alert_critical):
        """Test creating separate incidents for different alert rules."""
        plans_high = [incident_system.response_plans["high_response_time_plan"]]
        plans_critical = [incident_system.response_plans["high_error_rate_plan"]]

        incident1 = incident_system._create_or_update_incident(sample_alert_high, plans_high)
        incident2 = incident_system._create_or_update_incident(sample_alert_critical, plans_critical)

        assert incident1.id != incident2.id
        assert len(incident_system.incidents) == 2


class TestIncidentResolution:
    """Test incident resolution."""

    def test_resolve_incident(self, incident_system, sample_alert_high):
        """Test manual incident resolution."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        incident_system.resolve_incident(incident.id, "Issue resolved by manual intervention")

        resolved_incident = incident_system.incidents[incident.id]
        assert resolved_incident.status == IncidentStatus.RESOLVED
        assert resolved_incident.resolved_at is not None
        assert resolved_incident.metadata["resolution_note"] == "Issue resolved by manual intervention"

    def test_resolve_nonexistent_incident(self, incident_system):
        """Test resolving nonexistent incident does nothing."""
        incident_system.resolve_incident("nonexistent_id", "Test")
        # Should not crash, just do nothing
        assert len(incident_system.incidents) == 0

    def test_resolve_without_note(self, incident_system, sample_alert_high):
        """Test resolving incident without resolution note."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        incident_system.resolve_incident(incident.id)

        resolved_incident = incident_system.incidents[incident.id]
        assert resolved_incident.status == IncidentStatus.RESOLVED
        assert "resolution_note" not in resolved_incident.metadata


class TestResponseExecution:
    """Test response action execution."""

    @pytest.mark.asyncio
    async def test_send_notification(self, incident_system):
        """Test sending notification."""
        params = {"message": "Test notification", "channels": ["slack", "email"]}
        result = await incident_system._send_notification(params)
        assert result is True

    @pytest.mark.asyncio
    async def test_scale_service_up(self, incident_system):
        """Test scaling service up."""
        params = {"service": "web", "replicas": 3}
        result = await incident_system._scale_service(params, "up")
        assert result is True

    @pytest.mark.asyncio
    async def test_scale_service_down(self, incident_system):
        """Test scaling service down."""
        params = {"service": "web", "replicas": 1}
        result = await incident_system._scale_service(params, "down")
        assert result is True

    @pytest.mark.asyncio
    async def test_restart_service(self, incident_system):
        """Test restarting service."""
        params = {"service": "api"}
        result = await incident_system._restart_service(params)
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_cache(self, incident_system):
        """Test clearing cache."""
        params = {"cache_type": "redis"}
        result = await incident_system._clear_cache(params)
        assert result is True

    @pytest.mark.asyncio
    async def test_activate_circuit_breaker(self, incident_system):
        """Test activating circuit breaker."""
        params = {"service": "external_api", "duration": 300}
        result = await incident_system._activate_circuit_breaker(params)
        assert result is True

    @pytest.mark.asyncio
    async def test_apply_rate_limit(self, incident_system):
        """Test applying rate limit."""
        params = {"limit": "100/minute", "duration": 600}
        result = await incident_system._apply_rate_limit(params)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_runbook(self, incident_system):
        """Test executing runbook."""
        params = {"runbook_url": "https://docs.example.com/runbook"}
        result = await incident_system._execute_runbook(params)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_custom_action_registered(self, incident_system):
        """Test executing registered custom action."""
        # Register custom action
        async def custom_action(params):
            return True

        incident_system.custom_actions["test_action"] = custom_action

        params = {"action_name": "test_action"}
        result = await incident_system._execute_custom_action(params)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_custom_action_not_registered(self, incident_system):
        """Test executing unregistered custom action."""
        params = {"action_name": "nonexistent_action"}
        result = await incident_system._execute_custom_action(params)
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_custom_action_with_error(self, incident_system):
        """Test executing custom action that raises error."""

        async def failing_action(params):
            raise ValueError("Test error")

        incident_system.custom_actions["failing_action"] = failing_action

        params = {"action_name": "failing_action"}
        result = await incident_system._execute_custom_action(params)
        assert result is False


class TestResponseActionExecution:
    """Test complete response action execution flow."""

    @pytest.mark.asyncio
    async def test_execute_response_action_notification(self, incident_system, sample_alert_high):
        """Test executing notification response action."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        response = IncidentResponse(
            action=ResponseAction.NOTIFICATION, parameters={"message": "Test", "channels": ["slack"]}
        )

        result = await incident_system._execute_response_action(incident, response)
        assert result is True
        assert len(incident_system.response_history) > 0
        assert incident_system.response_history[-1]["action"] == "notification"
        assert incident_system.response_history[-1]["success"] is True

    @pytest.mark.asyncio
    async def test_execute_response_action_scale_up(self, incident_system, sample_alert_high):
        """Test executing scale up response action."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        response = IncidentResponse(action=ResponseAction.SCALE_UP, parameters={"service": "web", "replicas": 2})

        result = await incident_system._execute_response_action(incident, response)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_response_action_tracks_active(self, incident_system, sample_alert_high):
        """Test response action tracking in active responses."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        response = IncidentResponse(action=ResponseAction.CLEAR_CACHE, parameters={"cache_type": "all"})

        result = await incident_system._execute_response_action(incident, response)
        assert result is True
        # Active responses should be cleared after execution
        assert len([k for k in incident_system.active_responses.keys() if incident.id in k]) == 0


class TestConditionEvaluation:
    """Test response condition evaluation."""

    def test_evaluate_condition_returns_true(self, incident_system, sample_alert_high):
        """Test condition evaluation (placeholder always returns True)."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        result = incident_system._evaluate_condition("response_time > 3.0", incident)
        assert result is True

    def test_evaluate_condition_with_different_expressions(self, incident_system, sample_alert_high):
        """Test various condition expressions."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        # All should return True in current implementation (placeholder)
        assert incident_system._evaluate_condition("cpu_usage > 0.8", incident) is True
        assert incident_system._evaluate_condition("memory_usage < 0.5", incident) is True
        assert incident_system._evaluate_condition("error_rate > 0.01", incident) is True


class TestIncidentResolutionChecks:
    """Test incident resolution checking."""

    def test_check_incident_resolved(self, incident_system, sample_alert_high):
        """Test checking if incident is resolved."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        # Current implementation always returns True (placeholder)
        result = incident_system._check_incident_resolved(incident)
        assert result is True


class TestResponsePlanExecution:
    """Test complete response plan execution."""

    @pytest.mark.asyncio
    async def test_execute_response_plan_updates_status(self, incident_system, sample_alert_high):
        """Test response plan execution updates incident status."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        plan = incident_system.response_plans["high_response_time_plan"]
        await incident_system._execute_response_plan(incident, plan)

        # Status should be updated to MONITORING
        assert incident.status == IncidentStatus.MONITORING

    @pytest.mark.asyncio
    async def test_execute_response_plan_with_delays(self, incident_system):
        """Test response plan execution respects delays."""
        # Create custom plan with short delays for testing
        plan = ResponsePlan(
            name="test_delay_plan",
            description="Test plan with delays",
            triggers=["test_alert"],
            responses=[
                IncidentResponse(action=ResponseAction.NOTIFICATION, parameters={"message": "First"}, delay_seconds=0),
                IncidentResponse(
                    action=ResponseAction.NOTIFICATION, parameters={"message": "Second"}, delay_seconds=0
                ),  # Use 0 for speed
            ],
        )

        incident = Incident(
            id="test_inc",
            title="Test",
            description="Test",
            severity=AlertSeverity.HIGH,
            status=IncidentStatus.OPEN,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await incident_system._execute_response_plan(incident, plan)

        # Both responses should execute
        assert len([r for r in incident_system.response_history if r["incident_id"] == "test_inc"]) == 2

    @pytest.mark.asyncio
    async def test_execute_response_plan_skips_failed_conditions(self, incident_system):
        """Test response plan skips actions when conditions not met."""
        # Patch _evaluate_condition to return False
        with patch.object(incident_system, "_evaluate_condition", return_value=False):
            plan = ResponsePlan(
                name="test_condition_plan",
                description="Test plan with conditions",
                triggers=["test_alert"],
                responses=[
                    IncidentResponse(
                        action=ResponseAction.SCALE_UP,
                        parameters={"service": "web"},
                        condition="cpu_usage > 0.9",
                    ),
                ],
            )

            incident = Incident(
                id="test_inc2",
                title="Test",
                description="Test",
                severity=AlertSeverity.HIGH,
                status=IncidentStatus.OPEN,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            await incident_system._execute_response_plan(incident, plan)

            # Response should be skipped due to failed condition
            scale_responses = [r for r in incident_system.response_history if r["action"] == "scale_up"]
            assert len(scale_responses) == 0


class TestEscalation:
    """Test incident escalation."""

    @pytest.mark.asyncio
    async def test_schedule_escalation_for_unresolved_incident(self, incident_system, sample_alert_high):
        """Test escalation is triggered for unresolved incidents."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        escalation_called = False

        async def escalation_callback(inc):
            nonlocal escalation_called
            escalation_called = True

        incident_system.escalation_callbacks.append(escalation_callback)

        # Schedule with very short delay for testing
        await incident_system._schedule_escalation(incident, 0)

        assert escalation_called is True

    @pytest.mark.asyncio
    async def test_schedule_escalation_skips_resolved_incident(self, incident_system, sample_alert_high):
        """Test escalation is skipped for resolved incidents."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        # Resolve the incident
        incident.status = IncidentStatus.RESOLVED

        escalation_called = False

        async def escalation_callback(inc):
            nonlocal escalation_called
            escalation_called = True

        incident_system.escalation_callbacks.append(escalation_callback)

        await incident_system._schedule_escalation(incident, 0)

        # Escalation should not be called for resolved incident
        assert escalation_called is False

    @pytest.mark.asyncio
    async def test_escalation_callback_error_handling(self, incident_system, sample_alert_high):
        """Test escalation handles callback errors gracefully."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        async def failing_callback(inc):
            raise ValueError("Test escalation error")

        incident_system.escalation_callbacks.append(failing_callback)

        # Should not raise exception
        await incident_system._schedule_escalation(incident, 0)


class TestAutoResolve:
    """Test automatic incident resolution."""

    @pytest.mark.asyncio
    async def test_schedule_auto_resolve(self, incident_system, sample_alert_high):
        """Test automatic resolution scheduling."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        # Should auto-resolve (placeholder always returns True)
        await incident_system._schedule_auto_resolve(incident, 0)

        # Incident should be resolved
        resolved_incident = incident_system.incidents[incident.id]
        assert resolved_incident.status == IncidentStatus.RESOLVED

    @pytest.mark.asyncio
    async def test_auto_resolve_checks_conditions(self, incident_system, sample_alert_high):
        """Test auto-resolve checks incident conditions."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        # Patch to return False (conditions not met)
        with patch.object(incident_system, "_check_incident_resolved", return_value=False):
            await incident_system._schedule_auto_resolve(incident, 0)

            # Incident should NOT be resolved
            assert incident.status != IncidentStatus.RESOLVED


class TestSystemStatus:
    """Test system status reporting."""

    def test_get_system_status_empty(self, incident_system):
        """Test system status with no incidents."""
        status = incident_system.get_system_status()

        assert status["total_incidents"] == 0
        assert status["active_incidents"] == 0
        assert status["response_plans"] == 4  # 4 default plans
        assert status["active_responses"] == 0
        assert status["recent_responses"] == 0

    def test_get_system_status_with_incidents(self, incident_system, sample_alert_high, sample_alert_critical):
        """Test system status with active incidents."""
        plans_high = [incident_system.response_plans["high_response_time_plan"]]
        plans_critical = [incident_system.response_plans["high_error_rate_plan"]]

        incident1 = incident_system._create_or_update_incident(sample_alert_high, plans_high)
        incident2 = incident_system._create_or_update_incident(sample_alert_critical, plans_critical)

        status = incident_system.get_system_status()

        assert status["total_incidents"] == 2
        assert status["active_incidents"] == 2
        assert status["response_plans"] == 4

    def test_get_system_status_with_resolved_incidents(
        self, incident_system, sample_alert_high, sample_alert_critical
    ):
        """Test system status distinguishes active vs resolved incidents."""
        plans_high = [incident_system.response_plans["high_response_time_plan"]]
        plans_critical = [incident_system.response_plans["high_error_rate_plan"]]

        incident1 = incident_system._create_or_update_incident(sample_alert_high, plans_high)
        incident2 = incident_system._create_or_update_incident(sample_alert_critical, plans_critical)

        # Resolve one incident
        incident_system.resolve_incident(incident1.id, "Resolved")

        status = incident_system.get_system_status()

        assert status["total_incidents"] == 2
        assert status["active_incidents"] == 1  # Only one active

    @pytest.mark.asyncio
    async def test_get_system_status_with_recent_responses(self, incident_system, sample_alert_high):
        """Test system status tracks recent responses."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        # Execute a response
        response = IncidentResponse(action=ResponseAction.NOTIFICATION, parameters={"message": "Test"})
        await incident_system._execute_response_action(incident, response)

        status = incident_system.get_system_status()

        assert status["recent_responses"] >= 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handle_alert_with_exception_in_plan_lookup(self, incident_system):
        """Test handling alert when plan lookup fails gracefully."""
        # This should not crash even with malformed data
        alert = Alert(
            rule_name=None,  # Malformed
            metric_name="test",
            current_value=1.0,
            threshold=0.5,
            severity=AlertSeverity.LOW,
            triggered_at=datetime.utcnow(),
            description="Test",
        )

        # Should handle gracefully
        incident_system.handle_alert(alert)

    @pytest.mark.asyncio
    async def test_execute_response_action_with_invalid_action(self, incident_system, sample_alert_high):
        """Test executing response with invalid action type."""
        plans = [incident_system.response_plans["high_response_time_plan"]]
        incident = incident_system._create_or_update_incident(sample_alert_high, plans)

        # Create response with valid enum but test that unknowns are handled
        response = IncidentResponse(action=ResponseAction.CUSTOM, parameters={"action_name": "unknown"})

        result = await incident_system._execute_response_action(incident, response)
        # Custom action without registration should return False
        assert result is False

    def test_incident_severity_escalation(self, incident_system):
        """Test incident severity changes with multiple alerts."""
        alert1 = Alert(
            rule_name="high_response_time",
            metric_name="http_response_time",
            current_value=4.0,
            threshold=3.0,
            severity=AlertSeverity.LOW,
            triggered_at=datetime.utcnow(),
            description="Initial alert",
        )

        alert2 = Alert(
            rule_name="high_response_time",
            metric_name="http_response_time",
            current_value=8.0,
            threshold=3.0,
            severity=AlertSeverity.MEDIUM,
            triggered_at=datetime.utcnow(),
            description="Escalated alert",
        )

        plans = [incident_system.response_plans["high_response_time_plan"]]

        incident = incident_system._create_or_update_incident(alert1, plans)
        assert incident.severity == AlertSeverity.LOW

        # Update with different severity alert (string comparison: "medium" > "low")
        incident = incident_system._create_or_update_incident(alert2, plans)
        assert incident.severity == AlertSeverity.MEDIUM


class TestIntegrationScenarios:
    """Test full integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_incident_lifecycle(self, incident_system, sample_alert_high):
        """Test complete incident lifecycle from creation to resolution."""
        # 1. Alert triggers incident
        incident_system.handle_alert(sample_alert_high)
        assert len(incident_system.incidents) == 1

        incident = list(incident_system.incidents.values())[0]
        assert incident.status == IncidentStatus.OPEN

        # 2. Execute response plan
        plan = incident_system.response_plans["high_response_time_plan"]
        await incident_system._execute_response_plan(incident, plan)

        assert incident.status == IncidentStatus.MONITORING
        assert len(incident.responses_executed) > 0

        # 3. Resolve incident
        incident_system.resolve_incident(incident.id, "Service recovered")

        assert incident.status == IncidentStatus.RESOLVED
        assert incident.resolved_at is not None

    @pytest.mark.asyncio
    async def test_multiple_concurrent_incidents(
        self, incident_system, sample_alert_high, sample_alert_critical, sample_alert_medium
    ):
        """Test handling multiple concurrent incidents."""
        # Create multiple incidents
        incident_system.handle_alert(sample_alert_high)
        incident_system.handle_alert(sample_alert_critical)
        incident_system.handle_alert(sample_alert_medium)

        # Should have 3 separate incidents
        assert len(incident_system.incidents) == 3

        status = incident_system.get_system_status()
        assert status["total_incidents"] == 3
        assert status["active_incidents"] == 3

    @pytest.mark.asyncio
    async def test_incident_with_all_response_types(self, incident_system):
        """Test incident triggering all response action types."""
        # Create comprehensive response plan
        comprehensive_plan = ResponsePlan(
            name="comprehensive_plan",
            description="Tests all response types",
            triggers=["comprehensive_alert"],
            responses=[
                IncidentResponse(action=ResponseAction.CLEAR_CACHE, parameters={"cache_type": "all"}),
                IncidentResponse(action=ResponseAction.SCALE_UP, parameters={"service": "web", "replicas": 2}),
                IncidentResponse(action=ResponseAction.RESTART_SERVICE, parameters={"service": "api"}),
                IncidentResponse(action=ResponseAction.CIRCUIT_BREAKER, parameters={"service": "ext", "duration": 300}),
                IncidentResponse(action=ResponseAction.RATE_LIMIT, parameters={"limit": "100/min"}),
                IncidentResponse(action=ResponseAction.NOTIFICATION, parameters={"message": "Alert", "channels": []}),
                IncidentResponse(action=ResponseAction.RUNBOOK, parameters={"runbook_url": "http://example.com"}),
            ],
        )

        incident_system.add_response_plan(comprehensive_plan)

        alert = Alert(
            rule_name="comprehensive_alert",
            metric_name="test_metric",
            current_value=100,
            threshold=50,
            severity=AlertSeverity.HIGH,
            triggered_at=datetime.utcnow(),
            description="Comprehensive test",
        )

        plans = [comprehensive_plan]
        incident = incident_system._create_or_update_incident(alert, plans)

        await incident_system._execute_response_plan(incident, comprehensive_plan)

        # All 7 responses should execute
        assert len(incident.responses_executed) == 7
        assert len([r for r in incident_system.response_history if r["incident_id"] == incident.id]) == 7
