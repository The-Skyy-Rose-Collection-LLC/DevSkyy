# DevSkyy Authentication Quick Reference

## 🚀 Quick Start

### Environment Setup
```bash
# Required Environment Variables
export SECRET_KEY="your-256-bit-secret-key"
export AUTH0_DOMAIN="your-tenant.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
export AUTH0_CLIENT_SECRET="your-client-secret"
export AUTH0_AUDIENCE="https://api.devskyy.com"
```

### Basic Authentication Flow
```python
# 1. Register User
response = requests.post("/api/v1/auth/register", json={
    "email": "user@example.com",
    "username": "username",
    "password": "SecurePass123!"
})

# 2. Login User
response = requests.post("/api/v1/auth/login", data={
    "username": "user@example.com",
    "password": "SecurePass123!"
})
tokens = response.json()

# 3. Use Access Token
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
response = requests.get("/api/v1/auth/me", headers=headers)
```

## 📋 API Endpoints Reference

### Core Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/auth/register` | Register new user | ❌ |
| `POST` | `/api/v1/auth/login` | User login | ❌ |
| `POST` | `/api/v1/auth/refresh` | Refresh tokens | ❌ |
| `GET` | `/api/v1/auth/me` | Get current user | ✅ |
| `POST` | `/api/v1/auth/logout` | User logout | ✅ |
| `GET` | `/api/v1/auth/users` | List users (admin) | ✅ |

### Auth0 Integration

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/auth/auth0/login` | Initiate Auth0 login | ❌ |
| `GET` | `/api/v1/auth/auth0/callback` | Handle Auth0 callback | ❌ |
| `GET` | `/api/v1/auth/auth0/logout` | Auth0 logout | ❌ |
| `GET` | `/api/v1/auth/auth0/me` | Get Auth0 user info | ✅ |
| `GET` | `/api/v1/auth/auth0/demo` | Demo page | ❌ |

## 🔑 Authentication Methods

### 1. JWT Bearer Token
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     https://api.devskyy.com/api/v1/auth/me
```

### 2. OAuth2 Password Flow
```bash
curl -X POST https://api.devskyy.com/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=SecurePass123!"
```

### 3. Auth0 OAuth2 Flow
```bash
# Step 1: Get authorization URL
curl https://api.devskyy.com/api/v1/auth/auth0/login

# Step 2: User authenticates with Auth0
# Step 3: Handle callback
curl "https://api.devskyy.com/api/v1/auth/auth0/callback?code=AUTH_CODE&state=STATE"
```

## 📝 Request/Response Examples

### User Registration
```bash
# Request
curl -X POST https://api.devskyy.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "company": "Example Corp"
  }'

# Response (201 Created)
{
  "user_id": "uuid-string",
  "email": "john@example.com",
  "username": "johndoe",
  "role": "api_user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "permissions": []
}
```

### User Login
```bash
# Request
curl -X POST https://api.devskyy.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=SecurePass123!"

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Get Current User
```bash
# Request
curl -X GET https://api.devskyy.com/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response (200 OK)
{
  "user_id": "uuid-string",
  "email": "john@example.com",
  "username": "johndoe",
  "role": "api_user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z",
  "permissions": []
}
```

### Auth0 Login
```bash
# Request
curl https://api.devskyy.com/api/v1/auth/auth0/login

# Response (200 OK)
{
  "authorization_url": "https://your-tenant.auth0.com/authorize?response_type=code&client_id=...",
  "state": "random-state-string"
}
```

## 🛡️ Security Features

### Password Requirements
- ✅ Minimum 8 characters
- ✅ At least one uppercase letter
- ✅ At least one lowercase letter  
- ✅ At least one digit
- ✅ At least one special character
- ✅ No common passwords
- ✅ No repeated characters

### Account Protection
- ✅ **Account Lockout**: 5 failed attempts = 15-minute lockout
- ✅ **Token Blacklisting**: Immediate token revocation
- ✅ **Session Management**: Secure session tracking
- ✅ **Rate Limiting**: Protection against brute force

### Token Security
- ✅ **Short-lived Access Tokens**: 15 minutes
- ✅ **Refresh Tokens**: 7 days
- ✅ **Secure Algorithms**: HS256 for DevSkyy, RS256 for Auth0
- ✅ **Token Validation**: Comprehensive security checks

## ⚠️ Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `400` | Bad Request | Invalid input data |
| `401` | Unauthorized | Invalid or expired token |
| `403` | Forbidden | Insufficient permissions |
| `422` | Validation Error | Input validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate access token",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must contain at least one uppercase letter",
      "type": "value_error"
    }
  ]
}
```

#### 429 Rate Limited
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

## 🔧 Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/register` | 5 requests | 1 hour |
| `/auth/login` | 10 requests | 15 minutes |
| `/auth/refresh` | 20 requests | 1 hour |
| `/auth/me` | 100 requests | 1 hour |
| `/auth/auth0/*` | 50 requests | 1 hour |

### Rate Limit Headers
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1640995200
Retry-After: 900
```

## 🔐 User Roles & Permissions

### Default Roles
```python
class UserRole:
    API_USER = "api_user"          # Basic API access
    PREMIUM_USER = "premium_user"  # Premium features
    ADMIN = "admin"                # Admin access
    SUPER_ADMIN = "super_admin"    # Full system access
```

### Permission Examples
```python
# Check user permissions
@app.get("/admin/users")
async def admin_endpoint(
    user = Depends(require_permissions(["admin:users:read"]))
):
    # Admin-only endpoint
    pass

# Role-based access
@app.get("/premium/features")
async def premium_endpoint(
    current_user: TokenData = Depends(get_current_active_user)
):
    if current_user.role not in ["premium_user", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Premium access required")
```

## 🌐 Frontend Integration

### JavaScript/TypeScript Examples

#### Registration
```typescript
const registerUser = async (userData: RegisterRequest) => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return response.json();
};
```

#### Login with Token Storage
```typescript
const loginUser = async (email: string, password: string) => {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  const tokens = await response.json();
  
  // Store tokens securely
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
  
  return tokens;
};
```

#### Authenticated API Calls
```typescript
const makeAuthenticatedRequest = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    // Token expired, try to refresh
    await refreshToken();
    // Retry request
    return makeAuthenticatedRequest(url, options);
  }
  
  return response;
};
```

#### Token Refresh
```typescript
const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  
  if (!response.ok) {
    // Refresh failed, redirect to login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
    return;
  }
  
  const tokens = await response.json();
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
};
```

#### Auth0 Integration
```typescript
const initiateAuth0Login = async () => {
  const response = await fetch('/api/v1/auth/auth0/login');
  const data = await response.json();
  
  // Redirect to Auth0
  window.location.href = data.authorization_url;
};

const handleAuth0Callback = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  
  if (code && state) {
    const response = await fetch(`/api/v1/auth/auth0/callback?code=${code}&state=${state}`);
    const tokens = await response.json();
    
    // Store DevSkyy JWT tokens
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    
    return tokens;
  }
};
```

## 🐛 Troubleshooting

### Common Issues

#### Token Expired
```typescript
// Check token expiration
const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return Date.now() >= payload.exp * 1000;
  } catch {
    return true;
  }
};

// Auto-refresh expired tokens
if (isTokenExpired(accessToken)) {
  await refreshToken();
}
```

#### Account Locked
```bash
# Wait for lockout period (15 minutes) or contact admin
# Check lockout status
curl -X POST https://api.devskyy.com/api/v1/auth/login \
     -d "username=user@example.com&password=wrong"

# Response: "Account temporarily locked due to failed login attempts"
```

#### Auth0 Callback Error
```typescript
// Handle Auth0 errors
const urlParams = new URLSearchParams(window.location.search);
const error = urlParams.get('error');
const errorDescription = urlParams.get('error_description');

if (error) {
  console.error('Auth0 Error:', error, errorDescription);
  // Handle specific errors
  if (error === 'access_denied') {
    // User denied access
  } else {
    // Other Auth0 error
  }
}
```

#### Rate Limit Exceeded
```typescript
// Handle rate limiting with exponential backoff
const makeRequestWithRetry = async (url: string, options: RequestInit, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url, options);
    
    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      const delay = retryAfter ? parseInt(retryAfter) * 1000 : Math.pow(2, i) * 1000;
      
      await new Promise(resolve => setTimeout(resolve, delay));
      continue;
    }
    
    return response;
  }
  
  throw new Error('Max retries exceeded');
};
```

## 📞 Support

### Contact Information
- **Documentation**: https://docs.devskyy.com
- **Support Email**: support@devskyy.com
- **Status Page**: https://status.devskyy.com
- **Security Issues**: security@devskyy.com

### Useful Links
- [Full API Documentation](./API_AUTHENTICATION_DOCUMENTATION.md)
- [Auth0 Integration Guide](./AUTH0_INTEGRATION_GUIDE.md)
- [Security Guide](./AUTHENTICATION_SECURITY_GUIDE.md)
- [OpenAPI Specification](https://api.devskyy.com/docs)

---

*Quick Reference Guide v1.0 - Last updated: 2024-10-24*
