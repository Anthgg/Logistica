import json
from uuid import UUID
from app.database.session import SessionLocal
from app.models.branch import Branch
from app.modules.logistics.company_profile.services.signer_service import SignerService
from app.modules.logistics.documents.application.lifecycle_service import DocumentLifecycleService
from app.modules.logistics.documents.models import DocumentTypeModel
from sqlalchemy import select

with SessionLocal() as db:
    branch = db.scalars(select(Branch)).first()
    print("Found Branch:", branch.id, branch.name, branch.organization_id)
    org_id = branch.organization_id

    dts = db.scalars(select(DocumentTypeModel)).all()
    signer_srv = SignerService(db)
    life_srv = DocumentLifecycleService(db)

    for dt in dts[:5]:
        print(f"\n--- Testing doc type: {dt.code} ---")
        try:
            resolved_signer = signer_srv.resolve_authorized_signer(
                organization_id=org_id,
                branch_id=branch.id,
                document_family="OUTBOUND",
                document_type_code=dt.code,
                requested_signer_id=None,
            )
            draft = life_srv.create_draft(
                organization_id=org_id,
                branch_id=branch.id,
                warehouse_id=None,
                doc_type_code=dt.code,
                source_resource_type="PREVIEW",
                source_resource_id=UUID("00000000-0000-0000-0000-000000000000"),
                source_operation_id=UUID("00000000-0000-0000-0000-000000000000"),
                title=f"VISTA PREVIA INSTITUCIONAL {dt.code}",
                structured_data={
                    "resolved_signer": resolved_signer,
                    "custom_data": {},
                    "is_preview": True,
                },
                sensitivity="INTERNAL",
                actor_id=None,
            )
            print("Draft created:", draft.id)
            pdf_bytes, filename = life_srv.preview_document(draft.id, actor_id=None)
            print(f"SUCCESS! PDF rendered: {filename} ({len(pdf_bytes)} bytes)")
        except Exception as e:
            print(f"FAILED for {dt.code}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
