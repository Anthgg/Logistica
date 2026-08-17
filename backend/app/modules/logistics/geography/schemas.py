"""Pydantic schemas for geographic catalog and UBIGEO resolution."""

from pydantic import BaseModel, ConfigDict, Field


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(description="2-digit department code, e.g. '15'")
    name: str = Field(description="Department name, e.g. 'Lima'")


class ProvinceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(description="4-digit province code, e.g. '1501'")
    department_code: str = Field(description="2-digit parent department code, e.g. '15'")
    name: str = Field(description="Province name, e.g. 'Lima'")


class DistrictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(description="6-digit canonical UBIGEO code, e.g. '150122'")
    province_code: str = Field(description="4-digit parent province code, e.g. '1501'")
    department_code: str = Field(description="2-digit parent department code, e.g. '15'")
    name: str = Field(description="District name, e.g. 'Miraflores'")


class UbigeoHierarchyResponse(BaseModel):
    """Complete resolved geographic hierarchy for a 6-digit UBIGEO code."""

    model_config = ConfigDict(from_attributes=True)

    code: str = Field(description="6-digit canonical UBIGEO code, e.g. '150122'")
    department_code: str = Field(description="2-digit department code, e.g. '15'")
    department_name: str = Field(description="Department name, e.g. 'Lima'")
    province_code: str = Field(description="4-digit province code, e.g. '1501'")
    province_name: str = Field(description="Province name, e.g. 'Lima'")
    district_name: str = Field(description="District name, e.g. 'Miraflores'")
    formatted: str = Field(
        description="Formatted location string: 'Miraflores, Lima, Lima'",
        json_schema_extra={"example": "Miraflores, Lima, Lima"},
    )
