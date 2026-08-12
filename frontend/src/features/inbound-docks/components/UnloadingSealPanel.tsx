import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { StatusPill, SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows } from './ui/Primitives'
import { RecordUnloadingSealOpeningDialog } from './dialogs/UnloadingSupportDialogs'
import { formatServerDateTime, sealOpeningResultLabel } from '../utils/format'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { UnloadingOperation, UnloadingSealOpening } from '../types/inbound-docks'

export function UnloadingSealPanel({
  operation,
  seal,
  loading,
  error,
  onChanged,
}: {
  operation: UnloadingOperation | null
  seal: UnloadingSealOpening | null | undefined
  loading: boolean
  error: string | null
  onChanged?: () => void
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canRecord = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.recordSealOpening)
  const [open, setOpen] = useState(false)
  if (loading) {
    return (
      <SectionPanel title="Precinto" description="Apertura registrada">
        <SkeletonRows rows={3} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Precinto" description="Apertura registrada">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!operation) {
    return (
      <SectionPanel title="Precinto" description="Apertura registrada">
        <EmptyPanel title="Sin operación" />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Precinto"
      description="Resultado de apertura y evidencia"
      actions={
        canRecord && (
          <Button size="small" variant="primary" onClick={() => setOpen(true)}>
            Registrar apertura
          </Button>
        )
      }
    >
      {seal ? (
        <div className="space-y-2 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill tone={seal.has_anomaly ? 'danger' : 'success'}>
              {sealOpeningResultLabel(seal.result)}
            </StatusPill>
            {seal.has_anomaly && (
              <StatusPill tone="danger">Anomalía</StatusPill>
            )}
          </div>
          <p>Esperado: <span className="font-mono text-slate-800">{seal.expected_seal_number ?? '—'}</span></p>
          <p>Observado: <span className="font-mono text-slate-800">{seal.observed_seal_number ?? '—'}</span></p>
          {seal.observation && <p>Observación: {seal.observation}</p>}
          {seal.opened_by && <p>Abierto por: {seal.opened_by.display_name}</p>}
          {seal.witness && <p>Testigo: {seal.witness.display_name}</p>}
          {seal.photo_before_file_id && <p>Foto previa: {seal.photo_before_file_id}</p>}
          {seal.photo_after_file_id && <p>Foto posterior: {seal.photo_after_file_id}</p>}
          <p className="text-[10px] text-slate-500">Registrado: {formatServerDateTime(seal.created_at)}</p>
        </div>
      ) : (
        <EmptyPanel title="Sin apertura" description="Aún no se registra la apertura del precinto." />
      )}
      {seal?.has_anomaly && (
        <div className="mt-2 rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
          Se detectó una anomalía. El inicio de descarga puede estar bloqueado.
        </div>
      )}
      <RecordUnloadingSealOpeningDialog
        open={open}
        operation={operation}
        existing={seal ?? null}
        onOpenChange={setOpen}
        onRecorded={() => { onChanged?.() }}
      />
    </SectionPanel>
  )
}
