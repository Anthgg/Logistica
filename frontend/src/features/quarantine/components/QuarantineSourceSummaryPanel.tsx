import { useQuery } from '../../inbound-docks/hooks/useQuery'
import type {
  QualityQuarantineCase,
  QualityInspection,
  QualityInspectionEvidence,
} from '../types/quarantine'
import { StatusBadge } from '../../../components/common/StatusBadge'

interface Props {
  quarantineCase: QualityQuarantineCase
  inspection: QualityInspection | null
}

export function QuarantineSourceSummaryPanel({ quarantineCase, inspection }: Props) {
  const evidenceQuery = useQuery<{ items: QualityInspectionEvidence[] }>(
    ['quarantine-evidence', quarantineCase.case_id],
    `/logistics/quality-inspection-evidence/evidence?case_id=${quarantineCase.case_id}`,
    {},
    { enabled: !!quarantineCase.case_id },
  )

  const evidenceItems = evidenceQuery.data?.items ?? []

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-ink mb-3">Resumen de origen de cuarentena</h3>
        <div className="rounded-lg border border-slate-200 divide-y divide-slate-200">
          {/* Receipt */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Recepción</span>
              <p className="font-medium text-ink">{quarantineCase.receipt_code ?? 'N/A'}</p>
            </div>
            <div>
              <span className="text-muted">Caso de diferencia</span>
              <p className="font-medium text-ink">{quarantineCase.difference_case_code ?? 'N/A'}</p>
            </div>
          </div>

          {/* Supplier & Warehouse */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Proveedor</span>
              <p className="font-medium text-ink">{quarantineCase.supplier?.trade_name ?? quarantineCase.supplier?.name ?? 'N/A'}</p>
              {quarantineCase.supplier && (
                <p className="text-muted mt-0.5">{quarantineCase.supplier.document_type}: {quarantineCase.supplier.document_number}</p>
              )}
            </div>
            <div>
              <span className="text-muted">Almacén</span>
              <p className="font-medium text-ink">{quarantineCase.warehouse.name}</p>
              <p className="text-muted mt-0.5">{quarantineCase.warehouse.code}</p>
            </div>
          </div>

          {/* Product */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div className="col-span-2">
              <span className="text-muted">Producto</span>
              <p className="font-medium text-ink">{quarantineCase.product?.name ?? 'N/A'}</p>
              <p className="text-muted mt-0.5">SKU: {quarantineCase.product?.sku ?? 'N/A'}</p>
            </div>
          </div>

          {/* Quantities */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Cantidad recibida</span>
              <p className="font-medium text-ink">{quarantineCase.total_quantity} {quarantineCase.unit?.symbol ?? ''}</p>
            </div>
            <div>
              <span className="text-muted">Unidad de medida</span>
              <p className="font-medium text-ink">{quarantineCase.unit?.name ?? 'N/A'} ({quarantineCase.unit?.symbol ?? ''})</p>
            </div>
          </div>

          {/* Tracking */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Lotes observados</span>
              <p className="font-medium text-ink">{quarantineCase.allocation_count} asignaciones</p>
            </div>
            <div>
              <span className="text-muted">Fecha de expiración</span>
              <p className="font-medium text-ink">{inspection?.lot_number ?? 'N/A'}</p>
            </div>
          </div>

          {/* Evidence */}
          <div className="p-4 text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-muted">Evidencia adjunta</span>
              <span className="font-medium text-ink">{evidenceItems.length} archivos</span>
            </div>
            {evidenceItems.length > 0 && (
              <div className="space-y-1">
                {evidenceItems.slice(0, 5).map((ev) => (
                  <div key={ev.evidence_id} className="flex items-center gap-2 text-[11px] text-muted">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
                    <span className="truncate">{ev.file.filename}</span>
                    <span className="text-ink font-medium">{ev.evidence_type}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Differences */}
          <div className="p-4 text-xs">
            <span className="text-muted">Diferencias detectadas</span>
            <p className="font-medium text-ink mt-1">
              {quarantineCase.reason}
            </p>
          </div>

          {/* Quarantine Reason */}
          <div className="p-4 text-xs">
            <span className="text-muted">Motivo de cuarentena</span>
            <div className="mt-1">
              <StatusBadge value={quarantineCase.reason} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
