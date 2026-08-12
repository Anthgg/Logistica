import { render, type RenderResult } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, type InitialEntry } from 'react-router-dom'
import {
  AuthContext,
  type AuthContextValue,
} from '../contexts/auth-context'
import {
  I18nContext,
  type I18nContextValue,
} from '../contexts/i18n-context'
import {
  ContinuousAuthContext,
  type ContinuousAuthContextValue,
} from '../features/continuous-auth/contexts/continuous-auth-context'
import type { ContinuousAuthStatus } from '../features/continuous-auth/types/continuous-auth'
import type { AuthResponse } from '../types/auth'
import type { I18nCatalogResponse } from '../types/i18n'
import type { CurrentSession } from '../types/session'
import type { User } from '../types/user'

export const testUser: User = {
  id: '0f02a6e1-b9ca-4e4a-b85d-5fd469943a78',
  email: 'usuario@example.com',
  full_name: 'Usuario de Prueba',
  role: 'admin',
  is_active: true,
  is_verified: true,
  created_at: '2026-01-10T10:00:00Z',
}

export const testSession: CurrentSession = {
  id: '481f1eb4-5eb0-43f8-b5ac-5e44491730d2',
  authentication_level: 'password',
  created_at: '2026-07-20T10:00:00Z',
  last_activity_at: '2026-07-23T10:00:00Z',
  expires_at: '2026-08-20T10:00:00Z',
  device_id: null,
}

export const testAuthResponse: AuthResponse = {
  success: true,
  message: 'Operación completada',
  user: testUser,
  session: testSession,
}

export const testContinuousAuthStatus: ContinuousAuthStatus = {
  enabled: true,
  continuous_auth_status: 'active',
  risk_level: 'low',
  authentication_level: 'continuously_verified',
  last_evaluation_at: '2026-07-23T10:00:00Z',
  recommended_action: 'maintain_session',
  applied_action: 'maintain_session',
  components_available: [],
  next_evaluation_after: null,
  degraded: false,
  degraded_reason: null,
}

export const testCatalog: I18nCatalogResponse = {
  locale: 'es',
  supported_locales: ['es', 'en', 'pt'],
  translations: {
    common: {
      admin: 'Administrador',
      operator: 'Operador',
    },
    status: {
      active: 'Activo',
      inactive: 'Inactivo',
      registered: 'Registrado',
      pending_pickup: 'Por recoger',
      picked_up: 'Recogido',
      warehouse_received: 'En almacén',
      in_transit: 'En tránsito',
      out_for_delivery: 'En reparto',
      delivered: 'Entregado',
      delayed: 'Retrasado',
      cancelled: 'Cancelado',
      returned: 'Devuelto',
    },
    priority: {
      low: 'Baja',
      normal: 'Normal',
      high: 'Alta',
      urgent: 'Urgente',
    },
    event: {},
    resource: {
      system: 'sistema',
    },
    risk: {
      low: 'Riesgo bajo',
      medium: 'Riesgo moderado',
      high: 'Riesgo alto',
      critical: 'Riesgo crítico',
      unknown: 'Riesgo sin determinar',
    },
    auth_level: {
      traditional: 'Sesión tradicional',
      continuously_verified: 'Identidad verificada continuamente',
      verification_required: 'Reverificación requerida',
      restricted: 'Sesión restringida',
      terminated: 'Sesión finalizada',
      password: 'Contraseña',
    },
    continuous_auth_status: {
      active: 'Activa',
      available: 'Disponible',
      pending: 'Pendiente',
      unavailable: 'No disponible',
      failed: 'Error temporal',
      degraded: 'Disponibilidad limitada',
    },
    action: {
      maintain_session: 'Mantener sesión',
      increase_monitoring: 'Incrementar supervisión',
      request_reverification: 'Solicitar reverificación',
      restrict_sensitive_operations: 'Restringir operaciones sensibles',
      terminate_session: 'Finalizar sesión',
      none: 'Sin acción adicional',
    },
  },
}

export function createI18nValue(
  overrides: Partial<I18nContextValue> = {},
): I18nContextValue {
  const catalog = overrides.catalog ?? testCatalog

  return {
    language: 'es-PE',
    locale: catalog.locale,
    catalog,
    catalogVersion: 1,
    contentLanguage: 'es',
    isChangingLanguage: false,
    error: null,
    translate: (namespace, key, fallback) =>
      catalog.translations[namespace][key] ?? fallback ?? key,
    changeLanguage: async () => undefined,
    reloadCatalog: async () => undefined,
    clearError: () => undefined,
    ...overrides,
  }
}

export function createContinuousAuthValue(
  overrides: Partial<ContinuousAuthContextValue> = {},
): ContinuousAuthContextValue {
  const status =
    'status' in overrides
      ? (overrides.status ?? null)
      : testContinuousAuthStatus

  return {
    status,
    riskLevel: status?.risk_level ?? 'unknown',
    authenticationLevel:
      status?.authentication_level ?? 'traditional',
    recommendedAction: status?.recommended_action ?? 'none',
    appliedAction: status?.applied_action ?? 'none',
    components: status?.components_available ?? [],
    isLoading: false,
    isEvaluating: false,
    isReverifying: false,
    isPolling: true,
    error: null,
    errorCode: null,
    notice: null,
    lastUpdatedAt: '2026-07-23T10:00:00Z',
    isReverificationOpen: false,
    refreshStatus: async () => status,
    evaluate: async () => null,
    reverify: async () => ({
      success: true,
      authentication_level: 'continuously_verified',
      continuous_auth_status: 'active',
      reverified_at: '2026-07-23T10:00:00Z',
    }),
    clearError: () => undefined,
    clearNotice: () => undefined,
    stopPolling: () => undefined,
    startPolling: () => undefined,
    requestReverification: () => undefined,
    closeReverification: () => undefined,
    handleSecurityError: () => undefined,
    ...overrides,
  }
}

export function createAuthValue(
  overrides: Partial<AuthContextValue> = {},
): AuthContextValue {
  return {
    user: null,
    session: null,
    currentSession: null,
    isAuthenticated: false,
    isLoading: false,
    authError: null,
    login: async () => testAuthResponse,
    register: async () => testAuthResponse,
    logout: async () => undefined,
    logoutAll: async () => undefined,
    refreshSession: async () => testAuthResponse,
    changePassword: async () => ({
      success: true,
      message: 'Contraseña actualizada.',
      revoked_sessions: 0,
    }),
    reloadCurrentUser: async () => undefined,
    refreshUser: async () => undefined,
    clearAuthError: () => undefined,
    invalidateSession: () => undefined,
    ...overrides,
  }
}

export function renderWithAuth(
  element: ReactElement,
  options: {
    auth?: AuthContextValue
    continuousAuth?: ContinuousAuthContextValue
    i18n?: I18nContextValue
    initialEntries?: InitialEntry[]
  } = {},
): RenderResult {
  const auth = options.auth ?? createAuthValue()
  const continuousAuth =
    options.continuousAuth ?? createContinuousAuthValue()
  const i18n = options.i18n ?? createI18nValue()
  const initialEntries = options.initialEntries ?? ['/']

  return render(
    <I18nContext.Provider value={i18n}>
      <AuthContext.Provider value={auth}>
        <ContinuousAuthContext.Provider value={continuousAuth}>
          <MemoryRouter initialEntries={initialEntries}>
            {element}
          </MemoryRouter>
        </ContinuousAuthContext.Provider>
      </AuthContext.Provider>
    </I18nContext.Provider>,
  )
}
