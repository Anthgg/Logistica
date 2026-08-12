# Phase 040 — Step-Up Authentication

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

CRITICAL severity cases require step-up authentication (re-authentication) before approval or closure.

## 2. When Step-Up Auth Required

| Operation                    | Condition                              |
| ---------------------------- | -------------------------------------- |
| Approve CRITICAL case        | Severity == CRITICAL                   |
| Close CRITICAL case          | Severity == CRITICAL                   |
| Override severity to CRITICAL| New severity == CRITICAL               |
| Escalate to CRITICAL         | Severity becomes CRITICAL              |

## 3. Step-Up Auth Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │───▶│ Request  │───▶│  Step-Up │───▶│ Approved │
│  Action  │    │  Action  │    │  Auth    │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                       │              │
                       ▼              ▼
                 ┌──────────┐  ┌──────────┐
                 │  403     │  │  Re-auth │
                 │ Response │  │  Screen  │
                 └──────────┘  └──────────┘
```

## 4. Implementation

### 4.1 Check Step-Up Requirement

```python
async def check_step_up_requirement(
    case: CaseAggregate,
    user: User,
    action: str,
) -> bool:
    """Check if step-up auth is required."""
    if case.severity != Severity.CRITICAL:
        return False
    
    if action in ("approve", "close", "override_severity"):
        return not user.has_step_up_auth
    
    return False
```

### 4.2 Step-Up Auth Response

```json
{
  "error": {
    "code": "STEP_UP_AUTH_REQUIRED",
    "message": "Re-authentication required for CRITICAL severity case",
    "details": {
      "case_severity": "CRITICAL",
      "required_action": "step_up_authentication",
      "step_up_url": "/auth/step-up",
      "expires_in": 300
    }
  }
}
```

### 4.3 Step-Up Token

```python
def create_step_up_token(
    user_id: str,
    tenant_id: str,
    case_id: str,
) -> str:
    """Create short-lived step-up token."""
    return create_jwt(
        payload={
            "sub": user_id,
            "tenant_id": tenant_id,
            "case_id": case_id,
            "step_up": True,
            "exp": datetime.utcnow() + timedelta(minutes=5),
        },
        secret=STEP_UP_SECRET,
    )
```

## 5. Step-Up Auth Callback

```python
@router.post("/auth/step-up")
async def step_up_authenticate(
    credentials: StepUpCredentials,
    user: User = Depends(get_current_user),
):
    """Perform step-up authentication."""
    # Verify credentials (e.g., password, biometric)
    verified = await auth_service.verify_step_up(
        user.id,
        credentials,
    )
    
    if not verified:
        raise HTTPException(status_code=401)
    
    # Generate step-up token
    step_up_token = create_step_up_token(
        user.id,
        user.tenant_id,
        credentials.case_id,
    )
    
    return {"step_up_token": step_up_token}
```

## 6. Step-Up Credentials

```python
class StepUpCredentials(BaseModel):
    case_id: str
    password: Optional[str] = None
    totp_code: Optional[str] = None
    biometric_token: Optional[str] = None
```

## 7. Token Validation

```python
async def validate_step_up_token(
    token: str,
    case_id: str,
) -> bool:
    """Validate step-up token for specific case."""
    payload = decode_jwt(token, secret=STEP_UP_SECRET)
    
    return (
        payload.get("step_up") is True
        and payload.get("case_id") == case_id
        and payload.get("exp") > datetime.utcnow()
    )
```

---

**See also**: `41_security_overview.md` for security architecture
