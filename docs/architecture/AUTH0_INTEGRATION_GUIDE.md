# 🔐 **AUTH0 ENTERPRISE INTEGRATION GUIDE (Optional Integration)**

> NOTE: Auth0 integration is optional. The repository's main application (main.py) includes hooks for JWT-based auth via a JWTManager, but it does not ship a fully-configured Auth0 integration by default. Many referenced modules in docs are conditionally imported in main.py and may be missing in this repository. Follow the steps below to add Auth0 support to your running DevSkyy instance.

## 🎯 **OVERVIEW**

DevSkyy can be integrated with Auth0 for enterprise authentication. Auth0 integration is not enabled by default in the codebase; the platform uses an internal JWTManager when available and falls back to environment-driven settings. The guide below shows how to add Auth0 safely and how to wire it into the FastAPI app.

---

## 🚀 **QUICK SETUP GUIDE**

### **1. Prerequisites**
```bash
# Ensure Auth0 Deploy CLI is installed (optional for large tenant configuration)
npm install -g auth0-deploy-cli

# Verify installation
a0deploy --version
# (optional) Should show a recent version
```

### **2. Auth0 Account Setup (Manual Steps)**
1. Create an Auth0 account at https://auth0.com/signup
2. Create a tenant and required Applications / APIs for your environment (Web SPA, API, M2M)
3. Create a Machine-to-Machine application for backend-to-backend access if needed

> Note: DevSkyy does not bundle an Auth0 tenant configuration. Use the Auth0 Management API or auth0-deploy-cli to apply tenant configuration.

### **3. Configure Environment**

Create or update your .env with Auth0 variables (used by the integration you add):

```bash
# Auth0 Configuration
AUTH0_DOMAIN=devskyy.auth0.com
AUTH0_AUDIENCE=https://api.devskyy.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# Optional: management API M2M client
AUTH0_M2M_CLIENT_ID=your-m2m-client-id
AUTH0_M2M_CLIENT_SECRET=your-m2m-client-secret
```

> Important: per Truth Protocol Rule #5, never commit secrets to source. Use environment variables or a secrets store.

---

## 🔧 **MINIMAL INTEGRATION (FastAPI)**

Below is a minimal approach to add Auth0 JWT verification as an optional dependency alongside the existing JWTManager in the repository.

1. Create a small helper module (e.g. `security/auth0_auth.py`) and implement token verification using JWKs from your Auth0 tenant.

```python
# security/auth0_auth.py
from functools import lru_cache
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
import httpx
from jose import jwt, JWTError
import os

security = HTTPBearer()
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

@lru_cache()
def get_jwks():
    if not AUTH0_DOMAIN:
        raise RuntimeError("AUTH0_DOMAIN not configured")
    r = httpx.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", timeout=10)
    r.raise_for_status()
    return r.json()

async def verify_auth0_token(token: str = Depends(security)):
    try:
        jwks = get_jwks()
        payload = jwt.decode(
            token.credentials,
            jwks,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

2. Use the dependency in FastAPI endpoints in place of (or alongside) the existing JWTManager-based dependency. Example usage:

```python
# In an endpoint module
from fastapi import Depends
from security.auth0_auth import verify_auth0_token

@app.get("/api/v1/protected")
async def protected_endpoint(token_payload=Depends(verify_auth0_token)):
    user_id = token_payload.get("sub")
    return {"user_id": user_id, "message": "Access granted via Auth0"}
```

3. If you want to prefer Auth0 only when configured, guard the import/usage with environment checks just like main.py does for optional modules.

---

## 🔒 **SECURITY & DEPLOYMENT NOTES**

- Do not store Auth0 secrets in code or commit them. Use environment variables or a secrets manager.
- Validate audience and issuer claims on incoming tokens.
- Pair Auth0 with existing RBAC in DevSkyy (roles/scopes) rather than bypassing server-side checks.
- Consider token introspection or management API checks for revoked tokens if you need immediate revocation semantics.

---

## 📦 **FRONTEND INTEGRATION (React / Next.js)**

Frontend integration steps are the same as standard Auth0 SPA integration. Use the Auth0 SDK for React and configure `audience` to match the API where tokens are validated.

---

## 🚀 **CHECKLIST**

- [ ] Create Auth0 tenant & applications
- [ ] Add Auth0 env vars to deployment
- [ ] Add `security/auth0_auth.py` (or similar) to verify tokens
- [ ] Replace or augment JWT-based dependencies in endpoints
- [ ] Test authenticated flows end-to-end

---

## 🎯 **NEXT STEPS**
1. Implement the small helper module (security/auth0_auth.py) shown above
2. Integrate endpoints by using verify_auth0_token as a dependency
3. Optionally replace or wrap existing JWTManager with Auth0 verification


**Short summary**: Auth0 integration is supported as an optional add-on. The repository's main application performs conditional imports and will continue to function without Auth0. Carefully add verification code and environment variables as shown above.
