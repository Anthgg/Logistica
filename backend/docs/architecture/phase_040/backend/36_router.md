# Phase 040 — Router

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/presentation/router.py`

## 1. Overview

64 API endpoints organized by resource.

## 2. Endpoint Groups

| Group               | Endpoints | Prefix                       |
| ------------------- | --------- | ---------------------------- |
| Cases               | 14        | `/api/v1/reception-differences/cases` |
| Items               | 12        | `/api/v1/reception-differences/cases/{id}/items` |
| Evidence            | 8         | `/api/v1/reception-differences/cases/{id}/evidence` |
| Documents           | 6         | `/api/v1/reception-differences/cases/{id}/documents` |
| Snapshots           | 6         | `/api/v1/reception-differences/cases/{id}/snapshots` |
| Integrity           | 4         | `/api/v1/reception-differences/integrity` |
| Statistics          | 8         | `/api/v1/reception-differences/stats` |
| Bulk Operations     | 6         | `/api/v1/reception-differences/bulk` |
| Workflows           | 6         | `/api/v1/reception-differences/cases/{id}/workflow` |
| **Total**           | **64**    |                              |

## 3. Case Endpoints

| Method  | Path                           | Description                |
| ------- | ------------------------------ | -------------------------- |
| POST    | `/cases`                       | Create case                |
| GET     | `/cases`                       | List cases                 |
| GET     | `/cases/{case_id}`             | Get case                   |
| PUT     | `/cases/{case_id}`             | Update case                |
| DELETE  | `/cases/{case_id}`             | Delete case                |
| POST    | `/cases/{case_id}/submit`      | Submit for review          |
| POST    | `/cases/{case_id}/approve`     | Approve case               |
| POST    | `/cases/{case_id}/reject`      | Reject case                |
| POST    | `/cases/{case_id}/close`       | Close case                 |
| POST    | `/cases/{case_id}/cancel`      | Cancel case                |
| POST    | `/cases/{case_id}/escalate`    | Escalate case              |
| POST    | `/cases/{case_id}/hold`        | Put on hold                |
| POST    | `/cases/{case_id}/resume`      | Resume from hold           |
| GET     | `/cases/{case_id}/history`     | Get case history           |

## 4. Item Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| POST    | `/cases/{case_id}/items`                        | Add item               |
| GET     | `/cases/{case_id}/items`                        | List items             |
| GET     | `/cases/{case_id}/items/{item_id}`              | Get item               |
| PUT     | `/cases/{case_id}/items/{item_id}`              | Update item            |
| DELETE  | `/cases/{case_id}/items/{item_id}`              | Remove item            |
| POST    | `/cases/{case_id}/items/{item_id}/formalize`    | Formalize item         |
| POST    | `/cases/{case_id}/items/{item_id}/reject`       | Reject item            |
| POST    | `/cases/{case_id}/items/{item_id}/resolve`      | Resolve item           |
| POST    | `/cases/{case_id}/items/bulk-formalize`         | Bulk formalize        |
| POST    | `/cases/{case_id}/items/bulk-reject`            | Bulk reject           |
| POST    | `/cases/{case_id}/items/bulk-resolve`           | Bulk resolve          |
| GET     | `/cases/{case_id}/items/statistics`             | Item statistics        |

## 5. Evidence Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| POST    | `/cases/{case_id}/evidence`                     | Upload evidence        |
| GET     | `/cases/{case_id}/evidence`                     | List evidence          |
| GET     | `/cases/{case_id}/evidence/{evidence_id}`       | Get evidence           |
| DELETE  | `/cases/{case_id}/evidence/{evidence_id}`       | Delete evidence        |
| POST    | `/cases/{case_id}/evidence/{evidence_id}/verify`| Verify evidence        |
| POST    | `/cases/{case_id}/evidence/request`             | Request evidence       |
| GET     | `/cases/{case_id}/evidence/requests`            | List evidence requests |
| POST    | `/cases/{case_id}/evidence/bulk-upload`         | Bulk upload            |

## 6. Document Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| POST    | `/cases/{case_id}/documents/issue`              | Issue DIF document     |
| GET     | `/cases/{case_id}/documents`                    | List documents         |
| GET     | `/cases/{case_id}/documents/{doc_id}`           | Get document           |
| GET     | `/cases/{case_id}/documents/{doc_id}/download`  | Download document      |
| POST    | `/cases/{case_id}/documents/{doc_id}/void`      | Void document          |
| GET     | `/cases/{case_id}/documents/number`             | Get next doc number    |

## 7. Snapshot Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| POST    | `/cases/{case_id}/snapshots`                    | Create snapshot        |
| GET     | `/cases/{case_id}/snapshots`                    | List snapshots         |
| GET     | `/cases/{case_id}/snapshots/{snapshot_id}`      | Get snapshot           |
| GET     | `/cases/{case_id}/snapshots/latest`             | Get latest snapshot    |
| GET     | `/cases/{case_id}/snapshots/compare`            | Compare snapshots      |
| DELETE  | `/cases/{case_id}/snapshots/{snapshot_id}`      | Delete snapshot        |

## 8. Integrity Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| POST    | `/integrity/verify/{case_id}`                   | Verify case integrity  |
| POST    | `/integrity/verify-batch`                       | Batch verify           |
| GET     | `/integrity/history/{case_id}`                  | Integrity history      |
| GET     | `/integrity/statistics`                         | Integrity statistics   |

## 9. Statistics Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| GET     | `/stats/overview`                               | Overview statistics    |
| GET     | `/stats/by-status`                              | By status              |
| GET     | `/stats/by-severity`                            | By severity            |
| GET     | `/stats/by-category`                            | By category            |
| GET     | `/stats/by-supplier`                            | By supplier            |
| GET     | `/stats/by-warehouse`                           | By warehouse           |
| GET     | `/stats/timeline`                               | Timeline statistics    |
| GET     | `/stats/sla-compliance`                         | SLA compliance         |

## 10. Bulk Operation Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| POST    | `/bulk/create`                                  | Bulk create cases      |
| POST    | `/bulk/update-status`                           | Bulk update status     |
| POST    | `/bulk/assign-responsibility`                   | Bulk assign            |
| POST    | `/bulk/close`                                   | Bulk close             |
| POST    | `/bulk/export`                                  | Export to CSV/Excel    |
| POST    | `/bulk/import`                                  | Import from CSV/Excel  |

## 11. Workflow Endpoints

| Method  | Path                                            | Description            |
| ------- | ----------------------------------------------- | ---------------------- |
| GET     | `/cases/{case_id}/workflow/transitions`         | Get allowed transitions|
| POST    | `/cases/{case_id}/workflow/transition`          | Perform transition     |
| GET     | `/cases/{case_id}/workflow/history`             | Transition history     |
| GET     | `/cases/{case_id}/workflow/approvals`           | Approval history       |
| POST    | `/cases/{case_id}/workflow/approve`             | Approve                |
| POST    | `/cases/{case_id}/workflow/reject`              | Reject                 |

---

**See also**: `37_request_response_examples.md` for examples
