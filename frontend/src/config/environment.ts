export type AppEnvironment = 'local' | 'test' | 'staging' | 'production'

export interface AppConfig {
  readonly appEnv: AppEnvironment
  readonly appName: string
  readonly appVersion: string
  readonly buildSha: string
  readonly apiUrl: string
  readonly companyName: string
  readonly featureFlags: {
    readonly logisticsEnabled: boolean
    readonly stepUpEnabled: boolean
    readonly auditEnabled: boolean
    readonly mapsEnabled: boolean
    readonly documentsEnabled: boolean
  }
  readonly continuousAuth: {
    readonly statusIntervalMs: number
    readonly maxFailures: number
  }
}

function parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
  if (value === undefined || value === '') return defaultValue
  return value.toLowerCase() === 'true' || value === '1'
}

function parsePositiveInt(value: string | undefined, fallback: number): number {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback
}

function validateAndResolveApiUrl(rawUrl: string | undefined, env: AppEnvironment): string {
  const inputUrl = rawUrl?.trim() || (env === 'production'
    ? 'https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/api'
    : 'http://localhost:8000/api')

  let normalized = inputUrl.replace(/\/+$/, '')

  // Permitir rutas relativas como "/api"
  if (normalized.startsWith('/')) {
    if (normalized.startsWith('//')) {
      normalized = normalized.replace(/^\/+/, '/')
    }
    if (!normalized.endsWith('/api')) {
      normalized = `${normalized}/api`.replace(/\/+/g, '/')
    }
    return normalized
  }

  // Prevent double /api/api
  if (normalized.endsWith('/api/api')) {
    normalized = normalized.slice(0, -4)
  }

  let parsed: URL
  try {
    parsed = new URL(normalized)
  } catch {
    parsed = new URL('http://localhost:8000/api')
  }

  if (env === 'production' && parsed.protocol !== 'https:') {
    throw new Error(`[Config Error] VITE_API_URL debe usar HTTPS en producción. Recibido: "${inputUrl}"`)
  }

  if (env === 'production' && (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1')) {
    throw new Error(`[Config Error] VITE_API_URL no puede apuntar a localhost en ambiente de producción.`)
  }

  let cleanPath = parsed.pathname.replace(/\/+$/, '')
  if (!cleanPath.endsWith('/api')) {
    cleanPath = `${cleanPath}/api`
  }
  parsed.pathname = cleanPath

  return parsed.toString().replace(/\/+$/, '')
}

function resolveAppEnvironment(rawEnv: string | undefined): AppEnvironment {
  const normalized = rawEnv?.trim().toLowerCase()
  if (normalized === 'production' || normalized === 'prod') return 'production'
  if (normalized === 'staging' || normalized === 'stg') return 'staging'
  if (normalized === 'test') return 'test'
  return 'local'
}

export function loadEnvironmentConfig(): AppConfig {
  const rawEnv = import.meta.env.VITE_APP_ENV
  const appEnv = resolveAppEnvironment(rawEnv)

  const apiUrl = validateAndResolveApiUrl(import.meta.env.VITE_API_URL, appEnv)

  return {
    appEnv,
    appName: import.meta.env.VITE_APP_NAME?.trim() || 'AndesLog Operaciones S.A.C.',
    appVersion: import.meta.env.VITE_APP_VERSION?.trim() || '1.0.0',
    buildSha: import.meta.env.VITE_BUILD_SHA?.trim() || 'dev-build',
    companyName: import.meta.env.VITE_COMPANY_NAME?.trim() || 'AndesLog Operaciones S.A.C.',
    apiUrl,
    featureFlags: {
      logisticsEnabled: parseBoolean(import.meta.env.VITE_LOGISTICS_ENABLED, true),
      stepUpEnabled: parseBoolean(import.meta.env.VITE_STEP_UP_ENABLED, true),
      auditEnabled: parseBoolean(import.meta.env.VITE_AUDIT_ENABLED, true),
      mapsEnabled: parseBoolean(import.meta.env.VITE_MAPS_ENABLED, true),
      documentsEnabled: parseBoolean(import.meta.env.VITE_DOCUMENTS_ENABLED, true),
    },
    continuousAuth: {
      statusIntervalMs: parsePositiveInt(import.meta.env.VITE_CONTINUOUS_AUTH_STATUS_INTERVAL_MS, 10_000),
      maxFailures: parsePositiveInt(import.meta.env.VITE_CONTINUOUS_AUTH_MAX_FAILURES, 3),
    },
  }
}

export const envConfig = loadEnvironmentConfig()
