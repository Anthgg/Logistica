import { useState } from 'react'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import type {
  QualityInspectionSampleSet,
  QualityInspectionSampleReference,
  QualityInspectionControl,
} from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface QualityInspectionSamplingPanelProps {
  inspectionId: string
  controls: QualityInspectionControl[]
}

export function QualityInspectionSamplingPanel({
  inspectionId,
  controls,
}: QualityInspectionSamplingPanelProps) {
  const auth = useLogisticsPermissions()
  const canRecord = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.recordSample)

  const { data: sampleSets, isLoading, refetch } = useQuery<QualityInspectionSampleSet[]>(
    ['sample-sets', inspectionId],
    `/logistics/quality-inspections/inspections/${inspectionId}/sample-sets`,
    undefined,
    { enabled: Boolean(inspectionId) },
  )

  const [selectedReceivedLine, setSelectedReceivedLine] = useState<string>('')
  const [observedLot, setObservedLot] = useState<string>('')
  const [observedSerial, setObservedSerial] = useState<string>('')
  const [packageNumber, setPackageNumber] = useState<string>('')
  const [guidedReference, setGuidedReference] = useState<string>('')
  const [selectedSampleSetId, setSelectedSampleSetId] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const recordSampleMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionsApi.recordControlResult(
        controls[0]?.control_id ?? '',
        input,
      ),
    {
      onSuccess: () => {
        void refetch()
        setSelectedReceivedLine('')
        setObservedLot('')
        setObservedSerial('')
        setPackageNumber('')
        setGuidedReference('')
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  const allSampleSets = sampleSets ?? []
  const allSamples: QualityInspectionSampleReference[] = allSampleSets.flatMap((ss) => ss.samples ?? [])
  const inspectedCount = allSamples.filter((s) => s.inspected).length
  const totalSamples = allSamples.length

  const sampleControls = controls.filter((c) => c.result_value_type === 'SAMPLE_SET')

  function handleRecordSample() {
    if (!canRecord) return
    setError(null)

    void recordSampleMutation.mutate({
      control_id: selectedSampleSetId || (controls[0]?.control_id ?? ''),
      result_value: JSON.stringify({
        received_line: selectedReceivedLine || undefined,
        observed_lot: observedLot || undefined,
        observed_serial: observedSerial || undefined,
        package_number: packageNumber || undefined,
        guided_reference: guidedReference || undefined,
      }),
    } as Record<string, unknown>)
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-4">
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold text-sm text-slate-800">Panel de muestreo</h4>
        <StatusBadge value={inspectedCount === totalSamples && totalSamples > 0 ? 'completed' : 'in_progress'} />
      </div>

      {isLoading ? (
        <div className="py-4 text-center text-slate-500">Cargando muestras…</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 rounded-lg bg-slate-50 border border-slate-200 p-3">
            <div className="text-[11px]">
              <span className="text-slate-500">Población: </span>
              <span className="font-medium">{allSampleSets[0]?.population_size ?? '—'}</span>
            </div>
            <div className="text-[11px]">
              <span className="text-slate-500">Unidad: </span>
              <span className="font-medium">{allSampleSets[0]?.sample_unit ?? '—'}</span>
            </div>
            <div className="text-[11px]">
              <span className="text-slate-500">Muestras requeridas: </span>
              <span className="font-medium">{allSampleSets[0]?.calculated_sample_size ?? '—'}</span>
            </div>
            <div className="text-[11px]">
              <span className="text-slate-500">Muestras registradas: </span>
              <span className="font-medium">{allSampleSets[0]?.actual_sample_size ?? inspectedCount}</span>
            </div>
            <div className="text-[11px]">
              <span className="text-slate-500">Método: </span>
              <span className="font-medium">{allSampleSets[0]?.selection_method ?? '—'}</span>
            </div>
            <div className="text-[11px]">
              <span className="text-slate-500">Redondeo: </span>
              <span className="font-medium">{allSampleSets[0]?.rounding_mode ?? '—'}</span>
            </div>
          </div>

          {sampleControls.length > 0 && (
            <div>
              <h5 className="text-[11px] font-semibold text-slate-600 mb-1">Controles asociados</h5>
              <div className="space-y-1">
                {sampleControls.map((sc) => (
                  <div key={sc.control_id} className="flex items-center gap-2 text-[11px] text-slate-500">
                    <StatusBadge value={sc.status.toLowerCase().replace(/_/g, ' ')} />
                    <span>{sc.name}</span>
                    <span className="text-slate-400">({sc.code})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {allSamples.length > 0 && (
            <div>
              <h5 className="text-[11px] font-semibold text-slate-600 mb-1">
                Referencias ({inspectedCount}/{totalSamples})
              </h5>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {allSamples.map((sr) => (
                  <div
                    key={sr.reference_id}
                    className={`flex items-center justify-between rounded px-2 py-1 text-[11px] ${
                      sr.inspected ? 'bg-emerald-50 border border-emerald-200' : 'bg-slate-50 border border-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium">#{sr.sample_number}</span>
                      {sr.lot_number && <span>Lote: {sr.lot_number}</span>}
                      {sr.serial_number && <span>Serie: {sr.serial_number}</span>}
                      {sr.package_code && <span>Paq: {sr.package_code}</span>}
                    </div>
                    <div className="flex items-center gap-1">
                      {sr.inspected ? (
                        <StatusBadge value={sr.inspection_result ?? 'completed'} />
                      ) : (
                        <span className="text-slate-400">Pendiente</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {canRecord && (
            <div className="space-y-2 border-t border-slate-200 pt-3">
              <h5 className="text-[11px] font-semibold text-slate-600">Registrar nueva muestra</h5>

              {allSampleSets.length > 1 && (
                <div>
                  <label className="field__label text-xs" htmlFor="sample-set-select">Conjunto de muestras</label>
                  <select
                    id="sample-set-select"
                    className="field__input text-xs"
                    value={selectedSampleSetId}
                    onChange={(e) => setSelectedSampleSetId(e.target.value)}
                  >
                    <option value="">Seleccionar…</option>
                    {allSampleSets.map((ss) => (
                      <option key={ss.sample_set_id} value={ss.sample_set_id}>
                        Conjunto {ss.sample_set_id.slice(0, 8)} — {ss.selection_method}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <Input
                  id="sample-received-line"
                  label="Línea recibida"
                  value={selectedReceivedLine}
                  onChange={(e) => setSelectedReceivedLine(e.target.value)}
                  disabled={recordSampleMutation.isPending}
                  placeholder="ID línea"
                />
                <Input
                  id="sample-lot"
                  label="Lote observado"
                  value={observedLot}
                  onChange={(e) => setObservedLot(e.target.value)}
                  disabled={recordSampleMutation.isPending}
                  placeholder="Número de lote"
                />
                <Input
                  id="sample-serial"
                  label="Serie observada"
                  value={observedSerial}
                  onChange={(e) => setObservedSerial(e.target.value)}
                  disabled={recordSampleMutation.isPending}
                  placeholder="Número de serie"
                />
                <Input
                  id="sample-package"
                  label="Nº de paquete"
                  value={packageNumber}
                  onChange={(e) => setPackageNumber(e.target.value)}
                  disabled={recordSampleMutation.isPending}
                  placeholder="Código de paquete"
                />
              </div>

              <Input
                id="sample-guided"
                label="Referencia guiada"
                value={guidedReference}
                onChange={(e) => setGuidedReference(e.target.value)}
                disabled={recordSampleMutation.isPending}
                placeholder="Referencia de la guía de muestreo"
              />

              <Button
                type="button"
                variant="primary"
                size="small"
                onClick={handleRecordSample}
                isLoading={recordSampleMutation.isPending}
                disabled={recordSampleMutation.isPending}
              >
                Registrar muestra
              </Button>
            </div>
          )}

          {allSampleSets.length === 0 && (
            <Alert variant="info">
              No hay conjuntos de muestras definidos para esta inspección.
            </Alert>
          )}
        </>
      )}

      {error && <Alert variant="error">{error}</Alert>}
    </div>
  )
}
