"""
Certificate Authority Implementation

This module provides certificate authority implementations for Zero Trust architecture:
- SelfSignedCA: Development and testing CA
- VaultCA: Production-grade CA using HashiCorp Vault
- Certificate validation and revocation checking
"""

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import ExtensionOID, NameOID

logger = logging.getLogger(__name__)


class CertificateRevocationList:
    """Certificate Revocation List (CRL) manager"""

    def __init__(self, crl_path: Path):
        self.crl_path = crl_path
        self.revoked_certs: dict[int, datetime] = {}
        self.load()

    def load(self):
        """Load CRL from disk"""
        if self.crl_path.exists():
            try:
                with open(self.crl_path) as f:
                    data = json.load(f)
                    self.revoked_certs = {
                        int(serial): datetime.fromisoformat(revoked_at)
                        for serial, revoked_at in data.items()
                    }
                logger.info(f"Loaded {len(self.revoked_certs)} revoked certificates from CRL")
            except Exception as e:
                logger.error(f"Failed to load CRL: {e}")

    def save(self):
        """Save CRL to disk"""
        try:
            self.crl_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                str(serial): revoked_at.isoformat()
                for serial, revoked_at in self.revoked_certs.items()
            }
            with open(self.crl_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved CRL with {len(self.revoked_certs)} revoked certificates")
        except Exception as e:
            logger.error(f"Failed to save CRL: {e}")

    def revoke(self, serial_number: int):
        """Add certificate to revocation list"""
        self.revoked_certs[serial_number] = datetime.utcnow()
        self.save()
        logger.warning(f"Revoked certificate with serial {serial_number}")

    def is_revoked(self, serial_number: int) -> bool:
        """Check if certificate is revoked"""
        return serial_number in self.revoked_certs

    def get_revocation_time(self, serial_number: int) -> datetime | None:
        """Get revocation time for a certificate"""
        return self.revoked_certs.get(serial_number)


class SelfSignedCA:
    """
    Self-Signed Certificate Authority for Development

    Provides a complete CA implementation for development and testing:
    - Root CA generation and management
    - Service certificate generation and signing
    - Certificate validation and verification
    - Certificate revocation list (CRL) management
    """

    def __init__(self, cert_dir: Path):
        self.cert_dir = cert_dir
        self.ca_cert_path = cert_dir / "ca" / "ca-cert.pem"
        self.ca_key_path = cert_dir / "ca" / "ca-key.pem"
        self.crl_path = cert_dir / "ca" / "crl.json"
        self.crl = CertificateRevocationList(self.crl_path)
        self.logger = logging.getLogger(f"{__name__}.SelfSignedCA")

        # Ensure CA directory exists
        (cert_dir / "ca").mkdir(parents=True, exist_ok=True)

    def generate_root_ca(
        self,
        organization: str = "DevSkyy",
        validity_years: int = 10,
        force: bool = False,
    ) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
        """
        Generate root CA certificate and private key

        Args:
            organization: Organization name for the CA
            validity_years: CA certificate validity in years
            force: Force regeneration even if CA exists

        Returns:
            Tuple of (ca_certificate, ca_private_key)
        """
        # Check if CA already exists
        if self.ca_cert_path.exists() and self.ca_key_path.exists() and not force:
            self.logger.info("Root CA already exists, loading from disk")
            return self.load_ca()

        self.logger.info(f"Generating new root CA for {organization}")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )

        # Build certificate
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, f"{organization} Root CA"),
            ]
        )

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.public_key(private_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(datetime.utcnow())
        builder = builder.not_valid_after(datetime.utcnow() + timedelta(days=validity_years * 365))

        # Add CA extensions
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        )

        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )

        builder = builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        )

        # Self-sign certificate
        certificate = builder.sign(private_key, hashes.SHA256(), default_backend())

        # Save to disk
        with open(self.ca_cert_path, "wb") as f:
            f.write(certificate.public_bytes(serialization.Encoding.PEM))

        with open(self.ca_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Set restrictive permissions
        os.chmod(self.ca_cert_path, 0o644)
        os.chmod(self.ca_key_path, 0o600)

        self.logger.info(f"Generated root CA, valid for {validity_years} years")
        self.logger.info(f"CA certificate: {self.ca_cert_path}")
        self.logger.info(f"CA private key: {self.ca_key_path}")

        return certificate, private_key

    def load_ca(self) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
        """Load CA certificate and private key from disk"""
        if not self.ca_cert_path.exists() or not self.ca_key_path.exists():
            raise FileNotFoundError("CA certificate or key not found")

        # Load certificate
        with open(self.ca_cert_path, "rb") as f:
            cert_data = f.read()
        ca_cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        # Load private key
        with open(self.ca_key_path, "rb") as f:
            key_data = f.read()
        ca_key = serialization.load_pem_private_key(
            key_data, password=None, backend=default_backend()
        )

        self.logger.info("Loaded root CA from disk")
        return ca_cert, ca_key

    def generate_service_cert(
        self,
        service_name: str,
        validity_days: int = 30,
        san_names: list[str] | None = None,
    ) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
        """
        Generate service certificate signed by root CA

        Args:
            service_name: Name of the service
            validity_days: Certificate validity in days
            san_names: Additional Subject Alternative Names

        Returns:
            Tuple of (certificate, private_key)
        """
        # Load CA
        ca_cert, ca_key = self.load_ca()

        # Generate private key for service
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
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

        # Add Subject Alternative Names
        from ipaddress import IPv4Address, ip_address

        san_list = [
            x509.DNSName(service_name),
            x509.DNSName(f"{service_name}.devskyy.local"),
            x509.DNSName("localhost"),
            x509.IPAddress(IPv4Address("127.0.0.1")),
        ]

        if san_names:
            for name in san_names:
                try:
                    # Try as IP address first
                    san_list.append(x509.IPAddress(ip_address(name)))
                except ValueError:
                    # Otherwise treat as DNS name
                    san_list.append(x509.DNSName(name))

        builder = builder.add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )

        # Add basic constraints
        builder = builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )

        # Add key usage
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

        # Add extended key usage
        builder = builder.add_extension(
            x509.ExtendedKeyUsage(
                [
                    x509.ExtendedKeyUsageOID.SERVER_AUTH,
                    x509.ExtendedKeyUsageOID.CLIENT_AUTH,
                ]
            ),
            critical=False,
        )

        # Add authority key identifier
        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )

        # Sign certificate
        certificate = builder.sign(ca_key, hashes.SHA256(), default_backend())

        self.logger.info(
            f"Generated service certificate for {service_name}, valid for {validity_days} days"
        )

        return certificate, private_key

    def verify_certificate(
        self,
        cert: x509.Certificate,
        check_revocation: bool = True,
    ) -> bool:
        """
        Verify certificate is valid and signed by this CA

        Args:
            cert: Certificate to verify
            check_revocation: Check if certificate is revoked

        Returns:
            True if certificate is valid
        """
        try:
            # Load CA certificate
            ca_cert, _ = self.load_ca()

            # Verify signature

            ca_public_key = ca_cert.public_key()

            # Use the certificate's signature hash algorithm
            chosen_hash = cert.signature_hash_algorithm

            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                chosen_hash,
            )

            # Check expiry with timezone-aware datetime

            now = datetime.now(UTC)
            if now < cert.not_valid_before_utc or now > cert.not_valid_after_utc:
                self.logger.error("Certificate is expired or not yet valid")
                return False

            # Check revocation
            if check_revocation and self.crl.is_revoked(cert.serial_number):
                self.logger.error(f"Certificate with serial {cert.serial_number} is revoked")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Certificate verification failed: {e}")
            return False

    def revoke_certificate(self, serial_number: int):
        """Revoke a certificate"""
        self.crl.revoke(serial_number)

    def get_certificate_info(self, cert_path: Path) -> dict:
        """Get detailed information about a certificate"""
        try:
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            # Extract subject info
            subject_attrs = {}
            for attr in cert.subject:
                subject_attrs[attr.oid._name] = attr.value

            # Extract issuer info
            issuer_attrs = {}
            for attr in cert.issuer:
                issuer_attrs[attr.oid._name] = attr.value

            # Check if revoked
            is_revoked = self.crl.is_revoked(cert.serial_number)
            revoked_at = None
            if is_revoked:
                revoked_at = self.crl.get_revocation_time(cert.serial_number)

            return {
                "subject": subject_attrs,
                "issuer": issuer_attrs,
                "serial_number": str(cert.serial_number),
                "not_valid_before": cert.not_valid_before_utc.isoformat(),
                "not_valid_after": cert.not_valid_after_utc.isoformat(),
                "fingerprint": cert.fingerprint(hashes.SHA256()).hex(),
                "is_ca": cert.extensions.get_extension_for_oid(
                    ExtensionOID.BASIC_CONSTRAINTS
                ).value.ca,
                "is_revoked": is_revoked,
                "revoked_at": revoked_at.isoformat() if revoked_at else None,
            }
        except Exception as e:
            self.logger.error(f"Failed to get certificate info: {e}")
            return {"error": str(e)}


class VaultCA:
    """
    HashiCorp Vault-based Certificate Authority (Production)

    This is a stub implementation for production use with HashiCorp Vault.
    Requires Vault server with PKI secrets engine configured.
    """

    def __init__(
        self,
        vault_url: str,
        vault_token: str,
        pki_path: str = "pki",
    ):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.pki_path = pki_path
        self.logger = logging.getLogger(f"{__name__}.VaultCA")

        # Note: Full implementation requires hvac library
        # pip install hvac

    def generate_service_cert(
        self,
        service_name: str,
        validity_ttl: str = "720h",  # 30 days
        san_names: list[str] | None = None,
    ) -> tuple[str, str, str]:
        """
        Generate service certificate using Vault PKI

        Args:
            service_name: Service common name
            validity_ttl: Certificate TTL (e.g., "720h", "30d")
            san_names: Additional Subject Alternative Names

        Returns:
            Tuple of (certificate_pem, private_key_pem, ca_chain_pem)
        """
        # Placeholder for Vault integration
        self.logger.warning("VaultCA is a stub implementation")

        # In production, this would:
        # 1. Connect to Vault using hvac client
        # 2. Request certificate from PKI backend
        # 3. Return certificate, key, and CA chain

        raise NotImplementedError(
            "VaultCA requires HashiCorp Vault integration. "
            "Install hvac library and configure Vault PKI backend."
        )

    def revoke_certificate(self, serial_number: str):
        """Revoke certificate in Vault"""
        raise NotImplementedError("VaultCA revocation not implemented")

    def verify_certificate(self, cert_pem: str) -> bool:
        """Verify certificate against Vault CA"""
        raise NotImplementedError("VaultCA verification not implemented")


class CertificateValidator:
    """Utility class for certificate validation"""

    @staticmethod
    def validate_cert_chain(
        cert: x509.Certificate,
        ca_cert: x509.Certificate,
        intermediate_certs: list[x509.Certificate] | None = None,
    ) -> bool:
        """
        Validate certificate chain

        Args:
            cert: End-entity certificate
            ca_cert: Root CA certificate
            intermediate_certs: Optional intermediate certificates

        Returns:
            True if chain is valid
        """
        try:
            # Build chain
            chain = intermediate_certs or []
            chain.append(ca_cert)

            # Verify each link in the chain
            current_cert = cert
            for ca in chain:
                ca_public_key = ca.public_key()
                ca_public_key.verify(
                    current_cert.signature,
                    current_cert.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    current_cert.signature_hash_algorithm,
                )
                current_cert = ca

            return True
        except Exception as e:
            logger.error(f"Certificate chain validation failed: {e}")
            return False

    @staticmethod
    def check_certificate_expiry(cert: x509.Certificate) -> dict:
        """
        Check certificate expiry status

        Returns:
            Dictionary with expiry information
        """

        now = datetime.now(UTC)
        days_until_expiry = (cert.not_valid_after_utc - now).days

        return {
            "is_expired": now > cert.not_valid_after_utc,
            "not_yet_valid": now < cert.not_valid_before_utc,
            "days_until_expiry": days_until_expiry,
            "needs_renewal": days_until_expiry < 7,
            "not_valid_before": cert.not_valid_before_utc.isoformat(),
            "not_valid_after": cert.not_valid_after_utc.isoformat(),
        }

    @staticmethod
    def extract_san_names(cert: x509.Certificate) -> list[str]:
        """Extract Subject Alternative Names from certificate"""
        try:
            san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            return [str(name.value) for name in san_ext.value]
        except x509.ExtensionNotFound:
            return []

    @staticmethod
    def get_certificate_fingerprint(cert: x509.Certificate, algorithm: str = "SHA256") -> str:
        """Get certificate fingerprint"""
        hash_algo = getattr(hashes, algorithm)()
        return cert.fingerprint(hash_algo).hex()
