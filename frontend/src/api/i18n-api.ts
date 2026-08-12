import { apiRequest } from './api-client'
import { ApiRequestError } from '../types/api'
import {
  SUPPORTED_LOCALES,
  TRANSLATION_NAMESPACES,
  type I18nCatalogResponse,
  type SupportedLocale,
  type TranslationCatalog,
} from '../types/i18n'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function parseLocale(value: unknown): SupportedLocale {
  if (
    typeof value !== 'string' ||
    !SUPPORTED_LOCALES.includes(value as SupportedLocale)
  ) {
    throw new ApiRequestError(
      'El catálogo de idioma devolvió una configuración inválida.',
      { code: 'INVALID_RESPONSE' },
    )
  }

  return value as SupportedLocale
}

function parseTranslations(value: unknown): TranslationCatalog {
  if (!isRecord(value)) {
    throw new ApiRequestError(
      'El catálogo de idioma devolvió traducciones inválidas.',
      { code: 'INVALID_RESPONSE' },
    )
  }

  return Object.fromEntries(
    TRANSLATION_NAMESPACES.map((namespace) => {
      const entries = value[namespace]
      if (!isRecord(entries)) {
        throw new ApiRequestError(
          'El catálogo de idioma está incompleto.',
          { code: 'INVALID_RESPONSE' },
        )
      }

      const translations = Object.fromEntries(
        Object.entries(entries).map(([key, label]) => {
          if (typeof label !== 'string') {
            throw new ApiRequestError(
              'El catálogo de idioma contiene una etiqueta inválida.',
              { code: 'INVALID_RESPONSE' },
            )
          }
          return [key, label]
        }),
      )
      return [namespace, translations]
    }),
  ) as TranslationCatalog
}

function parseCatalog(value: unknown): I18nCatalogResponse {
  if (
    !isRecord(value) ||
    !Array.isArray(value.supported_locales)
  ) {
    throw new ApiRequestError(
      'El servidor devolvió un catálogo de idioma inválido.',
      { code: 'INVALID_RESPONSE' },
    )
  }

  return {
    locale: parseLocale(value.locale),
    supported_locales: value.supported_locales.map(parseLocale),
    translations: parseTranslations(value.translations),
  }
}

export async function getI18nCatalog(
  signal?: AbortSignal,
): Promise<I18nCatalogResponse> {
  const response = await apiRequest<unknown>({
    path: '/i18n/catalog',
    signal,
  })
  return parseCatalog(response)
}
