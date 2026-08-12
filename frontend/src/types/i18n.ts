export const SUPPORTED_LANGUAGES = [
  'es-PE',
  'en-US',
  'pt-BR',
] as const

export type SupportedLanguage =
  (typeof SUPPORTED_LANGUAGES)[number]

export const SUPPORTED_LOCALES = ['es', 'en', 'pt'] as const

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

export const TRANSLATION_NAMESPACES = [
  'common',
  'status',
  'priority',
  'event',
  'resource',
  'risk',
  'auth_level',
  'continuous_auth_status',
  'action',
] as const

export type TranslationNamespace =
  (typeof TRANSLATION_NAMESPACES)[number]

export type TranslationCatalog = Record<
  TranslationNamespace,
  Record<string, string>
>

export interface I18nCatalogResponse {
  locale: SupportedLocale
  supported_locales: SupportedLocale[]
  translations: TranslationCatalog
}
