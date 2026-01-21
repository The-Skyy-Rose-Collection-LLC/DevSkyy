# services/notifications/__init__.py
"""Notification services package.

Provides email and other notification capabilities.
"""

from services.notifications.email_notifications import (
    EmailConfig,
    EmailNotificationService,
    EmailTemplate,
    NotificationError,
    get_email_service,
)

__all__ = [
    "EmailConfig",
    "EmailNotificationService",
    "EmailTemplate",
    "NotificationError",
    "get_email_service",
]
