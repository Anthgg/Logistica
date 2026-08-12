from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Operación realizada correctamente."
    data: DataT


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: list[DataT]
    page: int
    page_size: int
    total: int
    total_pages: int
