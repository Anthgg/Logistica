# Phase 040 — RBAC Permissions

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

34 permissions controlling access to module operations.

## 2. Permission List

### 2.1 Case Permissions (14)

| Permission              | Description                              |
| ----------------------- | ---------------------------------------- |
| `case:create`           | Create new cases                         |
| `case:read`             | View case details                        |
| `case:update`           | Update case details                      |
| `case:delete`           | Delete cases                             |
| `case:submit`           | Submit for review                        |
| `case:approve`          | Approve cases                            |
| `case:reject`           | Reject cases                             |
| `case:close`            | Close cases                              |
| `case:cancel`           | Cancel cases                             |
| `case:escalate`         | Escalate to management                   |
| `case:hold`             | Put on hold                              |
| `case:resume`           | Resume from hold                         |
| `case:assign`           | Assign responsibility                    |
| `case:override_severity`| Override severity level                  |

### 2.2 Item Permissions (8)

| Permission              | Description                              |
| ----------------------- | ---------------------------------------- |
| `item:create`           | Add items to case                        |
| `item:read`             | View item details                        |
| `item:update`           | Update item details                      |
| `item:delete`           | Remove items                             |
| `item:formalize`        | Formalize candidate items                |
| `item:reject`           | Reject items                             |
| `item:resolve`          | Resolve items                            |
| `item:bulk_operate`     | Perform bulk operations                  |

### 2.3 Evidence Permissions (4)

| Permission              | Description                              |
| ----------------------- | ---------------------------------------- |
| `evidence:upload`       | Upload evidence files                    |
| `evidence:read`         | View evidence                            |
| `evidence:delete`       | Delete evidence                          |
| `evidence:verify`       | Verify evidence                          |

### 2.4 Document Permissions (4)

| Permission              | Description                              |
| ----------------------- | ---------------------------------------- |
| `document:issue`        | Issue DIF documents                      |
| `document:read`         | View documents                           |
| `document:download`     | Download documents                       |
| `document:void`         | Void documents                           |

### 2.5 System Permissions (4)

| Permission              | Description                              |
| ----------------------- | ---------------------------------------- |
| `snapshot:create`       | Create snapshots                         |
| `snapshot:read`         | View snapshots                           |
| `integrity:verify`      | Verify integrity                         |
| `stats:read`            | View statistics                          |

## 3. Role Assignments

### 3.1 Operator

| Permission              | Assigned |
| ----------------------- | -------- |
| `case:create`           | ✓        |
| `case:read`             | ✓        |
| `item:create`           | ✓        |
| `item:read`             | ✓        |
| `item:update`           | ✓        |
| `evidence:upload`       | ✓        |
| `evidence:read`         | ✓        |
| `document:read`         | ✓        |
| `document:download`     | ✓        |

### 3.2 Supervisor

| Permission              | Assigned |
| ----------------------- | -------- |
| All Operator permissions | ✓        |
| `case:submit`           | ✓        |
| `case:approve`          | ✓        |
| `case:reject`           | ✓        |
| `case:hold`             | ✓        |
| `case:resume`           | ✓        |
| `item:formalize`        | ✓        |
| `item:reject`           | ✓        |
| `evidence:verify`       | ✓        |
| `document:issue`        | ✓        |

### 3.3 Manager

| Permission              | Assigned |
| ----------------------- | -------- |
| All Supervisor permissions | ✓       |
| `case:escalate`         | ✓        |
| `case:assign`           | ✓        |
| `case:override_severity`| ✓        |
| `item:bulk_operate`     | ✓        |
| `snapshot:create`       | ✓        |
| `integrity:verify`      | ✓        |
| `stats:read`            | ✓        |

### 3.4 Admin

| Permission              | Assigned |
| ----------------------- | -------- |
| All Manager permissions | ✓        |
| `case:delete`           | ✓        |
| `case:cancel`           | ✓        |
| `case:close`            | ✓        |
| `item:delete`           | ✓        |
| `evidence:delete`       | ✓        |
| `document:void`         | ✓        |

## 4. Permission Checking

```python
def require_permission(permission: str):
    """Decorator to check user permission."""
    async def decorator(
        user: User = Depends(get_current_user),
    ):
        if permission not in user.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permission: {permission}"
            )
        return user
    return decorator

# Usage
@router.post("/cases")
async def create_case(
    user: User = Depends(require_permission("case:create")),
):
    ...
```

---

**See also**: `40_authentication.md` for authentication details
