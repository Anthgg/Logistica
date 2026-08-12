export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export const USER_ROLES = [
  'admin',
  'supervisor',
  'dispatcher',
  'warehouse_operator',
] as const

export type UserRole = (typeof USER_ROLES)[number]
