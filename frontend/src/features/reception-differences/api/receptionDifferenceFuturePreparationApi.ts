import { apiRequest } from '../../../api/api-client'
import type {
  QualityInspectionPreparation,
  FutureQuarantineRecommendation,
  FutureClaimPreparation,
} from '../types/reception-differences'

const BASE = '/logistics/reception-difference-cases'

export const receptionDifferenceFuturePreparationApi = {
  async getQualityPreparation(caseId: string): Promise<QualityInspectionPreparation> {
    return apiRequest({ path: `${BASE}/${caseId}/quality-preparation`, method: 'GET' })
  },

  async getQuarantineRecommendations(caseId: string): Promise<FutureQuarantineRecommendation[]> {
    return apiRequest({ path: `${BASE}/${caseId}/quarantine-recommendations`, method: 'GET' })
  },

  async getClaimPreparation(caseId: string): Promise<FutureClaimPreparation> {
    return apiRequest({ path: `${BASE}/${caseId}/claim-preparation`, method: 'GET' })
  },
}
