# JWT Authentication Middleware Usage Guide

This document explains how to use the JWT authentication middleware in the CifraPartit API.

## Overview

The authentication middleware provides three dependency functions that can be used in FastAPI route handlers to protect endpoints and inject authenticated user context.

## Available Dependencies

### 1. `get_current_user` - Required Authentication

Use this dependency when an endpoint requires authentication. It will:
- Extract and validate the JWT token from the Authorization header
- Return the authenticated User object
- Raise 401 Unauthorized if token is invalid or missing

**Example:**

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get the current user's profile."""
    return {
        "email": current_user.email,
        "subscription_tier": current_user.subscription_tier,
        "is_verified": current_user.is_verified
    }
```

### 2. `get_current_active_user` - Required Verified User

Use this dependency when an endpoint requires a verified user account. It will:
- Validate authentication (same as `get_current_user`)
- Check if the user's email is verified
- Raise 403 Forbidden if user is not verified

**Example:**

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/transcriptions")
async def create_transcription(
    current_user: User = Depends(get_current_active_user)
):
    """Create a new transcription (requires verified account)."""
    # Only verified users can create transcriptions
    return {"message": "Transcription created", "user_id": current_user.id}
```

### 3. `get_optional_user` - Optional Authentication

Use this dependency when an endpoint should work for both authenticated and anonymous users. It will:
- Return the User object if a valid token is provided
- Return None if no token or invalid token is provided
- Never raise authentication errors

**Example:**

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_optional_user
from app.models.user import User
from typing import Optional

router = APIRouter()

@router.get("/features")
async def list_features(current_user: Optional[User] = Depends(get_optional_user)):
    """List available features (different for authenticated users)."""
    if current_user:
        # Show premium features for authenticated users
        return {
            "features": ["basic", "advanced", "premium"],
            "user_tier": current_user.subscription_tier
        }
    else:
        # Show only basic features for anonymous users
        return {"features": ["basic"]}
```

## Token Refresh Mechanism

The API provides a token refresh endpoint to obtain new access tokens without requiring the user to log in again.

### How It Works

1. When a user logs in, they receive both an `access_token` and a `refresh_token`
2. Access tokens expire after 30 minutes (configurable)
3. Refresh tokens expire after 7 days
4. Before the access token expires, the client can use the refresh token to get a new pair

### Refresh Token Endpoint

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Client-Side Implementation Example

```javascript
// Store tokens after login
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const { access_token, refresh_token } = await loginResponse.json();
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// Refresh token before it expires
async function refreshAccessToken() {
  const refresh_token = localStorage.getItem('refresh_token');
  
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });
  
  if (response.ok) {
    const { access_token, refresh_token: new_refresh_token } = await response.json();
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', new_refresh_token);
    return access_token;
  } else {
    // Refresh failed, redirect to login
    window.location.href = '/login';
  }
}

// Use access token in API requests
async function makeAuthenticatedRequest(url, options = {}) {
  let access_token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${access_token}`
    }
  });
  
  // If token expired, refresh and retry
  if (response.status === 401) {
    access_token = await refreshAccessToken();
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${access_token}`
      }
    });
  }
  
  return response;
}
```

## Security Considerations

### HTTPS Requirement (Requirement 23.2)

All authentication endpoints and protected routes MUST be accessed over HTTPS in production. The middleware validates JWT tokens but relies on HTTPS to prevent token interception.

**Production Configuration:**
- Configure your reverse proxy (nginx, Apache) to enforce HTTPS
- Redirect all HTTP traffic to HTTPS
- Use valid SSL/TLS certificates

### Token Storage

**Best Practices:**
- Store tokens in httpOnly cookies (most secure) or localStorage
- Never store tokens in regular cookies accessible to JavaScript
- Clear tokens on logout
- Implement token rotation (refresh tokens)

### Rate Limiting

The refresh endpoint is protected by rate limiting (5 attempts per 15 minutes per IP) to prevent abuse.

## Testing

The middleware includes comprehensive tests in `backend/tests/test_auth_middleware.py`:

```bash
# Run middleware tests
pytest backend/tests/test_auth_middleware.py -v

# Run all auth tests
pytest backend/tests/test_auth*.py -v
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 10.4**: User authentication with JWT tokens
- **Requirement 23.2**: HTTPS transmission (enforced at deployment level)

The middleware provides:
✅ Token validation and user context injection
✅ Token refresh mechanism with 7-day refresh tokens
✅ Three authentication levels (required, verified-only, optional)
✅ Proper error handling with appropriate HTTP status codes
✅ Rate limiting on refresh endpoint
