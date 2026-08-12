import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { getI18nCatalog } from '../api/i18n-api'
import { API_ROOT } from '../api/config'
import {
  getLastContentLanguage,
  getRequestLanguage,
  languageToLocale,
  normalizeLanguage,
  setRequestLanguage,
  subscribeToContentLanguage,
} from '../api/locale'
import { getCsrfToken } from '../api/csrf'
import { Button } from '../components/common/Button'
import { LoadingScreen } from '../components/common/LoadingScreen'
import type {
  I18nCatalogResponse,
  SupportedLanguage,
  TranslationNamespace,
} from '../types/i18n'
import { getErrorMessage } from '../utils/errors'
import {
  I18nContext,
  type I18nContextValue,
} from './i18n-context'

function browserLanguage(): SupportedLanguage {
  return normalizeLanguage(
    typeof navigator === 'undefined' ? 'es-PE' : navigator.language,
  )
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const initialLanguageRef = useRef<SupportedLanguage>(browserLanguage())
  const cacheRef = useRef(
    new Map<SupportedLanguage, I18nCatalogResponse>(),
  )
  const changeControllerRef = useRef<AbortController | null>(null)
  const [language, setLanguage] = useState<SupportedLanguage>(
    initialLanguageRef.current,
  )
  const [catalog, setCatalog] =
    useState<I18nCatalogResponse | null>(null)
  const [catalogVersion, setCatalogVersion] = useState(0)
  const [contentLanguage, setContentLanguage] = useState(
    getLastContentLanguage,
  )
  const [isBootstrapping, setIsBootstrapping] = useState(true)
  const [isChangingLanguage, setIsChangingLanguage] = useState(false)
  const [fatalBootstrapError, setFatalBootstrapError] =
    useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [bootstrapAttempt, setBootstrapAttempt] = useState(0)

  const applyCatalog = useCallback(
    (
      selectedLanguage: SupportedLanguage,
      response: I18nCatalogResponse,
    ) => {
      cacheRef.current.set(selectedLanguage, response)
      setCatalog(response)
      setCatalogVersion((current) => current + 1)
      document.documentElement.lang = response.locale
    },
    [],
  )

  useEffect(
    () => subscribeToContentLanguage(setContentLanguage),
    [],
  )

  const [isRetrying, setIsRetrying] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const selectedLanguage = initialLanguageRef.current
    setRequestLanguage(selectedLanguage)
    setIsBootstrapping(true)
    setFatalBootstrapError(null)

    const bootstrap = async () => {
      // 1. Healthcheck inicial a ${API_URL}/health
      try {
        const healthRes = await fetch(`${API_ROOT}/health`, {
          method: 'GET',
          credentials: 'include',
          signal: controller.signal,
          headers: {
            Accept: 'application/json',
            'Accept-Language': getRequestLanguage(),
          },
        })
        if (!healthRes.ok) {
          throw new Error(`HTTP ${healthRes.status}: Error al verificar el estado de la API`)
        }
      } catch (caughtError: unknown) {
        if (!controller.signal.aborted) {
          const message = String(caughtError)
          if (message.includes('Failed to fetch') || message.includes('NETWORK_ERROR') || message.includes('NetworkError') || caughtError instanceof TypeError) {
            setFatalBootstrapError(
              `No se pudo establecer conexión con la API en ${API_ROOT}. Verifica que el backend esté ejecutándose o revisa si hay un bloqueo de seguridad CORS (asegúrate de que el backend tenga configurada la variable FRONTEND_URL permitida).`,
            )
          } else {
            setFatalBootstrapError(`Error de inicialización: ${getErrorMessage(caughtError)}`)
          }
          setIsBootstrapping(false)
          setIsRetrying(false)
        }
        return
      }

      // 2. Token CSRF inicial
      try {
        await getCsrfToken()
      } catch (caughtError: unknown) {
        if (!controller.signal.aborted) {
          const message = String(caughtError)
          if (message.includes('Failed to fetch') || message.includes('NETWORK_ERROR') || caughtError instanceof TypeError) {
            setFatalBootstrapError(
              `Bloqueo de seguridad CORS o fallo de red en ${API_ROOT}/auth/csrf. Asegúrate de que el backend esté ejecutándose y tenga configurada la variable FRONTEND_URL permitida.`,
            )
          } else {
            setFatalBootstrapError(getErrorMessage(caughtError))
          }
          setIsBootstrapping(false)
          setIsRetrying(false)
        }
        return
      }

      // 3. Catálogo i18n
      try {
        const response = await getI18nCatalog(controller.signal)
        applyCatalog(selectedLanguage, response)
        setError(null)
      } catch (caughtError: unknown) {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError))
          document.documentElement.lang =
            languageToLocale(selectedLanguage)
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsBootstrapping(false)
          setIsRetrying(false)
        }
      }
    }

    void bootstrap()
    return () => controller.abort()
  }, [applyCatalog, bootstrapAttempt])

  const fetchCatalog = useCallback(
    async (selectedLanguage: SupportedLanguage) => {
      changeControllerRef.current?.abort()
      const controller = new AbortController()
      changeControllerRef.current = controller
      setRequestLanguage(selectedLanguage)
      setLanguage(selectedLanguage)
      setIsChangingLanguage(true)
      setError(null)

      const cached = cacheRef.current.get(selectedLanguage)
      if (cached) {
        setCatalog(cached)
        document.documentElement.lang = cached.locale
      }

      try {
        const response = await getI18nCatalog(controller.signal)
        applyCatalog(selectedLanguage, response)
      } catch (caughtError: unknown) {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError))
          document.documentElement.lang =
            languageToLocale(selectedLanguage)
        }
        throw caughtError
      } finally {
        if (changeControllerRef.current === controller) {
          changeControllerRef.current = null
          setIsChangingLanguage(false)
        }
      }
    },
    [applyCatalog],
  )

  useEffect(
    () => () => changeControllerRef.current?.abort(),
    [],
  )

  const changeLanguage = useCallback(
    async (selectedLanguage: SupportedLanguage) => {
      if (
        selectedLanguage === language &&
        catalog?.locale === languageToLocale(selectedLanguage)
      ) {
        return
      }
      await fetchCatalog(selectedLanguage)
    },
    [catalog?.locale, fetchCatalog, language],
  )

  const reloadCatalog = useCallback(
    () => fetchCatalog(language),
    [fetchCatalog, language],
  )

  const translate = useCallback(
    (
      namespace: TranslationNamespace,
      key: string,
      fallback?: string,
    ) => catalog?.translations[namespace][key] ?? fallback ?? key,
    [catalog],
  )

  const clearError = useCallback(() => setError(null), [])

  const value = useMemo<I18nContextValue>(
    () => ({
      language,
      locale: catalog?.locale ?? languageToLocale(language),
      catalog,
      catalogVersion,
      contentLanguage,
      isChangingLanguage,
      error,
      translate,
      changeLanguage,
      reloadCatalog,
      clearError,
    }),
    [
      catalog,
      catalogVersion,
      changeLanguage,
      clearError,
      contentLanguage,
      error,
      isChangingLanguage,
      language,
      reloadCatalog,
      translate,
    ],
  )

  if (isBootstrapping) {
    return <LoadingScreen message="Preparando la aplicación…" />
  }

  if (fatalBootstrapError) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-100 p-4">
        <section
          className="w-full max-w-md rounded-2xl border border-rose-200 bg-white p-6 text-center shadow-lg"
          role="alert"
        >
          <h1 className="text-xl font-bold text-slate-950">
            No se pudo iniciar la aplicación
          </h1>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            {fatalBootstrapError}
          </p>
          <Button
            className="mt-5 w-full sm:w-auto"
            disabled={isRetrying}
            onClick={() => {
              setIsRetrying(true)
              setBootstrapAttempt((current) => current + 1)
            }}
          >
            {isRetrying ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Conectando...
              </span>
            ) : (
              'Reintentar inicialización'
            )}
          </Button>
        </section>
      </main>
    )
  }

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  )
}
