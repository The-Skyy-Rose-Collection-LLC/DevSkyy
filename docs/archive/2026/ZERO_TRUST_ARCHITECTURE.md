# Zero Trust Architecture

## Overview

This document provides comprehensive guidance on DevSkyy's Zero Trust security architecture implementation. Zero Trust is a security model that assumes no implicit trust and verifies every request regardless of its source.

### Core Principles

1. **Never Trust, Always Verify**: Every request must be authenticated and authorized
2. **Least Privilege Access**: Grant minimum necessary permissions
3. **Assume Breach**: Design systems assuming attackers may already be inside
4. **Verify Explicitly**: Use all available data points for authentication decisions
5. **Microsegmentation**: Isolate services and data into smallest possible segments

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Zero Trust Architecture                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Certificate Authority (CA)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Self-Signed │  │  Vault PKI   │  │ Cert-Manager │          │
│  │  (Dev/Test)  │  │ (Production) │  │ (Kubernetes) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Certificate Management                         │
│  • Certificate Generation & Signing                              │
│  • Automatic Rotation (30-day default)                           │
│  • Revocation List (CRL) Management                              │
│  • Certificate Chain Validation                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Mutual TLS (mTLS) Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   API        │  │  Database    │  │   Redis      │          │
│  │  (Port 8000) │  │ (Port 5432)  │  │ (Port 6379)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Commerce    │  │  Marketing   │  │  Analytics   │          │
│  │   Agent      │  │    Agent     │  │    Agent     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Identity & AuthZ                      │
│  • Service-to-Service Authentication                             │
│  • Peer Certificate Verification                                 │
│  • Allowed Peers Enforcement                                     │
│  • Network Policy Enforcement                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Zero Trust Configuration (`security/zero_trust_config.py`)

Central configuration management for Zero Trust architecture.

#### Key Classes

##### `ZeroTrustConfig`

```python
from security.zero_trust_config import ZeroTrustConfig, ServiceIdentity

config = ZeroTrustConfig(
    enabled=True,
    ca_type="self-signed",  # or "vault", "cert-manager"
    cert_dir=Path("/etc/devskyy/certs"),
    auto_rotate=True,
    rotation_days=30,
    services=[
        ServiceIdentity(name="api", port=8000, require_mtls=True),
        ServiceIdentity(name="database", port=5432, require_mtls=True),
    ]
)
```

##### `CertificateManager`

```python
from security.zero_trust_config import CertificateManager

manager = CertificateManager(config)

# Generate certificate
cert, key = manager.generate_cert("api", ca_cert, ca_key)

# Save certificate
cert_path, key_path = manager.save_cert("api", cert, key)

# Rotate certificate
manager.rotate_cert("api", ca_cert, ca_key)

# Check rotation status
needs_rotation = manager.check_rotation_needed()
```

### 2. Certificate Authority (`security/certificate_authority.py`)

Manages certificate lifecycle and validation.

#### Self-Signed CA (Development)

```python
from security.certificate_authority import SelfSignedCA

ca = SelfSignedCA(cert_dir=Path("/etc/devskyy/certs"))

# Generate root CA
ca_cert, ca_key = ca.generate_root_ca(
    organization="DevSkyy",
    validity_years=10
)

# Generate service certificate
service_cert, service_key = ca.generate_service_cert(
    service_name="api",
    validity_days=30,
    san_names=["api.devskyy.com", "192.168.1.10"]
)

# Verify certificate
is_valid = ca.verify_certificate(service_cert)

# Revoke certificate
ca.revoke_certificate(service_cert.serial_number)
```

#### Vault CA (Production)

```python
from security.certificate_authority import VaultCA

# Configure Vault PKI backend
vault_ca = VaultCA(
    vault_url="https://vault.devskyy.com",
    vault_token=os.getenv("VAULT_TOKEN"),
    pki_path="pki"
)

# Note: Requires hvac library and Vault PKI configuration
# See Vault setup section below
```

### 3. Mutual TLS Handler (`security/mtls_handler.py`)

Manages mTLS connections between services.

#### Client Configuration

```python
from security.mtls_handler import MTLSHandler

handler = MTLSHandler(config)

# Enable client TLS
context = handler.enable_client_tls(
    service_name="api",
    server_hostname="database"
)

# Create secure connection
ssl_sock = handler.create_secure_client_socket(
    service_name="api",
    server_host="localhost",
    server_port=5432,
    server_hostname="database"
)
```

#### Server Configuration

```python
# Enable server TLS
context = handler.enable_server_tls(
    service_name="database",
    require_client_cert=True  # Enable mTLS
)

# Create secure server socket
ssl_sock = handler.create_secure_server_socket(
    service_name="database",
    bind_address="0.0.0.0",
    bind_port=5432
)

# Accept connection
client_sock, addr = ssl_sock.accept()

# Get peer certificate info
peer_info = handler.get_peer_certificate_info(client_sock)
print(f"Connected client: {peer_info['common_name']}")
```

#### Certificate Verification

```python
# Verify peer certificate
is_valid = handler.verify_peer_certificate(
    cert_path=Path("/etc/devskyy/certs/api/cert.pem"),
    expected_service="api"
)

# Verify certificate chain
is_valid = handler.verify_certificate_chain(
    cert_path=Path("/etc/devskyy/certs/api/cert.pem"),
    max_depth=3
)
```

## Setup Instructions

### Development Setup (Self-Signed CA)

#### 1. Configure Zero Trust

Edit `config/zero_trust/zero_trust_config.yaml`:

```yaml
zero_trust:
  enabled: true
  ca_type: self-signed
  cert_dir: /etc/devskyy/certs
  auto_rotate: true
  cert_rotation_days: 30

  services:
    - name: api
      port: 8000
      require_mtls: true
      allowed_peers:
        - database
        - redis
```

#### 2. Generate Root CA

```python
from pathlib import Path
from security.certificate_authority import SelfSignedCA

# Initialize CA
ca = SelfSignedCA(cert_dir=Path("/etc/devskyy/certs"))

# Generate root CA (only once)
ca_cert, ca_key = ca.generate_root_ca(
    organization="DevSkyy",
    validity_years=10,
    force=False  # Don't regenerate if exists
)

print(f"Root CA generated:")
print(f"  Certificate: /etc/devskyy/certs/ca/ca-cert.pem")
print(f"  Private Key: /etc/devskyy/certs/ca/ca-key.pem")
```

#### 3. Generate Service Certificates

```python
from security.zero_trust_config import ZeroTrustConfig, CertificateManager

# Load configuration
config = ZeroTrustConfig.from_yaml("config/zero_trust/zero_trust_config.yaml")

# Initialize certificate manager
manager = CertificateManager(config)

# Load CA
ca = SelfSignedCA(config.cert_dir)
ca_cert, ca_key = ca.load_ca()

# Generate certificates for all services
for service in config.services:
    print(f"Generating certificate for {service.name}...")

    cert, key = manager.generate_cert(service.name, ca_cert, ca_key)
    cert_path, key_path = manager.save_cert(service.name, cert, key)

    print(f"  Certificate: {cert_path}")
    print(f"  Private Key: {key_path}")
```

#### 4. Enable mTLS for Services

```python
# Example: API service with mTLS
from security.mtls_handler import MTLSHandler
import socket

handler = MTLSHandler(config)

# Server side (database)
server_context = handler.enable_server_tls("database", require_client_cert=True)
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(("0.0.0.0", 5432))
server_sock.listen(5)
ssl_server = server_context.wrap_socket(server_sock, server_side=True)

# Client side (api)
client_context = handler.enable_client_tls("api", server_hostname="database")
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_client = client_context.wrap_socket(client_sock, server_hostname="database")
ssl_client.connect(("localhost", 5432))
```

### Production Setup (HashiCorp Vault)

#### 1. Install Vault

```bash
# Download and install Vault
wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip
unzip vault_1.15.0_linux_amd64.zip
sudo mv vault /usr/local/bin/

# Start Vault server
vault server -dev  # Dev mode for testing
```

#### 2. Configure PKI Backend

```bash
# Enable PKI secrets engine
vault secrets enable pki

# Configure max lease TTL
vault secrets tune -max-lease-ttl=87600h pki

# Generate root CA
vault write -field=certificate pki/root/generate/internal \
    common_name="DevSkyy Root CA" \
    ttl=87600h > /etc/devskyy/certs/ca-cert.pem

# Configure CA and CRL URLs
vault write pki/config/urls \
    issuing_certificates="https://vault.devskyy.com:8200/v1/pki/ca" \
    crl_distribution_points="https://vault.devskyy.com:8200/v1/pki/crl"

# Create role for service certificates
vault write pki/roles/devskyy-services \
    allowed_domains="devskyy.local,devskyy.com" \
    allow_subdomains=true \
    max_ttl=720h
```

#### 3. Configure Zero Trust for Vault

```yaml
zero_trust:
  enabled: true
  ca_type: vault
  vault_url: https://vault.devskyy.com:8200
  vault_pki_path: pki
  cert_rotation_days: 30
```

#### 4. Use Vault CA

```python
from security.certificate_authority import VaultCA

vault_ca = VaultCA(
    vault_url="https://vault.devskyy.com:8200",
    vault_token=os.getenv("VAULT_TOKEN"),
    pki_path="pki"
)

# Generate service certificate
cert_pem, key_pem, ca_chain_pem = vault_ca.generate_service_cert(
    service_name="api.devskyy.local",
    validity_ttl="720h",
    san_names=["api.devskyy.com", "192.168.1.10"]
)
```

### Kubernetes Setup (cert-manager)

#### 1. Install cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

#### 2. Create Issuer

```yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: devskyy-ca-issuer
  namespace: devskyy
spec:
  ca:
    secretName: devskyy-ca-keypair
```

#### 3. Generate Certificates

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-cert
  namespace: devskyy
spec:
  secretName: api-tls
  duration: 720h  # 30 days
  renewBefore: 168h  # 7 days
  subject:
    organizations:
      - DevSkyy
  commonName: api
  dnsNames:
    - api
    - api.devskyy.svc
    - api.devskyy.svc.cluster.local
  issuerRef:
    name: devskyy-ca-issuer
    kind: Issuer
```

## Service-to-Service mTLS Configuration

### Example: API to Database Connection

#### 1. Generate Certificates

```bash
# Using provided script
python scripts/generate_certs.py --service api
python scripts/generate_certs.py --service database
```

Or programmatically:

```python
from security.zero_trust_config import ZeroTrustConfig, CertificateManager
from security.certificate_authority import SelfSignedCA

config = ZeroTrustConfig.from_yaml("config/zero_trust/zero_trust_config.yaml")
ca = SelfSignedCA(config.cert_dir)
ca_cert, ca_key = ca.load_ca()

manager = CertificateManager(config)

# Generate certificates
for service_name in ["api", "database"]:
    cert, key = manager.generate_cert(service_name, ca_cert, ca_key)
    manager.save_cert(service_name, cert, key)
```

#### 2. Configure Database (PostgreSQL)

Edit `postgresql.conf`:

```conf
ssl = on
ssl_cert_file = '/etc/devskyy/certs/database/cert.pem'
ssl_key_file = '/etc/devskyy/certs/database/key.pem'
ssl_ca_file = '/etc/devskyy/certs/ca/ca-cert.pem'
ssl_min_protocol_version = 'TLSv1.3'
```

Edit `pg_hba.conf`:

```conf
# Require SSL with client certificate
hostssl all all 0.0.0.0/0 cert clientcert=verify-full
```

#### 3. Configure API Client

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="devskyy",
    user="api_user",
    sslmode="verify-full",
    sslcert="/etc/devskyy/certs/api/cert.pem",
    sslkey="/etc/devskyy/certs/api/key.pem",
    sslrootcert="/etc/devskyy/certs/ca/ca-cert.pem"
)
```

Or using MTLSHandler:

```python
from security.mtls_handler import MTLSHandler

handler = MTLSHandler(config)

# Create secure connection
ssl_sock = handler.create_secure_client_socket(
    service_name="api",
    server_host="localhost",
    server_port=5432,
    server_hostname="database"
)
```

### Example: API to Redis Connection

#### 1. Configure Redis

Edit `redis.conf`:

```conf
tls-port 6380
port 0  # Disable non-TLS

tls-cert-file /etc/devskyy/certs/redis/cert.pem
tls-key-file /etc/devskyy/certs/redis/key.pem
tls-ca-cert-file /etc/devskyy/certs/ca/ca-cert.pem

tls-auth-clients yes  # Require client certificates
tls-protocols "TLSv1.3"
```

#### 2. Configure API Client

```python
import redis

r = redis.Redis(
    host="localhost",
    port=6380,
    ssl=True,
    ssl_certfile="/etc/devskyy/certs/api/cert.pem",
    ssl_keyfile="/etc/devskyy/certs/api/key.pem",
    ssl_ca_certs="/etc/devskyy/certs/ca/ca-cert.pem",
    ssl_cert_reqs="required"
)
```

## Certificate Rotation

### Automatic Rotation

Configure automatic rotation in `zero_trust_config.yaml`:

```yaml
zero_trust:
  auto_rotate: true
  cert_rotation_days: 30
```

Run rotation service:

```python
from security.zero_trust_config import ZeroTrustConfig, CertificateManager
from security.certificate_authority import SelfSignedCA
import time

config = ZeroTrustConfig.from_yaml("config/zero_trust/zero_trust_config.yaml")
manager = CertificateManager(config)
ca = SelfSignedCA(config.cert_dir)

while True:
    # Check certificates needing rotation
    needs_rotation = manager.check_rotation_needed()

    if needs_rotation:
        print(f"Rotating certificates for: {needs_rotation}")
        ca_cert, ca_key = ca.load_ca()

        for service_name in needs_rotation:
            manager.rotate_cert(service_name, ca_cert, ca_key)
            print(f"Rotated certificate for {service_name}")

    # Check every hour
    time.sleep(3600)
```

### Manual Rotation

```python
from security.zero_trust_config import ZeroTrustConfig, CertificateManager
from security.certificate_authority import SelfSignedCA

config = ZeroTrustConfig.from_yaml("config/zero_trust/zero_trust_config.yaml")
manager = CertificateManager(config)
ca = SelfSignedCA(config.cert_dir)

ca_cert, ca_key = ca.load_ca()

# Rotate specific service
result = manager.rotate_cert("api", ca_cert, ca_key)
if result:
    print("Certificate rotated successfully")
    print("Restart service to load new certificate")
```

### Rotation Best Practices

1. **Rotate Before Expiry**: Rotate certificates at least 7 days before expiry
2. **Rolling Updates**: Use rolling updates to avoid service disruption
3. **Monitor Rotation**: Alert on rotation failures
4. **Backup Old Certificates**: Keep backup of rotated certificates
5. **Test After Rotation**: Verify mTLS connections after rotation

## Troubleshooting

### Certificate Verification Failures

#### Problem: "Certificate verification failed"

**Diagnosis:**

```python
from security.zero_trust_config import CertificateManager
from security.certificate_authority import SelfSignedCA

ca = SelfSignedCA(config.cert_dir)
cert_info = ca.get_certificate_info(Path("/etc/devskyy/certs/api/cert.pem"))

print(f"Certificate Info:")
print(f"  Issuer: {cert_info['issuer']}")
print(f"  Expiry: {cert_info['not_valid_after']}")
print(f"  Revoked: {cert_info['is_revoked']}")
```

**Solutions:**

1. Check certificate hasn't expired
2. Verify certificate is signed by correct CA
3. Check certificate hasn't been revoked
4. Ensure CA certificate is trusted

### mTLS Connection Failures

#### Problem: "SSL handshake failed"

**Diagnosis:**

```bash
# Test connection with openssl
openssl s_client \
  -connect localhost:5432 \
  -cert /etc/devskyy/certs/api/cert.pem \
  -key /etc/devskyy/certs/api/key.pem \
  -CAfile /etc/devskyy/certs/ca/ca-cert.pem \
  -tls1_3
```

**Solutions:**

1. Verify server requires TLS 1.3
2. Check certificate paths are correct
3. Verify file permissions (cert: 644, key: 600)
4. Ensure server hostname matches certificate SAN

### Service Identity Mismatch

#### Problem: "Service identity validation failed"

**Diagnosis:**

```python
from security.mtls_handler import MTLSHandler

handler = MTLSHandler(config)

is_valid = handler.verify_peer_certificate(
    cert_path=Path("/etc/devskyy/certs/api/cert.pem"),
    expected_service="api"
)

if not is_valid:
    # Check certificate details
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    with open("/etc/devskyy/certs/api/cert.pem", 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read(), default_backend())

    cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    print(f"Certificate CN: {cn}")
```

**Solutions:**

1. Verify certificate CN matches service name
2. Check SAN includes service name
3. Regenerate certificate with correct service name

### Certificate Rotation Issues

#### Problem: "Auto rotation not working"

**Diagnosis:**

```python
from security.zero_trust_config import CertificateManager

manager = CertificateManager(config)

# Check rotation status
status = manager.get_cert_status()
for service, info in status.items():
    print(f"{service}:")
    print(f"  Days until expiry: {info['days_until_expiry']}")
    print(f"  Needs rotation: {info['needs_rotation']}")
```

**Solutions:**

1. Check `auto_rotate` is enabled in config
2. Verify rotation service is running
3. Check CA certificate is accessible
4. Review rotation logs for errors

## Security Best Practices

### 1. Certificate Management

- Use strong key sizes (4096 bits for RSA)
- Rotate certificates regularly (30-90 days)
- Store private keys securely (permissions 600)
- Never commit certificates or keys to version control
- Use hardware security modules (HSM) for CA keys in production

### 2. mTLS Configuration

- Always require TLS 1.3 or higher
- Use strong cipher suites only
- Enable hostname verification
- Require client certificates for service-to-service communication
- Implement certificate pinning for critical connections

### 3. Access Control

- Define allowed peers for each service
- Implement least privilege access
- Use network segmentation
- Monitor and alert on unauthorized connection attempts
- Implement rate limiting

### 4. Monitoring and Alerting

- Log all mTLS connections
- Alert on certificate expiry
- Monitor certificate rotation status
- Track authentication failures
- Audit certificate issuance and revocation

### 5. Incident Response

- Have certificate revocation procedures
- Maintain backup CA for emergencies
- Document certificate rotation playbooks
- Test disaster recovery procedures
- Keep audit logs for compliance

## Integration with Service Mesh

### Istio Integration

Generate Istio policies:

```python
from security.mtls_handler import ServiceMeshIntegration

# Generate PeerAuthentication policy
peer_auth = ServiceMeshIntegration.generate_istio_peer_authentication(
    service_name="api",
    namespace="devskyy",
    mode="STRICT"  # Require mTLS
)

# Generate AuthorizationPolicy
authz_policy = ServiceMeshIntegration.generate_istio_authorization_policy(
    service_name="database",
    allowed_services=["api", "analytics-agent"],
    namespace="devskyy"
)
```

Apply policies:

```bash
kubectl apply -f peer-authentication.yaml
kubectl apply -f authorization-policy.yaml
```

### Linkerd Integration

Linkerd automatically provides mTLS between services. Configure trust anchor:

```bash
# Install Linkerd with custom trust anchor
linkerd install \
  --identity-trust-anchors-file=/etc/devskyy/certs/ca/ca-cert.pem \
  | kubectl apply -f -
```

## Compliance and Auditing

### Audit Logging

Enable comprehensive audit logging:

```python
import logging

# Configure audit logger
audit_logger = logging.getLogger("devskyy.security.audit")
audit_logger.setLevel(logging.INFO)

handler = logging.FileHandler("/var/log/devskyy/security-audit.log")
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(handler)
```

### Compliance Reports

Generate compliance reports:

```python
from security.zero_trust_config import CertificateManager

manager = CertificateManager(config)
status = manager.get_cert_status()

# Generate report
print("Certificate Compliance Report")
print("=" * 60)

for service, info in status.items():
    print(f"\nService: {service}")
    print(f"  Expiry: {info['not_valid_after']}")
    print(f"  Days Remaining: {info['days_until_expiry']}")
    print(f"  Status: {'COMPLIANT' if not info['needs_rotation'] else 'NEEDS ROTATION'}")
```

## References

- [NIST Zero Trust Architecture](https://www.nist.gov/publications/zero-trust-architecture)
- [HashiCorp Vault PKI Secrets Engine](https://www.vaultproject.io/docs/secrets/pki)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Mutual TLS Best Practices](https://developers.google.com/identity/protocols/oauth2/openid-connect#obtainuserinfo)
- [TLS 1.3 RFC](https://datatracker.ietf.org/doc/html/rfc8446)

## Support

For issues or questions:

- File an issue in the DevSkyy repository
- Contact the security team
- Review audit logs in `/var/log/devskyy/security-audit.log`
