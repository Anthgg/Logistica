import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../api/api-client'
import { purchaseOrdersV2Api } from '../api/purchaseOrdersV2Api'

vi.mock('../../../api/api-client', () => ({
  apiRequest: vi.fn(),
}))

const mockedRequest = vi.mocked(apiRequest)

describe('purchaseOrdersV2Api · contrato backend 0.9.1', () => {
  beforeEach(() => {
    mockedRequest.mockReset()
    mockedRequest.mockResolvedValue([])
  })

  it('lista únicamente con filtros publicados y paginación offset/limit', async () => {
    await purchaseOrdersV2Api.list({
      branch_id: 'branch-1',
      supplier_id: 'supplier-1',
      status: 'DRAFT',
      approval_status: 'PENDING',
      limit: 20,
      offset: 40,
    })

    expect(mockedRequest).toHaveBeenCalledWith({
      path:
        '/logistics/procurement/purchase-orders' +
        '?branch_id=branch-1&supplier_id=supplier-1&status=DRAFT' +
        '&approval_status=PENDING&limit=20&offset=40',
    })
  })

  it('crea el plan con evaluation_decision_id sin ejecutar órdenes', async () => {
    mockedRequest.mockResolvedValueOnce({
      evaluation_decision_id: 'decision-1',
      evaluation_decision_status: 'RECORDED',
      is_executable: true,
      total_orders_to_create: 2,
    })

    await purchaseOrdersV2Api.createGenerationPlan({
      evaluation_decision_id: 'decision-1',
    })

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/procurement/purchase-orders/plan-generation',
      method: 'POST',
      body: { evaluation_decision_id: 'decision-1' },
    })
  })

  it('envía los motivos con los nombres exactos del OpenAPI', async () => {
    mockedRequest.mockResolvedValue({
      revisions: [],
    })

    await purchaseOrdersV2Api.reject(
      'po-1',
      { reason: 'El presupuesto requiere una revisión adicional.' },
      'key-reject',
    )
    await purchaseOrdersV2Api.returnForChanges(
      'po-1',
      { reason: 'Corrige las condiciones comerciales antes de continuar.' },
      'key-return',
    )
    await purchaseOrdersV2Api.cancel(
      'po-1',
      { cancellation_reason: 'Proveedor sin disponibilidad confirmada.' },
      'key-cancel',
    )

    expect(mockedRequest).toHaveBeenNthCalledWith(1, {
      path: '/logistics/procurement/purchase-orders/po-1/reject',
      method: 'POST',
      headers: { 'X-Idempotency-Key': 'key-reject' },
      body: {
        reason: 'El presupuesto requiere una revisión adicional.',
      },
    })
    expect(mockedRequest).toHaveBeenNthCalledWith(2, {
      path:
        '/logistics/procurement/purchase-orders/po-1/return-for-changes',
      method: 'POST',
      headers: { 'X-Idempotency-Key': 'key-return' },
      body: {
        reason: 'Corrige las condiciones comerciales antes de continuar.',
      },
    })
    expect(mockedRequest).toHaveBeenNthCalledWith(3, {
      path: '/logistics/procurement/purchase-orders/po-1/cancel',
      method: 'POST',
      headers: { 'X-Idempotency-Key': 'key-cancel' },
      body: {
        cancellation_reason: 'Proveedor sin disponibilidad confirmada.',
      },
    })
  })

  it('no llama al backend para documentos todavía no publicados', async () => {
    await expect(
      purchaseOrdersV2Api.downloadDocument('po-1', 'document-1'),
    ).rejects.toThrow('todavía no está publicado')
    expect(mockedRequest).not.toHaveBeenCalled()
  })
})
