import { useEffect, useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsContextSelector } from '../../logistics-permissions/hooks/useLogisticsContextSelector'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { DockFiltersPanel, type DockFilter } from '../components/Filters'
import { DockModal } from '../components/dialogs/DockModal'
import { ErrorPanel, SkeletonRows, SectionPanel, StatusPill } from '../components/ui/Primitives'
import { WarehouseDocksBoard } from '../components/WarehouseDocksBoard'
import { WarehouseDockForm } from '../components/WarehouseDockForm'
import { DockOperationExportPanel } from '../components/DockOperationExportPanel'
import { dockStatusLabel } from '../utils/format'
import {
  useWarehouseDocks,
} from '../hooks/useInboundDocksQueries'
import { useMutation } from '../hooks/useQuery'
import { warehouseDocksApi } from '../api/warehouseDocksApi'
import type { WarehouseDock, WarehouseDockCreate, WarehouseDockUpdate } from '../types/inbound-docks'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function WarehouseDocksSettingsPage() {
  const { context, options } = useLogisticsContextSelector()
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.manageDocks)
  const [filter, setFilter] = useState<DockFilter>({})
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<WarehouseDock | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  useEffect(() => {
    if (!filter.warehouse_id) {
      setFilter((prev) => ({ ...prev, warehouse_id: context.warehouse_id ?? options.warehouses[0]?.id ?? '' }))
    }
  }, [filter.warehouse_id, context.warehouse_id, options.warehouses])
  const docks = useWarehouseDocks({ ...filter, page_size: 100 })
  const createMutation = useMutation<WarehouseDockCreate, WarehouseDock>(
    async (data: WarehouseDockCreate) => warehouseDocksApi.create(data),
    {
      onSuccess: () => { setCreateOpen(false); void docks.refetch() },
      onError: (err) => setErrorMessage(err.message),
    },
  )
  const updateMutation = useMutation<{ id: string; data: WarehouseDockUpdate }, WarehouseDock>(
    async ({ id, data }: { id: string; data: WarehouseDockUpdate }) => warehouseDocksApi.update(id, data),
    {
      onSuccess: () => { setEditing(null); void docks.refetch() },
      onError: (err) => setErrorMessage(err.message),
    },
  )
  return (
    <div className="page">
      <PageHeader
        eyebrow="Fase 038"
        title="Configuración de muelles"
        description="Gestión de muelles, horarios y blackouts."
        actions={
          canManage && (
            <Button type="button" variant="primary" onClick={() => setCreateOpen(true)}>
              Nuevo muelle
            </Button>
          )
        }
      />
      {!canManage && (
        <ErrorPanel message="No tienes capability para configurar muelles." />
      )}
      <DockFiltersPanel
        value={filter}
        onChange={setFilter}
        warehouses={options.warehouses.length ? options.warehouses : (filter.warehouse_id ? [{ id: filter.warehouse_id, label: filter.warehouse_id }] : [])}
      />
      {docks.isLoading ? (
        <SkeletonRows rows={4} />
      ) : docks.isError ? (
        <ErrorPanel message={docks.error ?? 'No se pudo cargar la lista de muelles.'} />
      ) : (
        <>
          <SectionPanel
            title="Muelles"
            description="Listado de muelles filtrado. Selecciona uno para editarlo."
            actions={
              <StatusPill tone="muted">
                {docks.data?.total ?? 0} muelle(s)
              </StatusPill>
            }
          >
            <ul className="space-y-2 text-xs">
              {(docks.data?.items ?? []).map((d) => (
                <li
                  key={d.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white p-3"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{d.code} — {d.name}</p>
                    <p className="text-[11px] text-slate-500">{d.warehouse_name} · {d.type}</p>
                    <p className="text-[11px] text-slate-500">Estado maestro: {dockStatusLabel(d.status)}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {canManage && (
                      <Button size="small" variant="secondary" onClick={async () => {
                        const detail = await warehouseDocksApi.get(d.id)
                        setEditing(detail)
                      }}>
                        Editar
                      </Button>
                    )}
                  </div>
                </li>
              ))}
              {(docks.data?.items ?? []).length === 0 && (
                <li className="rounded-md border border-dashed border-slate-200 bg-white p-3 text-[11px] text-slate-400">
                  Sin muelles.
                </li>
              )}
            </ul>
          </SectionPanel>
          <WarehouseDocksBoard
            docks={docks.data?.items ?? []}
            emptyMessage="Sin muelles para mostrar."
          />
          <DockOperationExportPanel
            defaultWarehouseId={filter.warehouse_id}
          />
        </>
      )}
      <DockModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Nuevo muelle"
        description="Los datos se enviarán al backend. No se crean almacenes ni ubicaciones de inventario."
        size="xl"
        footer={null}
      >
        <WarehouseDockForm
          warehouses={options.warehouses.length ? options.warehouses : (filter.warehouse_id ? [{ id: filter.warehouse_id, label: filter.warehouse_id }] : [])}
          onSubmit={(data) => createMutation.mutate(data as WarehouseDockCreate)}
          onCancel={() => setCreateOpen(false)}
          isSubmitting={createMutation.isPending}
          errorMessage={createMutation.error ?? errorMessage}
        />
      </DockModal>
      <DockModal
        open={Boolean(editing)}
        onOpenChange={(o) => { if (!o) setEditing(null) }}
        title={`Editar muelle ${editing?.code ?? ''}`}
        description="Solo se envían los campos modificados."
        size="xl"
        footer={null}
      >
        {editing && (
          <WarehouseDockForm
            initial={editing}
            warehouses={options.warehouses.length ? options.warehouses : [{ id: editing.warehouse_id, label: editing.warehouse_name }]}
            onSubmit={(data) => updateMutation.mutate({ id: editing.id, data: data as WarehouseDockUpdate })}
            onCancel={() => setEditing(null)}
            isSubmitting={updateMutation.isPending}
            errorMessage={updateMutation.error ?? errorMessage}
            title="Editar muelle"
          />
        )}
      </DockModal>
    </div>
  )
}
