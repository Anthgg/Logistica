import { useCallback, useMemo } from 'react'
import { useLogisticsPermissions } from '../hooks/useLogisticsPermissions'
import type {
  LogisticsPermissionsContext,
  LogisticsRoleScope,
} from '../../../types/logistics-permissions'

export interface LogisticsContextOption {
  id: string
  label: string
}

interface DerivedOptions {
  organizations: LogisticsContextOption[]
  branches: LogisticsContextOption[]
  warehouses: LogisticsContextOption[]
}

function dedupeById(items: LogisticsContextOption[]): LogisticsContextOption[] {
  const seen = new Set<string>()
  const result: LogisticsContextOption[] = []
  for (const item of items) {
    if (!seen.has(item.id)) {
      seen.add(item.id)
      result.push(item)
    }
  }
  return result
}

function roleLabel(role: LogisticsRoleScope, id: string): string {
  if (role.role_name) return `${role.role_name} · ${id}`
  return id
}

export function useLogisticsContextSelector() {
  const auth = useLogisticsPermissions()

  const options: DerivedOptions = useMemo(() => {
    const orgs: LogisticsContextOption[] = []
    const branches: LogisticsContextOption[] = []
    const warehouses: LogisticsContextOption[] = []

    for (const role of auth.roles) {
      if (role.scope_type === 'GLOBAL') continue
      if (role.organization_id) {
        orgs.push({
          id: role.organization_id,
          label: roleLabel(role, role.organization_id),
        })
      }
      if (role.branch_id) {
        branches.push({
          id: role.branch_id,
          label: roleLabel(role, role.branch_id),
        })
      }
      if (role.warehouse_id) {
        warehouses.push({
          id: role.warehouse_id,
          label: roleLabel(role, role.warehouse_id),
        })
      }
    }

    return {
      organizations: dedupeById(orgs),
      branches: dedupeById(branches),
      warehouses: dedupeById(warehouses),
    }
  }, [auth.roles])

  const canSelect = auth.roles.some(
    (role) => role.scope_type !== 'GLOBAL',
  )

  const selectContext = useCallback(
    async (next: Partial<LogisticsPermissionsContext>): Promise<void> => {
      if (!auth.canAccessScope({
        organization_id: next.organization_id ?? auth.context.organization_id,
        branch_id: next.branch_id ?? auth.context.branch_id,
        warehouse_id: next.warehouse_id ?? auth.context.warehouse_id,
      })) {
        return
      }
      await auth.setContext(next)
    },
    [auth],
  )

  return {
    canSelect,
    options,
    context: auth.context,
    selectContext,
    resetContext: auth.resetContext,
  }
}