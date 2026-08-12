"""RBAC module — logistics roles, scope rules, assignments and conflicts.

Router factory is imported lazily to avoid circular imports.
"""

__all__ = ["create_rbac_router"]


def create_rbac_router():
    from app.modules.logistics.rbac.api.router import _create_rbac_router
    return _create_rbac_router()