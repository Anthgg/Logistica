import type { Identifier, PaginatedResponse } from './operations'

export type ResearchScenario =
  | 'register_shipment'
  | 'search_shipment'
  | 'update_shipment_status'
  | 'assign_route'
  | 'register_inventory_movement'
  | 'report_incident'
  | 'review_dashboard'
  | 'mixed_operations'
export type ResearchSessionStatus =
  | 'created'
  | 'active'
  | 'completed'
  | 'cancelled'
  | 'invalid'

export interface Participant {
  id: Identifier
  linked_user_id: Identifier | null
  participant_code: string
  is_active: boolean
  enrollment_date: string
  withdrawal_date: string | null
  created_at: string
  updated_at: string
}
export interface SelfEnrollResponse {
  success: boolean
  created: boolean
  participant: Participant
}
export interface Consent {
  id: Identifier
  participant_id: Identifier
  consent_version: string
  accepted: boolean
  accepted_at: string
  withdrawn_at: string | null
}
export interface CollectorConfiguration {
  id: Identifier
  scenario: ResearchScenario
  status: ResearchSessionStatus
  started_at: string
  capture_interval_seconds: number
  batch_interval_seconds: number
  max_batch_events: number
  max_image_size_bytes: number
}
export interface ExperimentalSession {
  id: Identifier
  participant_id: Identifier
  scenario: ResearchScenario
  status: ResearchSessionStatus
  started_at: string
  ended_at: string | null
  duration_seconds: number
  facial_capture_count: number
  keyboard_event_count: number
  mouse_event_count: number
  batch_count: number
  error_count: number
  protocol_version: string
  collector_version: string
  identity_label: 'genuine' | 'impostor'
  sample_role: 'enrollment' | 'verification' | 'change_operator'
  operator_change_at: string | null
  presentation_label: 'bona_fide' | 'attack' | null
  attack_type:
    | 'none'
    | 'printed_photo'
    | 'screen_photo'
    | 'replayed_video'
    | null
  source_device: string | null
  pad_source_id: string | null
  annotation_status: 'pending' | 'confirmed'
}
export interface StartSessionRequest {
  participant_id: string
  scenario: ResearchScenario
  expected_duration_minutes: number
  client_timezone: string
  client_timezone_offset_minutes: number
  client_language: string
  screen_width: number
  screen_height: number
  screen_pixel_ratio: number
  browser: string
  operating_system: string
  device_type: string
  collector_version: string
}
export interface SessionStartResponse {
  success: boolean
  session: CollectorConfiguration
}
export interface SessionMutationResponse {
  success: boolean
  session: ExperimentalSession
}
export interface ExperimentalSessionAnnotation {
  identity_label: 'genuine' | 'impostor'
  sample_role: 'enrollment' | 'verification' | 'change_operator'
  operator_change_at?: string | null
  presentation_label?: 'bona_fide' | 'attack' | null
  attack_type?:
    | 'none'
    | 'printed_photo'
    | 'screen_photo'
    | 'replayed_video'
    | null
  source_device?: string | null
  pad_source_id?: string | null
  annotation_notes?: string | null
  confirmed?: boolean
}
export interface BehavioralBatchResponse {
  success: boolean
  id: Identifier
  batch_id: Identifier
  sequence_number: number
  event_count: number
  keyboard_event_count: number
  mouse_event_count: number
  idempotent_replay: boolean
  behavioral_window_id?: Identifier | null
}
export interface FacialCaptureResponse {
  success: boolean
  id: Identifier
  sequence_number: number
  file_size: number
  width: number
  height: number
  captured_at: string
  processing_status: string
  idempotent_replay: boolean
}
export type KeyboardCategory =
  | 'alphanumeric'
  | 'navigation'
  | 'modifier'
  | 'correction'
  | 'function'
  | 'other'

export interface KeyboardBehaviorEvent {
  type: 'keyboard'
  event: 'timing'
  timestamp: string
  sequence_index: number
  category: KeyboardCategory
  dwell_time_ms: number
  flight_time_ms: number
  interval_from_previous_ms: number
  is_backspace: boolean
  is_modifier: boolean
}

export type MouseBehaviorEventName =
  | 'move'
  | 'click'
  | 'scroll'
  | 'pointerdown'
  | 'pointerup'

export type MouseButtonCategory =
  | 'primary'
  | 'middle'
  | 'secondary'
  | 'none'
  | 'other'

export interface MouseBehaviorEvent {
  type: 'mouse'
  event: MouseBehaviorEventName
  timestamp: string
  sequence_index: number
  normalized_x: number
  normalized_y: number
  delta_x: number
  delta_y: number
  distance: number
  velocity: number
  button_category: MouseButtonCategory
  scroll_delta: number
}

export type BehavioralEvent = KeyboardBehaviorEvent | MouseBehaviorEvent
export interface BehavioralBatch {
  batch_id: string
  sequence_number: number
  started_at: string
  ended_at: string
  visibility_state: string
  client_timezone_offset_minutes: number
  dropped_event_count: number
  collector_error_count: number
  events: BehavioralEvent[]
}
export interface ResearchSessionState {
  configuration: CollectorConfiguration
  participantId: Identifier
  startedAtEpoch: number
  errorCount: number
  cameraEnabled: boolean
}
export type ExperimentalSessionPage = PaginatedResponse<ExperimentalSession>
