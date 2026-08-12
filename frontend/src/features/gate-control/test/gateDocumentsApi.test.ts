import { beforeEach, describe, expect, it, vi } from 'vitest'
import { gateDocumentsApi } from '../api/gateDocumentsApi'

type FetchFn = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
let fetchMock: ReturnType<typeof vi.fn<FetchFn>>

function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
}

function pdfResponse(): Response {
  return new Response(new Blob(['%PDF-1.4'], { type: 'application/pdf' }), {
    status: 200,
    headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': 'attachment' },
  })
}

const cpvDoc = {
  document_instance_id: 'doc-1',
  check_in_id: 'ci-1',
  document_code: 'CPV-0001',
  status: 'ISSUED',
  issued_at: '2026-08-01T12:00:00Z',
  snapshot_hash: 'abc123def456',
  download_url: '/api/logistics/gate-check-ins/ci-1/document/pdf',
  expires_at: null,
}

describe('gateDocumentsApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    fetchMock = vi.fn<FetchFn>()
    vi.stubGlobal('fetch', fetchMock)
  })

  describe('issueDocument', () => {
    it('sends POST with Idempotency-Key and CSRF headers', async () => {
      fetchMock
        .mockResolvedValueOnce(jsonResponse({ csrf_token: 'tok-csrf' }))
        .mockResolvedValueOnce(jsonResponse(cpvDoc, 201))

      const result = await gateDocumentsApi.issueDocument('ci-1')

      expect(result.document_instance_id).toBe('doc-1')
      const issueCall = fetchMock.mock.calls[1]
      const init = issueCall[1]!
      const h = init.headers instanceof Headers ? init.headers : new Headers(init.headers as HeadersInit)
      expect(h.get('X-CSRF-Token')).toBe('tok-csrf')
      expect(h.get('Idempotency-Key')).toBeTruthy()
      expect(h.has('X-Idempotency-Key')).toBe(false)
      expect(init.method).toBe('POST')
      expect(String(issueCall[0])).toContain('/logistics/gate-check-ins/ci-1/issue-document')
    })
  })

  describe('getDocument', () => {
    it('returns typed GateCpvDocumentResponse on 200', async () => {
      fetchMock.mockResolvedValueOnce(jsonResponse(cpvDoc))

      const result = await gateDocumentsApi.getDocument('ci-1')

      expect(result).not.toBeNull()
      expect(result!.document_instance_id).toBe('doc-1')
      expect(result!.document_code).toBe('CPV-0001')
      expect(result!.status).toBe('ISSUED')
    })

    it('returns null on 404 GATE_DOCUMENT_NOT_ISSUED', async () => {
      fetchMock.mockResolvedValueOnce(
        jsonResponse({ code: 'GATE_DOCUMENT_NOT_ISSUED', message: 'Not issued' }, 404),
      )

      const result = await gateDocumentsApi.getDocument('ci-1')

      expect(result).toBeNull()
    })

    it('throws on non-404 errors', async () => {
      fetchMock.mockResolvedValueOnce(jsonResponse({ message: 'Server error' }, 500))

      await expect(gateDocumentsApi.getDocument('ci-1')).rejects.toThrow()
    })
  })

  describe('downloadDocument', () => {
    it('fetches /document/pdf with credentials include', async () => {
      fetchMock.mockResolvedValueOnce(pdfResponse())

      const blob = await gateDocumentsApi.downloadDocument('ci-1')

      expect(blob).toBeInstanceOf(Blob)
      const call = fetchMock.mock.calls[0]
      expect(String(call[0])).toContain('/logistics/gate-check-ins/ci-1/document/pdf')
      expect(call[1]!.credentials).toBe('include')
      expect((call[1]!.headers as Record<string, string>).Accept).toBe('application/pdf')
    })

    it('does not send CSRF on GET download', async () => {
      fetchMock.mockResolvedValueOnce(pdfResponse())

      await gateDocumentsApi.downloadDocument('ci-1')

      const headers = fetchMock.mock.calls[0][1]!.headers as Record<string, string>
      expect(headers['X-CSRF-Token']).toBeUndefined()
    })

    it('rejects JSON response disguised as PDF', async () => {
      fetchMock.mockResolvedValueOnce(
        jsonResponse({ error: 'not found' }),
      )

      await expect(gateDocumentsApi.downloadDocument('ci-1')).rejects.toThrow(
        /Se esperaba application\/pdf/,
      )
    })

    it('throws on non-ok status', async () => {
      fetchMock.mockResolvedValueOnce(new Response(null, { status: 403 }))

      await expect(gateDocumentsApi.downloadDocument('ci-1')).rejects.toThrow(/403/)
    })
  })
})
