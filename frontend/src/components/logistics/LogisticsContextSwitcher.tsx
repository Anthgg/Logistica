import { useEffect, useMemo, useState } from 'react'
import { useLogisticsAccess } from '../../features/logistics-me/hooks/useLogisticsAccess'
import { useQuery } from '../../features/inbound-docks/hooks/useQuery'
import type {
  OrganizationResponse,
  PaginatedResponse,
} from '../../types/logistics-resources'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'

export interface LogisticsContextSwitcherProps {
  compact?: boolean
  inline?: boolean
}

export function LogisticsContextSwitcher({
  compact = false,
  inline = false,
}: LogisticsContextSwitcherProps) {
  const {
    organizations,
    branches,
    warehouses,
    currentContext,
    changeContext,
    isChangingContext,
    contextError,
  } = useLogisticsAccess()

  const globalOrganizations = useQuery<PaginatedResponse<OrganizationResponse>>(
    ['logistics-context-organizations'],
    '/logistics/organizations',
    { page: 1, page_size: 100 },
    { enabled: organizations.length === 0 },
  )

  const selectableOrganizations = useMemo(() => {
    if (organizations.length > 0) {
      return organizations.map((id) => ({ id, name: id, code: id }))
    }
    return (globalOrganizations.data?.items ?? []).map(({ id, name, code }) => ({
      id,
      name,
      code,
    }))
  }, [globalOrganizations.data, organizations])

  const [isOpen, setIsOpen] = useState(false)
  const [pendingOrg, setPendingOrg] = useState<string | null>(
    currentContext.organization_id,
  )
  const [pendingBranch, setPendingBranch] = useState<string | null>(
    currentContext.branch_id,
  )
  const [pendingWarehouse, setPendingWarehouse] = useState<string | null>(
    currentContext.warehouse_id,
  )

  useEffect(() => {
    if (isOpen) {
      setPendingOrg(currentContext.organization_id)
      setPendingBranch(currentContext.branch_id)
      setPendingWarehouse(currentContext.warehouse_id)
    }
  }, [isOpen, currentContext])

  const hasMultipleOptions =
    selectableOrganizations.length > 1 ||
    branches.length > 1 ||
    warehouses.length > 1

  const currentLabel = useMemo(() => {
    const parts: string[] = []
    if (currentContext.organization_id) {
      const selected = selectableOrganizations.find(
        ({ id }) => id === currentContext.organization_id,
      )
      parts.push(`Org: ${selected?.name ?? currentContext.organization_id.slice(0, 8)}`)
    }
    if (currentContext.branch_id) parts.push(`Sede: ${currentContext.branch_id.slice(0, 8)}`)
    if (currentContext.warehouse_id) parts.push(`Almacén: ${currentContext.warehouse_id.slice(0, 8)}`)
    return parts.length > 0 ? parts.join(' · ') : 'Sin contexto'
  }, [currentContext, selectableOrganizations])

  const needsOrganizationSelection =
    !currentContext.organization_id && selectableOrganizations.length > 0

  if (!hasMultipleOptions && !needsOrganizationSelection) {
    return null
  }

  const handleConfirm = async () => {
    const success = await changeContext({
      organization_id: pendingOrg,
      branch_id: pendingBranch,
      warehouse_id: pendingWarehouse,
    })
    if (success) {
      setIsOpen(false)
    }
  }

  const handleCancel = () => {
    setIsOpen(false)
    setPendingOrg(currentContext.organization_id)
    setPendingBranch(currentContext.branch_id)
    setPendingWarehouse(currentContext.warehouse_id)
  }

  if (inline && !isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-1 text-slate-400 transition-colors hover:text-slate-600"
        aria-label="Cambiar contexto organizacional"
        aria-expanded={isOpen}
      >
        <LogisticsIcon name="building" size={12} />
        <span className="max-w-[120px] truncate">{currentLabel}</span>
      </button>
    )
  }

  if (compact && !isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 rounded-xl bg-slate-800/80 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
        aria-label="Cambiar contexto organizacional"
        aria-expanded={isOpen}
      >
        <LogisticsIcon name="building" size={16} />
        <span className="max-w-[200px] truncate">{currentLabel}</span>
      </button>
    )
  }

  if (!isOpen) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400" aria-label="Contexto actual">
          {currentLabel}
        </span>
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="text-xs font-medium text-orange-400 hover:text-orange-300"
        >
          Cambiar
        </button>
      </div>
    )
  }

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={handleCancel}
    >
      <div
        className="dialog max-w-md"
        role="dialog"
        aria-modal="true"
        aria-labelledby="context-switcher-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="context-switcher-title" className="text-lg font-bold text-slate-900">
          Cambiar contexto organizacional
        </h2>
        <p className="text-sm text-slate-600 mt-1">
          Selecciona la organización, sede y almacén. Solo aparecen opciones autorizadas.
        </p>

        <div className="mt-4 space-y-3">
          <fieldset>
            <legend className="text-sm font-medium text-slate-700 mb-1">
              Organización
            </legend>
            <select
              className="field__input w-full"
              aria-label="Organización"
              value={pendingOrg ?? ''}
              onChange={(event) => {
                setPendingOrg(event.target.value || null)
                setPendingBranch(null)
                setPendingWarehouse(null)
              }}
              disabled={isChangingContext || selectableOrganizations.length === 0}
              aria-describedby="context-org-help"
            >
              <option value="">Sin organización</option>
              {selectableOrganizations.map(({ id, name, code }) => (
                <option key={id} value={id}>
                  {name} ({code})
                </option>
              ))}
            </select>
            <p id="context-org-help" className="text-xs text-slate-500 mt-1">
              {globalOrganizations.isLoading
                ? 'Cargando organizaciones…'
                : `${selectableOrganizations.length} organización(es) disponible(s)`}
            </p>
          </fieldset>

          <fieldset>
            <legend className="text-sm font-medium text-slate-700 mb-1">
              Sede
            </legend>
            <select
              className="field__input w-full"
              aria-label="Sede"
              value={pendingBranch ?? ''}
              onChange={(event) => {
                setPendingBranch(event.target.value || null)
                setPendingWarehouse(null)
              }}
              disabled={isChangingContext || branches.length === 0}
            >
              <option value="">Sin sede</option>
              {branches.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </fieldset>

          <fieldset>
            <legend className="text-sm font-medium text-slate-700 mb-1">
              Almacén
            </legend>
            <select
              className="field__input w-full"
              aria-label="Almacén"
              value={pendingWarehouse ?? ''}
              onChange={(event) => setPendingWarehouse(event.target.value || null)}
              disabled={isChangingContext || warehouses.length === 0}
            >
              <option value="">Sin almacén</option>
              {warehouses.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </fieldset>

          {contextError && (
            <p className="text-sm text-rose-600" role="alert">
              {contextError}
            </p>
          )}
        </div>

        <div className="dialog__actions mt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={handleCancel}
            disabled={isChangingContext}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={() => void handleConfirm()}
            isLoading={isChangingContext}
            disabled={isChangingContext}
          >
            Confirmar contexto
          </Button>
        </div>
      </div>
    </div>
  )
}
