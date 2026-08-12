import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from './api-client'
import { purchaseOrdersApi } from './purchase-orders-api'

vi.mock('./api-client', () => ({
  apiRequest: vi.fn(),
  getCsrfToken: vi.fn().mockResolvedValue('test-csrf-token'),
}))

const mockedRequest = vi.mocked(apiRequest)

describe('purchaseOrdersApi', () => {
  beforeEach(() => {
    mockedRequest.mockReset()
    mockedRequest.mockResolvedValue({ id: 'po-1' })
  })

  it('envía únicamente los filtros soportados al listar', async () => {
    await purchaseOrdersApi.list({
      status: 'APPROVED',
      supplier_id: 'supplier-1',
    })

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/procurement/purchase-orders?status=APPROVED&supplier_id=supplier-1',
    })
  })

  it('usa la transición real para emitir', async () => {
    await purchaseOrdersApi.issue('po-1')

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/procurement/purchase-orders/po-1/submit',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'test-csrf-token' },
    })
  })

  it('adjunta el comprobante step-up al aprobar', async () => {
    await purchaseOrdersApi.approve('po-1', 'proof-1')

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/procurement/purchase-orders/po-1/approve',
      method: 'POST',
      headers: {
        'X-CSRF-Token': 'test-csrf-token',
        'X-Step-Up-Proof-ID': 'proof-1',
      },
    })
  })

  it('envía el motivo requerido al anular', async () => {
    await purchaseOrdersApi.cancel('po-1', {
      reason: 'Proveedor sin disponibilidad confirmada.',
    })

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/procurement/purchase-orders/po-1/cancel',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'test-csrf-token' },
      body: { reason: 'Proveedor sin disponibilidad confirmada.' },
    })
  })
})
