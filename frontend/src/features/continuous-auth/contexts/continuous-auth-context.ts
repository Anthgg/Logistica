import { createContext } from 'react'
import type {
  AuthenticationLevel,
  ContinuousAuthComponentSummary,
  ContinuousAuthEvaluationResponse,
  ContinuousAuthStatus,
  RecommendedAction,
  ReverificationResponse,
  RiskLevel,
} from '../types/continuous-auth'

export interface ContinuousAuthContextValue {
  status: ContinuousAuthStatus | null
  riskLevel: RiskLevel
  authenticationLevel: AuthenticationLevel
  recommendedAction: RecommendedAction
  appliedAction: RecommendedAction
  components: ContinuousAuthComponentSummary[]
  isLoading: boolean
  isEvaluating: boolean
  isReverifying: boolean
  isPolling: boolean
  error: string | null
  errorCode: string | null
  notice: string | null
  lastUpdatedAt: string | null
  isReverificationOpen: boolean
  refreshStatus: () => Promise<ContinuousAuthStatus | null>
  evaluate: () => Promise<ContinuousAuthEvaluationResponse | null>
  reverify: (password: string) => Promise<ReverificationResponse>
  clearError: () => void
  clearNotice: () => void
  stopPolling: () => void
  startPolling: () => void
  requestReverification: () => void
  closeReverification: () => void
  handleSecurityError: (error: unknown) => void
}

export const ContinuousAuthContext =
  createContext<ContinuousAuthContextValue | null>(null)
