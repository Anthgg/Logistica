from contextvars import ContextVar, Token
from typing import Any, Literal, cast

from fastapi import Request

from app.core.config import settings
from app.i18n.catalogs import CATALOGS, PUBLIC_PREFIXES

Locale = Literal["es", "en", "pt"]
SUPPORTED_LOCALES: tuple[Locale, ...] = ("es", "en", "pt")
DEFAULT_LOCALE: Locale = settings.DEFAULT_LOCALE
_current_locale: ContextVar[Locale] = ContextVar(
    "request_locale", default=DEFAULT_LOCALE
)


def _normalize_locale(value: str) -> Locale | None:
    language = value.strip().lower().replace("_", "-").split("-", 1)[0]
    if language in SUPPORTED_LOCALES:
        return cast(Locale, language)
    return None


def negotiate_locale(accept_language: str | None) -> Locale:
    """Select the best supported locale from an RFC 9110 Accept-Language value."""
    if not accept_language:
        return DEFAULT_LOCALE

    weighted: list[tuple[float, int, Locale]] = []
    for index, raw_candidate in enumerate(accept_language.split(",")[:20]):
        parts = [part.strip() for part in raw_candidate.split(";")]
        if not parts or not parts[0]:
            continue
        locale = DEFAULT_LOCALE if parts[0] == "*" else _normalize_locale(parts[0])
        if locale is None:
            continue
        quality = 1.0
        for parameter in parts[1:]:
            if parameter.lower().startswith("q="):
                try:
                    quality = float(parameter[2:])
                except ValueError:
                    quality = 0.0
        if 0 < quality <= 1:
            weighted.append((quality, -index, locale))

    if not weighted:
        return DEFAULT_LOCALE
    return max(weighted)[2]


def set_current_locale(locale: Locale) -> Token:
    return _current_locale.set(locale)


def reset_current_locale(token: Token) -> None:
    _current_locale.reset(token)


def get_current_locale() -> Locale:
    return _current_locale.get()


def locale_from_request(request: Request) -> Locale:
    locale = getattr(request.state, "locale", None)
    return locale if locale in SUPPORTED_LOCALES else negotiate_locale(
        request.headers.get("accept-language")
    )


def translate(
    key: str,
    locale: Locale | None = None,
    *,
    default: str | None = None,
) -> str:
    selected = locale or get_current_locale()
    return CATALOGS[selected].get(
        key,
        CATALOGS[DEFAULT_LOCALE].get(key, default if default is not None else key),
    )


def _error_category(code: str) -> str:
    if code in {"AUTHENTICATION_ERROR", "SESSION_REQUIRED"}:
        return "authentication"
    if "PERMISSION" in code or "FORBIDDEN" in code:
        return "permission"
    if "NOT_FOUND" in code:
        return "not_found"
    if "RATE_LIMIT" in code or "LIMIT_EXCEEDED" in code:
        return "rate_limit"
    if "UNAVAILABLE" in code:
        return "unavailable"
    if "EXPIRED" in code:
        return "expired"
    if (
        "INVALID" in code
        or "MISMATCH" in code
        or code.startswith("WEAK_")
        or code.startswith("CAPTURE_")
    ):
        return "invalid"
    if (
        "CONFLICT" in code
        or "DUPLICATE" in code
        or "ALREADY" in code
        or code.endswith("_EXISTS")
        or code.endswith("_UNCHANGED")
    ):
        return "conflict"
    if code.startswith("INTERNAL_"):
        return "internal"
    return "default"


def translate_error(code: str, source_message: str, locale: Locale) -> str:
    exact_key = f"error.{code}"
    exact = CATALOGS[locale].get(exact_key)
    if exact is not None:
        return exact
    if locale == DEFAULT_LOCALE:
        return source_message
    return translate(f"error.{_error_category(code)}", locale)


def translate_validation_message(error_type: str, locale: Locale) -> str:
    normalized_type = error_type.split(".", 1)[0]
    return translate(
        f"validation.{normalized_type}",
        locale,
        default=translate("validation.invalid", locale),
    )


def translate_event(event_type: str, locale: Locale) -> str:
    return translate(
        f"event.{event_type}",
        locale,
        default=translate("event.unknown", locale),
    )


def translate_resource(resource_type: str | None, locale: Locale) -> str | None:
    if resource_type is None:
        return None
    return translate(
        f"resource.{resource_type}",
        locale,
        default=translate("common.unknown", locale),
    )


def public_catalog(locale: Locale) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in CATALOGS[locale].items():
        if not key.startswith(PUBLIC_PREFIXES):
            continue
        target = result
        parts = key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result
