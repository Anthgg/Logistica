import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { API_ROOT } from '../api/config'
import { clearCsrfToken } from '../api/csrf'
import { recordContentLanguage, setRequestLanguage } from '../api/locale'
import { useTranslations } from '../hooks/useTranslations'
import { testCatalog } from '../test/test-utils'
import type { I18nCatalogResponse } from '../types/i18n'
import { I18nProvider } from './I18nProvider'

function catalog(
  locale: 'es' | 'en',
  activity: string,
): I18nCatalogResponse {
  return {
    ...testCatalog,
    locale,
    translations: {
      ...testCatalog.translations,
      common: { ...testCatalog.translations.common, activity },
    },
  }
}

function jsonResponse(
  payload: unknown,
  contentLanguage: string,
): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Content-Language': contentLanguage,
    },
  })
}

function Harness() {
  const {
    language,
    catalogVersion,
    contentLanguage,
    translate,
    changeLanguage,
  } = useTranslations()

  const next = language === 'es-PE' ? 'en-US' : 'es-PE'
  return (
    <div>
      <output>
        {language}|{translate('common', 'activity')}|{catalogVersion}|
        {contentLanguage}
      </output>
      <button type="button" onClick={() => void changeLanguage(next)}>
        Cambiar
      </button>
    </div>
  )
}

describe('I18nProvider', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    clearCsrfToken()
    setRequestLanguage('es-PE')
    recordContentLanguage(null)
    vi.spyOn(window.navigator, 'language', 'get').mockReturnValue('es-PE')
  })

  it('cambia Accept-Language, vuelve a consultar y reutiliza el catálogo cacheado', async () => {
    const user = userEvent.setup()
    const catalogLanguages: string[] = []
    let catalogRequests = 0
    let resolveCachedRefresh:
      | ((response: Response) => void)
      | undefined

    const fetchMock = vi.fn((
      input: RequestInfo | URL,
      init?: RequestInit,
    ): Promise<Response> => {
      const url = String(input)
      const headers = new Headers(init?.headers)

      if (url === `${API_ROOT}/health`) {
        return Promise.resolve(
          jsonResponse({ status: 'ok', database: 'ok' }, 'es'),
        )
      }

      if (url === `${API_ROOT}/auth/csrf`) {
        expect(headers.get('Accept-Language')).toBe('es-PE')
        return Promise.resolve(
          jsonResponse({ csrf_token: 'bootstrap-csrf' }, 'es'),
        )
      }

      if (url === `${API_ROOT}/i18n/catalog`) {
        const language = headers.get('Accept-Language') ?? ''
        catalogLanguages.push(language)
        catalogRequests += 1

        if (catalogRequests === 1) {
          return Promise.resolve(
            jsonResponse(catalog('es', 'Actividad'), 'es'),
          )
        }
        if (catalogRequests === 2) {
          return Promise.resolve(
            jsonResponse(catalog('en', 'Activity'), 'en'),
          )
        }
        return new Promise<Response>((resolve) => {
          resolveCachedRefresh = resolve
        })
      }

      return Promise.reject(new Error(`Solicitud inesperada: ${url}`))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(
      <I18nProvider>
        <Harness />
      </I18nProvider>,
    )

    expect(await screen.findByText(/es-PE\|Actividad\|1\|es/))
      .toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Cambiar' }))
    expect(await screen.findByText(/en-US\|Activity\|2\|en/))
      .toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Cambiar' }))
    expect(await screen.findByText(/es-PE\|Actividad\|2\|en/))
      .toBeInTheDocument()

    resolveCachedRefresh?.(
      jsonResponse(catalog('es', 'Actividad'), 'es'),
    )
    await waitFor(() => {
      expect(screen.getByText(/es-PE\|Actividad\|3\|es/))
        .toBeInTheDocument()
    })
    expect(catalogLanguages).toEqual(['es-PE', 'en-US', 'es-PE'])
  })
})
