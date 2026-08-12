"""Inbound logistics bounded context.

Phase 036 only models expected arrivals and reception appointments.  Physical
gate entry, unloading, receiving and inventory remain outside this package.
"""

def create_inbound_router():
    from app.modules.logistics.inbound.router import create_inbound_router as factory

    return factory()


__all__ = ["create_inbound_router"]
