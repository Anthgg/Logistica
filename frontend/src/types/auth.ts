import type { CurrentSession } from './session'
import type { User } from './user'

export interface AuthResponse {
  success: boolean
  message: string
  user: User
  session: CurrentSession | null
}

export interface RegisterRequest {
  full_name: string
  email: string
  password: string
  password_confirmation: string
  accept_terms: boolean
}

export interface LoginRequest {
  email: string
  password: string
  remember_me: boolean
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  new_password_confirmation: string
  logout_other_sessions: boolean
}

export interface ActionResponse {
  success: boolean
  message: string
  revoked_sessions: number | null
}
