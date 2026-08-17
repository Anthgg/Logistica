"""API endpoints for geographic administrative divisions (UBIGEO)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_active_user
from app.models.user import User
from app.modules.logistics.geography.schemas import (
    DepartmentResponse,
    DistrictResponse,
    ProvinceResponse,
    UbigeoHierarchyResponse,
)
from app.modules.logistics.geography.service import GeographyService

router = APIRouter(prefix="/geography", tags=["Geography / UBIGEO"])


@router.get(
    "/departments",
    response_model=list[DepartmentResponse],
    summary="List all 25 departments of Peru",
)
def list_departments(
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
) -> list[DepartmentResponse]:
    """Retrieve all 25 departments of Peru ordered by their 2-digit code."""
    depts = GeographyService.list_departments(db)
    return [DepartmentResponse.model_validate(d) for d in depts]


@router.get(
    "/departments/{department_code}/provinces",
    response_model=list[ProvinceResponse],
    summary="List provinces by department code",
)
def list_provinces_by_department(
    department_code: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
) -> list[ProvinceResponse]:
    """Retrieve all provinces for a given 2-digit department code."""
    provinces = GeographyService.list_provinces_by_department(db, department_code)
    return [ProvinceResponse.model_validate(p) for p in provinces]


@router.get(
    "/provinces/{province_code}/districts",
    response_model=list[DistrictResponse],
    summary="List districts by province code",
)
def list_districts_by_province(
    province_code: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
) -> list[DistrictResponse]:
    """Retrieve all districts for a given 4-digit province code."""
    districts = GeographyService.list_districts_by_province(db, province_code)
    return [DistrictResponse.model_validate(d) for d in districts]


@router.get(
    "/districts/{ubigeo_code}",
    response_model=UbigeoHierarchyResponse,
    summary="Resolve full hierarchy for a 6-digit UBIGEO code",
)
def get_district_by_ubigeo(
    ubigeo_code: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
) -> UbigeoHierarchyResponse:
    """Resolve a 6-digit UBIGEO code into its complete department, province, and district hierarchy."""
    resolved = GeographyService.resolve_ubigeo(db, ubigeo_code)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UBIGEO_NOT_FOUND",
                "message": f"Código UBIGEO '{ubigeo_code}' no existe en el catálogo.",
            },
        )
    return resolved
