import type {
  GateVerificationPolicy,
  GateVerificationPolicyCreate,
  GateVerificationPolicyVersion,
  GateVerificationPolicyVersionCreate,
  GateVerificationCheckDefinition,
} from '../types/gate-control'

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado como endpoint independiente por el backend 0.9.3.`,
  )
}

export const gateVerificationPoliciesApi = {
  async list(): Promise<GateVerificationPolicy[]> {
    return []
  },

  async create(_payload: GateVerificationPolicyCreate): Promise<GateVerificationPolicy> {
    return unavailable('La creación de políticas de verificación de garita')
  },

  async get(_id: string): Promise<GateVerificationPolicy> {
    return unavailable('La consulta de política de verificación')
  },

  async update(_id: string, _payload: Partial<GateVerificationPolicyCreate>): Promise<GateVerificationPolicy> {
    return unavailable('La actualización de política de verificación')
  },

  async listVersions(_id: string): Promise<GateVerificationPolicyVersion[]> {
    return []
  },

  async createVersion(_id: string, _payload: GateVerificationPolicyVersionCreate): Promise<GateVerificationPolicyVersion> {
    return unavailable('La creación de versión de política')
  },

  async validateVersion(_id: string, _versionId: string): Promise<GateVerificationPolicyVersion> {
    return unavailable('La validación de versión de política')
  },

  async activateVersion(_id: string, _versionId: string): Promise<GateVerificationPolicyVersion> {
    return unavailable('La activación de versión de política')
  },

  async retireVersion(_id: string, _versionId: string): Promise<GateVerificationPolicyVersion> {
    return unavailable('El retiro de versión de política')
  },

  async listChecks(_id: string, _versionId: string): Promise<GateVerificationCheckDefinition[]> {
    return []
  },

  async createCheck(_id: string, _versionId: string, _payload: Partial<GateVerificationCheckDefinition>): Promise<GateVerificationCheckDefinition> {
    return unavailable('La creación de verificación')
  },
}