import { apiRequest } from '../../../api/api-client'
import type {
  QualityQuarantineIntegrity,
  PutawayPreparation,
  FutureInventoryMovementPreparation,
  FutureInventoryBalancePreparation,
  FutureTraceabilityPreparation,
} from '../types/quarantine'

export const quarantineIntegrityApi = {
  /** GET /quality-quarantine-cases/{caseId}/integrity */
  async getIntegrity(caseId: string): Promise<QualityQuarantineIntegrity> {
    return apiRequest({ path: `/logistics/quality-quarantine-cases/${caseId}/integrity`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/putaway-preparation */
  async getPutawayPreparation(caseId: string): Promise<PutawayPreparation> {
    return apiRequest({ path: `/logistics/quality-quarantine-cases/${caseId}/putaway-preparation`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/future-movement-preparation */
  async getFutureMovementPreparation(caseId: string): Promise<FutureInventoryMovementPreparation> {
    return apiRequest({ path: `/logistics/quality-quarantine-cases/${caseId}/future-movement-preparation`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/future-balance-preparation */
  async getFutureBalancePreparation(caseId: string): Promise<FutureInventoryBalancePreparation> {
    return apiRequest({ path: `/logistics/quality-quarantine-cases/${caseId}/future-balance-preparation`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/future-traceability-preparation */
  async getFutureTraceabilityPreparation(caseId: string): Promise<FutureTraceabilityPreparation> {
    return apiRequest({ path: `/logistics/quality-quarantine-cases/${caseId}/future-traceability-preparation`, method: 'GET' })
  },
}
