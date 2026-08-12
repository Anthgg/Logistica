import { useCallback, useEffect, useMemo, useState } from 'react'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { SelectField, TextareaField } from '../components/common/FormControls'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { QueryBar } from '../components/common/QueryBar'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useAuth } from '../hooks/useAuth'
import type { InventoryItem, InventoryItemCreate, InventoryMovement, InventoryMovementCreate, MovementType, Warehouse } from '../types/operations'
import { formatDateTime } from '../utils/date'
import { getErrorMessage } from '../utils/errors'
import { permissionsFor } from '../utils/permissions'

const emptyItem: InventoryItemCreate = { warehouse_id: '', sku: '', name: '', description: '', current_stock: 0, minimum_stock: 0, unit: 'unidad' }
const emptyMovement: InventoryMovementCreate = { inventory_item_id: '', movement_type: 'entry', quantity: 1, reason: '', shipment_id: null, adjustment_resulting_stock: null }

export function InventoryPage() {
  const { user } = useAuth()
  const permissions = user ? permissionsFor(user.role) : permissionsFor('')
  const { guardSensitiveAction } = useSensitiveOperationGuard()
  const [items, setItems] = useState<InventoryItem[]>([])
  const [movements, setMovements] = useState<InventoryMovement[]>([])
  const [warehouses, setWarehouses] = useState<Warehouse[]>([])
  const [search, setSearch] = useState('')
  const [lowStock, setLowStock] = useState(false)
  const [tab, setTab] = useState<'items' | 'movements'>('items')
  const [itemForm, setItemForm] = useState(emptyItem)
  const [movementForm, setMovementForm] = useState(emptyMovement)
  const [dialog, setDialog] = useState<'item' | 'movement' | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [inventory, movementPage, warehousePage] = await Promise.all([
        operationsApi.inventory.list({ page_size: 100, search, low_stock: lowStock || undefined }),
        operationsApi.inventory.movements({ page_size: 100 }),
        operationsApi.warehouses.list({ page_size: 100, is_active: true }),
      ])
      setItems(inventory.items)
      setMovements(movementPage.items)
      setWarehouses(warehousePage.items)
    } catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsLoading(false) }
  }, [lowStock, search])

  useEffect(() => { const timer = window.setTimeout(() => void load(), 250); return () => window.clearTimeout(timer) }, [load])

  const saveItem = async () => {
    setIsSaving(true)
    try { await operationsApi.inventory.create(itemForm); setItemForm(emptyItem); setDialog(null); await load() }
    catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsSaving(false) }
  }
  const saveMovement = async () => {
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await operationsApi.inventory.createMovement({
          ...movementForm,
          adjustment_resulting_stock: movementForm.movement_type === 'adjustment' ? movementForm.adjustment_resulting_stock : null,
        })
      })
      if (!executed) return
      setMovementForm(emptyMovement); setDialog(null); await load()
    } catch (caught: unknown) { setError(getErrorMessage(caught)) }
    finally { setIsSaving(false) }
  }

  const itemColumns = useMemo<TableColumn<InventoryItem>[]>(() => [
    { key: 'item', label: 'Artículo', render: (row) => <div className="table-primary"><strong>{row.name}</strong><small>{row.sku}</small></div> },
    { key: 'warehouse', label: 'Almacén', render: (row) => warehouses.find((warehouse) => warehouse.id === row.warehouse_id)?.name ?? row.warehouse_id },
    { key: 'stock', label: 'Existencia', render: (row) => <strong>{row.current_stock} {row.unit}</strong> },
    { key: 'minimum', label: 'Mínimo', render: (row) => row.minimum_stock },
    { key: 'state', label: 'Estado', render: (row) => Number(row.current_stock) <= Number(row.minimum_stock) ? <StatusBadge value="high">Stock bajo</StatusBadge> : <StatusBadge value="active">Disponible</StatusBadge> },
  ], [warehouses])
  const movementColumns = useMemo<TableColumn<InventoryMovement>[]>(() => [
    { key: 'date', label: 'Fecha', render: (row) => formatDateTime(row.created_at) },
    { key: 'item', label: 'Artículo', render: (row) => items.find((item) => item.id === row.inventory_item_id)?.name ?? row.inventory_item_id },
    { key: 'type', label: 'Tipo', render: (row) => <StatusBadge value={row.movement_type}>{row.movement_type}</StatusBadge> },
    { key: 'quantity', label: 'Cantidad', render: (row) => row.quantity },
    { key: 'stock', label: 'Stock resultante', render: (row) => row.resulting_stock },
    { key: 'reason', label: 'Motivo', render: (row) => row.reason },
  ], [items])

  return <div className="page">
    <PageHeader eyebrow="Control de existencias" title="Inventario" description="Disponibilidad por almacén y libro de movimientos." actions={<>{permissions.manageInventory && <Button onClick={() => setDialog('item')}>Nuevo artículo</Button>}{permissions.registerMovements && <Button variant="secondary" onClick={() => setDialog('movement')}>Registrar movimiento</Button>}</>} />
    {error && <Alert variant="error">{error}</Alert>}
    <div className="tabs" role="tablist"><button className={tab === 'items' ? 'is-active' : ''} onClick={() => setTab('items')}>Artículos</button><button className={tab === 'movements' ? 'is-active' : ''} onClick={() => setTab('movements')}>Movimientos</button></div>
    <section className="panel operations-section">
      {tab === 'items' && <QueryBar search={search} onSearch={setSearch}><label className="check-filter"><input type="checkbox" checked={lowStock} onChange={(e) => setLowStock(e.target.checked)} /> Solo stock bajo</label></QueryBar>}
      {isLoading ? <div className="loading-panel"><span className="spinner" /><p>Cargando inventario…</p></div> : tab === 'items' ? <OperationsTable rows={items} columns={itemColumns} getRowKey={(row) => row.id} /> : <OperationsTable rows={movements} columns={movementColumns} getRowKey={(row) => row.id} />}
    </section>
    <ResourceDialog isOpen={dialog === 'item'} title="Nuevo artículo" submitLabel="Crear artículo" isSubmitting={isSaving} onClose={() => setDialog(null)} onSubmit={() => void saveItem()}>
      <div className="form-grid">
        <SelectField label="Almacén" value={itemForm.warehouse_id} onChange={(e) => setItemForm((current) => ({ ...current, warehouse_id: e.target.value }))} required><option value="">Selecciona</option>{warehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}</SelectField>
        <Input label="SKU" value={itemForm.sku} onChange={(e) => setItemForm((current) => ({ ...current, sku: e.target.value }))} required />
        <Input label="Nombre" value={itemForm.name} onChange={(e) => setItemForm((current) => ({ ...current, name: e.target.value }))} required />
        <Input label="Unidad" value={itemForm.unit} onChange={(e) => setItemForm((current) => ({ ...current, unit: e.target.value }))} required />
        <TextareaField className="form-grid__full" label="Descripción" value={itemForm.description ?? ''} onChange={(e) => setItemForm((current) => ({ ...current, description: e.target.value }))} />
        <Input label="Stock inicial" type="number" min="0" value={itemForm.current_stock} onChange={(e) => setItemForm((current) => ({ ...current, current_stock: Number(e.target.value) }))} />
        <Input label="Stock mínimo" type="number" min="0" value={itemForm.minimum_stock} onChange={(e) => setItemForm((current) => ({ ...current, minimum_stock: Number(e.target.value) }))} />
      </div>
    </ResourceDialog>
    <ResourceDialog isOpen={dialog === 'movement'} title="Registrar movimiento" submitLabel="Registrar movimiento" isSubmitting={isSaving} onClose={() => setDialog(null)} onSubmit={() => void saveMovement()}>
      <SelectField label="Artículo" value={movementForm.inventory_item_id} onChange={(e) => setMovementForm((current) => ({ ...current, inventory_item_id: e.target.value }))} required><option value="">Selecciona</option>{items.map((item) => <option key={item.id} value={item.id}>{item.sku} · {item.name}</option>)}</SelectField>
      <SelectField label="Tipo de movimiento" value={movementForm.movement_type} onChange={(e) => setMovementForm((current) => ({ ...current, movement_type: e.target.value as MovementType }))}><option value="entry">Entrada</option><option value="exit">Salida</option><option value="adjustment">Ajuste</option></SelectField>
      <Input label="Cantidad" type="number" min="0.01" step="0.01" value={movementForm.quantity} onChange={(e) => setMovementForm((current) => ({ ...current, quantity: Number(e.target.value) }))} required />
      {movementForm.movement_type === 'adjustment' && <Input label="Stock resultante" type="number" min="0" value={movementForm.adjustment_resulting_stock ?? ''} onChange={(e) => setMovementForm((current) => ({ ...current, adjustment_resulting_stock: Number(e.target.value) }))} required />}
      <Input label="ID de envío relacionado (opcional)" value={movementForm.shipment_id ?? ''} onChange={(e) => setMovementForm((current) => ({ ...current, shipment_id: e.target.value || null }))} />
      <TextareaField label="Motivo" value={movementForm.reason} onChange={(e) => setMovementForm((current) => ({ ...current, reason: e.target.value }))} minLength={2} required />
    </ResourceDialog>
  </div>
}
