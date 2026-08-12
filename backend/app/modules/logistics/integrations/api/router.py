"""Integrations API — router factory."""

from fastapi import APIRouter, Depends

from app.modules.logistics.dependencies import get_logistics_current_user


def create_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/",
        summary="Integrations module status",
        description="Reports the integrations sub-module registration status.",
    )
    def integrations_status(
        _user=Depends(get_logistics_current_user),
    ) -> dict[str, str]:
        return {
            "status": "ok",
            "module": "integrations",
            "phase": "phase-003",
        }

    return router