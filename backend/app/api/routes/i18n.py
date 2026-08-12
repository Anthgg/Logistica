from fastapi import APIRouter, Request

from app.i18n import SUPPORTED_LOCALES, locale_from_request, public_catalog
from app.schemas.i18n import TranslationCatalogResponse

router = APIRouter(prefix="/i18n", tags=["Internationalization"])


@router.get(
    "/catalog",
    response_model=TranslationCatalogResponse,
    summary="Obtener etiquetas traducidas para el frontend",
)
def translation_catalog(request: Request) -> TranslationCatalogResponse:
    locale = locale_from_request(request)
    return TranslationCatalogResponse(
        locale=locale,
        supported_locales=SUPPORTED_LOCALES,
        translations=public_catalog(locale),
    )
