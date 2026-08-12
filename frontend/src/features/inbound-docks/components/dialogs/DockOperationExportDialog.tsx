import { useEffect, useState } from 'react'
import { Button } from '../../../../components/common/Button'
import { DockModal } from './DockModal'
import { useMutation, useQuery } from '../../hooks/useQuery'
import { dockAssignmentsApi } from '../../api/dockAssignmentsApi'
import { useLogisticsPermissions } from '../../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../../logistics-permissions/logistics-permissions-map'
import { formatServerDateTime, formatServerTime } from '../../utils/format'
import type { DockOperationExportJob, ExportFormat } from '../../types/inbound-docks'

const FORMATS: Array<{ value: ExportFormat; label: string; description: string }> = [
  { value: 'CSV', label: 'CSV', description: 'Texto separado por comas' },
  { value: 'XLSX', label: 'XLSX', description: 'Hoja de cálculo' },
  { value: 'PDF', label: 'PDF operativo', description: 'Reporte operativo imprimible' },
]

export function DockOperationExportDialog({
  open,
  onOpenChange,
  defaultWarehouseId,
  defaultDockIds,
  defaultDateFrom,
  defaultDateTo,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  defaultWarehouseId?: string
  defaultDockIds?: string[]
  defaultDateFrom?: string
  defaultDateTo?: string
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canExport = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.export)
  const [format, setFormat] = useState<ExportFormat>('CSV')
  const [warehouseId, setWarehouseId] = useState(defaultWarehouseId ?? '')
  const [dockIds, setDockIds] = useState((defaultDockIds ?? []).join(','))
  const [dateFrom, setDateFrom] = useState(defaultDateFrom ?? '')
  const [dateTo, setDateTo] = useState(defaultDateTo ?? '')
  const [includeMetrics, setIncludeMetrics] = useState(true)
  const [includeTimeline, setIncludeTimeline] = useState(false)
  const [classification, setClassification] = useState('OPERATIONAL')
  const [jobId, setJobId] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (open) {
      setFormat('CSV')
      setWarehouseId(defaultWarehouseId ?? '')
      setDockIds((defaultDockIds ?? []).join(','))
      setDateFrom(defaultDateFrom ?? '')
      setDateTo(defaultDateTo ?? '')
      setIncludeMetrics(true)
      setIncludeTimeline(false)
      setClassification('OPERATIONAL')
      setJobId(null)
      setErrorMessage(null)
    }
  }, [open, defaultWarehouseId, defaultDockIds, defaultDateFrom, defaultDateTo])
  const mutation = useMutation<Parameters<typeof dockAssignmentsApi.createExportJob>[0], DockOperationExportJob>(
    async (data) => dockAssignmentsApi.createExportJob(data),
    { onSuccess: (job) => setJobId(job.id) },
  )
  const job = useQuery<DockOperationExportJob>(
    ['dock-export-job', jobId],
    jobId ? `/logistics/inbound/dock-assignments/export/${jobId}` : '',
    undefined,
    { enabled: Boolean(jobId), refetchIntervalMs: jobId ? 3_000 : null },
  )
  const submit = async () => {
    setErrorMessage(null)
    if (!warehouseId) {
      setErrorMessage('Selecciona un almacén.')
      return
    }
    await mutation.mutate({
      format,
      warehouse_id: warehouseId,
      dock_ids: dockIds
        .split(',')
        .map((d) => d.trim())
        .filter(Boolean),
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      include_metrics: includeMetrics,
      include_timeline: includeTimeline,
      classification,
    })
  }
  return (
    <DockModal
      open={open}
      onOpenChange={onOpenChange}
      title="Exportar reporte operativo"
      description="No incluye productos recibidos. Solo datos operativos (Fase 038)."
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cerrar
          </Button>
          {!jobId && (
            <Button type="button" variant="primary" onClick={submit} disabled={!canExport} isLoading={mutation.isPending}>
              Generar exportación
            </Button>
          )}
        </>
      }
    >
      <div className="space-y-3 text-xs">
        <fieldset>
          <legend className="mb-1 text-[11px] font-semibold uppercase text-slate-500">Formato</legend>
          <div className="flex flex-wrap gap-2">
            {FORMATS.map((f) => (
              <label
                key={f.value}
                className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold ${
                  format === f.value
                    ? 'border-[#1F4E6D] bg-[#1F4E6D]/5 text-[#1F4E6D]'
                    : 'border-slate-200 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="format"
                  value={f.value}
                  checked={format === f.value}
                  onChange={() => setFormat(f.value)}
                  className="sr-only"
                />
                <span>{f.label}</span>
                <span className="text-[10px] text-slate-500">{f.description}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="export-warehouse">Almacén</label>
          <input
            id="export-warehouse"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={warehouseId}
            onChange={(event) => setWarehouseId(event.target.value)}
            placeholder="ID de almacén"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="export-docks">Muelles (IDs separados por coma)</label>
          <input
            id="export-docks"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={dockIds}
            onChange={(event) => setDockIds(event.target.value)}
            placeholder="Opcional"
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="export-from">Desde (ISO)</label>
            <input
              id="export-from"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="export-to">Hasta (ISO)</label>
            <input
              id="export-to"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
            />
          </div>
        </div>
        <fieldset>
          <legend className="mb-1 text-[11px] font-semibold uppercase text-slate-500">Contenido</legend>
          <div className="flex flex-wrap gap-2">
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={includeMetrics}
                onChange={(event) => setIncludeMetrics(event.target.checked)}
                className="h-3.5 w-3.5"
              />
              Métricas
            </label>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={includeTimeline}
                onChange={(event) => setIncludeTimeline(event.target.checked)}
                className="h-3.5 w-3.5"
              />
              Timeline
            </label>
          </div>
        </fieldset>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="export-classification">Clasificación</label>
          <input
            id="export-classification"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={classification}
            onChange={(event) => setClassification(event.target.value)}
          />
        </div>
        {jobId && (
          <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-2 text-[11px]">
            <p>Job: <span className="font-mono text-slate-800">{jobId}</span></p>
            <p>Estado: <span className="font-mono text-slate-800">{job.data?.status ?? '—'}</span></p>
            {job.data?.completed_at && (
              <p>Completado: {formatServerDateTime(job.data.completed_at)}</p>
            )}
            {job.data?.expires_at && (
              <p>Vence: {formatServerTime(job.data.expires_at)}</p>
            )}
            {job.data?.error_message && (
              <p className="text-rose-700">Error: {job.data.error_message}</p>
            )}
            {job.data?.download_url && (
              <a
                className="text-[#1F4E6D] underline"
                href={job.data.download_url}
                rel="noreferrer"
                target="_blank"
              >
                Descargar archivo
              </a>
            )}
          </div>
        )}
        {errorMessage && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
        {mutation.error && <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{mutation.error}</p>}
        {!canExport && (
          <p className="rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700">
            No tienes capability para exportar.
          </p>
        )}
      </div>
    </DockModal>
  )
}
