import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { getCsrfToken } from './api-client'
import { companyProfileApi } from './company-profile-api'

vi.mock('./api-client', () => ({
  API_ROOT: '/api',
  apiRequest: vi.fn(),
  getCsrfToken: vi.fn(),
}))

const mockedCsrf = vi.mocked(getCsrfToken)

describe('companyProfileApi - Vista Previa Institucional (Fase 021)', () => {
  const originalFetch = globalThis.fetch
  const originalCreateObjectURL = URL.createObjectURL

  beforeEach(() => {
    mockedCsrf.mockReset()
    mockedCsrf.mockResolvedValue('test-csrf-token-xyz')
    globalThis.fetch = vi.fn()
    URL.createObjectURL = vi.fn(() => 'blob:http://localhost:3000/mock-uuid-1234')
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    URL.createObjectURL = originalCreateObjectURL
  })

  it('envía solicitud POST con branch_id y signer_id como null cuando no se especifican', async () => {
    const mockBuffer = new TextEncoder().encode('%PDF-1.4 mock content').buffer
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (header: string) => (header.toLowerCase() === 'content-type' ? 'application/pdf' : null),
      },
      arrayBuffer: vi.fn().mockResolvedValue(mockBuffer),
    })
    globalThis.fetch = mockFetch

    const resultBlob = await companyProfileApi.getPreviewDocumentBlob({
      doc_type_code: 'AREC',
    })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(mockFetch).toHaveBeenCalledWith('/api/logistics/company-profile/document-preview', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/pdf',
        'X-CSRF-Token': 'test-csrf-token-xyz',
      },
      body: JSON.stringify({
        doc_type_code: 'AREC',
        branch_id: null,
        signer_id: null,
        custom_data: {},
      }),
    })
    expect(resultBlob).toBeInstanceOf(Blob)
    expect(resultBlob.type).toBe('application/pdf')
  })

  it('envía sede, firmante y custom_data explícitos cuando son proporcionados', async () => {
    const mockBuffer = new TextEncoder().encode('%PDF-1.4 mock content').buffer
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (header: string) => (header.toLowerCase() === 'content-type' ? 'application/pdf' : null),
      },
      arrayBuffer: vi.fn().mockResolvedValue(mockBuffer),
    })
    globalThis.fetch = mockFetch

    const resultBlob = await companyProfileApi.getPreviewDocumentBlob({
      doc_type_code: 'GRR',
      branch_id: 'branch-uuid-001',
      signer_id: 'signer-uuid-002',
      custom_data: { receiver_name: 'Acme Corp', weight_kg: 150.5 },
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/logistics/company-profile/document-preview', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/pdf',
        'X-CSRF-Token': 'test-csrf-token-xyz',
      },
      body: JSON.stringify({
        doc_type_code: 'GRR',
        branch_id: 'branch-uuid-001',
        signer_id: 'signer-uuid-002',
        custom_data: { receiver_name: 'Acme Corp', weight_kg: 150.5 },
      }),
    })
    expect(resultBlob).toBeInstanceOf(Blob)
    expect(resultBlob.type).toBe('application/pdf')
  })

  it('genera un blob URL correctamente mediante getPreviewDocumentBlobUrl', async () => {
    const mockBuffer = new TextEncoder().encode('%PDF-1.4 mock content').buffer
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (header: string) => (header.toLowerCase() === 'content-type' ? 'application/pdf' : null),
      },
      arrayBuffer: vi.fn().mockResolvedValue(mockBuffer),
    })

    const blobUrl = await companyProfileApi.getPreviewDocumentBlobUrl({
      doc_type_code: 'CPV',
    })

    expect(blobUrl).toBe('blob:http://localhost:3000/mock-uuid-1234')
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1)
  })

  it('extrae el mensaje de error estructurado del backend en caso de fallo 400/422', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: vi.fn().mockResolvedValue({
        detail: 'El tipo documental AREC requiere una sede activa configurada.',
      }),
    })

    await expect(
      companyProfileApi.getPreviewDocumentBlob({
        doc_type_code: 'AREC',
      }),
    ).rejects.toThrow('El tipo documental AREC requiere una sede activa configurada.')
  })

  it('maneja errores con formato de array de validación de FastAPI/Pydantic', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: vi.fn().mockResolvedValue({
        detail: [
          { loc: ['body', 'doc_type_code'], msg: 'Código no soportado' },
          { loc: ['body', 'signer_id'], msg: 'UUID inválido' },
        ],
      }),
    })

    await expect(
      companyProfileApi.getPreviewDocumentBlob({
        doc_type_code: 'INVALID',
      }),
    ).rejects.toThrow('Código no soportado, UUID inválido')
  })

  it('lanza error si la respuesta HTTP es 200 pero el Content-Type no es PDF', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (header: string) => (header.toLowerCase() === 'content-type' ? 'application/json' : null),
      },
      json: vi.fn().mockResolvedValue({ error: 'Fallo al procesar plantilla Weasyprint' }),
    })

    await expect(
      companyProfileApi.getPreviewDocumentBlob({
        doc_type_code: 'AREC',
      }),
    ).rejects.toThrow(/Se esperaba un documento PDF pero el servidor respondió con application\/json/)
  })
})
