"""
Advanced Authentication & Authorization Security Module
======================================================

Enhanced security features for DevSkyy Enterprise Platform:
- Multi-Factor Authentication (MFA)
- Advanced rate limiting
- Session management
- Brute force protection
- Device fingerprinting
- Suspicious activity detection
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum

from fastapi import Request
from pydantic import BaseModel, Field

# Optional imports for MFA and Redis
try:
    import pyotp

    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    pyotp = None

try:
    from redis import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

logger = logging.getLogger(__name__)


class MFAMethod(str, Enum):
    """Multi-factor authentication methods"""

    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"  # SMS verification
    EMAIL = "email"  # Email verification
    BACKUP_CODES = "backup_codes"  # Backup recovery codes


class SecurityEvent(str, Enum):
    """Security event types for monitoring"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILED = "mfa_failed"
    SUSPICIOUS_LOGIN = "suspicious_login"
    ACCOUNT_LOCKED = "account_locked"
    PASSWORD_CHANGED = "password_changed"
    DEVICE_NEW = "device_new"


class DeviceFingerprint(BaseModel):
    """Device fingerprint for security tracking"""

    user_agent: str
    ip_address: str
    accept_language: str = ""
    timezone: str = ""
    screen_resolution: str = ""
    fingerprint_hash: str = ""

    def generate_hash(self) -> str:
        """Generate unique device fingerprint hash"""
        data = f"{self.user_agent}:{self.ip_address}:{self.accept_language}:{self.timezone}"
        self.fingerprint_hash = hashlib.sha256(data.encode()).hexdigest()[:16]
        return self.fingerprint_hash


class MFASetup(BaseModel):
    """MFA setup configuration"""

    method: MFAMethod
    secret_key: str = ""
    backup_codes: list[str] = Field(default_factory=list)
    phone_number: str = ""
    email: str = ""
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SecuritySession(BaseModel):
    """Enhanced security session"""

    session_id: str
    user_id: str
    device_fingerprint: str
    ip_address: str
    created_at: datetime
    last_activity: datetime
    is_mfa_verified: bool = False
    risk_score: int = 0  # 0-100, higher is riskier

    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if session is expired"""
        return datetime.now(UTC) - self.last_activity > timedelta(hours=max_age_hours)

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(UTC)


class AdvancedAuthManager:
    """
    Advanced authentication manager with enterprise security features.

    Features:
    - Multi-factor authentication
    - Rate limiting and brute force protection
    - Device fingerprinting
    - Session management
    - Security event logging
    - Risk-based authentication
    """

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.sessions: dict[str, SecuritySession] = {}
        self.failed_attempts: dict[str, list[datetime]] = {}
        self.device_fingerprints: dict[str, set[str]] = {}  # user_id -> device_hashes

        # Security configuration
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.session_timeout_hours = 24
        self.suspicious_login_threshold = 3

    def generate_mfa_secret(self) -> str:
        """Generate TOTP secret for MFA setup"""
        if PYOTP_AVAILABLE:
            return pyotp.random_base32()
        else:
            # Fallback: generate base32-compatible secret
            import base64

            return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup recovery codes"""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    def setup_mfa(self, user_id: str, method: MFAMethod, **kwargs) -> MFASetup:
        """Set up multi-factor authentication for user"""
        setup = MFASetup(method=method)

        if method == MFAMethod.TOTP:
            setup.secret_key = self.generate_mfa_secret()
            setup.backup_codes = self.generate_backup_codes()

        elif method == MFAMethod.SMS:
            setup.phone_number = kwargs.get("phone_number", "")
            setup.backup_codes = self.generate_backup_codes()

        elif method == MFAMethod.EMAIL:
            setup.email = kwargs.get("email", "")
            setup.backup_codes = self.generate_backup_codes()

        # Store MFA setup (in production, store in database)
        if self.redis:
            self.redis.setex(f"mfa_setup:{user_id}", 86400, setup.model_dump_json())  # 24 hours

        logger.info(f"MFA setup initiated for user {user_id} with method {method}")
        return setup

    def verify_mfa_code(self, user_id: str, code: str, method: MFAMethod) -> bool:
        """Verify MFA code"""
        try:
            if method == MFAMethod.TOTP:
                if not PYOTP_AVAILABLE:
                    logger.warning("TOTP verification requires pyotp package")
                    return False
                # Get user's TOTP secret
                if self.redis:
                    setup_data = self.redis.get(f"mfa_setup:{user_id}")
                    if setup_data:
                        setup = MFASetup.model_validate_json(setup_data)
                        totp = pyotp.TOTP(setup.secret_key)
                        return totp.verify(code, valid_window=1)

            elif method == MFAMethod.BACKUP_CODES:
                # Verify backup code (single use)
                if self.redis:
                    setup_data = self.redis.get(f"mfa_setup:{user_id}")
                    if setup_data:
                        setup = MFASetup.model_validate_json(setup_data)
                        if code.upper() in setup.backup_codes:
                            # Remove used backup code
                            setup.backup_codes.remove(code.upper())
                            self.redis.setex(f"mfa_setup:{user_id}", 86400, setup.model_dump_json())
                            return True

            return False

        except Exception as e:
            logger.error(f"MFA verification failed for user {user_id}: {e}")
            return False

    def create_device_fingerprint(self, request: Request) -> DeviceFingerprint:
        """Create device fingerprint from request"""
        fingerprint = DeviceFingerprint(
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host if request.client else "",
            accept_language=request.headers.get("accept-language", ""),
            timezone=request.headers.get("x-timezone", ""),
        )
        fingerprint.generate_hash()
        return fingerprint

    def is_device_trusted(self, user_id: str, device_hash: str) -> bool:
        """Check if device is trusted for user"""
        user_devices = self.device_fingerprints.get(user_id, set())
        return device_hash in user_devices

    def trust_device(self, user_id: str, device_hash: str):
        """Mark device as trusted for user"""
        if user_id not in self.device_fingerprints:
            self.device_fingerprints[user_id] = set()
        self.device_fingerprints[user_id].add(device_hash)

        # Store in Redis if available
        if self.redis:
            self.redis.sadd(f"trusted_devices:{user_id}", device_hash)
            self.redis.expire(f"trusted_devices:{user_id}", 86400 * 30)  # 30 days

    def calculate_risk_score(self, user_id: str, request: Request) -> int:
        """Calculate risk score for authentication attempt"""
        risk_score = 0

        # Check for new device
        fingerprint = self.create_device_fingerprint(request)
        if not self.is_device_trusted(user_id, fingerprint.fingerprint_hash):
            risk_score += 30

        # Check for unusual location (simplified - would use GeoIP in production)
        ip_address = fingerprint.ip_address
        if ip_address.startswith("10.") or ip_address.startswith("192.168."):
            risk_score += 10  # Private IP might be suspicious

        # Check recent failed attempts
        failed_attempts = self.failed_attempts.get(user_id, [])
        recent_failures = [
            attempt
            for attempt in failed_attempts
            if datetime.now(UTC) - attempt < timedelta(hours=1)
        ]
        risk_score += len(recent_failures) * 10

        # Check time of day (simplified)
        current_hour = datetime.now(UTC).hour
        if current_hour < 6 or current_hour > 22:  # Late night/early morning
            risk_score += 15

        return min(risk_score, 100)  # Cap at 100

    def is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked due to failed attempts"""
        failed_attempts = self.failed_attempts.get(user_id, [])

        # Remove old attempts
        cutoff_time = datetime.now(UTC) - timedelta(minutes=self.lockout_duration_minutes)
        recent_attempts = [attempt for attempt in failed_attempts if attempt > cutoff_time]
        self.failed_attempts[user_id] = recent_attempts

        return len(recent_attempts) >= self.max_failed_attempts

    def record_failed_attempt(self, user_id: str):
        """Record a failed authentication attempt"""
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = []

        self.failed_attempts[user_id].append(datetime.now(UTC))

        # Log security event
        self.log_security_event(user_id, SecurityEvent.LOGIN_FAILED)

        # Check if account should be locked
        if self.is_account_locked(user_id):
            self.log_security_event(user_id, SecurityEvent.ACCOUNT_LOCKED)

    def log_security_event(self, user_id: str, event: SecurityEvent, **metadata):
        """Log security event for monitoring"""
        event_data = {
            "user_id": user_id,
            "event": event.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata,
        }

        logger.info(f"Security event: {event_data}")

        # Store in Redis for real-time monitoring
        if self.redis:
            self.redis.lpush(f"security_events:{user_id}", str(event_data))
            self.redis.expire(f"security_events:{user_id}", 86400 * 7)  # 7 days

    def create_secure_session(
        self, user_id: str, request: Request, is_mfa_verified: bool = False
    ) -> SecuritySession:
        """Create a new secure session"""
        fingerprint = self.create_device_fingerprint(request)
        risk_score = self.calculate_risk_score(user_id, request)

        session = SecuritySession(
            session_id=secrets.token_urlsafe(32),
            user_id=user_id,
            device_fingerprint=fingerprint.fingerprint_hash,
            ip_address=fingerprint.ip_address,
            created_at=datetime.now(UTC),
            last_activity=datetime.now(UTC),
            is_mfa_verified=is_mfa_verified,
            risk_score=risk_score,
        )

        self.sessions[session.session_id] = session

        # Store in Redis if available
        if self.redis:
            self.redis.setex(
                f"session:{session.session_id}",
                self.session_timeout_hours * 3600,
                session.model_dump_json(),
            )

        return session

    def validate_session(self, session_id: str) -> SecuritySession | None:
        """Validate and return session if valid"""
        session = self.sessions.get(session_id)

        if not session and self.redis:
            # Try to load from Redis
            session_data = self.redis.get(f"session:{session_id}")
            if session_data:
                session = SecuritySession.model_validate_json(session_data)
                self.sessions[session_id] = session

        if session and not session.is_expired(self.session_timeout_hours):
            session.update_activity()
            return session

        # Clean up expired session
        if session_id in self.sessions:
            del self.sessions[session_id]
        if self.redis:
            self.redis.delete(f"session:{session_id}")

        return None

    def revoke_session(self, session_id: str):
        """Revoke a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if self.redis:
            self.redis.delete(f"session:{session_id}")

    def revoke_all_user_sessions(self, user_id: str):
        """Revoke all sessions for a user"""
        sessions_to_remove = [
            sid for sid, session in self.sessions.items() if session.user_id == user_id
        ]

        for session_id in sessions_to_remove:
            self.revoke_session(session_id)


# Global instance
advanced_auth = AdvancedAuthManager()
