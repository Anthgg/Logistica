"""Phase 039 receiving bounded context.

The router is intentionally imported lazily so model registration cannot form
a cycle through ``app.database.session``.
"""


def get_router():
    from .presentation.router import router
    return router


__all__ = ["get_router"]
