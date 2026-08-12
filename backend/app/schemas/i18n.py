from typing import Any

from pydantic import BaseModel

from app.i18n import Locale


class TranslationCatalogResponse(BaseModel):
    locale: Locale
    supported_locales: tuple[Locale, ...]
    translations: dict[str, Any]
