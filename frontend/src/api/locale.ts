import type {
  SupportedLanguage,
  SupportedLocale,
} from '../types/i18n'

let requestLanguage: SupportedLanguage = 'es-PE'
let lastContentLanguage: string | null = null
const contentLanguageListeners = new Set<
  (language: string | null) => void
>()

export function normalizeLanguage(
  value: string | null | undefined,
): SupportedLanguage {
  const normalized = value?.trim().toLowerCase() ?? ''

  if (normalized.startsWith('en')) {
    return 'en-US'
  }
  if (normalized.startsWith('pt')) {
    return 'pt-BR'
  }
  return 'es-PE'
}

export function languageToLocale(
  language: SupportedLanguage,
): SupportedLocale {
  return language.slice(0, 2) as SupportedLocale
}

export function getRequestLanguage(): SupportedLanguage {
  return requestLanguage
}

export function setRequestLanguage(
  language: SupportedLanguage,
): void {
  requestLanguage = language
}

export function recordContentLanguage(value: string | null): void {
  lastContentLanguage = value?.trim() || null
  contentLanguageListeners.forEach((listener) => {
    listener(lastContentLanguage)
  })
}

export function getLastContentLanguage(): string | null {
  return lastContentLanguage
}

export function subscribeToContentLanguage(
  listener: (language: string | null) => void,
): () => void {
  contentLanguageListeners.add(listener)
  return () => {
    contentLanguageListeners.delete(listener)
  }
}
