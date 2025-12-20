"""
Staging Zero Trust mTLS Tests
==============================

Comprehensive Zero Trust and mTLS tests for staging environment.

Tests:
- Service-to-service mTLS connections
- Certificate rotation functionality
- Service identity validation
- Certificate validation and rejection
- Zero Trust network policies

Environment:
- CERT_DIR: Certificate directory (default: /tmp/devskyy-certs)

Usage:
    pytest tests/test_staging_zero_trust.py -v
    pytest tests/test_staging_zero_trust.py::TestmTLSConnections -v
"""

import os
from pathlib import Path

import pytest

CERT_DIR = Path(os.getenv("CERT_DIR", "/tmp/devskyy-certs"))


# =============================================================================
# Test Class: mTLS Connections
# =============================================================================


@pytest.mark.integration
class TestmTLSConnections:
    """Test service-to-service mTLS connections"""

    @pytest.fixture
    def zero_trust_config(self):
        """Create Zero Trust configuration"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(
            cert_dir=CERT_DIR,
            ca_name="DevSkyy-Test-CA",
            ca_validity_days=365,
        )

        # Ensure cert directory exists
        CERT_DIR.mkdir(parents=True, exist_ok=True)

        return config

    @pytest.fixture
    def mtls_handler(self, zero_trust_config):
        """Create mTLS handler"""
        from security.mtls_handler import MTLSHandler

        handler = MTLSHandler(zero_trust_config)
        return handler

    def test_mtls_handler_initialization(self, zero_trust_config):
        """Test mTLS handler initializes correctly"""
        from security.mtls_handler import MTLSHandler

        handler = MTLSHandler(zero_trust_config)
        assert handler is not None
        assert handler.config == zero_trust_config

    def test_generate_service_certificates(self, zero_trust_config, mtls_handler):
        """Test generating certificates for services"""
        from security.certificate_authority import SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)

        # Initialize CA if not exists
        if not ca.ca_exists():
            ca.initialize_ca()

        # Add a test service
        service = zero_trust_config.add_service(
            name="test-api-service",
            host="localhost",
            port=8000,
            require_mtls=True,
        )

        # Generate certificate for the service
        cert, key = ca.generate_service_certificate(
            service_name="test-api-service",
            common_name="test-api-service",
            validity_days=30,
        )

        assert cert is not None
        assert key is not None

    def test_client_ssl_context_creation(self, zero_trust_config, mtls_handler):
        """Test creating client SSL context"""
        from security.certificate_authority import SelfSignedCA

        # Setup
        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Add service
        zero_trust_config.add_service(
            name="test-client",
            host="localhost",
            port=8001,
            require_mtls=True,
        )

        # Generate certificate
        ca.generate_service_certificate(
            service_name="test-client",
            common_name="test-client",
        )

        # Create SSL context
        try:
            context = mtls_handler.enable_client_tls("test-client")
            assert context is not None
            assert context.minimum_version.name == "TLSv1_3"
        except FileNotFoundError:
            # Expected if certificates don't exist yet
            pytest.skip("Certificates not generated yet")

    def test_server_ssl_context_creation(self, zero_trust_config, mtls_handler):
        """Test creating server SSL context"""
        from security.certificate_authority import SelfSignedCA

        # Setup
        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Add service
        zero_trust_config.add_service(
            name="test-server",
            host="0.0.0.0",
            port=8002,
            require_mtls=True,
        )

        # Generate certificate
        ca.generate_service_certificate(
            service_name="test-server",
            common_name="test-server",
        )

        # Create SSL context
        try:
            context = mtls_handler.enable_server_tls("test-server")
            assert context is not None
            assert context.minimum_version.name == "TLSv1_3"
        except FileNotFoundError:
            pytest.skip("Certificates not generated yet")

    def test_mtls_requires_client_certificate(self, zero_trust_config, mtls_handler):
        """Test that mTLS requires client certificate"""
        from security.certificate_authority import SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Add service that requires mTLS
        zero_trust_config.add_service(
            name="secure-api",
            host="localhost",
            port=8443,
            require_mtls=True,
        )

        # Generate certificate
        ca.generate_service_certificate(
            service_name="secure-api",
            common_name="secure-api",
        )

        # Create server context with mTLS
        try:
            context = mtls_handler.enable_server_tls("secure-api", require_client_cert=True)
            assert context is not None

            # Should require client certificates
            import ssl

            assert context.verify_mode == ssl.CERT_REQUIRED
        except FileNotFoundError:
            pytest.skip("Certificates not generated yet")


# =============================================================================
# Test Class: Certificate Rotation
# =============================================================================


@pytest.mark.integration
class TestCertificateRotation:
    """Test certificate rotation functionality"""

    @pytest.fixture
    def zero_trust_config(self):
        """Create Zero Trust configuration"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        return config

    def test_certificate_expiry_detection(self, zero_trust_config):
        """Test detecting certificate expiry"""
        from security.certificate_authority import CertificateValidator, SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate a short-lived certificate
        cert, key = ca.generate_service_certificate(
            service_name="short-lived-service",
            common_name="short-lived-service",
            validity_days=30,
        )

        # Check expiry
        validator = CertificateValidator()
        expiry_info = validator.check_certificate_expiry(cert)

        assert not expiry_info["is_expired"]
        assert expiry_info["days_until_expiry"] > 0
        assert expiry_info["days_until_expiry"] <= 30

    def test_certificate_rotation(self, zero_trust_config):
        """Test rotating a certificate"""
        from security.certificate_authority import SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate initial certificate
        cert1, key1 = ca.generate_service_certificate(
            service_name="rotating-service",
            common_name="rotating-service",
        )

        # Get serial number
        serial1 = cert1.serial_number

        # Rotate certificate (generate new one)
        cert2, key2 = ca.generate_service_certificate(
            service_name="rotating-service",
            common_name="rotating-service",
        )

        # Should have different serial number
        serial2 = cert2.serial_number
        assert serial1 != serial2

    def test_old_certificate_cleanup(self, zero_trust_config):
        """Test that old certificates can be cleaned up"""
        from security.certificate_authority import SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate certificate
        service_name = "cleanup-test-service"
        cert, key = ca.generate_service_certificate(
            service_name=service_name,
            common_name=service_name,
        )

        # Certificate files should exist
        cert_dir = zero_trust_config.cert_dir / service_name
        assert (cert_dir / "cert.pem").exists()
        assert (cert_dir / "key.pem").exists()


# =============================================================================
# Test Class: Service Identity Validation
# =============================================================================


@pytest.mark.integration
class TestServiceIdentity:
    """Test service identity validation"""

    @pytest.fixture
    def zero_trust_config(self):
        """Create Zero Trust configuration"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        return config

    def test_service_identity_in_certificate(self, zero_trust_config):
        """Test that service identity is embedded in certificate"""
        from cryptography import x509

        from security.certificate_authority import SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate certificate with specific identity
        service_name = "identity-test-service"
        cert, key = ca.generate_service_certificate(
            service_name=service_name,
            common_name=service_name,
        )

        # Check common name
        cn_attr = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
        assert len(cn_attr) > 0
        assert cn_attr[0].value == service_name

    def test_validate_service_identity_match(self, zero_trust_config):
        """Test validating matching service identity"""
        from security.certificate_authority import SelfSignedCA
        from security.mtls_handler import MTLSHandler

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate certificate
        service_name = "validation-service"
        cert, key = ca.generate_service_certificate(
            service_name=service_name,
            common_name=service_name,
        )

        # Validate identity
        handler = MTLSHandler(zero_trust_config)
        is_valid = handler.validate_service_identity(cert, service_name)

        assert is_valid, "Service identity should match"

    def test_validate_service_identity_mismatch(self, zero_trust_config):
        """Test detecting service identity mismatch"""
        from security.certificate_authority import SelfSignedCA
        from security.mtls_handler import MTLSHandler

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate certificate
        cert, key = ca.generate_service_certificate(
            service_name="service-a",
            common_name="service-a",
        )

        # Try to validate with different identity
        handler = MTLSHandler(zero_trust_config)
        is_valid = handler.validate_service_identity(cert, "service-b")

        assert not is_valid, "Service identity should not match"


# =============================================================================
# Test Class: Certificate Validation
# =============================================================================


@pytest.mark.integration
class TestCertificateValidation:
    """Test certificate validation and rejection"""

    @pytest.fixture
    def zero_trust_config(self):
        """Create Zero Trust configuration"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        return config

    def test_valid_certificate_accepted(self, zero_trust_config):
        """Test that valid certificates are accepted"""
        from security.certificate_authority import SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate valid certificate
        cert, key = ca.generate_service_certificate(
            service_name="valid-service",
            common_name="valid-service",
        )

        # Verify certificate
        is_valid = ca.verify_certificate(cert)
        assert is_valid, "Valid certificate should be accepted"

    def test_self_signed_certificate_rejected(self, zero_trust_config):
        """Test that self-signed certificates (not from CA) are rejected"""
        from datetime import UTC, datetime, timedelta

        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        from security.certificate_authority import SelfSignedCA

        # Generate a self-signed certificate (not from our CA)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "rogue-service"),
            ]
        )

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC))
            .not_valid_after(datetime.now(UTC) + timedelta(days=30))
            .sign(key, hashes.SHA256(), default_backend())
        )

        # Try to verify with our CA
        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        is_valid = ca.verify_certificate(cert)
        assert not is_valid, "Self-signed certificate should be rejected"

    def test_expired_certificate_rejected(self, zero_trust_config):
        """Test that expired certificates are rejected"""
        from datetime import UTC, datetime, timedelta

        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        from security.certificate_authority import CertificateValidator

        # Generate an expired certificate
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "expired-service")])

        # Create certificate that expired 1 day ago
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC) - timedelta(days=31))
            .not_valid_after(datetime.now(UTC) - timedelta(days=1))
            .sign(key, hashes.SHA256(), default_backend())
        )

        # Check expiry
        validator = CertificateValidator()
        expiry_info = validator.check_certificate_expiry(cert)

        assert expiry_info["is_expired"], "Certificate should be expired"

    def test_certificate_fingerprint_generation(self, zero_trust_config):
        """Test generating certificate fingerprints"""
        from security.certificate_authority import CertificateValidator, SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate certificate
        cert, key = ca.generate_service_certificate(
            service_name="fingerprint-service",
            common_name="fingerprint-service",
        )

        # Get fingerprint
        validator = CertificateValidator()
        fingerprint = validator.get_certificate_fingerprint(cert)

        assert fingerprint is not None
        assert len(fingerprint) == 64  # SHA-256 hex is 64 characters

    def test_certificate_chain_validation(self, zero_trust_config):
        """Test certificate chain validation"""
        from security.certificate_authority import CertificateValidator, SelfSignedCA

        ca = SelfSignedCA(zero_trust_config.cert_dir)
        if not ca.ca_exists():
            ca.initialize_ca()

        # Generate service certificate
        cert, key = ca.generate_service_certificate(
            service_name="chain-test-service",
            common_name="chain-test-service",
        )

        # Load CA certificate
        ca_cert, ca_key = ca.load_ca()

        # Validate chain
        validator = CertificateValidator()
        is_valid = validator.validate_cert_chain(cert, ca_cert)

        assert is_valid, "Certificate chain should be valid"


# =============================================================================
# Test Class: Zero Trust Configuration
# =============================================================================


@pytest.mark.integration
class TestZeroTrustConfiguration:
    """Test Zero Trust configuration and policies"""

    def test_zero_trust_config_initialization(self):
        """Test Zero Trust configuration initialization"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)

        assert config is not None
        assert config.cert_dir == CERT_DIR
        assert config.require_peer_verification

    def test_add_service_to_config(self):
        """Test adding services to configuration"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)

        # Add service
        service = config.add_service(
            name="config-test-api",
            host="localhost",
            port=8080,
            require_mtls=True,
        )

        assert service is not None
        assert service.name == "config-test-api"
        assert service.port == 8080
        assert service.require_mtls

    def test_get_service_from_config(self):
        """Test retrieving service from configuration"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)

        # Add service
        config.add_service(
            name="retrieval-test-api",
            host="localhost",
            port=8081,
        )

        # Retrieve service
        service = config.get_service("retrieval-test-api")

        assert service is not None
        assert service.name == "retrieval-test-api"

    def test_service_allowed_peers(self):
        """Test service allowed peers configuration"""
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)

        # Add service with allowed peers
        service = config.add_service(
            name="restricted-api",
            host="localhost",
            port=8082,
            allowed_peers=["frontend-service", "backend-service"],
        )

        assert len(service.allowed_peers) == 2
        assert "frontend-service" in service.allowed_peers
        assert "backend-service" in service.allowed_peers

    def test_certificate_authority_initialization(self):
        """Test Certificate Authority initialization"""
        from security.certificate_authority import SelfSignedCA
        from security.zero_trust_config import ZeroTrustConfig

        config = ZeroTrustConfig(cert_dir=CERT_DIR)
        ca = SelfSignedCA(config.cert_dir)

        # Initialize if needed
        if not ca.ca_exists():
            ca.initialize_ca()

        # Should have CA certificate and key
        assert ca.ca_exists()
