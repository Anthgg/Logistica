export interface CurrentSession {
  id: string
  authentication_level: string
  created_at: string
  last_activity_at: string
  expires_at: string
  device_id: string | null
}

export interface SessionSummary {
  id: string
  device_name: string | null
  browser: string | null
  operating_system: string | null
  device_type: string | null
  ip_address: string | null
  created_at: string
  last_activity_at: string
  expires_at: string
  is_current: boolean
}

export interface SessionsResponse {
  success: boolean
  sessions: SessionSummary[]
}
