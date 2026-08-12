import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  changePassword as changePasswordRequest,
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  logoutAll as logoutAllRequest,
  refreshSession as refreshSessionRequest,
  register as registerRequest,
} from '../api/auth-api'
import { subscribeToUnauthorized } from '../api/auth-events'
import { clearCsrfToken } from '../api/csrf'
import { ApiRequestError } from '../types/api'
import type {
  ActionResponse,
  AuthResponse,
  ChangePasswordRequest,
  LoginRequest,
  RegisterRequest,
} from '../types/auth'
import type { CurrentSession } from '../types/session'
import type { User } from '../types/user'
import {
  getErrorMessage,
  isAuthenticationError,
} from '../utils/errors'
import { normalizeEmail } from '../utils/validation'
import { AuthContext, type AuthContextValue } from './auth-context'

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [currentSession, setCurrentSession] =
    useState<CurrentSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [authError, setAuthError] = useState<string | null>(null)

  const invalidateSession = useCallback((message?: string) => {
    setUser(null)
    setCurrentSession(null)
    clearCsrfToken()
    setAuthError(message ?? null)
  }, [])

  const loadCurrentUser = useCallback(async (showSessionError: boolean) => {
    setIsLoading(true)

    try {
      const response = await getCurrentUser()
      setUser(response.user)
      setCurrentSession(response.session)
      setAuthError(null)
    } catch (error: unknown) {
      setUser(null)
      setCurrentSession(null)

      if (isAuthenticationError(error)) {
        clearCsrfToken()
        if (
          showSessionError &&
          error instanceof ApiRequestError &&
          error.code !== 'SESSION_REQUIRED'
        ) {
          setAuthError(getErrorMessage(error))
        } else {
          setAuthError(null)
        }
      } else {
        setAuthError(getErrorMessage(error))
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  const reloadCurrentUser = useCallback(
    async () => loadCurrentUser(true),
    [loadCurrentUser],
  )

  useEffect(() => {
    const unsubscribe = subscribeToUnauthorized((error) => {
      invalidateSession(getErrorMessage(error))
    })
    void loadCurrentUser(false)

    return unsubscribe
  }, [invalidateSession, loadCurrentUser])

  const login = useCallback(
    async (payload: LoginRequest): Promise<AuthResponse> => {
      setAuthError(null)

      try {
        const response = await loginRequest({
          ...payload,
          email: normalizeEmail(payload.email),
        })
        setUser(response.user)
        setCurrentSession(response.session)
        clearCsrfToken()
        return response
      } catch (error: unknown) {
        setAuthError(getErrorMessage(error))
        throw error
      }
    },
    [],
  )

  const register = useCallback(
    async (payload: RegisterRequest): Promise<AuthResponse> => {
      setAuthError(null)

      try {
        const response = await registerRequest({
          ...payload,
          full_name: payload.full_name.trim(),
          email: normalizeEmail(payload.email),
        })
        clearCsrfToken()
        return response
      } catch (error: unknown) {
        setAuthError(getErrorMessage(error))
        throw error
      }
    },
    [],
  )

  const logout = useCallback(async (): Promise<void> => {
    setAuthError(null)

    try {
      await logoutRequest()
      invalidateSession()
    } catch (error: unknown) {
      setAuthError(getErrorMessage(error))
      throw error
    }
  }, [invalidateSession])

  const logoutAll = useCallback(async (): Promise<void> => {
    setAuthError(null)

    try {
      await logoutAllRequest()
      invalidateSession()
    } catch (error: unknown) {
      setAuthError(getErrorMessage(error))
      throw error
    }
  }, [invalidateSession])

  const refreshSession = useCallback(async (): Promise<AuthResponse> => {
    setAuthError(null)

    try {
      const response = await refreshSessionRequest()
      setUser(response.user)
      setCurrentSession(response.session)
      return response
    } catch (error: unknown) {
      setAuthError(getErrorMessage(error))
      throw error
    }
  }, [])

  const changePassword = useCallback(
    async (payload: ChangePasswordRequest): Promise<ActionResponse> => {
      setAuthError(null)

      try {
        return await changePasswordRequest(payload)
      } catch (error: unknown) {
        setAuthError(getErrorMessage(error))
        throw error
      }
    },
    [],
  )

  const clearAuthError = useCallback(() => {
    setAuthError(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      session: currentSession,
      currentSession,
      isAuthenticated: user !== null,
      isLoading,
      authError,
      login,
      register,
      logout,
      logoutAll,
      refreshSession,
      changePassword,
      reloadCurrentUser,
      refreshUser: reloadCurrentUser,
      clearAuthError,
      invalidateSession,
    }),
    [
      authError,
      changePassword,
      clearAuthError,
      currentSession,
      invalidateSession,
      isLoading,
      login,
      logout,
      logoutAll,
      refreshSession,
      reloadCurrentUser,
      register,
      user,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
