import { createContext } from 'react'
import type {
  ActionResponse,
  AuthResponse,
  ChangePasswordRequest,
  LoginRequest,
  RegisterRequest,
} from '../types/auth'
import type { CurrentSession } from '../types/session'
import type { User } from '../types/user'

export interface AuthContextValue {
  user: User | null
  session: CurrentSession | null
  currentSession: CurrentSession | null
  isAuthenticated: boolean
  isLoading: boolean
  authError: string | null
  login: (payload: LoginRequest) => Promise<AuthResponse>
  register: (payload: RegisterRequest) => Promise<AuthResponse>
  logout: () => Promise<void>
  logoutAll: () => Promise<void>
  refreshSession: () => Promise<AuthResponse>
  changePassword: (
    payload: ChangePasswordRequest,
  ) => Promise<ActionResponse>
  reloadCurrentUser: () => Promise<void>
  refreshUser: () => Promise<void>
  clearAuthError: () => void
  invalidateSession: (message?: string) => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
)
