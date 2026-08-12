import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  InventoryLedgerCheckpointApi,
  InventoryLedgerReconciliationJobApi,
  InventoryLedgerReconciliationResultApi,
  InventoryLedgerVerificationApi,
} from '../types/inventory-ledger-api'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

function query(params: Record<string, string | number>): string {
  return `?${new URLSearchParams(
    Object.entries(params).map(([key, value]) => [key, String(value)]),
  ).toString()}`
}

export const inventoryLedgerIntegrityApi = {
  async verifyInventoryLedgerPartition(
    organizationId: string,
    partitionId: string,
  ): Promise<InventoryLedgerVerificationApi> {
    return apiRequest({
      path: `/logistics/inventory/ledger/partitions/${partitionId}/verify${query({ organization_id: organizationId })}`,
      method: 'POST',
      headers: { 'Idempotency-Key': generateKey() },
    })
  },

  async createInventoryLedgerCheckpoint(
    organizationId: string,
    partitionId: string,
    fromSequence: number,
    toSequence: number,
  ): Promise<InventoryLedgerCheckpointApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/ledger/partitions/${partitionId}/checkpoints${query({
        organization_id: organizationId,
        from_sequence: fromSequence,
        to_sequence: toSequence,
      })}`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },

  async createInventoryLedgerReconciliationJob(
    organizationId: string,
    scope: Record<string, unknown>,
  ): Promise<InventoryLedgerReconciliationJobApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/inventory/ledger/reconciliation-jobs${query({ organization_id: organizationId })}`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { scope },
    })
  },

  async getInventoryLedgerReconciliationJob(
    organizationId: string,
    jobId: string,
  ): Promise<InventoryLedgerReconciliationJobApi> {
    return apiRequest({
      path: `/logistics/inventory/ledger/reconciliation-jobs/${jobId}${query({ organization_id: organizationId })}`,
      method: 'GET',
    })
  },

  async listInventoryLedgerReconciliationResults(
    organizationId: string,
    jobId: string,
  ): Promise<InventoryLedgerReconciliationResultApi[]> {
    return apiRequest({
      path: `/logistics/inventory/ledger/reconciliation-jobs/${jobId}/results${query({ organization_id: organizationId })}`,
      method: 'GET',
    })
  },
}
