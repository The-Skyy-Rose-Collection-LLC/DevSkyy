# DevSkyy Enterprise - User Creation Guide

## 🔐 Authentication System Overview

The DevSkyy Enterprise Platform now includes a complete user authentication system with:

- **Password Hashing**: Secure bcrypt password hashing
- **JWT Tokens**: Access and refresh token authentication
- **Role-Based Access**: Multiple user roles with different permissions
- **Username/Email Login**: Login with either username or email address
- **Protected Endpoints**: Secure API access with token validation

## 🚀 Creating Your User Account

### Method 1: Interactive User Creation (Recommended)

Run the interactive user creation utility:

```bash
cd DevSkyy
python create_user.py
```

This will prompt you for:
- **Username**: Your preferred username
- **Email**: Your email address
- **Password**: Your secure password (hidden input)
- **Role**: Choose from available roles

### Method 2: Command Line User Creation

You can also create users programmatically by modifying the `create_user.py` script or using Python directly:

```python
from security.jwt_auth import user_manager, UserRole

# Create your user
user = user_manager.create_user(
    email="your-email@example.com",
    username="your-username",
    password="your-secure-password",
    role=UserRole.ADMIN  # or UserRole.API_USER, etc.
)
```

## 👥 Available User Roles

1. **super_admin** - Full system access (all permissions)
2. **admin** - Administrative access (most permissions)
3. **developer** - Development access (code and API access)
4. **api_user** - Standard API access (default role)
5. **read_only** - Read-only access (limited permissions)

## 🔑 Authentication Methods

### 1. API Login (OAuth2 Password Flow)

**Endpoint**: `POST /api/v1/auth/login`

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-username&password=your-password"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Using Access Tokens

Include the access token in the Authorization header:

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Login with Username or Email

You can login using either your username or email address:

```bash
# Login with username
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-username&password=your-password"

# Login with email
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-email@example.com&password=your-password"
```

## 🛠️ Testing Your Authentication

### Test User Creation
```bash
cd DevSkyy
python create_user.py
```

### Test Authentication
```bash
cd DevSkyy
python create_user.py test
```

### List Existing Users
```bash
cd DevSkyy
python create_user.py list
```

## 🔒 Protected Endpoints

Once authenticated, you can access protected endpoints:

### Get Current User Info
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Access Agent APIs
```bash
curl -X POST "http://localhost:8000/api/v1/agents/customer-service/execute" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"query": "test"}}'
```

### GDPR Data Export
```bash
curl -X GET "http://localhost:8000/api/v1/gdpr/export" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔄 Token Refresh

When your access token expires, use the refresh token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## 📝 Example: Complete Authentication Flow

1. **Create User**:
```bash
python create_user.py
# Enter: username=myuser, email=me@example.com, password=mypassword123, role=admin
```

2. **Login**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=myuser&password=mypassword123"
```

3. **Use Token**:
```bash
# Save the access_token from step 2
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

4. **Access Protected Resources**:
```bash
curl -X GET "http://localhost:8000/api/v1/agents" \
  -H "Authorization: Bearer $TOKEN"
```

## 🚨 Security Features

- **Password Hashing**: All passwords are hashed using bcrypt
- **JWT Security**: Tokens are signed and verified
- **Token Expiration**: Access tokens expire in 30 minutes
- **Refresh Tokens**: Long-lived tokens for getting new access tokens
- **Role-Based Access**: Different permissions based on user roles
- **Account Status**: Users can be disabled/enabled

## 🔧 Troubleshooting

### Common Issues

1. **"User already exists"**: Choose a different username or email
2. **"Authentication failed"**: Check username/email and password
3. **"Token expired"**: Use refresh token to get new access token
4. **"Insufficient permissions"**: Check your user role and permissions

### Debug Commands

```bash
# Check if user exists
python -c "from security.jwt_auth import user_manager; print(user_manager.get_user_by_username('your-username'))"

# Test password verification
python -c "from security.jwt_auth import user_manager; print(user_manager.authenticate_user('your-username', 'your-password'))"
```

## 🎯 Next Steps

1. Create your user account using the interactive utility
2. Test authentication with the login endpoint
3. Use your access token to access protected endpoints
4. Explore the 57 AI agents available via the API
5. Build your applications using the authenticated API

The authentication system is now production-ready with proper password hashing, secure token handling, and comprehensive user management!
