# Phase 040 — Evidence Workflow

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

Evidence links support documentation of reception differences. They are attached to cases and used during review and approval processes.

## 2. Evidence Types

| Format      | Description                  | Max Size | Allowed Extensions          |
| ----------- | ---------------------------- | -------- | --------------------------- |
| `PHOTO`     | Photographic evidence        | 10 MB    | .jpg, .jpeg, .png, .webp   |
| `DOCUMENT`  | PDF, Word, etc.              | 25 MB    | .pdf, .docx, .xlsx         |
| `VIDEO`     | Video evidence               | 100 MB   | .mp4, .mov, .avi           |
| `AUDIO`     | Audio recordings             | 25 MB    | .mp3, .wav, .m4a           |
| `OTHER`     | Other formats                | 10 MB    | *                          |

## 3. Evidence Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Uploaded │───▶│ Verified │───▶│ Accepted │───▶│ Archived │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │               │               │
      ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Rejected │    │ Pending  │    │ Deleted  │
└──────────┘    └──────────┘    └──────────┘
```

## 4. Upload Process

```python
async def upload_evidence(
    case_id: CaseId,
    file: UploadFile,
    evidence_type: EvidenceFormat,
    description: Optional[str],
) -> EvidenceLink:
    """
    Upload evidence file for a case.
    
    Steps:
    1. Validate file type and size
    2. Generate unique filename
    3. Upload to storage (S3/local)
    4. Create evidence record
    5. Attach to case
    """
    # Validate
    validate_file_type(file.filename, evidence_type)
    validate_file_size(file.size, evidence_type)
    
    # Generate path
    filename = f"{case_id}/{uuid4()}_{file.filename}"
    
    # Upload
    url = await storage_service.upload(filename, file)
    
    # Create record
    evidence = EvidenceLink(
        id=uuid4(),
        case_id=case_id,
        url=url,
        evidence_type=evidence_type,
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.utcnow(),
    )
    
    # Attach to case
    case = await case_repository.get(case_id)
    case.evidence_links.append(evidence)
    await case_repository.save(case)
    
    emit_event(EvidenceAttached, case_id=case_id, evidence_id=evidence.id)
    
    return evidence
```

## 5. Evidence Validation Rules

```python
EVIDENCE_RULES = {
    EvidenceFormat.PHOTO: {
        "max_size_mb": 10,
        "extensions": [".jpg", ".jpeg", ".png", ".webp"],
        "required_for": [
            DifferenceCategory.DAMAGED,
            DifferenceCategory.PACKAGING_DAMAGE,
        ],
    },
    EvidenceFormat.DOCUMENT: {
        "max_size_mb": 25,
        "extensions": [".pdf", ".docx", ".xlsx"],
        "required_for": [
            DifferenceCategory.MISSING_DOCUMENTATION,
        ],
    },
    EvidenceFormat.VIDEO: {
        "max_size_mb": 100,
        "extensions": [".mp4", ".mov", ".avi"],
        "required_for": [],
    },
}
```

## 6. Required Evidence by Category

| Category                   | Minimum Evidence                              |
| -------------------------- | --------------------------------------------- |
| `QUANTITY_SHORTAGE`        | 1 photo of delivery note                      |
| `QUANTITY_SURPLUS`         | 1 photo of received goods                     |
| `DAMAGED`                  | 2+ photos of damage                           |
| `WRONG_ITEM`               | 1 photo of wrong item + 1 of label            |
| `MISSING_DOCUMENTATION`    | Document listing missing items                 |
| `QUALITY_ISSUE`            | 2+ photos + quality report                    |
| `PACKAGING_DAMAGE`         | 2+ photos of packaging                        |
| `EXPIRED`                  | 1 photo of expiry date                        |
| `MISLABELED`               | 1 photo of label + 1 of actual product        |

## 7. Evidence Verification

```python
def verify_evidence(case: CaseAggregate) -> bool:
    """
    Verify case has required evidence for its category.
    
    Returns True if all required evidence is present.
    """
    category = case.category
    required = EVIDENCE_RULES.get(category, {}).get("required_for", [])
    
    if not required:
        return True
    
    attached_types = {e.evidence_type for e in case.evidence_links}
    
    for required_type in required:
        if required_type not in attached_types:
            return False
    
    return True
```

## 8. Evidence in Review Process

During case review, approvers can:
1. View all attached evidence
2. Request additional evidence
3. Accept or reject evidence
4. Add comments to evidence items

```python
def request_additional_evidence(
    case: CaseAggregate,
    requested_types: List[EvidenceFormat],
    reason: str,
) -> None:
    """Request additional evidence from case creator."""
    case.status = CaseStatus.AWAITING_EVIDENCE
    case.evidence_requests.append({
        "types": requested_types,
        "reason": reason,
        "requested_by": current_user.id,
        "requested_at": datetime.utcnow(),
    })
```

---

**See also**: `26_notification_service.md` for evidence request notifications
