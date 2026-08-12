import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows } from './ui/Primitives'
import { AssignUnloadingResponsibleDialog } from './dialogs/UnloadingSupportDialogs'
import { formatServerDateTime } from '../utils/format'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  UnloadingOperation,
  UnloadingResponsibleAssignment,
} from '../types/inbound-docks'

const STATUS_LABEL: Record<UnloadingResponsibleAssignment['status'], string> = {
  ASSIGNED: 'Asignado',
  ACCEPTED: 'Aceptado',
  RELEASED: 'Liberado',
  REVOKED: 'Revocado',
}

export function UnloadingResponsiblesPanel({
  operation,
  responsibles,
  loading,
  error,
  onChanged,
}: {
  operation: UnloadingOperation | null
  responsibles: UnloadingResponsibleAssignment[] | undefined
  loading: boolean
  error: string | null
  onChanged?: () => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageResponsibles)
  const [openDialog, setOpenDialog] = useState(false)
  if (loading) {
    return (
      <SectionPanel title="Responsables" description="Asignaciones operativas">
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Responsables" description="Asignaciones operativas">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!operation) {
    return (
      <SectionPanel title="Responsables" description="Asignaciones operativas">
        <EmptyPanel title="Sin operación" />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Responsables"
      description="Solo lectura de aceptaciones y liberaciones. Las asignaciones requieren capability."
      actions={
        canManage && (
          <Button size="small" variant="primary" onClick={() => setOpenDialog(true)}>
            Asignar responsable
          </Button>
        )
      }
    >
      {responsibles?.length ? (
        <ul className="space-y-2">
          {responsibles.map((r) => (
            <li key={r.id} className="rounded-lg border border-slate-200 bg-white p-3 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-slate-800">{r.responsibility_label}</p>
                  <p className="text-[11px] text-slate-500">{r.responsibility_type}</p>
                </div>
                <StatusPill tone={r.status === 'ACCEPTED' ? 'success' : r.status === 'RELEASED' || r.status === 'REVOKED' ? 'muted' : 'info'}>
                  {STATUS_LABEL[r.status]}
                </StatusPill>
              </div>
              <p className="mt-1 text-[11px] text-slate-600">
                {r.user ? `Usuario: ${r.user.display_name}` : r.team_name ? `Equipo: ${r.team_name}` : r.organization_name ?? '—'}
              </p>
              {r.assigned_by && (
                <p className="text-[10px] text-slate-500">
                  Asignado por: {r.assigned_by.display_name} · {formatServerDateTime(r.assigned_at)}
                </p>
              )}
              {r.accepted_at && (
                <p className="text-[10px] text-slate-500">Aceptado: {formatServerDateTime(r.accepted_at)}</p>
              )}
              {r.released_at && (
                <p className="text-[10px] text-slate-500">Liberado: {formatServerDateTime(r.released_at)}</p>
              )}
              {r.valid_until && (
                <p className="text-[10px] text-slate-500">Vigente hasta: {formatServerDateTime(r.valid_until)}</p>
              )}
              {r.comment && <p className="text-[11px] text-slate-600">Comentario: {r.comment}</p>}
            </li>
          ))}
        </ul>
      ) : (
        <EmptyPanel
          title="Sin responsables"
          description="Asigna responsables para registrar la operación."
        />
      )}
      <AssignUnloadingResponsibleDialog
        open={openDialog}
        operation={operation}
        responsibilityType="OPERATOR"
        onOpenChange={setOpenDialog}
        onAssigned={() => { onChanged?.() }}
      />
    </SectionPanel>
  )
}
