# DevSkyy Authentication API Documentation

## Overview

The DevSkyy platform provides a comprehensive authentication system with multiple authentication methods including traditional JWT-based authentication and Auth0 integration for enterprise-grade security. This documentation covers all authentication endpoints, security features, and integration patterns.

## Table of Contents

1. [Authentication Methods](#authentication-methods)
2. [Base URLs and Configuration](#base-urls-and-configuration)
3. [Core Authentication Endpoints](#core-authentication-endpoints)
4. [Auth0 Integration Endpoints](#auth0-integration-endpoints)
5. [Security Features](#security-features)
6. [Request/Response Models](#requestresponse-models)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Examples](#examples)

## Authentication Methods

### 1. JWT-Based Authentication
- **Type**: Bearer Token Authentication
- **Token Lifetime**: 15 minutes (access), 7 days (refresh)
- **Algorithm**: HS256
- **Security**: bcrypt password hashing with 12 rounds

### 2. Auth0 Integration
- **Type**: OAuth2 Authorization Code Flow
- **Provider**: Auth0
- **Token Bridge**: Converts Auth0 tokens to DevSkyy JWT format
- **Features**: SSO, MFA, Enterprise connections

### 3. API Key Authentication
- **Type**: Bearer Token
- **Usage**: Service-to-service authentication
- **Validation**: Security manager integration

## Base URLs and Configuration

```
Base API URL: https://api.devskyy.com/api/v1
Auth Endpoints: /auth
Auth0 Endpoints: /auth/auth0
```

### Environment Variables
```bash
# JWT Configuration
SECRET_KEY=your-256-bit-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=https://api.devskyy.com

# Application URLs
FRONTEND_URL=https://app.devskyy.com
API_BASE_URL=https://api.devskyy.com
```

## Core Authentication Endpoints

### 1. User Registration

**Endpoint**: `POST /api/v1/auth/register`

**Description**: Register a new user account with enhanced validation and security features.

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePass123!",
  "role": "api_user",
  "full_name": "John Doe",
  "company": "Example Corp"
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Response** (201 Created):
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "username": "username",
  "role": "api_user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "permissions": []
}
```

### 2. User Login

**Endpoint**: `POST /api/v1/auth/login`

**Description**: Authenticate user and receive access/refresh tokens.

**Request Body** (OAuth2 Password Flow):
```json
{
  "username": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 3. Token Refresh

**Endpoint**: `POST /api/v1/auth/refresh`

**Description**: Refresh access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 4. Get Current User

**Endpoint**: `GET /api/v1/auth/me`

**Description**: Get current authenticated user information.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "username": "username",
  "role": "api_user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z",
  "permissions": []
}
```

### 5. User Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Description**: Logout current user (invalidates token on client side).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "Successfully logged out",
  "user": "user@example.com"
}
```

### 6. List Users (Admin Only)

**Endpoint**: `GET /api/v1/auth/users`

**Description**: List all registered users (requires admin privileges).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "users": [
    {
      "user_id": "uuid-string",
      "email": "user@example.com",
      "username": "username",
      "role": "api_user",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

## Auth0 Integration Endpoints

### 1. Auth0 Login Initiation

**Endpoint**: `GET /api/v1/auth/auth0/login`

**Description**: Initiate Auth0 authentication flow.

**Query Parameters**:
- `redirect_uri` (optional): Custom redirect URI after login

**Response** (200 OK):
```json
{
  "authorization_url": "https://your-tenant.auth0.com/authorize?...",
  "state": "random-state-string"
}
```

### 2. Auth0 Callback

**Endpoint**: `GET /api/v1/auth/auth0/callback`

**Description**: Handle Auth0 callback and exchange code for tokens.

**Query Parameters**:
- `code`: Authorization code from Auth0
- `state`: State parameter for CSRF protection
- `error` (optional): Error from Auth0
- `error_description` (optional): Error description

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_info": {
    "sub": "auth0|user-id",
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://avatar.url",
    "email_verified": true
  }
}
```

### 3. Auth0 Logout

**Endpoint**: `GET /api/v1/auth/auth0/logout`

**Description**: Logout from Auth0 and clear session.

**Query Parameters**:
- `return_to` (optional): URL to return to after logout

**Response** (200 OK):
```json
{
  "logout_url": "https://your-tenant.auth0.com/v2/logout?...",
  "message": "Logout successful. Please visit the logout_url to complete Auth0 logout."
}
```

### 4. Auth0 User Info

**Endpoint**: `GET /api/v1/auth/auth0/me`

**Description**: Get current Auth0 user information.

**Headers**:
```
Authorization: Bearer <devskyy_jwt_token>
```

**Response** (200 OK):
```json
{
  "user_id": "auth0|user-id",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://avatar.url",
  "email_verified": true,
  "auth_provider": "auth0",
  "token_type": "access"
}
```

### 5. Auth0 Demo Page

**Endpoint**: `GET /api/v1/auth/auth0/demo`

**Description**: Demo page for testing Auth0 integration (HTML response).

**Response**: HTML page with Auth0 integration demo and API endpoint documentation.

## Security Features

### 1. Account Lockout Protection
- **Failed Attempts**: Maximum 5 failed login attempts
- **Lockout Duration**: 15 minutes
- **Automatic Reset**: Failed attempts reset after successful login

### 2. Token Security
- **Blacklisting**: Immediate token revocation capability
- **Short Lifetime**: 15-minute access tokens
- **Secure Storage**: Tokens should be stored securely on client side
- **HTTPS Only**: All authentication endpoints require HTTPS

### 3. Password Security
- **Hashing**: bcrypt with 12 rounds
- **Complexity**: Enforced password complexity requirements
- **No Personal Info**: Passwords cannot contain personal information

### 4. Rate Limiting
- **Login Attempts**: Limited per IP address
- **Registration**: Limited per IP address
- **Token Refresh**: Limited per user

### 5. Input Validation
- **SQL Injection Protection**: All inputs validated
- **XSS Prevention**: HTML sanitization
- **CSRF Protection**: State parameters and secure headers

## Request/Response Models

### User Roles
```python
class UserRole:
    API_USER = "api_user"
    PREMIUM_USER = "premium_user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
```

### Token Payload
```python
{
  "user_id": "string",
  "email": "string",
  "username": "string", 
  "role": "string",
  "token_type": "access|refresh",
  "exp": "timestamp",
  "iat": "timestamp",
  "iss": "devskyy-platform",
  "aud": "devskyy-api"
}
```

### Auth0 Token Payload
```python
{
  "sub": "auth0|user-id",
  "email": "string",
  "name": "string",
  "picture": "string",
  "email_verified": "boolean",
  "exp": "timestamp",
  "iat": "timestamp",
  "iss": "devskyy-platform",
  "aud": "devskyy-api",
  "token_type": "access",
  "auth_provider": "auth0"
}
```

## Error Handling

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
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

#### 403 Forbidden
```json
{
  "detail": "Admin access required"
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

#### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Registration failed"
}
```

### Auth0 Specific Errors

#### Auth0 Callback Error
```json
{
  "error": "access_denied",
  "error_description": "User denied the request"
}
```

## Rate Limiting

### Limits by Endpoint

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
```

## Examples

### Complete Authentication Flow

#### 1. Register User
```bash
curl -X POST "https://api.devskyy.com/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

#### 2. Login User
```bash
curl -X POST "https://api.devskyy.com/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=SecurePass123!"
```

#### 3. Use Access Token
```bash
curl -X GET "https://api.devskyy.com/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 4. Refresh Token
```bash
curl -X POST "https://api.devskyy.com/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Auth0 Integration Flow

#### 1. Initiate Auth0 Login
```bash
curl -X GET "https://api.devskyy.com/api/v1/auth/auth0/login"
```

#### 2. Handle Callback (typically done by browser)
```bash
curl -X GET "https://api.devskyy.com/api/v1/auth/auth0/callback?code=AUTH_CODE&state=STATE"
```

#### 3. Use Auth0 Token
```bash
curl -X GET "https://api.devskyy.com/api/v1/auth/auth0/me" \
  -H "Authorization: Bearer DEVSKYY_JWT_TOKEN"
```

### JavaScript/TypeScript Examples

#### Registration
```typescript
const registerUser = async (userData: {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}) => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  
  if (!response.ok) {
    throw new Error('Registration failed');
  }
  
  return response.json();
};
```

#### Login
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

## Best Practices

### 1. Token Management
- Store tokens securely (httpOnly cookies recommended for web apps)
- Implement automatic token refresh
- Clear tokens on logout
- Use short-lived access tokens

### 2. Error Handling
- Implement proper error handling for all authentication flows
- Show user-friendly error messages
- Log security events for monitoring

### 3. Security
- Always use HTTPS in production
- Implement CSRF protection
- Validate all inputs
- Monitor for suspicious activity

### 4. Auth0 Integration
- Use state parameter for CSRF protection
- Implement proper callback handling
- Handle Auth0 errors gracefully
- Test with different Auth0 connection types

## Support and Troubleshooting

### Common Issues

1. **Token Expired**: Implement automatic refresh or redirect to login
2. **Invalid Credentials**: Check username/email and password
3. **Account Locked**: Wait for lockout period to expire
4. **Auth0 Callback Error**: Check Auth0 configuration and callback URLs
5. **Rate Limit Exceeded**: Implement exponential backoff

### Contact Information
- **Support Email**: support@devskyy.com
- **Documentation**: https://docs.devskyy.com
- **Status Page**: https://status.devskyy.com

---

*This documentation is maintained by the DevSkyy Platform Team. Last updated: 2024-10-24*
