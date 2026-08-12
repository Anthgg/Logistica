import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest, getCsrfToken } from './api-client'
import { rucIntegrationApi } from './ruc-integration-api'

vi.mock('./api-client', () => ({
  apiRequest: vi.fn(),
  getCsrfToken: vi.fn(),
}))

const mockedRequest = vi.mocked(apiRequest)
const mockedCsrf = vi.mocked(getCsrfToken)

describe('rucIntegrationApi', () => {
  beforeEach(() => {
    mockedRequest.mockReset()
    mockedCsrf.mockReset()
    mockedCsrf.mockResolvedValue('csrf-token')
  })

  it('consulta el RUC por el path real y normaliza la respuesta del backend', async () => {
    mockedRequest.mockResolvedValue({
      query_ruc: '20123456789',
      normalized_ruc: '20123456789',
      legal_name: 'Proveedor Demo SAC',
      taxpayer_status: 'ACTIVO',
      domicile_condition: 'HABIDO',
      ubigeo_code: '150101',
      source: 'SUNAT_REDUCED_REGISTRY',
      source_name: 'SUNAT Padrón Reducido',
      fetched_at: '2026-07-28T12:00:00Z',
      lookup_at: '2026-07-28T12:01:00Z',
      data_age_days: 1,
      confidence_level: 'HIGH',
      cache_status: 'MISS',
      annex_addresses: [],
      warnings: [],
      field_provenance: {},
    })

    const result = await rucIntegrationApi.lookupRuc({
      ruc: '20123456789',
      include_annexes: true,
      use_authorized_provider: true,
    })

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/ruc/20123456789?include_annexes=true&allow_provider=true',
    })
    expect(result).toMatchObject({
      ruc: '20123456789',
      legal_name: 'Proveedor Demo SAC',
      source: 'OFFICIAL_PADRON',
      ubigeo: '150101',
    })
  })

  it('usa el endpoint real de salud de fuentes', async () => {
    mockedRequest.mockResolvedValue([
      {
        code: 'SUNAT',
        name: 'SUNAT',
        source_type: 'SUNAT_REDUCED_REGISTRY',
        status: 'ACTIVE',
        consecutive_failures: 0,
      },
    ])

    const sources = await rucIntegrationApi.listSources()

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/ruc/sources/health',
    })
    expect(sources[0]).toMatchObject({
      source_id: 'SUNAT',
      source_name: 'SUNAT',
      status: 'OPERATIONAL',
    })
  })

  it('inicia una importación con el contrato aceptado por el backend', async () => {
    mockedRequest.mockResolvedValue({
      id: 'job-1',
      dataset_type: 'RUC_GENERAL',
      status: 'QUEUED',
      created_at: '2026-07-28T12:00:00Z',
    })

    await rucIntegrationApi.startImport('RUC_GENERAL', 'Actualización mensual')

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/ruc/imports',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'csrf-token' },
      body: { dataset_type: 'RUC_GENERAL' },
    })
  })

  it('verifica y aplica datos usando las rutas RUC del socio', async () => {
    mockedRequest
      .mockResolvedValueOnce({
        verification_id: 'verification-1',
        ruc: '20123456789',
        verification_result: 'VERIFIED',
        confidence_level: 'HIGH',
        status: 'CURRENT',
      })
      .mockResolvedValueOnce({ message: 'ok' })

    const verification = await rucIntegrationApi.verifyPartnerRuc('partner-1', true)
    await rucIntegrationApi.applyRucDataToPartner('partner-1', {
      verification_id: verification.verification_id,
      apply_legal_name: true,
      reason: 'Sincronización con SUNAT',
    })

    expect(mockedRequest).toHaveBeenNthCalledWith(1, {
      path: '/logistics/ruc/business-partners/partner-1/verify-ruc?allow_provider=true',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'csrf-token' },
    })
    expect(mockedRequest).toHaveBeenNthCalledWith(2, {
      path: '/logistics/ruc/business-partners/partner-1/apply-ruc-data',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'csrf-token' },
      body: {
        verification_id: 'verification-1',
        apply_legal_name: true,
        reason: 'Sincronización con SUNAT',
      },
    })
  })
})
