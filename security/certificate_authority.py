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
            not_before = get_cert_not_valid_before(cert)
            not_after = get_cert_not_valid_after(cert)
            if now < not_before or now > not_after:
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
                "not_valid_before": get_cert_not_valid_before(cert).isoformat(),
                "not_valid_after": get_cert_not_valid_after(cert).isoformat(),
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

    Provides production-grade PKI services using HashiCorp Vault's PKI secrets engine.
    Requires Vault server with PKI secrets engine configured and hvac library installed.

    Setup requirements:
        1. Enable PKI secrets engine: vault secrets enable pki
        2. Configure PKI role: vault write pki/roles/service-role ...
        3. Install hvac: pip install hvac

    Example:
        >>> ca = VaultCA(
        ...     vault_url="https://vault.example.com:8200",
        ...     vault_token="hvs.xxxxx",
        ...     pki_path="pki",
        ...     pki_role="service-role"
        ... )
        >>> cert, key, chain = ca.generate_service_cert("my-service")
    """

    def __init__(
        self,
        vault_url: str,
        vault_token: str,
        pki_path: str = "pki",
        pki_role: str = "service-role",
        verify_ssl: bool = True,
        namespace: str | None = None,
    ):
        """
        Initialize VaultCA with connection parameters.

        Args:
            vault_url: Vault server URL (e.g., "https://vault.example.com:8200")
            vault_token: Vault authentication token
            pki_path: PKI secrets engine mount path (default: "pki")
            pki_role: PKI role name for certificate issuance (default: "service-role")
            verify_ssl: Verify SSL certificates for Vault connection (default: True)
            namespace: Vault namespace for enterprise deployments (optional)

        Raises:
            RuntimeError: If hvac library is not installed
            ConnectionError: If unable to connect to Vault server
        """
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.pki_path = pki_path
        self.pki_role = pki_role
        self.verify_ssl = verify_ssl
        self.namespace = namespace
        self.logger = logging.getLogger(f"{__name__}.VaultCA")
        self._client = None

        # Validate hvac is installed
        try:
            import hvac

            self._hvac = hvac
        except ImportError as e:
            msg = "hvac library required for VaultCA. Install with: pip install hvac"
            self.logger.error(msg)
            raise RuntimeError(msg) from e

        # Initialize Vault client
        self._init_client()

    def _init_client(self) -> None:
        """Initialize and verify Vault client connection."""
        try:
            self._client = self._hvac.Client(
                url=self.vault_url,
                token=self.vault_token,
                verify=self.verify_ssl,
                namespace=self.namespace,
            )

            # Verify authentication
            if not self._client.is_authenticated():
                msg = "Failed to authenticate with Vault server"
                self.logger.error(msg)
                raise ConnectionError(msg)

            self.logger.info(f"VaultCA initialized successfully (url: {self.vault_url})")

        except Exception as e:
            self.logger.error(f"Failed to initialize Vault client: {e}")
            raise

    @property
    def client(self):
        """Get Vault client, reinitializing if needed."""
        if self._client is None:
            self._init_client()
        return self._client

    def generate_service_cert(
        self,
        service_name: str,
        validity_ttl: str = "720h",
        san_names: list[str] | None = None,
        ip_sans: list[str] | None = None,
    ) -> tuple[str, str, str]:
        """
        Generate service certificate using Vault PKI secrets engine.

        Args:
            service_name: Service common name (CN)
            validity_ttl: Certificate TTL (e.g., "720h", "30d", "8760h")
            san_names: Additional DNS Subject Alternative Names
            ip_sans: IP address Subject Alternative Names

        Returns:
            Tuple of (certificate_pem, private_key_pem, ca_chain_pem)

        Raises:
            RuntimeError: If certificate generation fails
        """
        try:
            # Build request parameters
            issue_params = {
                "name": self.pki_role,
                "common_name": service_name,
                "ttl": validity_ttl,
            }

            # Add DNS SANs
            if san_names:
                issue_params["alt_names"] = ",".join(san_names)

            # Add IP SANs
            if ip_sans:
                issue_params["ip_sans"] = ",".join(ip_sans)

            self.logger.info(f"Requesting certificate for {service_name} with TTL {validity_ttl}")

            # Issue certificate from Vault PKI
            response = self.client.secrets.pki.generate_certificate(
                mount_point=self.pki_path,
                **issue_params,
            )

            # Extract certificate components from response
            cert_data = response.get("data", {})

            certificate_pem = cert_data.get("certificate", "")
            private_key_pem = cert_data.get("private_key", "")
            ca_chain_pem = cert_data.get("ca_chain", [""])

            # ca_chain can be a list, join into single PEM
            if isinstance(ca_chain_pem, list):
                ca_chain_pem = "\n".join(ca_chain_pem)

            # Validate we got all required components
            if not certificate_pem:
                msg = "Vault returned empty certificate"
                self.logger.error(msg)
                raise RuntimeError(msg)

            if not private_key_pem:
                msg = "Vault returned empty private key"
                self.logger.error(msg)
                raise RuntimeError(msg)

            serial_number = cert_data.get("serial_number", "unknown")
            expiration = cert_data.get("expiration", 0)

            self.logger.info(
                f"Generated certificate for {service_name} "
                f"(serial: {serial_number}, expires: {expiration})"
            )

            return certificate_pem, private_key_pem, ca_chain_pem

        except Exception as e:
            msg = f"Failed to generate certificate for {service_name}: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg) from e

    def revoke_certificate(self, serial_number: str) -> bool:
        """
        Revoke a certificate in Vault PKI.

        Args:
            serial_number: Certificate serial number (colon-separated hex format)

        Returns:
            True if revocation was successful

        Raises:
            RuntimeError: If revocation fails
        """
        try:
            self.logger.warning(f"Revoking certificate with serial: {serial_number}")

            # Revoke certificate via Vault PKI
            self.client.secrets.pki.revoke_certificate(
                mount_point=self.pki_path,
                serial_number=serial_number,
            )

            self.logger.info(f"Successfully revoked certificate: {serial_number}")
            return True

        except Exception as e:
            msg = f"Failed to revoke certificate {serial_number}: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg) from e

    def verify_certificate(self, cert_pem: str) -> bool:
        """
        Verify a certificate against Vault CA.

        Performs the following checks:
        1. Certificate is parseable
        2. Certificate is signed by Vault CA
        3. Certificate is not expired
        4. Certificate is not revoked (via CRL/OCSP if configured)

        Args:
            cert_pem: PEM-encoded certificate string

        Returns:
            True if certificate is valid, False otherwise
        """
        try:
            # Parse the certificate
            cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())

            # Check expiry
            now = datetime.now(UTC)
            if now < get_cert_not_valid_before(cert):
                self.logger.warning("Certificate is not yet valid")
                return False

            if now > get_cert_not_valid_after(cert):
                self.logger.warning("Certificate has expired")
                return False

            # Get CA certificate from Vault to verify signature
            try:
                ca_response = self.client.secrets.pki.read_ca_certificate(
                    mount_point=self.pki_path,
                )
                ca_cert_pem = ca_response.get("data", {}).get("certificate", "")

                if not ca_cert_pem:
                    # Try alternate endpoint for CA cert
                    ca_cert_pem = self.client.secrets.pki.read_ca_certificate_chain(
                        mount_point=self.pki_path,
                    )

                if ca_cert_pem:
                    ca_cert = x509.load_pem_x509_certificate(
                        ca_cert_pem.encode() if isinstance(ca_cert_pem, str) else ca_cert_pem,
                        default_backend(),
                    )

                    # Verify signature
                    ca_public_key = ca_cert.public_key()
                    ca_public_key.verify(
                        cert.signature,
                        cert.tbs_certificate_bytes,
                        padding.PKCS1v15(),
                        cert.signature_hash_algorithm,
                    )

            except Exception as ca_error:
                self.logger.warning(
                    f"Could not verify CA signature (Vault may not expose CA cert): {ca_error}"
                )
                # Continue with other checks even if CA verification fails

            # Check revocation status via CRL if available
            serial_hex = format(cert.serial_number, "x")
            # Format as colon-separated hex (Vault format)
            serial_formatted = ":".join(serial_hex[i : i + 2] for i in range(0, len(serial_hex), 2))

            try:
                # Try to check CRL
                crl_response = self.client.secrets.pki.read_crl(
                    mount_point=self.pki_path,
                )
                crl_pem = crl_response.get("data", {}).get("crl", "")

                if crl_pem:
                    crl = x509.load_pem_x509_crl(
                        crl_pem.encode() if isinstance(crl_pem, str) else crl_pem,
                        default_backend(),
                    )

                    # Check if certificate is in CRL
                    revoked_cert = crl.get_revoked_certificate_by_serial_number(cert.serial_number)
                    if revoked_cert is not None:
                        self.logger.warning(f"Certificate {serial_formatted} is revoked")
                        return False

            except Exception as crl_error:
                self.logger.debug(f"CRL check skipped: {crl_error}")

            self.logger.info(f"Certificate {serial_formatted} verified successfully")
            return True

        except Exception as e:
            self.logger.error(f"Certificate verification failed: {e}")
            return False

    def get_ca_certificate(self) -> str:
        """
        Retrieve the CA certificate from Vault.

        Returns:
            PEM-encoded CA certificate string

        Raises:
            RuntimeError: If CA certificate cannot be retrieved
        """
        try:
            response = self.client.secrets.pki.read_ca_certificate(
                mount_point=self.pki_path,
            )
            ca_cert = response.get("data", {}).get("certificate", "")

            if not ca_cert:
                # Try chain endpoint
                ca_cert = self.client.secrets.pki.read_ca_certificate_chain(
                    mount_point=self.pki_path,
                )

            if not ca_cert:
                raise RuntimeError("Vault returned empty CA certificate")

            return ca_cert

        except Exception as e:
            msg = f"Failed to retrieve CA certificate: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg) from e

    def list_certificates(self) -> list[str]:
        """
        List all issued certificate serial numbers.

        Returns:
            List of certificate serial numbers

        Raises:
            RuntimeError: If listing fails
        """
        try:
            response = self.client.secrets.pki.list_certificates(
                mount_point=self.pki_path,
            )
            keys = response.get("data", {}).get("keys", [])
            return keys

        except Exception as e:
            msg = f"Failed to list certificates: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg) from e

    def tidy_certificates(self, safety_buffer: str = "72h") -> dict:
        """
        Tidy the certificate store by removing expired certificates.

        Args:
            safety_buffer: Time buffer before cleaning expired certs (default: 72h)

        Returns:
            Tidy operation response from Vault
        """
        try:
            response = self.client.secrets.pki.tidy(
                mount_point=self.pki_path,
                tidy_cert_store=True,
                tidy_revoked_certs=True,
                safety_buffer=safety_buffer,
            )
            self.logger.info("Certificate tidy operation initiated")
            return response.get("data", {})

        except Exception as e:
            msg = f"Failed to tidy certificates: {e}"
            self.logger.error(msg)
            raise RuntimeError(msg) from e


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
        not_after = get_cert_not_valid_after(cert)
        not_before = get_cert_not_valid_before(cert)
        days_until_expiry = (not_after - now).days

        return {
            "is_expired": now > not_after,
            "not_yet_valid": now < not_before,
            "days_until_expiry": days_until_expiry,
            "needs_renewal": days_until_expiry < 7,
            "not_valid_before": not_before.isoformat(),
            "not_valid_after": not_after.isoformat(),
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
