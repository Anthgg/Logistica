"""Routes API — router factory."""

from fastapi import APIRouter, Depends

from app.modules.logistics.dependencies import get_logistics_current_user


def create_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/",
        summary="Routes module status",
        description="Reports the routes sub-module registration status.",
    )
    def routes_status(
        _user=Depends(get_logistics_current_user),
    ) -> dict[str, str]:
        return {
            "status": "ok",
            "module": "routes",
            "phase": "phase-003",
        }

    return router