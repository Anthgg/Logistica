import { beforeEach, describe, expect, it, vi } from 'vitest'
import { API_ROOT } from './config'
import { getI18nCatalog } from './i18n-api'
import {
  getLastContentLanguage,
  recordContentLanguage,
  setRequestLanguage,
} from './locale'
import { testCatalog } from '../test/test-utils'

describe('catálogo i18n', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    setRequestLanguage('en-US')
    recordContentLanguage(null)
  })

  it('valida el catálogo y conserva los idiomas de la respuesta', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({
        ...testCatalog,
        locale: 'en',
        translations: {
          ...testCatalog.translations,
          common: { activity: 'Activity' },
        },
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Content-Language': 'en',
        },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const catalog = await getI18nCatalog()

    expect(catalog.locale).toBe('en')
    expect(catalog.translations.common.activity).toBe('Activity')
    expect(fetchMock.mock.calls[0]?.[0]).toBe(`${API_ROOT}/i18n/catalog`)
    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers)
    expect(headers.get('Accept-Language')).toBe('en-US')
    expect(getLastContentLanguage()).toBe('en')
  })
})
