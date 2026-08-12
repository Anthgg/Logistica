import { envConfig } from '../config/environment'

declare global {
  interface Window {
    APP_CONFIG?: {
      API_URL?: string
    }
  }
}

export const API_URL = envConfig.apiUrl
export const API_ROOT = API_URL
export const APP_NAME = envConfig.appName
export const APP_ENV = envConfig.appEnv
export const APP_VERSION = envConfig.appVersion
export const BUILD_SHA = envConfig.buildSha
export const COMPANY_NAME = envConfig.companyName

export const CONTINUOUS_AUTH_STATUS_INTERVAL_MS = envConfig.continuousAuth.statusIntervalMs
export const CONTINUOUS_AUTH_MAX_FAILURES = envConfig.continuousAuth.maxFailures

export const FEATURE_FLAGS = envConfig.featureFlags
