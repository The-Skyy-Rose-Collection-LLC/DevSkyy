# DevSkyy Security

> AES-256-GCM | JWT + OAuth2 | OWASP compliance

---

## Learnings (Update When Claude Makes Mistakes)

### Encryption

- ❌ **Mistake**: Using ECB mode (insecure)
  - ✅ **Correct**: AES-256-GCM only (authenticated encryption)

- ❌ **Mistake**: Storing encryption keys in code
  - ✅ **Correct**: AWS Secrets Manager (prod), `.env` (dev only)

- ❌ **Mistake**: Not rotating encryption keys
  - ✅ **Correct**: Key rotation every 90 days (automated)

### JWT Tokens

- ❌ **Mistake**: Setting no expiration on tokens
  - ✅ **Correct**: Access tokens: 15 min, Refresh tokens: 7 days

- ❌ **Mistake**: Storing JWT secret in git
  - ✅ **Correct**: Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`

- ❌ **Mistake**: Not validating token signature
  - ✅ **Correct**: Always verify with `jwt.decode(verify_signature=True)`

### Input Validation

- ❌ **Mistake**: Trusting user input
  - ✅ **Correct**: Validate ALL inputs with Pydantic at API boundaries

- ❌ **Mistake**: SQL injection via string formatting
  - ✅ **Correct**: Use SQLAlchemy parameterized queries only

- ❌ **Mistake**: XSS via unescaped HTML
  - ✅ **Correct**: Always escape with `html.escape()` or template engine

### OWASP Top 10

- ❌ **Mistake**: Not checking for OWASP vulnerabilities
  - ✅ **Correct**: Use `security-reviewer` agent before commits

- ❌ **Mistake**: Disabled CSRF protection "for testing"
  - ✅ **Correct**: NEVER disable security features in prod

---

## Structure

```
security/
├── encryption.py             # AES-256-GCM encryption
├── jwt.py                    # JWT token management
├── audit_log.py              # Security audit logging
└── validators.py             # Input validation
```

---

## Usage Pattern

```python
# ✅ CORRECT: Encrypt sensitive data
from security.encryption import encrypt, decrypt

encrypted = encrypt(sensitive_data, key=key)  # AES-256-GCM
stored_data = base64.b64encode(encrypted)

# Later...
decrypted = decrypt(base64.b64decode(stored_data), key=key)
```

---

## Verification

```bash
# Security audit
pytest tests/unit/test_security.py -v -m security

# Check for hardcoded secrets
rg -i "(api_key|secret|password)\s*=\s*['\"]" security/ && echo "❌ Found hardcoded secrets!" || echo "✅ No hardcoded secrets"

# OWASP check
bandit -r security/ -ll
```

---

**"Security is not optional. It's mandatory."**
