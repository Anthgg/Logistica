"""Logistics domain — modular monolith entry point.

The router factory is imported lazily to avoid circular imports during
model registration.
"""

__all__ = ["create_logistics_router"]


def create_logistics_router():
    from app.modules.logistics.router import _create_logistics_router
    return _create_logistics_router()