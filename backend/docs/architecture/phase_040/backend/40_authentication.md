# Phase 040 — Authentication

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

All endpoints require authentication via JWT Bearer tokens. Some operations require step-up authentication.

## 2. Authentication Requirements

| Operation                    | Auth Level    | Description                      |
| ---------------------------- | ------------- | -------------------------------- |
| Read operations              | Standard JWT  | GET requests                     |
| Write operations             | Standard JWT  | POST/PUT/DELETE requests         |
| CRITICAL severity actions    | Step-up auth  | Re-authentication required       |
| Admin operations             | Admin role    | System admin only                |

## 3. JWT Token Structure

```json
{
  "sub": "user-123",
  "email": "user@example.com",
  "tenant_id": "tenant-001",
  "roles": ["operator", "reviewer"],
  "permissions": ["case:create", "case:read", "case:update"],
  "iat": 1690984800,
  "exp": 1690988400
}
```

## 4. Authentication Middleware

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Validate JWT and return current user."""
    try:
        payload = decode_jwt(credentials.credentials)
        return User(
            id=payload["sub"],
            email=payload["email"],
            tenant_id=payload["tenant_id"],
            roles=payload["roles"],
            permissions=payload["permissions"],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## 5. Step-Up Authentication

For CRITICAL severity cases:

```python
async def require_step_up_auth(
    user: User = Depends(get_current_user),
    case_id: str = Path(...),
) -> User:
    """Require step-up auth for critical operations."""
    case = await case_repository.get(case_id)
    
    if case.severity == Severity.CRITICAL:
        # Verify step-up token
        if not user.has_step_up_auth:
            raise HTTPException(
                status_code=403,
                detail="Step-up authentication required",
                headers={"X-Step-Up-Required": "true"},
            )
    
    return user
```

## 6. Step-Up Auth Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │───▶│ Request  │───▶│  Re-auth │───▶│ Approved │
│  Action  │    │  Step-up │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 7. Token Refresh

```python
async def refresh_token(
    refresh_token: str,
) -> dict:
    """Refresh access token."""
    payload = decode_refresh_token(refresh_token)
    
    new_access_token = create_access_token(
        user_id=payload["sub"],
        tenant_id=payload["tenant_id"],
        roles=payload["roles"],
    )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }
```

## 8. Authorization Headers

```http
Authorization: Bearer <access_token>
X-Tenant-ID: tenant-001
X-Request-ID: req_abc123
```

---

**See also**: `42_rbac_permissions.md` for role-based access control
