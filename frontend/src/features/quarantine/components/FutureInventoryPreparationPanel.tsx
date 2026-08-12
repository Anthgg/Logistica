import { useState } from 'react'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  FutureInventoryMovementPreparation,
  FutureInventoryBalancePreparation,
  FutureTraceabilityPreparation,
} from '../types/quarantine'

type TabKey = 'movement' | 'balance' | 'traceability'

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'movement', label: 'Movimiento futuro' },
  { key: 'balance', label: 'Balance futuro' },
  { key: 'traceability', label: 'Trazabilidad futura' },
]

function ReadOnlyField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex flex-col">
      <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="text-sm text-slate-800">{value ?? '—'}</dd>
    </div>
  )
}

function MovementTab({ allocationId }: { allocationId: string }) {
  const { data, isLoading, isError, error } = useQuery<FutureInventoryMovementPreparation>(
    ['future-movement', allocationId],
    `/logistics/quality-availability/future-movement-preparation/${allocationId}`,
  )

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
        {error ?? 'Error al cargar el movimiento futuro.'}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50/40 px-4 py-8 text-center text-xs text-slate-500">
        <p className="text-sm font-semibold text-slate-700">Sin movimiento</p>
        <p className="max-w-md">No existe un MOV de movimiento registrado aún.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <dl className="grid grid-cols-1 gap-x-4 gap-y-2 text-xs sm:grid-cols-2">
        <ReadOnlyField label="Evento preparado" value={data.movement_type} />
        <ReadOnlyField label="Estado origen" value={data.origin_location?.name ?? null} />
        <ReadOnlyField label="Estado destino" value={data.destination_location?.name ?? null} />
        <ReadOnlyField label="Cantidad" value={data.quantity} />
        <ReadOnlyField label="Unidad" value={data.unit?.symbol ?? null} />
        <ReadOnlyField label="Producto" value={data.product?.name ?? null} />
        <ReadOnlyField
          label="Hash"
          value={data.preparation_id ? `prep-${data.preparation_id.slice(0, 8)}` : null}
        />
        <ReadOnlyField label="Referencia de lote" value={data.lot_number} />
        <ReadOnlyField label="Referencia de serial" value={data.serial_number} />
      </dl>
      <p className="text-[11px] text-slate-500 italic">
        No MOV de movimiento registrado aún.
      </p>
    </div>
  )
}

function BalanceTab({ allocationId }: { allocationId: string }) {
  const { data, isLoading, isError, error } = useQuery<FutureInventoryBalancePreparation>(
    ['future-balance', allocationId],
    `/logistics/quality-availability/future-balance-preparation/${allocationId}`,
  )

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
        {error ?? 'Error al cargar el balance futuro.'}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50/40 px-4 py-8 text-center text-xs text-slate-500">
        <p className="text-sm font-semibold text-slate-700">Sin balance</p>
        <p className="max-w-md">No existe un balance general definitivo registrado aún.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <dl className="grid grid-cols-1 gap-x-4 gap-y-2 text-xs sm:grid-cols-2">
        <ReadOnlyField label="Tipo de balance" value={data.balance_type} />
        <ReadOnlyField label="Cantidad" value={data.quantity} />
        <ReadOnlyField label="Unidad" value={data.unit?.symbol ?? null} />
        <ReadOnlyField label="Producto" value={data.product?.name ?? null} />
        <ReadOnlyField
          label="Hash"
          value={data.preparation_id ? `prep-${data.preparation_id.slice(0, 8)}` : null}
        />
        <ReadOnlyField label="Referencia de lote" value={data.lot_number} />
        <ReadOnlyField label="Referencia de serial" value={data.serial_number} />
        <ReadOnlyField label="Fecha esperada" value={data.expected_date} />
      </dl>
      <p className="text-[11px] text-slate-500 italic">
        No balance general definitivo registrado aún.
      </p>
    </div>
  )
}

function TraceabilityTab({ allocationId }: { allocationId: string }) {
  const { data, isLoading, isError, error } = useQuery<FutureTraceabilityPreparation>(
    ['future-traceability', allocationId],
    `/logistics/quality-availability/future-traceability-preparation/${allocationId}`,
  )

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
        {error ?? 'Error al cargar la trazabilidad futura.'}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50/40 px-4 py-8 text-center text-xs text-slate-500">
        <p className="text-sm font-semibold text-slate-700">Sin trazabilidad</p>
        <p className="max-w-md">No existe un lote maestro o serial maestro asignado aún.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <dl className="grid grid-cols-1 gap-x-4 gap-y-2 text-xs sm:grid-cols-2">
        <ReadOnlyField label="Producto" value={data.product?.name ?? null} />
        <ReadOnlyField label="Lote" value={data.lot_number} />
        <ReadOnlyField label="Serial" value={data.serial_number} />
        <ReadOnlyField label="Vencimiento" value={data.expiration_date} />
        <ReadOnlyField label="Referencia de lote" value={data.batch_reference} />
        <ReadOnlyField label="Referencia de serial" value={null} />
      </dl>
      <p className="text-[11px] text-slate-500 italic">
        No lote maestro o serial maestro asignado aún.
      </p>
    </div>
  )
}

export function FutureInventoryPreparationPanel({
  allocationId,
}: {
  allocationId: string
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.quarantine.viewFuturePreparations)
  const [activeTab, setActiveTab] = useState<TabKey>('movement')

  if (!canView) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-800">Preparaciones de inventario futuro</h2>
        <p className="mt-2 text-xs text-slate-500">No tiene permisos para ver esta información.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <header className="mb-3 border-b border-slate-100 pb-2">
        <h2 className="text-sm font-bold text-slate-800">Preparaciones de inventario futuro</h2>
        <p className="mt-0.5 text-xs text-slate-500">
          Eventos futuros preparados para movimientos, balances y trazabilidad.
        </p>
      </header>

      <div
        className="mb-4 flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1"
        role="tablist"
      >
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              activeTab === tab.key
                ? 'bg-white text-[#1F4E6D] shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {activeTab === 'movement' && <MovementTab allocationId={allocationId} />}
        {activeTab === 'balance' && <BalanceTab allocationId={allocationId} />}
        {activeTab === 'traceability' && <TraceabilityTab allocationId={allocationId} />}
      </div>
    </div>
  )
}
