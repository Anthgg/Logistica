"""Audit module — unified logistics audit events."""

__all__ = ["create_audit_event_router"]


def create_audit_event_router():
    from app.modules.logistics.audit.api.router import create_audit_event_router as _r
    return _r()