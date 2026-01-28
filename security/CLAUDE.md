# DevSkyy Security

> Zero-trust, defense-in-depth | 32 files

## Architecture
```
security/
├── aes_gcm_crypto.py        # AES-256-GCM encryption
├── audit_logging.py         # Immutable audit trail
├── input_validation.py      # XSS/SQLi prevention
├── jwt_oauth2_auth.py       # JWT + OAuth2 + TOTP
├── secrets_manager.py       # AWS Secrets / local
└── rate_limiting.py         # Tier-based limits
```

## Pattern
```python
class SecurityValidator:
    def sanitize_html(self, input_text: str) -> str:
        return bleach.clean(input_text, tags=SAFE_TAGS, strip=True)

    def detect_sql_injection(self, value: str) -> bool:
        patterns = [r"(\bUNION\b.*\bSELECT\b)", r"(--|\#|\/\*)"]
        return any(re.search(p, value, re.I) for p in patterns)
```

## Components
| Component | Implementation |
|-----------|----------------|
| Crypto | AES-256-GCM (NIST compliant) |
| Auth | JWT + refresh, OAuth2, TOTP |
| Validation | XSS/SQLi prevention |
| Audit | Immutable logging |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
- **Agent**: `security-reviewer` | **Skill**: `security-review`

**"Security is not a feature. It's the foundation."**
