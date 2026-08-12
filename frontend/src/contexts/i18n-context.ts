import { createContext } from 'react'
import type {
  I18nCatalogResponse,
  SupportedLanguage,
  SupportedLocale,
  TranslationNamespace,
} from '../types/i18n'

export interface I18nContextValue {
  language: SupportedLanguage
  locale: SupportedLocale
  catalog: I18nCatalogResponse | null
  catalogVersion: number
  contentLanguage: string | null
  isChangingLanguage: boolean
  error: string | null
  translate: (
    namespace: TranslationNamespace,
    key: string,
    fallback?: string,
  ) => string
  changeLanguage: (language: SupportedLanguage) => Promise<void>
  reloadCatalog: () => Promise<void>
  clearError: () => void
}

export const I18nContext = createContext<I18nContextValue | null>(null)
