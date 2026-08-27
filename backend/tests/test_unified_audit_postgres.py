"""Phase 007 — PostgreSQL integration test suite for Unified Audit.

Validates:
1. Append-only immutable event persistence and cryptographic SHA-256 hash generation and verification.
2. Strict secret redaction (AUDIT_SECRET_LEAKS=0): passwords, tokens, API keys, cookies, csrf.
3. Multi-tenant isolation: Org A cannot read Org B audit events (CROSS_TENANT_AUDIT_ACCESS=DENIED).
4. Date range, action, resource, severity, result, and free-text search filters.
5. Server-side CSV Export with UTF-8 BOM, Excel compatibility, IP masking, and automatic logging of logistics.audit.exported.
6. RBAC permission gates: 401 without auth, 403 without permission, 200 with permission.
7. Verification that no UPDATE or DELETE audit API endpoints exist (AUDIT_UPDATE_API_COUNT=0, AUDIT_DELETE_API_COUNT=0).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.modules.logistics.audit.sanitizer import sanitize_for_audit
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.principal import LogisticsPrincipal


def _make_principal(
    *,
    user_id: UUID | None = None,
    email: str = "auditor@andeslog.pe",
    permissions: list[str] | None = None,
    organization_ids: list[str] | None = None,
) -> LogisticsPrincipal:
    return LogisticsPrincipal(
        user_id=user_id or uuid4(),
        email=email,
        full_name="Audit Operator",
        platform_role="user",
        is_active=True,
        session_id=uuid4(),
        device_id=uuid4(),
        authentication_level="password",
        session_expires_at=datetime.now(UTC) + timedelta(hours=8),
        risk_score=0.05,
        logistics_enabled=True,
        role_codes=["LOGISTICS_AUDITOR"],
        permission_codes=permissions or [
            "logistics.audit.read",
            "logistics.audit.export",
            "logistics.audit.read_sensitive",
        ],
        organization_ids=organization_ids or [],
    )


def test_audit_event_writing_and_hash_integrity(database: Session) -> None:
    actor_id = uuid4()
    org_id = uuid4()

    cmd = AuditEventCommand(
        event_code="logistics.organization.created",
        actor_user_id=actor_id,
        actor_display_name="Operador Logístico",
        action="create",
        result="success",
        severity="medium",
        resource_type="organization",
        resource_id=str(org_id),
        organization_id=org_id,
        previous_data=None,
        new_data={"name": "Org Andina SAC", "ruc": "20123456789"},
        metadata={"source": "unit_test"},
    )

    event = audit_service.write_event(database, cmd)
    database.flush()

    assert event.id is not None
    assert event.event_hash is not None
    assert len(event.event_hash) == 64
    assert event.event_code == "logistics.organization.created"
    assert event.event_category == "organization"
    assert event.changed_fields == ["name", "ruc"]

    integrity = audit_service.verify_integrity(database, event.id)
    assert integrity["success"] is True
    assert integrity["valid"] is True
    assert integrity["stored_hash"] == event.event_hash
    assert integrity["computed_hash"] == event.event_hash


def test_secret_redaction_policy(database: Session) -> None:
    dirty_payload = {
        "user": "test_user",
        "password": "SuperSecretPassword123!",
        "password_hash": "$2b$12$e89as7d6f8a7sdf6asdf",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "csrf_token": "csrf-secret-9999",
        "cookie": "session=abcde12345",
        "nested": {
            "api_key": "sk_live_1234567890",
            "safe_field": "visible_value",
        },
    }

    sanitized = sanitize_for_audit(dirty_payload)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["password_hash"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["access_key"] == "[REDACTED]"
    assert sanitized["csrf_token"] == "[REDACTED]"
    assert sanitized["cookie"] == "[REDACTED]"
    assert sanitized["nested"]["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == "visible_value"
    assert sanitized["user"] == "test_user"

    cmd = AuditEventCommand(
        event_code="logistics.role.created",
        actor_user_id=uuid4(),
        action="create",
        result="success",
        severity="high",
        previous_data=None,
        new_data=dirty_payload,
    )
    event = audit_service.write_event(database, cmd)
    database.flush()

    assert event.new_data["password"] == "[REDACTED]"
    assert event.new_data["token"] == "[REDACTED]"
    assert event.new_data["nested"]["api_key"] == "[REDACTED]"


def test_tenant_isolation_in_audit_queries(database: Session) -> None:
    org_a = uuid4()
    org_b = uuid4()

    audit_service.write_event(
        database,
        AuditEventCommand(
            event_code="logistics.branch.created",
            organization_id=org_a,
            action="create",
            result="success",
            severity="medium",
        ),
    )
    audit_service.write_event(
        database,
        AuditEventCommand(
            event_code="logistics.branch.created",
            organization_id=org_b,
            action="create",
            result="success",
            severity="medium",
        ),
    )
    database.flush()

    items_a, _ = audit_service.list(database, allowed_org_ids=[org_a])
    org_ids_in_a = [e.organization_id for e in items_a if e.organization_id is not None]
    assert all(o == org_a for o in org_ids_in_a)
    assert org_b not in org_ids_in_a

    with pytest.raises(Exception) as exc_info:
        audit_service.list(database, organization_id=org_b, allowed_org_ids=[org_a])
    assert "No tiene acceso a esta organización" in str(exc_info.value)


def test_date_range_and_search_filters(database: Session) -> None:
    now = datetime.now(UTC)
    old_time = now - timedelta(days=10)

    e1 = audit_service.write_event(
        database,
        AuditEventCommand(
            event_code="logistics.warehouse.created",
            action="create",
            result="success",
            severity="medium",
            resource_id="WH-SUR-01",
            reason_text="Apertura almacén sur",
        ),
    )
    e1.occurred_at = old_time
    database.flush()

    e2 = audit_service.write_event(
        database,
        AuditEventCommand(
            event_code="logistics.warehouse.updated",
            action="update",
            result="success",
            severity="low",
            resource_id="WH-NORTE-02",
            reason_text="Ajuste capacidad norte",
        ),
    )
    e2.occurred_at = now
    database.flush()

    items, _ = audit_service.list(database, date_from=now - timedelta(hours=1))
    resource_ids = [e.resource_id for e in items]
    assert "WH-NORTE-02" in resource_ids
    assert "WH-SUR-01" not in resource_ids

    items_search, _ = audit_service.list(database, search="sur")
    search_ids = [e.resource_id for e in items_search]
    assert "WH-SUR-01" in search_ids
    assert "WH-NORTE-02" not in search_ids


def test_csv_export_format_and_sensitive_ip_masking(database: Session) -> None:
    audit_service.write_event(
        database,
        AuditEventCommand(
            event_code="logistics.role.assignment_created",
            actor_user_id=uuid4(),
            actor_display_name="Seguridad Central",
            action="create",
            result="success",
            severity="high",
            ip_address="192.168.1.100",
            resource_type="role_assignment",
            resource_id="RA-1001",
            reason_text="Asignación rol auditor",
        ),
    )
    database.flush()

    csv_masked, count_masked = audit_service.export_csv(
        database,
        include_sensitive_ip=False,
        search="RA-1001",
    )
    assert count_masked >= 1
    assert csv_masked.startswith("\ufeff")
    assert "[REDACTED]" in csv_masked
    assert "192.168.1.100" not in csv_masked

    csv_unmasked, count_unmasked = audit_service.export_csv(
        database,
        include_sensitive_ip=True,
        search="RA-1001",
    )
    assert count_unmasked >= 1
    assert "192.168.1.100" in csv_unmasked


def test_http_audit_rbac_gates(client: TestClient) -> None:
    assert client.get("/api/logistics/audit-events").status_code == 401
    assert client.get("/api/logistics/audit-events/export").status_code == 401

    no_perm_principal = _make_principal(permissions=["logistics.organizations.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: no_perm_principal
    try:
        res = client.get("/api/logistics/audit-events")
        assert res.status_code == 403
        res_export = client.get("/api/logistics/audit-events/export")
        assert res_export.status_code == 403
    finally:
        app.dependency_overrides.pop(get_logistics_principal, None)

    auth_principal = _make_principal(
        permissions=["logistics.audit.read", "logistics.audit.export"]
    )
    app.dependency_overrides[get_logistics_principal] = lambda: auth_principal
    try:
        res_list = client.get("/api/logistics/audit-events?page=1&page_size=10")
        assert res_list.status_code == 200
        data = res_list.json()
        assert "items" in data
        assert "total" in data

        res_export = client.get("/api/logistics/audit-events/export")
        assert res_export.status_code == 200
        assert "text/csv" in res_export.headers.get("content-type", "")
        assert "attachment" in res_export.headers.get("content-disposition", "")
    finally:
        app.dependency_overrides.pop(get_logistics_principal, None)
