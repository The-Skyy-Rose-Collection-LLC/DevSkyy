"""
Mutual TLS (mTLS) Handler

This module provides mutual TLS configuration and management for service-to-service
communication in a Zero Trust architecture.
"""

import logging
import socket
import ssl
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from security.certificate_authority import CertificateValidator, SelfSignedCA
from security.zero_trust_config import ZeroTrustConfig

logger = logging.getLogger(__name__)


@dataclass
class TLSConfig:
    """TLS configuration for a service"""

    cert_path: Path
    key_path: Path
    ca_path: Path
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED
    check_hostname: bool = True
    minimum_version: ssl.TLSVersion = ssl.TLSVersion.TLSv1_3
    ciphers: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "cert_path": str(self.cert_path),
            "key_path": str(self.key_path),
            "ca_path": str(self.ca_path),
            "verify_mode": self.verify_mode.name,
            "check_hostname": self.check_hostname,
            "minimum_version": self.minimum_version.name,
            "ciphers": self.ciphers,
        }


class MTLSHandler:
    """
    Mutual TLS Handler for Zero Trust Service Communication

    Provides:
    - Client and server TLS context creation
    - Certificate verification
    - Service identity validation
    - Secure socket creation
    """

    # Secure cipher suites - TLS 1.3 uses different cipher names
    # For TLS 1.3, ciphers are set automatically and don't need explicit configuration
    # For backwards compatibility with TLS 1.2:
    SECURE_CIPHERS = None  # Let TLS 1.3 use defaults

    def __init__(self, config: ZeroTrustConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.MTLSHandler")
        self.ca = SelfSignedCA(config.cert_dir)
        self.validator = CertificateValidator()

    def enable_client_tls(
        self,
        service_name: str,
        server_hostname: str | None = None,
    ) -> ssl.SSLContext:
        """
        Create SSL context for client connections

        Args:
            service_name: Name of the client service
            server_hostname: Expected server hostname (for hostname verification)

        Returns:
            Configured SSL context for client
        """
        service = self.config.get_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found in configuration")

        # Get certificate paths
        cert_path = self.config.cert_dir / service_name / "cert.pem"
        key_path = self.config.cert_dir / service_name / "key.pem"
        ca_path = self.config.cert_dir / "ca" / "ca-cert.pem"

        if not cert_path.exists() or not key_path.exists():
            raise FileNotFoundError(
                f"Certificate or key not found for {service_name}. " f"Generate certificates first."
            )

        if not ca_path.exists():
            raise FileNotFoundError("CA certificate not found")

        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        # Set minimum TLS version
        context.minimum_version = ssl.TLSVersion.TLSv1_3

        # Load client certificate and key
        context.load_cert_chain(
            certfile=str(cert_path),
            keyfile=str(key_path),
        )

        # Load CA certificate for server verification
        context.load_verify_locations(cafile=str(ca_path))

        # Configure verification
        if self.config.require_peer_verification:
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = True
        else:
            context.verify_mode = ssl.CERT_NONE
            context.check_hostname = False
            self.logger.warning(
                f"Peer verification disabled for {service_name} - not recommended for production"
            )

        # Set secure ciphers (TLS 1.3 uses defaults, only set for TLS 1.2 compat)
        if self.SECURE_CIPHERS:
            context.set_ciphers(self.SECURE_CIPHERS)

        # Additional security options
        context.options |= ssl.OP_NO_COMPRESSION  # Prevent CRIME attack
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE

        self.logger.info(f"Enabled client TLS for {service_name}")

        return context

    def enable_server_tls(
        self,
        service_name: str,
        require_client_cert: bool = True,
    ) -> ssl.SSLContext:
        """
        Create SSL context for server connections

        Args:
            service_name: Name of the server service
            require_client_cert: Require client certificates (mTLS)

        Returns:
            Configured SSL context for server
        """
        service = self.config.get_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found in configuration")

        # Get certificate paths
        cert_path = self.config.cert_dir / service_name / "cert.pem"
        key_path = self.config.cert_dir / service_name / "key.pem"
        ca_path = self.config.cert_dir / "ca" / "ca-cert.pem"

        if not cert_path.exists() or not key_path.exists():
            raise FileNotFoundError(
                f"Certificate or key not found for {service_name}. " f"Generate certificates first."
            )

        if not ca_path.exists():
            raise FileNotFoundError("CA certificate not found")

        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # Set minimum TLS version
        context.minimum_version = ssl.TLSVersion.TLSv1_3

        # Load server certificate and key
        context.load_cert_chain(
            certfile=str(cert_path),
            keyfile=str(key_path),
        )

        # Configure client certificate verification (mTLS)
        if require_client_cert and service.require_mtls:
            context.load_verify_locations(cafile=str(ca_path))
            context.verify_mode = ssl.CERT_REQUIRED
            self.logger.info(f"mTLS enabled for {service_name} - client certificates required")
        else:
            context.verify_mode = ssl.CERT_NONE
            self.logger.warning(
                f"mTLS disabled for {service_name} - allowing connections without client certificates"
            )

        # Set secure ciphers (TLS 1.3 uses defaults, only set for TLS 1.2 compat)
        if self.SECURE_CIPHERS:
            context.set_ciphers(self.SECURE_CIPHERS)

        # Additional security options
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE

        self.logger.info(f"Enabled server TLS for {service_name}")

        return context

    def verify_peer_certificate(
        self,
        cert_path: Path,
        expected_service: str | None = None,
    ) -> bool:
        """
        Verify peer certificate

        Args:
            cert_path: Path to peer certificate
            expected_service: Expected service name in certificate CN

        Returns:
            True if certificate is valid
        """
        try:
            # Load certificate
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            # Verify certificate is signed by CA
            if not self.ca.verify_certificate(cert):
                self.logger.error("Certificate verification failed")
                return False

            # Check expiry
            expiry_info = self.validator.check_certificate_expiry(cert)
            if expiry_info["is_expired"]:
                self.logger.error("Certificate is expired")
                return False

            if expiry_info["not_yet_valid"]:
                self.logger.error("Certificate is not yet valid")
                return False

            # Verify service identity if expected
            if expected_service:
                cn_attr = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
                if cn_attr:
                    cn = cn_attr[0].value
                    if cn != expected_service:
                        self.logger.error(
                            f"Service identity mismatch: expected {expected_service}, got {cn}"
                        )
                        return False
                else:
                    self.logger.error("Certificate has no Common Name")
                    return False

            self.logger.info("Peer certificate verified successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to verify peer certificate: {e}")
            return False

    def validate_service_identity(
        self,
        cert: x509.Certificate,
        expected_service: str,
    ) -> bool:
        """
        Validate service identity from certificate

        Args:
            cert: Certificate to validate
            expected_service: Expected service name

        Returns:
            True if service identity matches
        """
        try:
            # Check Common Name
            cn_attr = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
            if cn_attr and cn_attr[0].value == expected_service:
                return True

            # Check Subject Alternative Names
            san_names = self.validator.extract_san_names(cert)
            if expected_service in san_names:
                return True

            self.logger.error(
                f"Service identity validation failed: expected {expected_service}, "
                f"got CN={cn_attr[0].value if cn_attr else 'None'}, "
                f"SANs={san_names}"
            )
            return False

        except Exception as e:
            self.logger.error(f"Service identity validation error: {e}")
            return False

    def verify_certificate_chain(
        self,
        cert_path: Path,
        max_depth: int | None = None,
    ) -> bool:
        """
        Verify certificate chain depth

        Args:
            cert_path: Path to certificate
            max_depth: Maximum allowed chain depth (default: config.max_cert_chain_depth)

        Returns:
            True if chain is valid and within depth limit
        """
        if max_depth is None:
            max_depth = self.config.max_cert_chain_depth

        try:
            # Load certificate
            with open(cert_path, "rb") as f:
                cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            # Load CA certificate
            ca_cert, _ = self.ca.load_ca()

            # Verify chain
            if not self.validator.validate_cert_chain(cert, ca_cert):
                self.logger.error("Certificate chain validation failed")
                return False

            # For our self-signed CA, chain depth is always 1
            # In production with intermediate CAs, this would check actual chain depth

            self.logger.info("Certificate chain verified successfully")
            return True

        except Exception as e:
            self.logger.error(f"Certificate chain verification failed: {e}")
            return False

    def create_secure_client_socket(
        self,
        service_name: str,
        server_host: str,
        server_port: int,
        server_hostname: str | None = None,
    ) -> ssl.SSLSocket:
        """
        Create secure client socket with mTLS

        Args:
            service_name: Client service name
            server_host: Server host address
            server_port: Server port
            server_hostname: Server hostname for verification

        Returns:
            Configured SSL socket
        """
        # Get SSL context
        context = self.enable_client_tls(service_name, server_hostname)

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Wrap with SSL
        hostname = server_hostname or server_host
        ssl_sock = context.wrap_socket(
            sock,
            server_hostname=hostname,
        )

        # Connect
        ssl_sock.connect((server_host, server_port))

        self.logger.info(
            f"Established secure connection from {service_name} to {server_host}:{server_port}"
        )

        return ssl_sock

    def create_secure_server_socket(
        self,
        service_name: str,
        bind_address: str = "0.0.0.0",
        bind_port: int | None = None,
        require_client_cert: bool = True,
    ) -> ssl.SSLSocket:
        """
        Create secure server socket with mTLS

        Args:
            service_name: Server service name
            bind_address: Address to bind to
            bind_port: Port to bind to (default: service.port)
            require_client_cert: Require client certificates

        Returns:
            Configured SSL socket
        """
        service = self.config.get_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")

        port = bind_port or service.port

        # Get SSL context
        context = self.enable_server_tls(service_name, require_client_cert)

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind
        sock.bind((bind_address, port))
        sock.listen(5)

        # Wrap with SSL
        ssl_sock = context.wrap_socket(sock, server_side=True)

        self.logger.info(
            f"Secure server socket created for {service_name} on {bind_address}:{port}"
        )

        return ssl_sock

    def get_peer_certificate_info(self, ssl_sock: ssl.SSLSocket) -> dict:
        """
        Get information about peer certificate from SSL socket

        Args:
            ssl_sock: SSL socket with established connection

        Returns:
            Dictionary with peer certificate information
        """
        try:
            peer_cert = ssl_sock.getpeercert(binary_form=True)
            if not peer_cert:
                return {"error": "No peer certificate"}

            cert = x509.load_der_x509_certificate(peer_cert, default_backend())

            # Extract information
            cn_attr = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
            common_name = cn_attr[0].value if cn_attr else "Unknown"

            san_names = self.validator.extract_san_names(cert)
            fingerprint = self.validator.get_certificate_fingerprint(cert)
            expiry_info = self.validator.check_certificate_expiry(cert)

            return {
                "common_name": common_name,
                "subject": str(cert.subject),
                "issuer": str(cert.issuer),
                "serial_number": str(cert.serial_number),
                "san_names": san_names,
                "fingerprint": fingerprint,
                "not_valid_before": cert.not_valid_before_utc.isoformat(),
                "not_valid_after": cert.not_valid_after_utc.isoformat(),
                "is_expired": expiry_info["is_expired"],
                "days_until_expiry": expiry_info["days_until_expiry"],
            }

        except Exception as e:
            self.logger.error(f"Failed to get peer certificate info: {e}")
            return {"error": str(e)}

    def test_connection(
        self,
        client_service: str,
        server_service: str,
        server_host: str = "localhost",
        server_port: int | None = None,
    ) -> bool:
        """
        Test mTLS connection between two services

        Args:
            client_service: Client service name
            server_service: Server service name
            server_host: Server host
            server_port: Server port (default: server_service.port)

        Returns:
            True if connection successful
        """
        try:
            server_svc = self.config.get_service(server_service)
            if not server_svc:
                raise ValueError(f"Server service {server_service} not found")

            port = server_port or server_svc.port

            # Create client socket
            ssl_sock = self.create_secure_client_socket(
                client_service,
                server_host,
                port,
                server_hostname=server_service,
            )

            # Get peer info
            peer_info = self.get_peer_certificate_info(ssl_sock)
            self.logger.info(f"Connected to {server_service}: {peer_info}")

            # Close connection
            ssl_sock.close()

            self.logger.info(f"mTLS test successful: {client_service} -> {server_service}")
            return True

        except Exception as e:
            self.logger.error(f"mTLS test failed: {e}")
            return False


class ServiceMeshIntegration:
    """Integration helpers for service mesh (Istio, Linkerd, etc.)"""

    @staticmethod
    def generate_istio_peer_authentication(
        service_name: str,
        namespace: str = "default",
        mode: str = "STRICT",
    ) -> str:
        """
        Generate Istio PeerAuthentication YAML

        Args:
            service_name: Service name
            namespace: Kubernetes namespace
            mode: mTLS mode (STRICT, PERMISSIVE, DISABLE)

        Returns:
            YAML string
        """
        yaml = f"""apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: {service_name}-mtls
  namespace: {namespace}
spec:
  selector:
    matchLabels:
      app: {service_name}
  mtls:
    mode: {mode}
"""
        return yaml

    @staticmethod
    def generate_istio_authorization_policy(
        service_name: str,
        allowed_services: list[str],
        namespace: str = "default",
    ) -> str:
        """
        Generate Istio AuthorizationPolicy YAML

        Args:
            service_name: Service name
            allowed_services: List of services allowed to access
            namespace: Kubernetes namespace

        Returns:
            YAML string
        """
        principals = [f"cluster.local/ns/{namespace}/sa/{svc}" for svc in allowed_services]

        yaml = f"""apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: {service_name}-authz
  namespace: {namespace}
spec:
  selector:
    matchLabels:
      app: {service_name}
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
"""
        for principal in principals:
            yaml += f"        - {principal}\n"

        return yaml
