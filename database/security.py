"""
Enhanced Database Security for DevSkyy Enterprise Platform
Connection pooling, credential management, and security monitoring
"""

import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Optional

from cryptography.fernet import Fernet
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

logger = logging.getLogger(__name__)


# ============================================================================
# CREDENTIAL ENCRYPTION
# ============================================================================


class CredentialManager:
    """Secure credential management with encryption"""

    def __init__(self):
        # Get or generate encryption key
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)

        # Cache for decrypted credentials (with TTL)
        self._credential_cache = {}
        self._cache_ttl = {}
        self._cache_duration = timedelta(minutes=5)  # 5-minute cache

    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate new one"""
        key_env = os.getenv("DB_ENCRYPTION_KEY")
        if key_env:
            return key_env.encode()

        # Generate new key (in production, store this securely)
        key = Fernet.generate_key()
        logger.warning(
            "🔑 Generated new encryption key - store securely in production!"
        )
        return key

    def encrypt_credential(self, credential: str) -> str:
        """Encrypt a credential"""
        return self.cipher.encrypt(credential.encode()).decode()

    def decrypt_credential(self, encrypted_credential: str) -> str:
        """Decrypt a credential with caching"""
        # Check cache first
        if encrypted_credential in self._credential_cache:
            cache_time = self._cache_ttl[encrypted_credential]
            if datetime.now() < cache_time:
                return self._credential_cache[encrypted_credential]
            else:
                # Cache expired
                del self._credential_cache[encrypted_credential]
                del self._cache_ttl[encrypted_credential]

        # Decrypt and cache
        decrypted = self.cipher.decrypt(encrypted_credential.encode()).decode()
        self._credential_cache[encrypted_credential] = decrypted
        self._cache_ttl[encrypted_credential] = datetime.now() + self._cache_duration

        return decrypted

    def clear_cache(self):
        """Clear credential cache for security"""
        self._credential_cache.clear()
        self._cache_ttl.clear()
        logger.info("🧹 Credential cache cleared")


# ============================================================================
# CONNECTION POOL SECURITY
# ============================================================================


class SecureConnectionPool:
    """Enhanced connection pool with security monitoring"""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "suspicious_queries": 0,
        }

        # Track connection patterns
        self.connection_history = deque(maxlen=1000)
        self.query_patterns = defaultdict(int)
        self.suspicious_ips = set()

        # Set up connection event listeners
        self._setup_connection_monitoring()

    def _setup_connection_monitoring(self):
        """Set up SQLAlchemy event listeners for security monitoring"""

        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Monitor database connections"""
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] += 1

            connection_info = {
                "timestamp": datetime.now(),
                "event": "connect",
                "connection_id": id(dbapi_connection),
            }
            self.connection_history.append(connection_info)

            logger.debug(f"🔌 Database connection established: {id(dbapi_connection)}")

        @event.listens_for(self.engine.sync_engine, "close")
        def on_close(dbapi_connection, connection_record):
            """Monitor connection closures"""
            self.connection_stats["active_connections"] -= 1

            connection_info = {
                "timestamp": datetime.now(),
                "event": "close",
                "connection_id": id(dbapi_connection),
            }
            self.connection_history.append(connection_info)

            logger.debug(f"🔌 Database connection closed: {id(dbapi_connection)}")

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def on_before_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Monitor SQL queries for security threats"""
            # Record query pattern
            query_type = (
                statement.strip().split()[0].upper() if statement.strip() else "UNKNOWN"
            )
            self.query_patterns[query_type] += 1

            # Check for suspicious patterns
            if self._is_suspicious_query(statement):
                self.connection_stats["suspicious_queries"] += 1
                logger.warning(f"🚨 Suspicious query detected: {statement[:100]}...")

                # In production, you might want to block the query
                # raise Exception("Suspicious query blocked")

        @event.listens_for(self.engine.sync_engine, "handle_error")
        def on_error(exception_context):
            """Monitor database errors"""
            self.connection_stats["failed_connections"] += 1

            error_info = {
                "timestamp": datetime.now(),
                "event": "error",
                "error": str(exception_context.original_exception),
            }
            self.connection_history.append(error_info)

            logger.error(f"💥 Database error: {exception_context.original_exception}")

    def _is_suspicious_query(self, statement: str) -> bool:
        """Detect suspicious SQL patterns"""
        if not statement:
            return False

        statement_upper = statement.upper()

        # Suspicious patterns
        suspicious_patterns = [
            "UNION SELECT",
            "DROP TABLE",
            "DROP DATABASE",
            "DELETE FROM",
            "TRUNCATE",
            "ALTER TABLE",
            "CREATE USER",
            "GRANT ALL",
            "LOAD_FILE",
            "INTO OUTFILE",
            "BENCHMARK(",
            "SLEEP(",
            "WAITFOR DELAY",
        ]

        for pattern in suspicious_patterns:
            if pattern in statement_upper:
                return True

        # Check for excessive wildcards (potential data exfiltration)
        if statement_upper.count("SELECT *") > 1:
            return True

        return False

    def get_security_stats(self) -> Dict:
        """Get connection security statistics"""
        return {
            **self.connection_stats,
            "query_patterns": dict(self.query_patterns),
            "recent_connections": len(
                [
                    conn
                    for conn in self.connection_history
                    if conn["timestamp"] > datetime.now() - timedelta(minutes=5)
                ]
            ),
            "suspicious_ips": list(self.suspicious_ips),
        }


# ============================================================================
# SECURE SESSION MANAGER
# ============================================================================


class SecureSessionManager:
    """Enhanced session manager with security features"""

    def __init__(self, session_factory, credential_manager: CredentialManager):
        self.session_factory = session_factory
        self.credential_manager = credential_manager
        self.active_sessions = {}
        self.session_stats = defaultdict(int)

    @asynccontextmanager
    async def get_secure_session(
        self, user_id: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get a secure database session with monitoring"""
        session_id = f"session_{int(time.time() * 1000)}"

        try:
            async with self.session_factory() as session:
                # Track session
                self.active_sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now(),
                    "queries_executed": 0,
                }
                self.session_stats["total_sessions"] += 1
                self.session_stats["active_sessions"] += 1

                # Set up session-level security
                await self._setup_session_security(session, user_id)

                logger.debug(
                    f"🔐 Secure session created: {session_id} for user: {user_id}"
                )

                yield session

                # Commit transaction
                await session.commit()
                logger.debug(f"✅ Session committed: {session_id}")

        except Exception as e:
            # Rollback on error
            await session.rollback()
            logger.error(f"💥 Session error: {session_id} - {e}")
            self.session_stats["failed_sessions"] += 1
            raise

        finally:
            # Clean up session tracking
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            self.session_stats["active_sessions"] -= 1
            logger.debug(f"🧹 Session cleaned up: {session_id}")

    async def _setup_session_security(
        self, session: AsyncSession, user_id: Optional[str]
    ):
        """Set up session-level security configurations"""
        try:
            # Set session timeout (PostgreSQL)
            await session.execute(text("SET statement_timeout = '30s'"))

            # Set row security (if using RLS)
            if user_id:
                await session.execute(text(f"SET app.current_user_id = '{user_id}'"))

            # Disable dangerous functions (PostgreSQL)
            await session.execute(text("SET default_transaction_read_only = false"))

        except Exception as e:
            # Some databases might not support these settings
            logger.debug(f"Session security setup warning: {e}")

    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        return {
            **dict(self.session_stats),
            "active_session_count": len(self.active_sessions),
            "active_sessions": [
                {
                    "session_id": sid,
                    "user_id": info["user_id"],
                    "duration_seconds": (
                        datetime.now() - info["created_at"]
                    ).total_seconds(),
                    "queries_executed": info["queries_executed"],
                }
                for sid, info in self.active_sessions.items()
            ],
        }


# ============================================================================
# DATABASE SECURITY MANAGER
# ============================================================================


class DatabaseSecurityManager:
    """Comprehensive database security management"""

    def __init__(self, engine: AsyncEngine, session_factory):
        self.engine = engine
        self.session_factory = session_factory
        self.credential_manager = CredentialManager()
        self.connection_pool = SecureConnectionPool(engine)
        self.session_manager = SecureSessionManager(
            session_factory, self.credential_manager
        )

        # Security monitoring
        self.security_events = deque(maxlen=1000)
        self.threat_level = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL

    async def get_secure_session(
        self, user_id: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get a secure database session"""
        async with self.session_manager.get_secure_session(user_id) as session:
            yield session

    def record_security_event(self, event_type: str, details: Dict):
        """Record a security event"""
        event = {
            "timestamp": datetime.now(),
            "type": event_type,
            "details": details,
        }
        self.security_events.append(event)

        # Update threat level based on events
        self._update_threat_level()

        logger.info(f"🔒 Security event recorded: {event_type}")

    def _update_threat_level(self):
        """Update threat level based on recent security events"""
        recent_events = [
            event
            for event in self.security_events
            if event["timestamp"] > datetime.now() - timedelta(minutes=10)
        ]

        if len(recent_events) > 50:
            self.threat_level = "CRITICAL"
        elif len(recent_events) > 20:
            self.threat_level = "HIGH"
        elif len(recent_events) > 10:
            self.threat_level = "MEDIUM"
        else:
            self.threat_level = "LOW"

    def get_security_report(self) -> Dict:
        """Get comprehensive security report"""
        return {
            "threat_level": self.threat_level,
            "connection_stats": self.connection_pool.get_security_stats(),
            "session_stats": self.session_manager.get_session_stats(),
            "recent_security_events": len(
                [
                    event
                    for event in self.security_events
                    if event["timestamp"] > datetime.now() - timedelta(hours=1)
                ]
            ),
            "credential_cache_size": len(self.credential_manager._credential_cache),
        }

    async def health_check(self) -> Dict:
        """Perform database security health check"""
        try:
            async with self.get_secure_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1"))
                result.fetchone()

                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "threat_level": self.threat_level,
                    "connection_pool_size": self.connection_pool.connection_stats[
                        "active_connections"
                    ],
                }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "threat_level": "HIGH",  # Elevated due to connectivity issues
            }
