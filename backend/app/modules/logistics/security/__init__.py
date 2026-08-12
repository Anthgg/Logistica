"""Security module — step-up authentication for sensitive logistics operations."""

__all__ = ["create_security_router"]


def create_security_router():
    from app.modules.logistics.security.step_up_router import create_security_router as _r
    return _r()