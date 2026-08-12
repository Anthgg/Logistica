/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_ENV: 'local' | 'test' | 'staging' | 'production' | 'development'
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_BUILD_SHA: string
  readonly VITE_API_URL: string
  readonly VITE_LOGISTICS_ENABLED?: string
  readonly VITE_STEP_UP_ENABLED?: string
  readonly VITE_AUDIT_ENABLED?: string
  readonly VITE_MAPS_ENABLED?: string
  readonly VITE_DOCUMENTS_ENABLED?: string
  readonly VITE_COMPANY_NAME?: string
  readonly VITE_CONTINUOUS_AUTH_STATUS_INTERVAL_MS?: string
  readonly VITE_CONTINUOUS_AUTH_MAX_FAILURES?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
