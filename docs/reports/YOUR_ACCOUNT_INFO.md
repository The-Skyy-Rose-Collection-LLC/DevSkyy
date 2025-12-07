# 🔐 Your DevSkyy Enterprise Account Information

## Account Creation & Security (Important)

DevSkyy follows a strict policy: DO NOT store or publish real credentials in documentation. All secrets must be provided via environment variables, secure secret stores, or the configured credentials manager.

This document provides guidance for creating and using accounts securely — it no longer contains hardcoded passwords or production credentials.

### Creating an Admin Account (recommended)

Use the platform's management tools (admin UI or API) to create users. Example API flow (replace placeholders):

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_admin_username",
    "email": "admin@example.com",
    "password": "<STRONG_PASSWORD>"
  }'
```

After creation, use the login endpoint to obtain tokens:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_admin_username&password=<STRONG_PASSWORD>"
```

The response will include an access token. Store tokens securely (not in repository or public docs).

### Login Example (placeholder)

```bash
# Save your token (example, DO NOT paste real credentials into repo)
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=SuperSecret123" | \
  python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Use token for protected requests
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Super Admin Privileges

If granted `super_admin`, a user can manage agents, users, credentials, and system configuration. Grant roles only to trusted operators.

- Avoid embedding passwords in documentation.
- Use application passwords or ephemeral tokens for automation.
- Prefer credential managers (see `config/wordpress_credentials` module) for integrations.

### Secure Practices

- Do not commit `.env` files or secrets to source control; use `.env.production.example` as a template only.
- In production, ensure `SECRET_KEY` and other sensitive variables are set in environment and not left to defaults. main.py will raise when SECRET_KEY is missing in production.
- Replace long-lived credentials with short-lived tokens where possible.

### Quick Start (development)

Run locally for development (use development-only credentials and never commit them):

```bash
# Start services (example)
docker-compose up -d

# Or run locally with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Notes

- This document no longer includes plaintext passwords or personal account data.
- If you see any documentation with hardcoded credentials, remove them and rotate those secrets immediately.
- For WordPress deployments, use the credential manager endpoints (`/api/v1/themes/credentials/*`) or the `config/wordpress_credentials` manager rather than embedding secrets in requests where possible.

### Support

If you need help creating or rotating credentials safely, contact the platform administrators or consult the deployment runbook.

