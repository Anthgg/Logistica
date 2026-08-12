from fastapi import APIRouter, Depends, Request

from app.core.permissions import RESEARCH_ADMIN_ROLES
from app.dependencies.permissions import require_permissions
from app.models.user import User
from app.schemas.model_status import (
    ModelComponentStatusRead,
    ModelStatusRead,
    ModelStatusResponse,
)
from app.services.model_loader_service import ModelLoaderService

router = APIRouter(prefix="/models", tags=["Model Runtime"])


@router.get(
    "/status",
    response_model=ModelStatusResponse,
    summary="Consultar estado sanitizado de modelos",
)
def model_status(
    request: Request,
    _: User = Depends(require_permissions(*RESEARCH_ADMIN_ROLES)),
) -> ModelStatusResponse:
    loader: ModelLoaderService = request.app.state.model_loader
    status = loader.status
    return ModelStatusResponse(
        models=ModelStatusRead(
            global_status=status.global_status,
            facial=ModelComponentStatusRead(
                available=status.facial.available,
                loaded=status.facial.loaded,
                checksum_valid=status.facial.checksum_valid,
                version=status.facial.version,
                reason_code=status.facial.reason_code,
            ),
            pad=ModelComponentStatusRead(
                available=status.pad.available,
                loaded=status.pad.loaded,
                checksum_valid=status.pad.checksum_valid,
                version=status.pad.version,
                reason_code=status.pad.reason_code,
            ),
            behavioral_available=status.behavioral_available,
            behavioral_loaded=status.behavioral_loaded,
            behavioral_versions=list(status.behavioral_versions),
            device=status.device,
            loaded_at=status.loaded_at,
            registry_checksum_valid=status.registry_checksum_valid,
            fusion_loaded=status.fusion_loaded,
            normalization_loaded=status.normalization_loaded,
            errors=list(status.errors),
        )
    )
