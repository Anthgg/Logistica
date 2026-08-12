import { useCallback, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { apiRequest, getCsrfToken } from '../../../api/api-client'
import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel } from '../../inbound-docks/components/ui/Primitives'
import { QualityPlanVersionWizard } from './QualityPlanVersionWizard'
import type {
  QualityInspectionPlanVersion,
  QualityInspectionPlanCapabilities,
  QualityInspectionPlanVersionStatus,
} from '../types/quality-inspection-plans'

const STATUS_TONE: Record<QualityInspectionPlanVersionStatus, 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'muted'> = {
  DRAFT: 'neutral',
  VALIDATING: 'info',
  VALIDATED: 'success',
  SCHEDULED: 'info',
  ACTIVE: 'success',
  RETIRED: 'muted',
}

const STATUS_LABEL: Record<QualityInspectionPlanVersionStatus, string> = {
  DRAFT: 'Borrador',
  VALIDATING: 'Validando',
  VALIDATED: 'Validada',
  SCHEDULED: 'Programada',
  ACTIVE: 'Activa',
  RETIRED: 'Retirada',
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-EC', { year: 'numeric', month: 'short', day: 'numeric' })
}

function formatDateTime(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-EC', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function QualityPlanVersionsPanel({
  planId,
  versions,
  capabilities,
  onRefresh,
}: {
  planId: string
  versions: QualityInspectionPlanVersion[]
  capabilities: QualityInspectionPlanCapabilities
  onRefresh: () => void
}) {
  const [wizardOpen, setWizardOpen] = useState(false)
  const [editingVersionId, setEditingVersionId] = useState<string | undefined>(undefined)
  const [, setHistoryVersionId] = useState<string | null>(null)
  const [compareIds, setCompareIds] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const cloneVersionMutation = useMutation<{ versionId: string }, { version_id: string }>(
    async (input) => {
      const csrf = await getCsrfToken()
      return apiRequest<{ version_id: string }>({
        path: `/logistics/quality/versions/${input.versionId}/clone`,
        method: 'POST',
        body: {},
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    {
      onSuccess: (result) => {
        setEditingVersionId(result?.version_id)
        setWizardOpen(true)
        onRefresh()
      },
      onError: (err) => setError(err.message),
    },
  )

  const validateMutation = useMutation<{ versionId: string }, void>(
    async (input) => {
      const csrf = await getCsrfToken()
      await apiRequest({
        path: `/logistics/quality/versions/${input.versionId}/validate`,
        method: 'POST',
        body: {},
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => onRefresh(), onError: (err) => setError(err.message) },
  )

  const activateMutation = useMutation<{ versionId: string }, void>(
    async (input) => {
      const csrf = await getCsrfToken()
      await apiRequest({
        path: `/logistics/quality/versions/${input.versionId}/activate`,
        method: 'POST',
        body: { confirmation: true },
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => onRefresh(), onError: (err) => setError(err.message) },
  )

  const retireMutation = useMutation<{ versionId: string; reason: string }, void>(
    async (input) => {
      const csrf = await getCsrfToken()
      await apiRequest({
        path: `/logistics/quality/versions/${input.versionId}/retire`,
        method: 'POST',
        body: { reason: input.reason },
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => onRefresh(), onError: (err) => setError(err.message) },
  )

  const handleEditDraft = useCallback((versionId: string) => {
    setEditingVersionId(versionId)
    setWizardOpen(true)
  }, [])

  const handleCreateVersion = useCallback(() => {
    setEditingVersionId(undefined)
    setWizardOpen(true)
  }, [])

  const handleClone = useCallback((versionId: string) => {
    cloneVersionMutation.mutate({ versionId })
  }, [cloneVersionMutation])

  const handleValidate = useCallback((versionId: string) => {
    validateMutation.mutate({ versionId })
  }, [validateMutation])

  const handleActivate = useCallback((versionId: string) => {
    activateMutation.mutate({ versionId })
  }, [activateMutation])

  const handleRetire = useCallback((versionId: string) => {
    const reason = window.prompt('Motivo de retiro:')
    if (reason) retireMutation.mutate({ versionId, reason })
  }, [retireMutation])

  const handleToggleCompare = useCallback((versionId: string) => {
    setCompareIds((prev) => {
      if (prev.includes(versionId)) return prev.filter((id) => id !== versionId)
      if (prev.length >= 2) return [prev[1], versionId]
      return [...prev, versionId]
    })
  }, [])

  const handleViewHistory = useCallback((versionId: string) => {
    setHistoryVersionId(versionId)
  }, [])

  if (error) {
    return <ErrorPanel message={error} onRetry={() => { setError(null); onRefresh() }} />
  }

  if (versions.length === 0) {
    return (
      <SectionPanel
        title="Versiones del plan"
        actions={capabilities.can_create_version ? (
          <Button variant="primary" size="small" onClick={handleCreateVersion}>
            Nueva versión
          </Button>
        ) : undefined}
      >
        <EmptyPanel
          title="Sin versiones"
          description="Este plan aún no tiene versiones. Cree la primera versión para comenzar a configurar los controles de inspección."
          action={capabilities.can_create_version ? (
            <Button variant="primary" size="small" onClick={handleCreateVersion}>
              Crear primera versión
            </Button>
          ) : undefined}
        />
      </SectionPanel>
    )
  }

  return (
    <SectionPanel
      title="Versiones del plan"
      description={`${versions.length} versión(es) registrada(s)`}
      actions={
        <div className="flex items-center gap-2">
          {compareIds.length === 2 && (
            <Button variant="secondary" size="small" onClick={() => setCompareIds([])}>
              Limpiar comparación ({compareIds.length})
            </Button>
          )}
          {capabilities.can_create_version && (
            <Button variant="primary" size="small" onClick={handleCreateVersion}>
              Nueva versión
            </Button>
          )}
        </div>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-left text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              <th className="px-2 py-2">Versión</th>
              <th className="px-2 py-2">Estado</th>
              <th className="px-2 py-2">Vigencia</th>
              <th className="px-2 py-2">Prioridad</th>
              <th className="px-2 py-2">Creada por</th>
              <th className="px-2 py-2">Validada por</th>
              <th className="px-2 py-2">Hash</th>
              <th className="px-2 py-2 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {versions.map((v) => {
              const isDraft = v.status === 'DRAFT'
              const isActive = v.status === 'ACTIVE'
              const isRetired = v.status === 'RETIRED'
              const canEditThis = isDraft && capabilities.can_manage_controls
              const canValidateThis = isDraft && capabilities.can_validate
              const canActivateThis = v.validation_status === 'VALID' && capabilities.can_activate && !isActive && !isRetired
              const canRetireThis = isActive && capabilities.can_retire
              const isCompareSelected = compareIds.includes(v.version_id)

              return (
                <tr key={v.version_id} className={isCompareSelected ? 'bg-indigo-50' : 'hover:bg-slate-50/50'}>
                  <td className="px-2 py-2">
                    <span className="font-mono font-bold text-slate-800">v{v.version_number}</span>
                  </td>
                  <td className="px-2 py-2">
                    <StatusPill tone={STATUS_TONE[v.status]}>
                      {STATUS_LABEL[v.status]}
                    </StatusPill>
                    {v.validation_status === 'INVALID' && (
                      <StatusPill tone="danger" className="ml-1">Inválida</StatusPill>
                    )}
                    {v.validation_status === 'WARNING' && (
                      <StatusPill tone="warning" className="ml-1">Advertencias</StatusPill>
                    )}
                  </td>
                  <td className="px-2 py-2 text-slate-600">
                    {formatDate(v.valid_from)} — {formatDate(v.valid_until)}
                  </td>
                  <td className="px-2 py-2 font-mono text-slate-700">{v.priority}</td>
                  <td className="px-2 py-2 text-slate-600">
                    {v.created_by.display_name}
                    <br />
                    <span className="text-[10px] text-slate-400">{formatDateTime(v.created_at)}</span>
                  </td>
                  <td className="px-2 py-2 text-slate-600">
                    {v.validated_by ? (
                      <>
                        {v.validated_by.display_name}
                        <br />
                        <span className="text-[10px] text-slate-400">{formatDateTime(v.validated_at)}</span>
                      </>
                    ) : '—'}
                  </td>
                  <td className="px-2 py-2 font-mono text-[10px] text-slate-400 max-w-[120px] truncate" title={v.hash ?? ''}>
                    {v.hash ? v.hash.slice(0, 12) + '…' : '—'}
                  </td>
                  <td className="px-2 py-2">
                    <div className="flex items-center justify-end gap-1 flex-wrap">
                      {canEditThis && (
                        <Button variant="ghost" size="small" onClick={() => handleEditDraft(v.version_id)}>
                          Editar
                        </Button>
                      )}
                      {isActive && (
                        <StatusPill tone="success">Activa</StatusPill>
                      )}
                      {!isDraft && !isActive && !isRetired && capabilities.can_clone && (
                        <Button variant="ghost" size="small" onClick={() => handleClone(v.version_id)}>
                          Clonar
                        </Button>
                      )}
                      {canValidateThis && (
                        <Button variant="ghost" size="small" onClick={() => handleValidate(v.version_id)}>
                          Validar
                        </Button>
                      )}
                      {canActivateThis && (
                        <Button variant="primary" size="small" onClick={() => handleActivate(v.version_id)}>
                          Activar
                        </Button>
                      )}
                      {canRetireThis && (
                        <Button variant="danger" size="small" onClick={() => handleRetire(v.version_id)}>
                          Retirar
                        </Button>
                      )}
                      {capabilities.can_detect_conflicts && (
                        <Button
                          variant={isCompareSelected ? 'secondary' : 'ghost'}
                          size="small"
                          onClick={() => handleToggleCompare(v.version_id)}
                        >
                          {isCompareSelected ? 'Quitar' : 'Comparar'}
                        </Button>
                      )}
                      {capabilities.can_view_history && (
                        <Button variant="ghost" size="small" onClick={() => handleViewHistory(v.version_id)}>
                          Historial
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {wizardOpen && (
        <QualityPlanVersionWizard
          planId={planId}
          versionId={editingVersionId}
          onComplete={() => { setWizardOpen(false); setEditingVersionId(undefined); onRefresh() }}
          onCancel={() => { setWizardOpen(false); setEditingVersionId(undefined) }}
        />
      )}
    </SectionPanel>
  )
}
