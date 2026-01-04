"""
Zero Trust Architecture Configuration

This module provides the foundational configuration for Zero Trust security,
including certificate management, service identity, and mTLS configuration.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

logger = logging.getLogger(__name__)


def get_cert_not_valid_before(cert: x509.Certificate) -> datetime:
    """Get certificate not_valid_before with compatibility for cryptography < 42.0"""
    try:
        return cert.not_valid_before_utc
    except AttributeError:
        # Pre-42.0: not_valid_before is naive, assume UTC
        dt = cert.not_valid_before
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def get_cert_not_valid_after(cert: x509.Certificate) -> datetime:
    """Get certificate not_valid_after with compatibility for cryptography < 42.0"""
    try:
        return cert.not_valid_after_utc
    except AttributeError:
        # Pre-42.0: not_valid_after is naive, assume UTC
        dt = cert.not_valid_after
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


@dataclass
class ServiceIdentity:
    """Service identity configuration"""

    name: str
    port: int
    require_mtls: bool = True
    allowed_peers: list[str] = field(default_factory=list)
    cert_path: Path | None = None
    key_path: Path | None = None
    ca_path: Path | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "port": self.port,
            "require_mtls": self.require_mtls,
            "allowed_peers": self.allowed_peers,
            "cert_path": str(self.cert_path) if self.cert_path else None,
            "key_path": str(self.key_path) if self.key_path else None,
            "ca_path": str(self.ca_path) if self.ca_path else None,
        }


@dataclass
class ZeroTrustConfig:
    """
    Zero Trust Architecture Configuration

    Manages the core configuration for Zero Trust security including:
    - Certificate authority type and settings
    - Certificate rotation policies
    - Service identity and mTLS requirements
    - Trust boundaries and policies
    """

    enabled: bool = False
    ca_type: str = "self-signed"  # Options: self-signed, vault, cert-manager
    cert_dir: Path = field(default_factory=lambda: Path("/etc/devskyy/certs"))
    auto_rotate: bool = True
    rotation_days: int = 30
    services: list[ServiceIdentity] = field(default_factory=list)

    # Advanced settings
    require_peer_verification: bool = True
    allow_insecure_connections: bool = False
    max_cert_chain_depth: int = 3
    crl_check_enabled: bool = True
    ocsp_check_enabled: bool = False

    # Key parameters
    key_size: int = 4096
    signature_algorithm: str = "SHA256"

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.ca_type not in ["self-signed", "vault", "cert-manager"]:
            raise ValueError(f"Invalid ca_type: {self.ca_type}")

        if self.rotation_days < 1:
            raise ValueError("rotation_days must be >= 1")

        if self.key_size < 2048:
            raise ValueError("key_size must be >= 2048")

        # Create cert directory if it doesn't exist
        if self.enabled:
            self.cert_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "ZeroTrustConfig":
        """Load configuration from YAML file"""
        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls()

        with open(config_path) as f:
            data = yaml.safe_load(f)

        zt_config = data.get("zero_trust", {})

        # Parse services
        services = []
        for svc_data in zt_config.get("services", []):
            services.append(
                ServiceIdentity(
                    name=svc_data["name"],
                    port=svc_data["port"],
                    require_mtls=svc_data.get("require_mtls", True),
                    allowed_peers=svc_data.get("allowed_peers", []),
                )
            )

        return cls(
            enabled=zt_config.get("enabled", False),
            ca_type=zt_config.get("ca_type", "self-signed"),
            cert_dir=Path(zt_config.get("cert_dir", "/etc/devskyy/certs")),
            auto_rotate=zt_config.get("auto_rotate", True),
            rotation_days=zt_config.get("cert_rotation_days", 30),
            services=services,
            require_peer_verification=zt_config.get("require_peer_verification", True),
            allow_insecure_connections=zt_config.get("allow_insecure_connections", False),
            max_cert_chain_depth=zt_config.get("max_cert_chain_depth", 3),
            crl_check_enabled=zt_config.get("crl_check_enabled", True),
            ocsp_check_enabled=zt_config.get("ocsp_check_enabled", False),
            key_size=zt_config.get("key_size", 4096),
            signature_algorithm=zt_config.get("signature_algorithm", "SHA256"),
        )

    def to_yaml(self, output_path: str | Path):
        """Save configuration to YAML file"""
        output_path = Path(output_path)

        data = {
            "zero_trust": {
                "enabled": self.enabled,
                "ca_type": self.ca_type,
                "cert_dir": str(self.cert_dir),
                "auto_rotate": self.auto_rotate,
                "cert_rotation_days": self.rotation_days,
                "require_peer_verification": self.require_peer_verification,
                "allow_insecure_connections": self.allow_insecure_connections,
                "max_cert_chain_depth": self.max_cert_chain_depth,
                "crl_check_enabled": self.crl_check_enabled,
                "ocsp_check_enabled": self.ocsp_check_enabled,
                "key_size": self.key_size,
                "signature_algorithm": self.signature_algorithm,
                "services": [svc.to_dict() for svc in self.services],
            }
        }

        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_service(self, service_name: str) -> ServiceIdentity | None:
        """Get service configuration by name"""
        for svc in self.services:
            if svc.name == service_name:
                return svc
        return None

    def add_service(self, service: ServiceIdentity):
        """Add a service to the configuration"""
        # Remove existing service with same name
        self.services = [s for s in self.services if s.name != service.name]
        self.services.append(service)


class CertificateInfo:
    """Certificate information wrapper"""

    def __init__(self, cert: x509.Certificate):
        self.cert = cert
        self.subject = cert.subject
        self.issuer = cert.issuer
        self.serial_number = cert.serial_number
        self.not_valid_before = get_cert_not_valid_before(cert)
        self.not_valid_after = get_cert_not_valid_after(cert)
        self.fingerprint = cert.fingerprint(hashes.SHA256()).hex()

    @property
    def common_name(self) -> str:
        """Get certificate common name"""
        cn_attr = self.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        return cn_attr[0].value if cn_attr else ""

    @property
    def is_expired(self) -> bool:
        """Check if certificate is expired"""
        return datetime.now(self.not_valid_after.tzinfo) > self.not_valid_after

    @property
    def days_until_expiry(self) -> int:
        """Days until certificate expires"""
        delta = self.not_valid_after - datetime.now(self.not_valid_after.tzinfo)
        return delta.days

    @property
    def needs_rotation(self) -> bool:
        """Check if certificate needs rotation based on expiry"""
        return self.days_until_expiry < 7  # Rotate within 7 days of expiry

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "subject": str(self.subject),
            "issuer": str(self.issuer),
            "serial_number": str(self.serial_number),
            "not_valid_before": self.not_valid_before.isoformat(),
            "not_valid_after": self.not_valid_after.isoformat(),
            "fingerprint": self.fingerprint,
            "common_name": self.common_name,
            "is_expired": self.is_expired,
            "days_until_expiry": self.days_until_expiry,
            "needs_rotation": self.needs_rotation,
        }


class CertificateManager:
    """
    Certificate Manager for Zero Trust Architecture

    Manages certificate lifecycle including:
    - Certificate generation and signing
    - Certificate rotation and renewal
    - Certificate verification and validation
    - Certificate storage and retrieval
    """

    def __init__(self, config: ZeroTrustConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CertificateManager")

    def generate_cert(
        self,
        service_name: str,
        ca_cert: x509.Certificate,
        ca_key: rsa.RSAPrivateKey,
        validity_days: int = None,
    ) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
        """
        Generate a service certificate signed by the CA

        Args:
            service_name: Name of the service
            ca_cert: CA certificate for signing
            ca_key: CA private key for signing
            validity_days: Certificate validity period (default: rotation_days)

        Returns:
            Tuple of (certificate, private_key)
        """
        if validity_days is None:
            validity_days = self.config.rotation_days

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=self.config.key_size, backend=default_backend()
        )

        # Build certificate
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DevSkyy"),
                x509.NameAttribute(NameOID.COMMON_NAME, service_name),
            ]
        )

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(ca_cert.subject)
        builder = builder.public_key(private_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(datetime.utcnow())
        builder = builder.not_valid_after(datetime.utcnow() + timedelta(days=validity_days))

        # Add extensions
        builder = builder.add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName(service_name),
                    x509.DNSName(f"{service_name}.devskyy.local"),
                ]
            ),
            critical=False,
        )

        builder = builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )

        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )

        builder = builder.add_extension(
            x509.ExtendedKeyUsage(
                [
                    x509.ExtendedKeyUsageOID.SERVER_AUTH,
                    x509.ExtendedKeyUsageOID.CLIENT_AUTH,
                ]
            ),
            critical=False,
        )

        # Sign certificate
        hash_algo = getattr(hashes, self.config.signature_algorithm)()
        certificate = builder.sign(ca_key, hash_algo, default_backend())

        self.logger.info(
            f"Generated certificate for {service_name}, valid for {validity_days} days"
        )

        return certificate, private_key

    def save_cert(
        self,
        service_name: str,
        cert: x509.Certificate,
        key: rsa.RSAPrivateKey,
    ):
        """Save certificate and key to disk"""
        service_dir = self.config.cert_dir / service_name
        service_dir.mkdir(parents=True, exist_ok=True)

        cert_path = service_dir / "cert.pem"
        key_path = service_dir / "key.pem"

        # Write certificate
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Write private key
        with open(key_path, "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Set restrictive permissions
        os.chmod(cert_path, 0o644)
        os.chmod(key_path, 0o600)

        self.logger.info(f"Saved certificate for {service_name} to {service_dir}")

        return cert_path, key_path

    def load_cert(self, service_name: str) -> CertificateInfo | None:
        """Load certificate from disk"""
        cert_path = self.config.cert_dir / service_name / "cert.pem"

        if not cert_path.exists():
            self.logger.warning(f"Certificate not found for {service_name}")
            return None

        try:
            with open(cert_path, "rb") as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            return CertificateInfo(cert)
        except Exception as e:
            self.logger.error(f"Failed to load certificate for {service_name}: {e}")
            return None

    def verify_cert(
        self,
        cert: x509.Certificate,
        ca_cert: x509.Certificate,
        check_expiry: bool = True,
    ) -> bool:
        """
        Verify certificate is valid and signed by CA

        Args:
            cert: Certificate to verify
            ca_cert: CA certificate
            check_expiry: Whether to check if certificate is expired

        Returns:
            True if certificate is valid
        """
        try:
            # Check if certificate is signed by CA
            from cryptography.hazmat.primitives.asymmetric import padding

            ca_public_key = ca_cert.public_key()
            chosen_hash = cert.signature_hash_algorithm

            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                chosen_hash,
            )

            # Check expiry
            if check_expiry:
                cert_info = CertificateInfo(cert)
                if cert_info.is_expired:
                    self.logger.error(f"Certificate expired on {cert_info.not_valid_after}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Certificate verification failed: {e}")
            return False

    def rotate_cert(
        self,
        service_name: str,
        ca_cert: x509.Certificate,
        ca_key: rsa.RSAPrivateKey,
    ) -> bool:
        """
        Rotate certificate for a service

        Args:
            service_name: Name of the service
            ca_cert: CA certificate for signing
            ca_key: CA private key for signing

        Returns:
            True if rotation successful
        """
        try:
            # Check if rotation is needed
            cert_info = self.load_cert(service_name)
            if cert_info and not cert_info.needs_rotation:
                self.logger.info(
                    f"Certificate for {service_name} does not need rotation "
                    f"({cert_info.days_until_expiry} days remaining)"
                )
                return True

            # Generate new certificate
            cert, key = self.generate_cert(service_name, ca_cert, ca_key)

            # Backup old certificate
            if cert_info:
                old_cert_dir = self.config.cert_dir / service_name / "old"
                old_cert_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                old_cert_path = old_cert_dir / f"cert_{timestamp}.pem"

                cert_path = self.config.cert_dir / service_name / "cert.pem"
                if cert_path.exists():
                    import shutil

                    shutil.copy2(cert_path, old_cert_path)

            # Save new certificate
            self.save_cert(service_name, cert, key)

            self.logger.info(f"Successfully rotated certificate for {service_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to rotate certificate for {service_name}: {e}")
            return False

    def check_rotation_needed(self) -> list[str]:
        """
        Check all service certificates and return list of services needing rotation

        Returns:
            List of service names that need certificate rotation
        """
        needs_rotation = []

        for service in self.config.services:
            cert_info = self.load_cert(service.name)
            if cert_info and cert_info.needs_rotation:
                needs_rotation.append(service.name)
                self.logger.warning(
                    f"Certificate for {service.name} needs rotation "
                    f"({cert_info.days_until_expiry} days until expiry)"
                )

        return needs_rotation

    def get_cert_status(self) -> dict[str, dict]:
        """Get status of all service certificates"""
        status = {}

        for service in self.config.services:
            cert_info = self.load_cert(service.name)
            if cert_info:
                status[service.name] = cert_info.to_dict()
            else:
                status[service.name] = {"error": "Certificate not found"}

        return status
