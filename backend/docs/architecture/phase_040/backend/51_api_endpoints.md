# Phase 040 — API Endpoints

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Complete Endpoint Reference

### 1.1 Cases (14 endpoints)

| Method | Path                          | Description            | Auth            |
| ------ | ----------------------------- | ---------------------- | --------------- |
| POST   | `/cases`                      | Create case            | `case:create`   |
| GET    | `/cases`                      | List cases             | `case:read`     |
| GET    | `/cases/{case_id}`            | Get case               | `case:read`     |
| PUT    | `/cases/{case_id}`            | Update case            | `case:update`   |
| DELETE | `/cases/{case_id}`            | Delete case            | `case:delete`   |
| POST   | `/cases/{case_id}/submit`     | Submit for review      | `case:submit`   |
| POST   | `/cases/{case_id}/approve`    | Approve case           | `case:approve`  |
| POST   | `/cases/{case_id}/reject`     | Reject case            | `case:reject`   |
| POST   | `/cases/{case_id}/close`      | Close case             | `case:close`    |
| POST   | `/cases/{case_id}/cancel`     | Cancel case            | `case:cancel`   |
| POST   | `/cases/{case_id}/escalate`   | Escalate case          | `case:escalate` |
| POST   | `/cases/{case_id}/hold`       | Put on hold            | `case:hold`     |
| POST   | `/cases/{case_id}/resume`     | Resume from hold       | `case:resume`   |
| GET    | `/cases/{case_id}/history`    | Get case history       | `case:read`     |

### 1.2 Items (12 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| POST   | `/cases/{case_id}/items`                       | Add item             | `item:create`   |
| GET    | `/cases/{case_id}/items`                       | List items           | `item:read`     |
| GET    | `/cases/{case_id}/items/{item_id}`             | Get item             | `item:read`     |
| PUT    | `/cases/{case_id}/items/{item_id}`             | Update item          | `item:update`   |
| DELETE | `/cases/{case_id}/items/{item_id}`             | Remove item          | `item:delete`   |
| POST   | `/cases/{case_id}/items/{item_id}/formalize`   | Formalize item       | `item:formalize`|
| POST   | `/cases/{case_id}/items/{item_id}/reject`      | Reject item          | `item:reject`   |
| POST   | `/cases/{case_id}/items/{item_id}/resolve`     | Resolve item         | `item:resolve`  |
| POST   | `/cases/{case_id}/items/bulk-formalize`        | Bulk formalize       | `item:bulk_operate`|
| POST   | `/cases/{case_id}/items/bulk-reject`           | Bulk reject          | `item:bulk_operate`|
| POST   | `/cases/{case_id}/items/bulk-resolve`          | Bulk resolve         | `item:bulk_operate`|
| GET    | `/cases/{case_id}/items/statistics`            | Item statistics      | `item:read`     |

### 1.3 Evidence (8 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| POST   | `/cases/{case_id}/evidence`                    | Upload evidence      | `evidence:upload`|
| GET    | `/cases/{case_id}/evidence`                    | List evidence        | `evidence:read` |
| GET    | `/cases/{case_id}/evidence/{evidence_id}`      | Get evidence         | `evidence:read` |
| DELETE | `/cases/{case_id}/evidence/{evidence_id}`      | Delete evidence      | `evidence:delete`|
| POST   | `/cases/{case_id}/evidence/{evidence_id}/verify`| Verify evidence    | `evidence:verify`|
| POST   | `/cases/{case_id}/evidence/request`            | Request evidence     | `evidence:upload`|
| GET    | `/cases/{case_id}/evidence/requests`           | List evidence requests| `evidence:read` |
| POST   | `/cases/{case_id}/evidence/bulk-upload`        | Bulk upload          | `evidence:upload`|

### 1.4 Documents (6 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| POST   | `/cases/{case_id}/documents/issue`             | Issue DIF document   | `document:issue`|
| GET    | `/cases/{case_id}/documents`                   | List documents       | `document:read` |
| GET    | `/cases/{case_id}/documents/{doc_id}`          | Get document         | `document:read` |
| GET    | `/cases/{case_id}/documents/{doc_id}/download` | Download document    | `document:download`|
| POST   | `/cases/{case_id}/documents/{doc_id}/void`     | Void document        | `document:void` |
| GET    | `/cases/{case_id}/documents/number`            | Get next doc number  | `document:read` |

### 1.5 Snapshots (6 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| POST   | `/cases/{case_id}/snapshots`                   | Create snapshot      | `snapshot:create`|
| GET    | `/cases/{case_id}/snapshots`                   | List snapshots       | `snapshot:read` |
| GET    | `/cases/{case_id}/snapshots/{snapshot_id}`     | Get snapshot         | `snapshot:read` |
| GET    | `/cases/{case_id}/snapshots/latest`            | Get latest snapshot  | `snapshot:read` |
| GET    | `/cases/{case_id}/snapshots/compare`           | Compare snapshots    | `snapshot:read` |
| DELETE | `/cases/{case_id}/snapshots/{snapshot_id}`     | Delete snapshot      | `snapshot:create`|

### 1.6 Integrity (4 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| POST   | `/integrity/verify/{case_id}`                  | Verify case integrity| `integrity:verify`|
| POST   | `/integrity/verify-batch`                      | Batch verify         | `integrity:verify`|
| GET    | `/integrity/history/{case_id}`                 | Integrity history    | `integrity:verify`|
| GET    | `/integrity/statistics`                        | Integrity statistics | `integrity:verify`|

### 1.7 Statistics (8 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| GET    | `/stats/overview`                              | Overview statistics  | `stats:read`    |
| GET    | `/stats/by-status`                             | By status            | `stats:read`    |
| GET    | `/stats/by-severity`                           | By severity          | `stats:read`    |
| GET    | `/stats/by-category`                           | By category          | `stats:read`    |
| GET    | `/stats/by-supplier`                           | By supplier          | `stats:read`    |
| GET    | `/stats/by-warehouse`                          | By warehouse         | `stats:read`    |
| GET    | `/stats/timeline`                              | Timeline statistics  | `stats:read`    |
| GET    | `/stats/sla-compliance`                        | SLA compliance       | `stats:read`    |

### 1.8 Bulk Operations (6 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| POST   | `/bulk/create`                                 | Bulk create cases    | `case:create`   |
| POST   | `/bulk/update-status`                          | Bulk update status   | `case:update`   |
| POST   | `/bulk/assign-responsibility`                  | Bulk assign          | `case:assign`   |
| POST   | `/bulk/close`                                  | Bulk close           | `case:close`    |
| POST   | `/bulk/export`                                 | Export to CSV/Excel  | `case:read`     |
| POST   | `/bulk/import`                                 | Import from CSV/Excel| `case:create`   |

### 1.9 Workflows (6 endpoints)

| Method | Path                                           | Description          | Auth            |
| ------ | ---------------------------------------------- | -------------------- | --------------- |
| GET    | `/cases/{case_id}/workflow/transitions`        | Get allowed transitions| `case:read`   |
| POST   | `/cases/{case_id}/workflow/transition`         | Perform transition   | `case:update`   |
| GET    | `/cases/{case_id}/workflow/history`            | Transition history   | `case:read`     |
| GET    | `/cases/{case_id}/workflow/approvals`          | Approval history     | `case:read`     |
| POST   | `/cases/{case_id}/workflow/approve`            | Approve              | `case:approve`  |
| POST   | `/cases/{case_id}/workflow/reject`             | Reject               | `case:reject`   |

---

**See also**: `36_router.md` for implementation details
