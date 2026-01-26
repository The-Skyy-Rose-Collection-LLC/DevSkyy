# tests/services/test_email_notifications.py
"""Unit tests for email notification service.

Tests the EmailNotificationService with proper SMTP mocking.
Target coverage: 70%+
"""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from services.notifications.email_notifications import (
    TEMPLATES,
    EmailConfig,
    EmailNotificationService,
    EmailTemplate,
    NotificationError,
    get_email_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def email_config() -> EmailConfig:
    """Create a fully configured email config."""
    return EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="test_password",
        from_email="noreply@skyyrose.com",
        from_name="SkyyRose Platform",
        use_tls=True,
        approval_recipients=["admin@skyyrose.com", "reviewer@skyyrose.com"],
        dashboard_url="https://dashboard.skyyrose.com",
    )


@pytest.fixture
def unconfigured_email_config() -> EmailConfig:
    """Create an unconfigured email config."""
    return EmailConfig()


@pytest.fixture
def email_service(email_config: EmailConfig) -> EmailNotificationService:
    """Create an email service with configured config."""
    return EmailNotificationService(config=email_config)


@pytest.fixture
def unconfigured_service(
    unconfigured_email_config: EmailConfig,
) -> EmailNotificationService:
    """Create an email service with unconfigured config."""
    return EmailNotificationService(config=unconfigured_email_config)


@pytest.fixture
def mock_approval_item() -> MagicMock:
    """Create a mock ApprovalItem for testing."""
    item = MagicMock()
    item.id = "item-123"
    item.asset_id = "asset-456"
    item.job_id = "job-789"
    item.original_url = "https://cdn.skyyrose.com/original/image.jpg"
    item.enhanced_url = "https://cdn.skyyrose.com/enhanced/image.jpg"
    item.product_id = "prod-001"
    item.product_name = "Rose Gold Necklace"
    item.revision_feedback = "Please adjust lighting"
    item.revision_priority = MagicMock()
    item.revision_priority.value = "high"
    return item


@pytest.fixture
def mock_approval_item_no_priority() -> MagicMock:
    """Create a mock ApprovalItem without revision priority."""
    item = MagicMock()
    item.id = "item-123"
    item.asset_id = "asset-456"
    item.job_id = "job-789"
    item.original_url = "https://cdn.skyyrose.com/original/image.jpg"
    item.enhanced_url = "https://cdn.skyyrose.com/enhanced/image.jpg"
    item.product_id = "prod-001"
    item.product_name = None  # Test None product_name
    item.revision_feedback = None  # Test None feedback
    item.revision_priority = None  # Test None priority
    return item


# =============================================================================
# Tests: EmailConfig
# =============================================================================


class TestEmailConfig:
    """Tests for EmailConfig dataclass."""

    def test_default_values(self) -> None:
        """EmailConfig should have sensible defaults."""
        config = EmailConfig()

        assert config.smtp_host == ""
        assert config.smtp_port == 587
        assert config.smtp_user == ""
        assert config.smtp_password == ""
        assert config.from_email == ""
        assert config.from_name == "SkyyRose Platform"
        assert config.use_tls is True
        assert config.approval_recipients == []
        assert config.dashboard_url == ""

    def test_is_configured_true(self, email_config: EmailConfig) -> None:
        """is_configured should return True when all required fields set."""
        assert email_config.is_configured is True

    def test_is_configured_false_missing_host(self) -> None:
        """is_configured should return False when smtp_host missing."""
        config = EmailConfig(
            smtp_user="user",
            smtp_password="pass",
            from_email="from@test.com",
        )
        assert config.is_configured is False

    def test_is_configured_false_missing_user(self) -> None:
        """is_configured should return False when smtp_user missing."""
        config = EmailConfig(
            smtp_host="smtp.test.com",
            smtp_password="pass",
            from_email="from@test.com",
        )
        assert config.is_configured is False

    def test_is_configured_false_missing_password(self) -> None:
        """is_configured should return False when smtp_password missing."""
        config = EmailConfig(
            smtp_host="smtp.test.com",
            smtp_user="user",
            from_email="from@test.com",
        )
        assert config.is_configured is False

    def test_is_configured_false_missing_from_email(self) -> None:
        """is_configured should return False when from_email missing."""
        config = EmailConfig(
            smtp_host="smtp.test.com",
            smtp_user="user",
            smtp_password="pass",
        )
        assert config.is_configured is False

    @patch.dict(
        "os.environ",
        {
            "SMTP_HOST": "smtp.env.com",
            "SMTP_PORT": "465",
            "SMTP_USER": "env_user",
            "SMTP_PASSWORD": "env_pass",
            "SMTP_FROM_EMAIL": "env@test.com",
            "SMTP_FROM_NAME": "Test Platform",
            "SMTP_USE_TLS": "false",
            "APPROVAL_EMAIL_RECIPIENTS": "admin@test.com, reviewer@test.com",
            "APPROVAL_DASHBOARD_URL": "https://dash.test.com",
        },
    )
    def test_from_env(self) -> None:
        """from_env should create config from environment variables."""
        config = EmailConfig.from_env()

        assert config.smtp_host == "smtp.env.com"
        assert config.smtp_port == 465
        assert config.smtp_user == "env_user"
        assert config.smtp_password == "env_pass"
        assert config.from_email == "env@test.com"
        assert config.from_name == "Test Platform"
        assert config.use_tls is False
        assert config.approval_recipients == ["admin@test.com", "reviewer@test.com"]
        assert config.dashboard_url == "https://dash.test.com"

    @patch.dict("os.environ", {}, clear=True)
    def test_from_env_defaults(self) -> None:
        """from_env should use defaults when env vars not set."""
        config = EmailConfig.from_env()

        assert config.smtp_host == ""
        assert config.smtp_port == 587
        assert config.smtp_user == ""
        assert config.smtp_password == ""
        assert config.from_email == ""
        assert config.from_name == "SkyyRose Platform"
        assert config.use_tls is True
        assert config.approval_recipients == []
        assert config.dashboard_url == ""

    @patch.dict(
        "os.environ",
        {"APPROVAL_EMAIL_RECIPIENTS": ", ,  , admin@test.com,  , "},
    )
    def test_from_env_strips_empty_recipients(self) -> None:
        """from_env should strip empty recipients from list."""
        config = EmailConfig.from_env()
        assert config.approval_recipients == ["admin@test.com"]


# =============================================================================
# Tests: EmailTemplate
# =============================================================================


class TestEmailTemplate:
    """Tests for EmailTemplate enum."""

    def test_template_values(self) -> None:
        """EmailTemplate should have correct string values."""
        assert EmailTemplate.APPROVAL_PENDING.value == "approval_pending"
        assert EmailTemplate.APPROVAL_BATCH.value == "approval_batch"
        assert EmailTemplate.REVISION_REQUESTED.value == "revision_requested"
        assert EmailTemplate.SYNC_COMPLETE.value == "sync_complete"
        assert EmailTemplate.SYNC_FAILED.value == "sync_failed"

    def test_templates_dict_has_required_keys(self) -> None:
        """TEMPLATES dict should have all template types."""
        assert EmailTemplate.APPROVAL_PENDING in TEMPLATES
        assert EmailTemplate.APPROVAL_BATCH in TEMPLATES
        assert EmailTemplate.REVISION_REQUESTED in TEMPLATES
        assert EmailTemplate.SYNC_COMPLETE in TEMPLATES

    def test_templates_have_required_fields(self) -> None:
        """Each template should have subject, html, and text."""
        for template_type in [
            EmailTemplate.APPROVAL_PENDING,
            EmailTemplate.APPROVAL_BATCH,
            EmailTemplate.REVISION_REQUESTED,
            EmailTemplate.SYNC_COMPLETE,
        ]:
            template = TEMPLATES[template_type]
            assert "subject" in template
            assert "html" in template
            assert "text" in template
            assert isinstance(template["subject"], str)
            assert isinstance(template["html"], str)
            assert isinstance(template["text"], str)


# =============================================================================
# Tests: NotificationError
# =============================================================================


class TestNotificationError:
    """Tests for NotificationError exception."""

    def test_basic_error(self) -> None:
        """NotificationError should store message."""
        error = NotificationError("Test error")
        assert str(error) == "Test error"
        assert error.correlation_id is None

    def test_error_with_correlation_id(self) -> None:
        """NotificationError should store correlation_id."""
        error = NotificationError("Test error", correlation_id="corr-123")
        assert str(error) == "Test error"
        assert error.correlation_id == "corr-123"

    def test_error_inheritance(self) -> None:
        """NotificationError should be an Exception."""
        error = NotificationError("Test")
        assert isinstance(error, Exception)


# =============================================================================
# Tests: EmailNotificationService
# =============================================================================


class TestEmailNotificationService:
    """Tests for EmailNotificationService."""

    def test_init_with_config(self, email_config: EmailConfig) -> None:
        """Service should initialize with provided config."""
        service = EmailNotificationService(config=email_config)
        assert service.is_configured is True

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_config_uses_env(self) -> None:
        """Service should use from_env when no config provided."""
        service = EmailNotificationService()
        assert service.is_configured is False

    def test_is_configured_property(
        self,
        email_service: EmailNotificationService,
        unconfigured_service: EmailNotificationService,
    ) -> None:
        """is_configured should reflect config state."""
        assert email_service.is_configured is True
        assert unconfigured_service.is_configured is False


class TestSendEmail:
    """Tests for send_email method."""

    @pytest.mark.asyncio
    async def test_send_email_success(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_email should return True on successful send."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_email(
                to=["test@example.com"],
                subject="Test Subject",
                html_body="<p>HTML content</p>",
                text_body="Text content",
            )

            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(
                "user@example.com",
                "test_password",
            )
            mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_unconfigured(
        self,
        unconfigured_service: EmailNotificationService,
    ) -> None:
        """send_email should return False when not configured."""
        result = await unconfigured_service.send_email(
            to=["test@example.com"],
            subject="Test",
            html_body="<p>HTML</p>",
            text_body="Text",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_smtp_error(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_email should return False on SMTP error."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.side_effect = smtplib.SMTPException(
                "Connection failed"
            )

            result = await email_service.send_email(
                to=["test@example.com"],
                subject="Test",
                html_body="<p>HTML</p>",
                text_body="Text",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_no_tls(self, email_config: EmailConfig) -> None:
        """send_email should skip starttls when use_tls is False."""
        email_config.use_tls = False
        service = EmailNotificationService(config=email_config)

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await service.send_email(
                to=["test@example.com"],
                subject="Test",
                html_body="<p>HTML</p>",
                text_body="Text",
            )

            assert result is True
            mock_server.starttls.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_email should handle multiple recipients."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            recipients = ["user1@test.com", "user2@test.com", "user3@test.com"]
            result = await email_service.send_email(
                to=recipients,
                subject="Test",
                html_body="<p>HTML</p>",
                text_body="Text",
            )

            assert result is True
            call_args = mock_server.sendmail.call_args
            assert call_args[0][1] == recipients

    @pytest.mark.asyncio
    async def test_send_email_with_correlation_id(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_email should accept correlation_id for logging."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_email(
                to=["test@example.com"],
                subject="Test",
                html_body="<p>HTML</p>",
                text_body="Text",
                correlation_id="corr-test-123",
            )

            assert result is True


class TestSendApprovalNotification:
    """Tests for send_approval_notification method."""

    @pytest.mark.asyncio
    async def test_send_approval_notification_success(
        self,
        email_service: EmailNotificationService,
        mock_approval_item: MagicMock,
    ) -> None:
        """send_approval_notification should send formatted email."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_approval_notification(
                item=mock_approval_item,
                correlation_id="corr-123",
            )

            assert result is True
            mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_approval_notification_no_product_name(
        self,
        email_service: EmailNotificationService,
        mock_approval_item_no_priority: MagicMock,
    ) -> None:
        """send_approval_notification should handle None product_name."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_approval_notification(
                item=mock_approval_item_no_priority,
            )

            assert result is True


class TestSendBatchNotification:
    """Tests for send_batch_notification method."""

    @pytest.mark.asyncio
    async def test_send_batch_notification_success(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_batch_notification should send formatted email."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_batch_notification(
                count=10,
                products=5,
            )

            assert result is True
            mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_batch_notification_with_correlation_id(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_batch_notification should accept correlation_id."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_batch_notification(
                count=3,
                products=2,
                correlation_id="batch-corr-456",
            )

            assert result is True


class TestSendRevisionNotification:
    """Tests for send_revision_notification method."""

    @pytest.mark.asyncio
    async def test_send_revision_notification_success(
        self,
        email_service: EmailNotificationService,
        mock_approval_item: MagicMock,
    ) -> None:
        """send_revision_notification should send formatted email."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_revision_notification(
                item=mock_approval_item,
                revision_id="rev-001",
            )

            assert result is True
            mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_revision_notification_no_priority(
        self,
        email_service: EmailNotificationService,
        mock_approval_item_no_priority: MagicMock,
    ) -> None:
        """send_revision_notification should handle None priority."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_revision_notification(
                item=mock_approval_item_no_priority,
                revision_id="rev-002",
            )

            assert result is True


class TestSendSyncCompleteNotification:
    """Tests for send_sync_complete_notification method."""

    @pytest.mark.asyncio
    async def test_send_sync_complete_notification_success(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_sync_complete_notification should send formatted email."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_sync_complete_notification(
                count=25,
                products=8,
            )

            assert result is True
            mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sync_complete_notification_with_correlation_id(
        self,
        email_service: EmailNotificationService,
    ) -> None:
        """send_sync_complete_notification should accept correlation_id."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = await email_service.send_sync_complete_notification(
                count=15,
                products=4,
                correlation_id="sync-corr-789",
            )

            assert result is True


# =============================================================================
# Tests: Module Singleton
# =============================================================================


class TestGetEmailService:
    """Tests for get_email_service singleton function."""

    def test_get_email_service_returns_service(self) -> None:
        """get_email_service should return an EmailNotificationService."""
        # Reset singleton for test isolation
        import services.notifications.email_notifications as module

        module._email_service = None

        service = get_email_service()
        assert isinstance(service, EmailNotificationService)

    def test_get_email_service_returns_same_instance(self) -> None:
        """get_email_service should return singleton instance."""
        import services.notifications.email_notifications as module

        module._email_service = None

        service1 = get_email_service()
        service2 = get_email_service()
        assert service1 is service2


# =============================================================================
# Tests: Template Rendering
# =============================================================================


class TestTemplateRendering:
    """Tests for template string formatting."""

    def test_approval_pending_template_formatting(self) -> None:
        """APPROVAL_PENDING template should format correctly."""
        template = TEMPLATES[EmailTemplate.APPROVAL_PENDING]
        context = {
            "product_name": "Test Product",
            "asset_id": "asset-123",
            "original_url": "http://original.jpg",
            "enhanced_url": "http://enhanced.jpg",
            "dashboard_url": "http://dash.com",
            "item_id": "item-456",
        }

        subject = template["subject"].format(**context)
        html = template["html"].format(**context)
        text = template["text"].format(**context)

        # Verify subject
        assert "Approval" in subject

        # Verify HTML content
        assert "Test Product" in html
        assert "asset-123" in html
        assert "http://original.jpg" in html
        assert "http://enhanced.jpg" in html
        assert "http://dash.com/approval/item-456" in html

        # Verify text content
        assert "Test Product" in text
        assert "asset-123" in text

    def test_approval_batch_template_formatting(self) -> None:
        """APPROVAL_BATCH template should format correctly."""
        template = TEMPLATES[EmailTemplate.APPROVAL_BATCH]
        context = {
            "count": 5,
            "products": 3,
            "dashboard_url": "http://dash.com",
        }

        subject = template["subject"].format(**context)
        html = template["html"].format(**context)
        text = template["text"].format(**context)

        # Verify subject
        assert "5" in subject

        # Verify HTML content
        assert "5" in html
        assert "3" in html
        assert "http://dash.com/approval" in html

        # Verify text content
        assert "5" in text
        assert "3" in text

    def test_revision_requested_template_formatting(self) -> None:
        """REVISION_REQUESTED template should format correctly."""
        template = TEMPLATES[EmailTemplate.REVISION_REQUESTED]
        context = {
            "product_name": "Luxury Ring",
            "asset_id": "asset-789",
            "priority": "high",
            "priority_display": "HIGH",
            "feedback": "Needs better lighting",
            "dashboard_url": "http://dash.com",
            "revision_id": "rev-001",
        }

        subject = template["subject"].format(**context)
        html = template["html"].format(**context)
        text = template["text"].format(**context)

        # Verify subject
        assert "Luxury Ring" in subject
        assert "Revision" in subject

        # Verify HTML content
        assert "Luxury Ring" in html
        assert "HIGH" in html
        assert "Needs better lighting" in html
        assert "http://dash.com/revisions/rev-001" in html

        # Verify text content
        assert "Luxury Ring" in text
        assert "Needs better lighting" in text

    def test_sync_complete_template_formatting(self) -> None:
        """SYNC_COMPLETE template should format correctly."""
        template = TEMPLATES[EmailTemplate.SYNC_COMPLETE]
        context = {
            "count": 20,
            "products": 7,
        }

        subject = template["subject"].format(**context)
        html = template["html"].format(**context)

        assert "20" in subject
        assert "20" in html
        assert "7" in html
