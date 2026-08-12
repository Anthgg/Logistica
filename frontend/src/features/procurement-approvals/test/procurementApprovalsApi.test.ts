import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../api/api-client'
import {
  parseApprovalAssignments,
  parseApprovalAuditSeal,
  procurementApprovalsApi,
} from '../api/procurementApprovalsApi'

vi.mock('../../../api/api-client', () => ({
  apiRequest: vi.fn(),
}))

const mockedRequest = vi.mocked(apiRequest)

describe('procurementApprovalsApi · contrato backend 0.9.1', () => {
  beforeEach(() => {
    mockedRequest.mockReset()
    mockedRequest.mockResolvedValue({})
  })

  it('lista políticas con organización y tipo de recurso', async () => {
    mockedRequest.mockResolvedValueOnce([])

    await procurementApprovalsApi.listPolicies(
      'organization-1',
      'PURCHASE_ORDER',
    )

    expect(mockedRequest).toHaveBeenCalledWith({
      path:
        '/logistics/procurement-approvals/policies' +
        '?organization_id=organization-1&subject_type=PURCHASE_ORDER',
    })
  })

  it('registra una decisión sin enviar assurance_level calculado', async () => {
    await procurementApprovalsApi.recordDecision(
      'assignment-1',
      'user-1',
      {
        decision_type: 'REJECT',
        reason: 'La solicitud excede el presupuesto autorizado.',
      },
    )

    expect(mockedRequest).toHaveBeenCalledWith({
      path:
        '/logistics/procurement-approvals/assignments/assignment-1/decision' +
        '?user_id=user-1',
      method: 'POST',
      body: {
        decision_type: 'REJECT',
        reason: 'La solicitud excede el presupuesto autorizado.',
      },
    })
  })

  it('activa una versión usando el user_id del contexto', async () => {
    await procurementApprovalsApi.activateVersion(
      'version-1',
      'user-1',
    )

    expect(mockedRequest).toHaveBeenCalledWith({
      path:
        '/logistics/procurement-approvals/policy-versions/version-1/activate' +
        '?user_id=user-1',
      method: 'POST',
    })
  })
})

describe('parsers defensivos de respuestas OpenAPI sin schema', () => {
  it('extrae solo campos seguros de asignaciones', () => {
    const parsed = parseApprovalAssignments({
      items: [
        {
          assignment_id: 'assignment-1',
          status: 'PENDING',
          delegated: true,
          request: {
            id: 'request-1',
            request_code: 'APR-001',
            amount: '1500.00',
            currency_code: 'PEN',
          },
          step: { name: 'Responsable de costo', sequence: 2 },
          signature: 'never-expose-this',
        },
      ],
    })

    expect(parsed).toEqual([
      {
        id: 'assignment-1',
        request_id: 'request-1',
        request_code: 'APR-001',
        subject_type: null,
        subject_id: null,
        subject_code: null,
        status: 'PENDING',
        step_name: 'Responsable de costo',
        step_sequence: 2,
        due_at: null,
        amount: '1500.00',
        currency_code: 'PEN',
        delegated: true,
      },
    ])
    expect(JSON.stringify(parsed)).not.toContain('never-expose-this')
  })

  it('no conserva firma ni digest completo del sello', () => {
    const parsed = parseApprovalAuditSeal({
      seal_id: 'seal-1',
      integrity_status: 'VALID',
      signature_algorithm: 'KMS_RSA_SHA256',
      kms_key_id: 'key-1',
      signature: 'private-signature',
      digest: 'full-digest',
    })

    expect(parsed).toEqual({
      id: 'seal-1',
      status: 'VALID',
      algorithm: 'KMS_RSA_SHA256',
      key_id: 'key-1',
      created_at: null,
      verified_at: null,
      verification_status: null,
    })
    expect(JSON.stringify(parsed)).not.toContain('private-signature')
    expect(JSON.stringify(parsed)).not.toContain('full-digest')
  })
})
