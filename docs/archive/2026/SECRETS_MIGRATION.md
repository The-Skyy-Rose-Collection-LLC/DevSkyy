# Secrets Management Migration Guide

This guide explains how to migrate from `.env` file-based secrets to cloud-based secrets management using AWS Secrets Manager or HashiCorp Vault.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Backend Options](#backend-options)
- [AWS Secrets Manager Setup](#aws-secrets-manager-setup)
- [HashiCorp Vault Setup](#hashicorp-vault-setup)
- [Local Development Setup](#local-development-setup)
- [Migration Process](#migration-process)
- [Testing](#testing)
- [Secret Rotation](#secret-rotation)
- [Troubleshooting](#troubleshooting)

---

## Overview

The DevSkyy platform now supports enterprise-grade secrets management through multiple backends:

- **AWS Secrets Manager** (Recommended for AWS deployments)
- **HashiCorp Vault** (Recommended for on-premises or multi-cloud)
- **Local Encrypted Storage** (Development only)

Benefits of migrating to cloud secrets management:

- Centralized secret storage and access control
- Automatic secret rotation
- Audit logging of secret access
- No secrets committed to version control
- Fine-grained IAM permissions
- Encryption at rest and in transit

---

## Prerequisites

### For AWS Secrets Manager

- AWS account with Secrets Manager enabled
- AWS CLI configured (`aws configure`)
- IAM user/role with appropriate permissions
- boto3 Python library: `pip install boto3`

### For HashiCorp Vault

- Vault server accessible (self-hosted or cloud)
- Vault CLI installed
- Vault authentication token
- hvac Python library: `pip install hvac`

### For All Backends

- Python 3.11+
- cryptography library: `pip install cryptography`
- pydantic library: `pip install pydantic`

---

## Backend Options

The SecretsManager automatically detects which backend to use based on environment variables:

| Priority | Backend | Detection |
|----------|---------|-----------|
| 1 | AWS Secrets Manager | `AWS_REGION` or `AWS_DEFAULT_REGION` is set |
| 2 | HashiCorp Vault | `VAULT_ADDR` is set |
| 3 | Local Encrypted | Fallback for development |

You can also explicitly specify the backend:

```python
from security.secrets_manager import SecretsManager, SecretBackendType

# Explicit backend selection
secrets = SecretsManager(backend_type=SecretBackendType.AWS_SECRETS_MANAGER)
```

---

## AWS Secrets Manager Setup

### 1. Install boto3

```bash
pip install boto3
```

### 2. Configure AWS Credentials

**Option A: Environment Variables**

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
```

**Option B: AWS CLI Configuration**

```bash
aws configure
# Follow prompts to enter credentials
```

**Option C: IAM Role (Recommended for EC2/ECS/Lambda)**

No credentials needed - instance profile provides automatic authentication.

### 3. Set Required IAM Permissions

Your IAM user/role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:UpdateSecret",
        "secretsmanager:PutSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:devskyy/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:RotateSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:devskyy/*",
      "Condition": {
        "StringEquals": {
          "secretsmanager:RotationLambdaARN": "arn:aws:lambda:*:*:function:devskyy-rotation"
        }
      }
    }
  ]
}
```

### 4. Create Secrets via AWS CLI

```bash
# JWT Secret Key
aws secretsmanager create-secret \
  --name jwt/secret_key \
  --description "JWT signing secret for DevSkyy" \
  --secret-string "your-super-secret-jwt-key-min-32-chars" \
  --region us-east-1

# Encryption Master Key
aws secretsmanager create-secret \
  --name encryption/master_key \
  --description "AES-256-GCM master encryption key" \
  --secret-string "your-encryption-key-32-bytes-hex" \
  --region us-east-1

# Database Connection String
aws secretsmanager create-secret \
  --name database/connection_string \
  --description "PostgreSQL connection string" \
  --secret-string "postgresql://user:password@host:5432/database" \
  --region us-east-1

# OpenAI API Key
aws secretsmanager create-secret \
  --name openai/api_key \
  --description "OpenAI API key" \
  --secret-string "sk-..." \
  --region us-east-1

# Anthropic API Key
aws secretsmanager create-secret \
  --name anthropic/api_key \
  --description "Anthropic API key" \
  --secret-string "sk-ant-..." \
  --region us-east-1
```

### 5. Create Secrets via Python

```python
from security.secrets_manager import SecretsManager, SecretBackendType

# Initialize AWS Secrets Manager
secrets = SecretsManager(backend_type=SecretBackendType.AWS_SECRETS_MANAGER)

# Create secrets
secrets.set_secret("jwt/secret_key", "your-super-secret-jwt-key")
secrets.set_secret("encryption/master_key", "your-encryption-key")
secrets.set_secret("database/connection_string", "postgresql://...")
secrets.set_secret("openai/api_key", "sk-...")
secrets.set_secret("anthropic/api_key", "sk-ant-...")
```

---

## HashiCorp Vault Setup

### 1. Install hvac

```bash
pip install hvac
```

### 2. Configure Vault Connection

```bash
export VAULT_ADDR=https://vault.example.com:8200
export VAULT_TOKEN=your-vault-token
export VAULT_NAMESPACE=devskyy  # Optional
```

### 3. Enable KV Secrets Engine

```bash
# Enable KV v2 secrets engine
vault secrets enable -path=secret kv-v2
```

### 4. Create Secrets via Vault CLI

```bash
# JWT Secret Key
vault kv put secret/jwt/secret_key value="your-super-secret-jwt-key"

# Encryption Master Key
vault kv put secret/encryption/master_key value="your-encryption-key"

# Database Connection String
vault kv put secret/database/connection_string value="postgresql://..."

# API Keys
vault kv put secret/openai/api_key value="sk-..."
vault kv put secret/anthropic/api_key value="sk-ant-..."
```

### 5. Create Secrets via Python

```python
from security.secrets_manager import SecretsManager, SecretBackendType

# Initialize HashiCorp Vault
secrets = SecretsManager(backend_type=SecretBackendType.HASHICORP_VAULT)

# Create secrets
secrets.set_secret("jwt/secret_key", "your-super-secret-jwt-key")
secrets.set_secret("encryption/master_key", "your-encryption-key")
secrets.set_secret("database/connection_string", "postgresql://...")
```

---

## Local Development Setup

For development environments, use the local encrypted backend:

### 1. Set Encryption Key (Optional but Recommended)

```bash
export SECRETS_ENCRYPTION_KEY="your-local-dev-encryption-key"
```

If not set, an ephemeral key is generated (secrets won't persist across restarts).

### 2. Create Secrets via Python

```python
from security.secrets_manager import SecretsManager

# Auto-detects local backend if AWS_REGION and VAULT_ADDR not set
secrets = SecretsManager()

# Create secrets
secrets.set_secret("jwt/secret_key", "dev-jwt-secret-key")
secrets.set_secret("encryption/master_key", "dev-encryption-key")
secrets.set_secret("database/connection_string", "sqlite:///dev.db")
```

Secrets are stored in `./secrets/` directory with AES encryption.

**WARNING: Local encrypted backend is for development only. Use AWS Secrets Manager or Vault for production.**

---

## Migration Process

### Step 1: Inventory Current Secrets

List all secrets currently in `.env` file:

```bash
# Example .env contents
JWT_SECRET_KEY=abc123...
ENCRYPTION_MASTER_KEY=def456...
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### Step 2: Create Migration Script

Create `scripts/migrate_secrets.py`:

```python
#!/usr/bin/env python3
"""
Migrate secrets from .env to AWS Secrets Manager
"""
import os
from dotenv import load_dotenv
from security.secrets_manager import SecretsManager, SecretBackendType

# Load current .env file
load_dotenv()

# Initialize secrets manager (use AWS)
secrets = SecretsManager(backend_type=SecretBackendType.AWS_SECRETS_MANAGER)

# Define secret mappings (secret_name -> env_var)
SECRET_MAPPINGS = {
    "jwt/secret_key": "JWT_SECRET_KEY",
    "encryption/master_key": "ENCRYPTION_MASTER_KEY",
    "database/connection_string": "DATABASE_URL",
    "openai/api_key": "OPENAI_API_KEY",
    "anthropic/api_key": "ANTHROPIC_API_KEY",
    "google/api_key": "GOOGLE_API_KEY",
    "aws/access_key_id": "AWS_ACCESS_KEY_ID",
    "aws/secret_access_key": "AWS_SECRET_ACCESS_KEY",
}

# Migrate each secret
for secret_name, env_var in SECRET_MAPPINGS.items():
    value = os.getenv(env_var)
    if value:
        print(f"Migrating {env_var} -> {secret_name}")
        secrets.set_secret(secret_name, value, tags={"migrated_from": "env"})
        print(f"✓ Migrated {secret_name}")
    else:
        print(f"⚠ Skipping {env_var} (not set)")

print("\nMigration complete!")
print("\nNext steps:")
print("1. Verify secrets in AWS Secrets Manager console")
print("2. Test application with secrets manager")
print("3. Remove secrets from .env file")
print("4. Add .env to .gitignore if not already")
```

### Step 3: Run Migration

```bash
# Ensure AWS credentials are configured
export AWS_REGION=us-east-1

# Run migration script
python scripts/migrate_secrets.py
```

### Step 4: Verify Migration

```python
from security.secrets_manager import SecretsManager

secrets = SecretsManager()

# Verify each secret
print(secrets.get_secret("jwt/secret_key"))
print(secrets.get_secret("encryption/master_key"))
print(secrets.list_secrets())
```

### Step 5: Update Application Configuration

The application is already configured to use SecretsManager in `main_enterprise.py`.

Ensure environment variable is set:

```bash
export AWS_REGION=us-east-1
```

### Step 6: Remove Secrets from .env

**IMPORTANT: Backup .env file before removing secrets!**

```bash
# Backup
cp .env .env.backup

# Create new .env with non-secret configuration only
cat > .env << EOF
# DevSkyy Configuration (non-secrets only)
ENVIRONMENT=production
CORS_ORIGINS=https://devskyy.com,https://app.devskyy.com
LOG_LEVEL=INFO

# AWS Region (for Secrets Manager)
AWS_REGION=us-east-1

# Feature Flags
ENABLE_WEBHOOKS=true
ENABLE_ANALYTICS=true
EOF
```

### Step 7: Update .gitignore

Ensure `.env` and `.env.backup` are in `.gitignore`:

```bash
echo ".env" >> .gitignore
echo ".env.backup" >> .gitignore
echo "secrets/" >> .gitignore
```

---

## Testing

### Test 1: Verify Secret Retrieval

```python
from security.secrets_manager import get_secret

# Test retrieving secrets
jwt_secret = get_secret("jwt/secret_key")
print(f"JWT Secret loaded: {jwt_secret[:10]}...")

db_url = get_secret("database/connection_string")
print(f"Database URL loaded: {db_url[:20]}...")
```

### Test 2: Verify Fallback to Environment Variables

```python
from security.secrets_manager import SecretsManager

secrets = SecretsManager()

# This tries secrets manager first, falls back to env var
value = secrets.get_or_env("jwt/secret_key", "JWT_SECRET_KEY")
print(f"Value loaded: {value[:10]}...")
```

### Test 3: Start Application

```bash
# Start the application
uvicorn main_enterprise:app --reload

# Check logs for:
# ✓ JWT_SECRET_KEY loaded from secrets manager
# ✓ ENCRYPTION_MASTER_KEY loaded from secrets manager
# ✓ DATABASE_URL loaded from secrets manager
```

### Test 4: Integration Test

```bash
# Test authentication endpoint
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Should return JWT token if secrets loaded correctly
```

### Test 5: Verify Health Check

```bash
curl http://localhost:8000/health

# Should return healthy status
```

---

## Secret Rotation

### AWS Secrets Manager Automatic Rotation

#### 1. Create Rotation Lambda Function

Create `lambda/rotate_jwt_secret.py`:

```python
import json
import boto3
import secrets as python_secrets

def lambda_handler(event, context):
    """Rotate JWT secret key"""
    service_client = boto3.client('secretsmanager')

    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    if step == "createSecret":
        # Generate new secret
        new_secret = python_secrets.token_urlsafe(64)
        service_client.put_secret_value(
            SecretId=arn,
            ClientRequestToken=token,
            SecretString=new_secret,
            VersionStages=['AWSPENDING']
        )

    elif step == "setSecret":
        # Update application configuration (if needed)
        pass

    elif step == "testSecret":
        # Test new secret works
        pass

    elif step == "finishSecret":
        # Finalize rotation
        service_client.update_secret_version_stage(
            SecretId=arn,
            VersionStage='AWSCURRENT',
            MoveToVersionId=token,
            RemoveFromVersionId=event['PreviousVersion']
        )

    return {'statusCode': 200}
```

#### 2. Enable Rotation

```bash
# Create rotation configuration
aws secretsmanager rotate-secret \
  --secret-id jwt/secret_key \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789:function:rotate-jwt \
  --rotation-rules AutomaticallyAfterDays=30
```

### Manual Secret Rotation

```python
from security.secrets_manager import SecretsManager
import secrets

# Generate new secret
new_jwt_secret = secrets.token_urlsafe(64)

# Update in secrets manager
secrets_mgr = SecretsManager()
version = secrets_mgr.set_secret("jwt/secret_key", new_jwt_secret)

print(f"Secret rotated to version: {version}")

# Restart application to load new secret
```

### Scheduled Rotation (Future Enhancement)

The codebase includes comments for a future `SecretRotationScheduler`:

```python
# TODO: Implement in future update
# from security.secrets_manager import SecretRotationScheduler
#
# scheduler = SecretRotationScheduler(secrets_manager)
# scheduler.add_rotation_policy(
#     secret_pattern="jwt/*",
#     interval_days=30,
#     notify_days_before=7,
# )
# scheduler.start()
```

---

## Troubleshooting

### Issue: "boto3 is required for AWS Secrets Manager"

**Solution:**

```bash
pip install boto3
```

### Issue: "Failed to initialize AWS Secrets Manager client"

**Possible Causes:**

1. AWS credentials not configured
2. Invalid AWS region
3. Network connectivity issues

**Solutions:**

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Set region explicitly
export AWS_REGION=us-east-1

# Test AWS connectivity
aws secretsmanager list-secrets --region us-east-1
```

### Issue: "Secret 'jwt/secret_key' not found in AWS Secrets Manager"

**Solution:**

Create the secret:

```bash
aws secretsmanager create-secret \
  --name jwt/secret_key \
  --secret-string "your-secret-value" \
  --region us-east-1
```

### Issue: "hvac library required for HashiCorp Vault"

**Solution:**

```bash
pip install hvac
```

### Issue: "Failed to authenticate with Vault"

**Possible Causes:**

1. Invalid VAULT_TOKEN
2. Token expired
3. Incorrect VAULT_ADDR

**Solutions:**

```bash
# Verify Vault connection
vault status

# Renew token
vault token renew

# Check token info
vault token lookup
```

### Issue: "Using local encrypted storage" (in production)

**Problem:** Application falling back to local storage instead of cloud backend.

**Solution:**

Ensure environment variables are set:

```bash
# For AWS
export AWS_REGION=us-east-1

# For Vault
export VAULT_ADDR=https://vault.example.com:8200
export VAULT_TOKEN=your-token
```

### Issue: Secrets not updating after rotation

**Solution:**

Restart the application - secrets are loaded once at startup:

```bash
# Development
pkill -f uvicorn
uvicorn main_enterprise:app --reload

# Production (Kubernetes)
kubectl rollout restart deployment devskyy-api

# Production (Docker)
docker-compose restart api
```

---

## Best Practices

### 1. Secret Naming Convention

Use hierarchical naming:

- `service/secret_type/secret_name`
- Examples:
  - `jwt/secret_key`
  - `database/connection_string`
  - `api/openai/key`
  - `encryption/master_key`

### 2. Tagging

Use tags for organization and filtering:

```python
secrets.set_secret(
    "api/openai/key",
    "sk-...",
    tags={
        "environment": "production",
        "service": "devskyy",
        "cost_center": "engineering",
        "compliance": "pci-dss"
    }
)
```

### 3. Rotation Schedule

- **JWT keys**: Every 30 days
- **Database passwords**: Every 90 days
- **API keys**: Every 180 days
- **Encryption keys**: Annually

### 4. Access Control

Use least-privilege IAM policies:

- Read-only access for applications
- Write access only for deployment pipelines
- Rotation access only for Lambda functions

### 5. Audit Logging

Enable AWS CloudTrail for Secrets Manager:

```bash
aws cloudtrail create-trail \
  --name devskyy-secrets-audit \
  --s3-bucket-name devskyy-audit-logs
```

### 6. Backup

Regularly export secrets to secure backup:

```python
# Export all secrets
secrets = SecretsManager()
all_secrets = secrets.list_secrets()

backup = {}
for secret_name in all_secrets:
    backup[secret_name] = secrets.get_secret(secret_name)

# Encrypt and store backup securely
```

---

## Additional Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [DevSkyy Security Documentation](./README.md)

---

## Support

For issues or questions:

- Create an issue in the repository
- Contact the DevOps team
- Review the troubleshooting section above

---

**Migration Checklist:**

- [ ] Choose backend (AWS Secrets Manager, HashiCorp Vault, or Local)
- [ ] Install required dependencies (`boto3` or `hvac`)
- [ ] Configure credentials and environment variables
- [ ] Create secrets in chosen backend
- [ ] Run migration script
- [ ] Test secret retrieval
- [ ] Verify application starts successfully
- [ ] Remove secrets from `.env` file
- [ ] Update `.gitignore`
- [ ] Configure secret rotation
- [ ] Document custom secrets for your team
- [ ] Set up monitoring and alerts

---

Last Updated: 2025-12-19
