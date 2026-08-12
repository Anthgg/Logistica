import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { purchaseRequisitionsApi } from '../api/purchase-requisitions-api'
import { warehousesApi } from '../api/warehouses-modeling-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { CostCenterSelector, RequisitionPrioritySelector } from '../components/purchase-requisitions/CostCenterSelector'
import { PurchaseRequisitionLinesEditor } from '../components/purchase-requisitions/PurchaseRequisitionLinesEditor'
import type {
  PurchaseRequisitionCreate,
  PurchaseRequisitionLineCreate,
  PurchaseRequisitionPriority,
} from '../types/purchase-requisitions'
import type { Warehouse } from '../types/warehouse-modeling'

export function PurchaseRequisitionFormPage() {
  const { requisitionId } = useParams<{ requisitionId?: string }>()
  const navigate = useNavigate()
  const isEditing = Boolean(requisitionId)

  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Form State
  const [costCenterId, setCostCenterId] = useState('')
  const [priority, setPriority] = useState<PurchaseRequisitionPriority>('NORMAL')
  const [priorityReason, setPriorityReason] = useState('')
  const [requiredDate, setRequiredDate] = useState(() => {
    const nextWeek = new Date()
    nextWeek.setDate(nextWeek.getDate() + 7)
    return nextWeek.toISOString().split('T')[0]
  })
  const [warehouseId, setWarehouseId] = useState('')
  const [justification, setJustification] = useState('')
  const [purpose, setPurpose] = useState('')
  const [lines, setLines] = useState<PurchaseRequisitionLineCreate[]>([])

  const [warehouses, setWarehouses] = useState<Warehouse[]>([])

  useEffect(() => {
    warehousesApi.list({ page_size: 100 })
      .then((res) => {
        setWarehouses(res.items || [])
        if (res.items && res.items.length > 0 && !warehouseId) {
          setWarehouseId(res.items[0].id)
        }
      })
      .catch(() => setWarehouses([]))
  }, [warehouseId])

  useEffect(() => {
    if (!requisitionId) return
    setLoading(true)
    purchaseRequisitionsApi.get(requisitionId)
      .then((req) => {
        setCostCenterId(req.cost_center_id)
        setPriority(req.priority)
        setPriorityReason(req.priority_reason || '')
        setRequiredDate(req.required_date)
        setWarehouseId(req.destination_warehouse_id)
        setJustification(req.summary_justification)
        setPurpose(req.business_purpose || '')
        setLines(
          req.lines.map((l) => ({
            product_id: l.product_id,
            requested_quantity: l.requested_quantity,
            unit_of_measure_id: l.unit_of_measure_id,
            required_date: l.required_date,
            destination_warehouse_id: l.destination_warehouse_id,
            justification: l.justification || undefined,
          })),
        )
      })
      .finally(() => setLoading(false))
  }, [requisitionId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!costCenterId || !warehouseId || !justification.trim() || lines.length === 0 || submitting) return
    setSubmitting(true)
    try {
      const payload: PurchaseRequisitionCreate = {
        branch_id: warehouses.find((w) => w.id === warehouseId)?.branch_id || 'DEFAULT_BRANCH',
        cost_center_id: costCenterId,
        priority,
        priority_reason: priorityReason.trim() || undefined,
        required_date: requiredDate,
        destination_warehouse_id: warehouseId,
        summary_justification: justification.trim(),
        business_purpose: purpose.trim() || undefined,
        lines,
      }

      if (isEditing && requisitionId) {
        await purchaseRequisitionsApi.update(requisitionId, payload)
        navigate(`/logistics/purchasing/requisitions/${requisitionId}`)
      } else {
        const created = await purchaseRequisitionsApi.create(payload)
        navigate(`/logistics/purchasing/requisitions/${created.id}`)
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al guardar borrador de requerimiento')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSkeleton rows={10} />

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title={isEditing ? 'Editar Requerimiento de Compra' : 'Elaborar Nuevo Requerimiento de Compra'}
        description="Formulario de cabecera y líneas para bienes, materiales o repuestos operacionales."
      />

      <form onSubmit={handleSubmit} className="space-y-6 text-xs">
        {/* General Info Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">
            1. Cabecera e Imputación de Costos
          </h3>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <CostCenterSelector
              value={costCenterId}
              onChange={(id) => {
                setCostCenterId(id)
              }}
            />

            <div>
              <label className="mb-1 block font-bold text-slate-700">Almacén Destino de Entrega *</label>
              <select
                value={warehouseId}
                onChange={(e) => setWarehouseId(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white font-medium text-slate-800"
              >
                <option value="">Seleccionar almacén de recepción...</option>
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>
                    [{w.code}] {w.name} ({w.branch_name})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block font-bold text-slate-700">Fecha Requerida General *</label>
              <input
                type="date"
                value={requiredDate}
                onChange={(e) => setRequiredDate(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800"
              />
            </div>
          </div>

          <RequisitionPrioritySelector
            priority={priority}
            priorityReason={priorityReason}
            onChange={(p, r) => {
              setPriority(p)
              if (r !== undefined) setPriorityReason(r)
            }}
          />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block font-bold text-slate-700">Justificación General de la Necesidad *</label>
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                rows={2}
                required
                placeholder="Describe el motivo operacional de la compra..."
                className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>

            <div>
              <label className="mb-1 block font-bold text-slate-700">Propósito Empresarial / Proyecto (Opcional)</label>
              <textarea
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                rows={2}
                placeholder="Proyecto, OT o mantención asociada..."
                className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
              />
            </div>
          </div>
        </div>

        {/* Lines Editor */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <PurchaseRequisitionLinesEditor
            lines={lines}
            onChange={setLines}
            defaultRequiredDate={requiredDate}
            defaultWarehouseId={warehouseId}
          />
        </div>

        <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
          <Button type="button" variant="secondary" onClick={() => navigate('/logistics/purchasing/requisitions')}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={submitting} loadingLabel="Guardando Borrador...">
            Guardar Borrador de Requerimiento
          </Button>
        </div>
      </form>
    </div>
  )
}
