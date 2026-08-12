# Phase 040 — Document Service

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

**Source**: `app/modules/logistics/inbound/reception_differences/application/document_service.py`

## 1. Overview

The document service handles DIF document generation and issuance workflow.

## 2. Document Issuance Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Approved │───▶│ Generate │───▶│  Store   │───▶│ Notify   │
│  Case    │    │   PDF    │    │ Document │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │               │               │               │
      ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Pending  │    │Generation│    │  Upload  │    │  Sent    │
│ Document │    │  Failed  │    │  Failed  │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 3. Implementation

```python
class DocumentService:
    """Document issuance workflow."""
    
    def __init__(
        self,
        case_repository: CaseRepository,
        pdf_generator: DIFGenerator,
        storage_service: StorageService,
        notification_service: NotificationService,
    ):
        self.case_repository = case_repository
        self.pdf_generator = pdf_generator
        self.storage_service = storage_service
        self.notification_service = notification_service
    
    async def issue_document(
        self,
        case_id: CaseId,
        user_id: str,
        tenant_id: str,
    ) -> DocumentResult:
        """
        Issue DIF document for approved case.
        
        Steps:
        1. Verify case is in PENDING_DOCUMENT status
        2. Generate PDF
        3. Upload to storage
        4. Update case status
        5. Notify stakeholders
        """
        case = await self.case_repository.get(case_id)
        
        # Verify tenant
        if case.tenant_id != tenant_id:
            raise TenantMismatchError()
        
        # Verify status
        if case.status != CaseStatus.PENDING_DOCUMENT:
            raise InvalidCaseStatusError(
                f"Case must be in PENDING_DOCUMENT status, got {case.status.value}"
            )
        
        # Verify case has items
        if not case.items:
            raise CaseValidationError("Case must have at least one item")
        
        # Generate document number
        doc_number = generate_document_number(
            datetime.utcnow().year,
            await self._get_next_sequence(),
        )
        
        # Generate PDF
        try:
            pdf_path = f"dif/{case.id}/{doc_number}.pdf"
            await self.pdf_generator.generate(case, pdf_path)
        except Exception as e:
            raise DocumentGenerationError(str(e))
        
        # Upload to storage
        try:
            document_url = await self.storage_service.upload(
                pdf_path,
                f"documents/dif/{doc_number}.pdf",
            )
        except Exception as e:
            raise DocumentGenerationError(f"Failed to upload: {e}")
        
        # Update case
        case.status = CaseStatus.DOCUMENT_ISSUED
        case.document_number = doc_number
        case.document_url = document_url
        case.document_issued_at = datetime.utcnow()
        case.document_issued_by = user_id
        case.updated_at = datetime.utcnow()
        
        # Recompute hash
        case.canonical_hash = canonical_hash_diff(case)
        
        # Save
        await self.case_repository.save(case)
        
        # Notify
        await self.notification_service.notify_document_issued(case)
        
        return DocumentResult(
            case_id=case_id,
            document_number=doc_number,
            document_url=document_url,
            issued_at=case.document_issued_at,
        )
```

## 4. Document Result

```python
@dataclass
class DocumentResult:
    case_id: CaseId
    document_number: str
    document_url: str
    issued_at: datetime
```

## 5. Document Numbering

```python
async def _get_next_sequence(self) -> int:
    """Get next document sequence number."""
    # Atomic counter in database
    result = await self.session.execute(
        text("SELECT nextval('dif_document_seq')")
    )
    return result.scalar()
```

---

**See also**: `13_pdf_generator.md` for PDF generation details
