"""Domain service for geographic administrative divisions and UBIGEO lookup."""

from sqlalchemy.orm import Session

from app.modules.logistics.geography.models import GeoDepartment, GeoDistrict, GeoProvince
from app.modules.logistics.geography.schemas import UbigeoHierarchyResponse


class GeographyService:
    """Read-only service for querying standardized Peruvian administrative geography."""

    @staticmethod
    def list_departments(db: Session) -> list[GeoDepartment]:
        """List all 25 departments of Peru ordered by code."""
        return db.query(GeoDepartment).order_by(GeoDepartment.code).all()

    @staticmethod
    def list_provinces_by_department(db: Session, department_code: str) -> list[GeoProvince]:
        """List all provinces belonging to a given department."""
        dept_code = department_code.strip()
        return (
            db.query(GeoProvince)
            .filter(GeoProvince.department_code == dept_code)
            .order_by(GeoProvince.code)
            .all()
        )

    @staticmethod
    def list_districts_by_province(db: Session, province_code: str) -> list[GeoDistrict]:
        """List all districts belonging to a given province."""
        prov_code = province_code.strip()
        return (
            db.query(GeoDistrict)
            .filter(GeoDistrict.province_code == prov_code)
            .order_by(GeoDistrict.code)
            .all()
        )

    @staticmethod
    def get_district_by_code(db: Session, ubigeo_code: str) -> GeoDistrict | None:
        """Fetch a single district by its 6-digit canonical UBIGEO code."""
        code = ubigeo_code.strip()
        return db.query(GeoDistrict).filter(GeoDistrict.code == code).first()

    @classmethod
    def resolve_ubigeo(cls, db: Session, ubigeo_code: str | None) -> UbigeoHierarchyResponse | None:
        """Resolve a 6-digit UBIGEO code into its full structured hierarchy."""
        if not ubigeo_code:
            return None
        code = ubigeo_code.strip()
        dist = db.query(GeoDistrict).filter(GeoDistrict.code == code).first()
        if not dist:
            return None

        prov = dist.province
        dept = dist.department
        dept_name = dept.name if dept else ""
        prov_name = prov.name if prov else ""
        dist_name = dist.name

        formatted = f"{dist_name}, {prov_name}, {dept_name}"
        return UbigeoHierarchyResponse(
            code=dist.code,
            department_code=dist.department_code,
            department_name=dept_name,
            province_code=dist.province_code,
            province_name=prov_name,
            district_name=dist_name,
            formatted=formatted,
        )
