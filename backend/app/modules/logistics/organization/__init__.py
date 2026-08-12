"""Organization module — lazy router factory."""

__all__ = ["create_organization_router"]


def create_organization_router():
    from app.modules.logistics.organization.api.router import _create_organization_router
    return _create_organization_router()