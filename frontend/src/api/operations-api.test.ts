import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { clearCsrfToken } from './csrf'
import { API_ROOT } from './config'
import { operationsApi } from './operations-api'
import { researchApi } from './research-api'
import { makeBatch, retryWithBackoff } from '../research/telemetry'

const server = setupServer()

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  clearCsrfToken()
  vi.unstubAllGlobals()
})
afterAll(() => server.close())

describe('API operacional con MSW', () => {
  it('envía búsqueda y paginación sin omitir credenciales', async () => {
    server.use(
      http.get(`${API_ROOT}/clients`, ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('page')).toBe('2')
        expect(url.searchParams.get('search')).toBe('andina')
        expect(request.credentials).toBe('include')
        return HttpResponse.json({
          items: [],
          page: 2,
          page_size: 20,
          total: 0,
          total_pages: 0,
        })
      }),
    )

    const result = await operationsApi.clients.list({
      page: 2,
      search: 'andina',
    })
    expect(result.page).toBe(2)
  })

  it('obtiene CSRF y lo adjunta a las mutaciones JSON', async () => {
    server.use(
      http.get(`${API_ROOT}/auth/csrf`, () =>
        HttpResponse.json({ csrf_token: 'csrf-operational' }),
      ),
      http.post(`${API_ROOT}/clients`, async ({ request }) => {
        expect(request.headers.get('x-csrf-token')).toBe('csrf-operational')
        expect(request.headers.get('content-type')).toContain('application/json')
        const body = await request.json() as { business_name: string }
        return HttpResponse.json({
          ...body,
          id: 'client-1',
          document_type: 'RUC',
          document_number: '20123456789',
          address: 'Av. Principal 123',
          district: 'Lima',
          province: 'Lima',
          department: 'Lima',
          contact_name: null,
          contact_email: null,
          contact_phone: null,
          is_active: true,
          created_at: '2026-07-23T00:00:00Z',
          updated_at: '2026-07-23T00:00:00Z',
        }, { status: 201 })
      }),
    )

    const result = await operationsApi.clients.create({
      document_type: 'RUC',
      document_number: '20123456789',
      business_name: 'Empresa Andina',
      address: 'Av. Principal 123',
      district: 'Lima',
      province: 'Lima',
      department: 'Lima',
      contact_name: null,
      contact_email: null,
      contact_phone: null,
    })
    expect(result.business_name).toBe('Empresa Andina')
  })

  it('usa el contrato canónico y la paginación de envíos', async () => {
    server.use(
      http.get(`${API_ROOT}/shipments`, ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('page')).toBe('2')
        expect(url.searchParams.get('page_size')).toBe('20')
        expect(url.searchParams.get('status')).toBe('in_transit')
        expect(url.searchParams.get('sort_by')).toBe('created_at')
        expect(url.searchParams.get('sort_order')).toBe('desc')
        return HttpResponse.json({
          items: [{
            id: 'shipment-1',
            tracking_code: 'SHP-0001',
            client_id: 'client-1',
            origin_address: 'Origen 1',
            destination_address: 'Destino 1',
            origin_district: 'Lima',
            destination_district: 'Callao',
            package_description: 'Caja',
            package_count: 2,
            total_weight: '12.50',
            declared_value: '199.90',
            priority: 'urgent',
            priority_label: 'Urgente',
            status: 'in_transit',
            status_label: 'En tránsito',
            expected_delivery_at: null,
            assigned_route_id: null,
            delivered_at: null,
            created_by: 'user-1',
            created_at: '2026-07-25T10:00:00Z',
            updated_at: '2026-07-25T10:00:00Z',
          }],
          page: 2,
          page_size: 20,
          total: 21,
          total_pages: 2,
        })
      }),
    )

    const result = await operationsApi.shipments.list({
      page: 2,
      status: 'in_transit',
    })

    expect(result).toMatchObject({
      page: 2,
      page_size: 20,
      total: 21,
      total_pages: 2,
    })
    expect(result.items[0]).toMatchObject({
      total_weight: '12.50',
      declared_value: '199.90',
      status: 'in_transit',
      status_label: 'En tránsito',
      priority: 'urgent',
      priority_label: 'Urgente',
    })
  })

  it('limpia el payload y protege el cambio de estado con cookies y CSRF', async () => {
    server.use(
      http.get(`${API_ROOT}/auth/csrf`, () =>
        HttpResponse.json({ csrf_token: 'csrf-shipment-status' }),
      ),
      http.post(
        `${API_ROOT}/shipments/shipment-1/status`,
        async ({ request }) => {
          expect(request.credentials).toBe('include')
          expect(request.headers.get('x-csrf-token'))
            .toBe('csrf-shipment-status')
          expect(request.headers.get('content-type'))
            .toContain('application/json')
          await expect(request.json()).resolves.toEqual({
            status: 'in_transit',
            location: 'Almacén Ate',
            description: null,
          })

          return HttpResponse.json({
            id: 'shipment-1',
            tracking_code: 'SHP-0001',
            client_id: 'client-1',
            origin_address: 'Origen 1',
            destination_address: 'Destino 1',
            origin_district: 'Lima',
            destination_district: 'Callao',
            package_description: 'Caja',
            package_count: 2,
            total_weight: '12.50',
            declared_value: null,
            priority: 'normal',
            priority_label: 'Normal',
            status: 'in_transit',
            status_label: 'En tránsito',
            expected_delivery_at: null,
            assigned_route_id: null,
            delivered_at: null,
            created_by: 'user-1',
            created_at: '2026-07-25T10:00:00Z',
            updated_at: '2026-07-25T10:05:00Z',
          })
        },
      ),
    )

    const result = await operationsApi.shipments.status(
      'shipment-1',
      {
        status: 'in_transit',
        location: '  Almacén Ate  ',
        description: '   ',
      },
    )

    expect(result.status).toBe('in_transit')
    expect(result.status_label).toBe('En tránsito')
  })

  it('deja que el navegador genere el boundary multipart de capturas', async () => {
    const image = new Blob(['webp'], { type: 'image/webp' })
    const capture = {
      image,
      capturedAt: '2026-07-23T00:00:00Z',
      sequenceNumber: 1,
      width: 320,
      height: 240,
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(HttpResponse.json({ csrf_token: 'csrf-capture' }))
      .mockResolvedValueOnce(
        HttpResponse.json(
          {
            success: false,
            error: { code: 'TEMPORARY_ERROR', message: 'Reintentar' },
          },
          { status: 503 },
        ),
      )
      .mockResolvedValueOnce(
        HttpResponse.json(
          { success: true, idempotent_replay: false },
          { status: 201 },
        ),
      )
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      retryWithBackoff(
        () => researchApi.sendCapture('session-1', capture),
        1,
        [0],
      ),
    ).resolves.toMatchObject({ success: true })

    const options = fetchMock.mock.calls[1]?.[1] as RequestInit
    const retryOptions = fetchMock.mock.calls[2]?.[1] as RequestInit
    const headers = new Headers(options.headers)
    expect(options.body).toBeInstanceOf(FormData)
    expect(headers.has('Content-Type')).toBe(false)
    expect((options.body as FormData).get('sequence_number')).toBe('1')
    expect((options.body as FormData).get('image')).toBeInstanceOf(File)
    expect((retryOptions.body as FormData).get('sequence_number')).toBe('1')
    const firstFile = (options.body as FormData).get('image') as File
    const retryFile = (retryOptions.body as FormData).get('image') as File
    expect(retryFile.name).toBe(firstFile.name)
    expect(retryFile.size).toBe(firstFile.size)
    expect(retryFile.type).toBe(firstFile.type)
  })

  it('rechaza capturas fuera de las dimensiones admitidas antes de enviarlas', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      researchApi.sendCapture('session-1', {
        image: new Blob(['webp'], { type: 'image/webp' }),
        capturedAt: '2026-07-23T00:00:00Z',
        sequenceNumber: 1,
        width: 63,
        height: 240,
      }),
    ).rejects.toMatchObject({
      code: 'INVALID_CAPTURE_DIMENSIONS',
      status: 422,
    })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('envía una anotación experimental estructurada con PATCH y CSRF', async () => {
    server.use(
      http.get(`${API_ROOT}/auth/csrf`, () =>
        HttpResponse.json({ csrf_token: 'csrf-annotation' }),
      ),
      http.patch(
        `${API_ROOT}/research/sessions/session-1/annotation`,
        async ({ request }) => {
          expect(request.headers.get('x-csrf-token')).toBe('csrf-annotation')
          expect(await request.json()).toEqual({
            identity_label: 'genuine',
            sample_role: 'verification',
            presentation_label: 'bona_fide',
            attack_type: 'none',
            annotation_notes: 'muestra confirmada',
            operator_change_at: null,
            source_device: null,
            pad_source_id: null,
            confirmed: true,
          })
          return HttpResponse.json({
            id: 'session-1',
            participant_id: 'participant-1',
            scenario: 'register_shipment',
            status: 'completed',
            started_at: '2026-07-23T00:00:00Z',
            ended_at: '2026-07-23T00:05:00Z',
            duration_seconds: 300,
            facial_capture_count: 5,
            keyboard_event_count: 10,
            mouse_event_count: 20,
            batch_count: 2,
            error_count: 0,
            protocol_version: 'research-v1',
            collector_version: 'frontend-v1',
            identity_label: 'genuine',
            sample_role: 'verification',
            operator_change_at: null,
            presentation_label: 'bona_fide',
            attack_type: 'none',
            source_device: null,
            pad_source_id: null,
            annotation_status: 'confirmed',
          })
        },
      ),
    )

    const result = await researchApi.annotate('session-1', {
      identity_label: 'genuine',
      sample_role: 'verification',
      presentation_label: 'bona_fide',
      attack_type: 'none',
      annotation_notes: 'muestra confirmada',
      confirmed: true,
    })

    expect(result.status).toBe('completed')
  })

  it('reintenta un lote conservando batch_id y sequence_number', async () => {
    const batch = makeBatch([
      {
        type: 'mouse',
        event: 'click',
        timestamp: '2026-07-25T12:00:00.000Z',
        sequence_index: 1,
        normalized_x: 0.5,
        normalized_y: 0.4,
        delta_x: 0,
        delta_y: 0,
        distance: 0,
        velocity: 0,
        button_category: 'primary',
        scroll_delta: 0,
      },
    ], 9)
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(HttpResponse.json({ csrf_token: 'csrf-batch' }))
      .mockResolvedValueOnce(
        HttpResponse.json(
          {
            success: false,
            error: { code: 'TEMPORARY_ERROR', message: 'Reintentar' },
          },
          { status: 503 },
        ),
      )
      .mockResolvedValueOnce(
        HttpResponse.json({ success: true, idempotent_replay: true }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await retryWithBackoff(
      () => researchApi.sendBatch('session-1', batch),
      1,
      [0],
    )

    const firstBody = JSON.parse(
      String(fetchMock.mock.calls[1]?.[1]?.body),
    ) as { batch_id: string; sequence_number: number }
    const retryBody = JSON.parse(
      String(fetchMock.mock.calls[2]?.[1]?.body),
    ) as { batch_id: string; sequence_number: number }
    expect(retryBody.batch_id).toBe(firstBody.batch_id)
    expect(retryBody.sequence_number).toBe(firstBody.sequence_number)
  })
})
