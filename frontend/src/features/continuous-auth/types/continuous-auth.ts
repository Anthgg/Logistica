export type RiskLevel =
  | 'low'
  | 'medium'
  | 'high'
  | 'critical'
  | 'unknown'

export type AuthenticationLevel =
  | 'traditional'
  | 'continuously_verified'
  | 'verification_required'
  | 'restricted'
  | 'terminated'

export type RecommendedAction =
  | 'maintain_session'
  | 'increase_monitoring'
  | 'request_reverification'
  | 'restrict_sensitive_operations'
  | 'terminate_session'
  | 'none'

export type ComponentStatus =
  | 'available'
  | 'unavailable'
  | 'pending'
  | 'failed'
  | 'degraded'

export interface ContinuousAuthComponentSummary {
  name: string
  available: boolean
  status: ComponentStatus
  last_evaluated_at: string | null
  reason: string | null
}

export interface ContinuousAuthStatus {
  enabled: boolean
  continuous_auth_status: string
  risk_level: RiskLevel
  risk_score?: number
  authentication_level: AuthenticationLevel
  last_evaluation_at: string | null
  recommended_action: RecommendedAction
  applied_action: RecommendedAction
  components_available: ContinuousAuthComponentSummary[]
  next_evaluation_after: string | null
  degraded: boolean
  degraded_reason: string | null
}

export interface ContinuousAuthEvaluationRequest {
  experimental_session_id: string
  facial_capture_id: string | null
  behavioral_window_id: string | null
  evaluation_timestamp: string
}

export interface ContinuousAuthEvaluationResponse {
  id: string
  risk_score: number
  risk_level: RiskLevel
  authentication_level: AuthenticationLevel
  recommended_action: RecommendedAction
  applied_action: RecommendedAction
  evaluated_at: string
  components: ContinuousAuthComponentSummary[]
}

export interface ReverificationRequest {
  password: string
}

export interface ReverificationResponse {
  success: boolean
  authentication_level: AuthenticationLevel
  continuous_auth_status: string
  reverified_at: string
}

export interface AdminEvaluationSummary {
  id: string
  user_id: string
  session_id: string
  participant_id: string | null
  risk_level: RiskLevel
  authentication_level: AuthenticationLevel
  recommended_action: RecommendedAction
  applied_action: RecommendedAction
  latency_ms: number
  evaluated_at: string
}

export interface AdminEntitySummary {
  id: string
  label: string | null
}

export interface RiskHistoryEntry {
  id: string
  risk_level: RiskLevel
  authentication_level: AuthenticationLevel
  recommended_action: RecommendedAction
  applied_action: RecommendedAction
  evaluated_at: string
}

export interface AdminEvaluationDetail {
  id: string
  user: AdminEntitySummary
  session: AdminEntitySummary
  participant: AdminEntitySummary | null
  component_scores: Record<string, number | null>
  component_risks: Record<string, number | null>
  combined_risk: number | null
  risk_level: RiskLevel
  authentication_level: AuthenticationLevel
  recommended_action: RecommendedAction
  applied_action: RecommendedAction
  model_versions: Record<string, string>
  latency: number | Record<string, number>
  evaluated_at: string
  risk_history?: RiskHistoryEntry[]
}

export interface ModelStatus {
  overall_status: string
  facial_loaded: boolean
  pad_loaded: boolean
  behavioral_available_count: number
  behavioral_loaded_count: number
  versions: Record<string, string>
  device: string
  loaded_at: string | null
  checksums_valid: boolean
  fusion_loaded: boolean
  normalization_loaded: boolean
  errors: string[]
}

export interface EvaluationFiltersValue {
  user_id: string
  session_id: string
  participant_id: string
  risk_level: RiskLevel | ''
  authentication_level: AuthenticationLevel | ''
  date_from: string
  date_to: string
}

export interface EvaluationListQuery {
  user_id?: string
  session_id?: string
  participant_id?: string
  risk_level?: Exclude<RiskLevel, 'unknown'>
  authentication_level?: AuthenticationLevel
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export interface AdminEvaluationPage {
  items: AdminEvaluationSummary[]
  page: number
  page_size: number
  total: number
  total_pages: number
}
