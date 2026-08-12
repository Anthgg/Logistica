import { useState } from 'react'
import { warehousesApi } from '../../api/warehouses-modeling-api'
import { ResourceDialog } from '../../components/common/ResourceDialog'
import type { GenerationPreviewResponse, LocationGenerationRequest } from '../../types/warehouse-modeling'
import { getErrorMessage } from '../../utils/errors'

interface WarehouseLocationGenerationWizardProps {
  warehouseId: string
  isOpen: boolean
  onClose: () => void
  onSuccess: () => Promise<void>
}

export function WarehouseLocationGenerationWizard({
  warehouseId,
  isOpen,
  onClose,
  onSuccess,
}: WarehouseLocationGenerationWizardProps) {
  const [step, setStep] = useState<1 | 2>(1)
  const [form, setForm] = useState<LocationGenerationRequest>({
    parent_id: null,
    zones_count: 2,
    aisles_count: 5,
    racks_count: 10,
    shelves_count: 4,
    bins_count: 2,
    padding_length: 2,
    usage_type: 'STORAGE',
  })

  const [preview, setPreview] = useState<GenerationPreviewResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRequestPreview = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await warehousesApi.previewGeneration(warehouseId, form)
      setPreview(res)
      setStep(2)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!preview) return
    setIsLoading(true)
    setError(null)
    try {
      await warehousesApi.executeGeneration(warehouseId, preview.request_hash)
      await onSuccess()
      onClose()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <ResourceDialog
      isOpen={isOpen}
      title="Asistente de Generación Masiva de Ubicaciones"
      submitLabel={step === 1 ? 'Solicitar Vista Previa' : 'Ejecutar Generación'}
      isSubmitting={isLoading}
      onClose={onClose}
      onSubmit={() => void (step === 1 ? handleRequestPreview() : handleExecute())}
    >
      <div className="space-y-4 text-xs">
        {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

        {step === 1 ? (
          <div className="space-y-3">
            <p className="text-slate-500 text-[11px]">
              Configura los rangos jerárquicos. El backend calculará el resumen autoritativo y verificará potenciales colisiones.
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Cantidad de Zonas (Z01..Z99)</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  className="input-field"
                  value={form.zones_count || 1}
                  onChange={(e) => setForm((c) => ({ ...c, zones_count: Number(e.target.value) }))}
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Pasillos por Zona (A01..A99)</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  className="input-field"
                  value={form.aisles_count || 1}
                  onChange={(e) => setForm((c) => ({ ...c, aisles_count: Number(e.target.value) }))}
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Estantes por Pasillo (R01..R99)</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  className="input-field"
                  value={form.racks_count || 1}
                  onChange={(e) => setForm((c) => ({ ...c, racks_count: Number(e.target.value) }))}
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Niveles por Estante (S01..S99)</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  className="input-field"
                  value={form.shelves_count || 1}
                  onChange={(e) => setForm((c) => ({ ...c, shelves_count: Number(e.target.value) }))}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 space-y-1.5 text-blue-900">
              <span className="font-bold text-xs">Resumen Autoritativo de la Vista Previa:</span>
              <p className="font-mono text-sm font-bold text-slate-900">
                Total de Nodos Novedosos a Crear: {preview?.total_nodes}
              </p>
              <p className="text-[11px] text-slate-500">Hash de idempotencia: {preview?.request_hash}</p>
            </div>

            {preview && preview.conflicts.length > 0 && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-rose-900">
                <span className="font-bold">Conflicto de colisión detectado:</span>
                <ul className="list-disc list-inside mt-1">
                  {preview.conflicts.map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </ResourceDialog>
  )
}
