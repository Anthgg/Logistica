import { describe, expect, it } from 'vitest'
import { loadEnvironmentConfig } from './environment'

describe('loadEnvironmentConfig', () => {
  it('valida la URL de API y devuelve configuraciones por defecto para desarrollo', () => {
    const config = loadEnvironmentConfig()
    expect(config.apiUrl).toContain('/api')
    expect(config.appEnv).toBeDefined()
    expect(config.featureFlags.logisticsEnabled).toBe(true)
    expect(config.featureFlags.stepUpEnabled).toBe(true)
  })

  it('no produce URLs duplicadas con /api/api', () => {
    const config = loadEnvironmentConfig()
    expect(config.apiUrl.endsWith('/api/api')).toBe(false)
  })
})
