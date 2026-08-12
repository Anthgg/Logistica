"""Files API — router factory."""

from fastapi import APIRouter
from app.modules.logistics.files.presentation.routes.router import router as files_router


def create_router() -> APIRouter:
    return files_router