import { test, expect } from '@playwright/test'
import { installApiMocks } from './fixtures/api-mocks'

const permissions = [
  'logistics.warehouses.read',
  'logistics.inbound_docks.read',
  'logistics.inbound_docks.view_queue',
  'logistics.inbound_docks.change_priority',
  'logistics.inbound_docks.assign',
  'logistics.inbound_docks.start_unloading',
  'logistics.inbound_docks.complete',
]

const roles = [
  {
    role_code: 'WAREHOUSE_OPERATOR',
    role_name: 'Operador de almacén',
    scope_type: 'WAREHOUSE' as const,
    organization_id: 'org-1',
    branch_id: 'branch-1',
    warehouse_id: 'wh-1',
    expires_at: null,
  },
]

test.describe('Fase 038 - Muelles de Entrada (Inbound Docks)', () => {
  test.beforeEach(async ({ page }) => {
    await installApiMocks(
      page,
      { permissions, roles },
      {
        enabled: true,
        permissions,
        roles: ['LOGISTICS_ADMIN'],
        organizations: ['org-1'],
        branches: ['branch-1'],
        warehouses: ['wh-1'],
      },
    )

    await page.route(/\/api\/logistics\/inbound\/dock-queue\/summary/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          server_time: '2026-08-01T12:00:00Z',
          timezone: 'America/Lima',
          total_in_queue: 3,
          total_assigned: 1,
          total_unloading: 1,
          total_waiting: 2,
          docks_available: 4,
          docks_reserved: 1,
          docks_occupied: 2,
          total_paused: 0,
          total_completed_pending_release: 0,
          prolonged_waits: 0,
          operations_with_anomalies: 0,
          operations_with_incomplete_data: 0,
          avg_waiting_seconds: 420,
        }),
      }),
    )

    await page.route(/\/api\/logistics\/inbound\/dock-queue(\?.*)?$/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'queue-entry-1',
              position: 1,
              priority: 'NORMAL',
              status: 'WAITING',
              check_in_id: 'chk-100',
              cpv_code: 'CPV-2026-001',
              cit_code: 'CIT-100',
              warehouse_id: 'wh-1',
              warehouse_name: 'Almacén Central',
              supplier_name: 'Distribuidora Global S.A.',
              carrier_name: 'Transportes Rápidos',
              vehicle_plate: 'ABC-123',
              waiting_seconds: 300,
              alerts: [],
              entered_queue_at: '2026-08-01T11:55:00Z',
            },
          ],
          page: 1,
          page_size: 20,
          total: 1,
          total_pages: 1,
        }),
      }),
    )

    await page.route(/\/api\/logistics\/inbound\/dock-assignments/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'assign-1',
              dock_id: 'dock-1',
              dock_code: 'M-01',
              dock_name: 'Muelle General 1',
              warehouse_id: 'wh-1',
              status: 'ASSIGNED',
              priority: 'HIGH',
              cpv_code: 'CPV-2026-002',
              vehicle: { id: 'v-1', plate: 'XYZ-999', vehicle_type: 'TRUCK' },
              supplier: { id: 's-1', name: 'Logística SAC' },
              assigned_at: '2026-08-01T11:45:00Z',
              alerts: [],
              server_time: '2026-08-01T12:00:00Z',
            },
          ],
          page: 1,
          page_size: 20,
          total: 1,
          total_pages: 1,
        }),
      }),
    )

    await page.route(/\/api\/logistics\/inbound\/unloading-operations/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'op-1',
              assignment_id: 'assign-1',
              check_in_id: 'chk-100',
              cpv_code: 'CPV-2026-002',
              dock_id: 'dock-1',
              dock_code: 'M-01',
              warehouse_id: 'wh-1',
              vehicle: { id: 'v-1', plate: 'XYZ-999' },
              status: 'ACTIVE',
              started_at: '2026-08-01T11:50:00Z',
              accumulated_pause_seconds: 0,
              alerts: [],
              responsibles: [{ user: { display_name: 'Juan Pérez' } }],
              server_time: '2026-08-01T12:00:00Z',
            },
          ],
          page: 1,
          page_size: 20,
          total: 1,
          total_pages: 1,
        }),
      }),
    )

    await page.route(/\/api\/logistics\/inbound\/docks(\?.*)?$/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'dock-1',
              code: 'M-01',
              name: 'Muelle General 1',
              warehouse_id: 'wh-1',
              warehouse_name: 'Almacén Central',
              type: 'STANDARD',
              direction: 'INBOUND',
              status: 'ACTIVE',
              operational_status: 'OCCUPIED',
              active_assignment_id: 'assign-1',
              active_assignment_vehicle_plate: 'XYZ-999',
              occupied_since: '2026-08-01T11:45:00Z',
            },
            {
              id: 'dock-2',
              code: 'M-02',
              name: 'Muelle Frío 2',
              warehouse_id: 'wh-1',
              warehouse_name: 'Almacén Central',
              type: 'REFRIGERATED',
              direction: 'INBOUND',
              status: 'ACTIVE',
              operational_status: 'AVAILABLE',
              active_assignment_id: null,
              active_assignment_vehicle_plate: null,
              occupied_since: null,
            },
          ],
          page: 1,
          page_size: 20,
          total: 2,
          total_pages: 1,
        }),
      }),
    )
  })

  test('carga el tablero operativo de muelles y alterna vistas', async ({ page }) => {
    await page.goto('/logistics/inbound/docks')

    await expect(page.getByRole('heading', { name: 'Muelles de entrada' })).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('Vistas')).toBeVisible()

    await page.getByRole('button', { name: 'Tabla' }).click()
    await expect(page.getByText('Tabla de operaciones')).toBeVisible()

    await page.getByRole('button', { name: 'Calendario' }).click()
    await expect(page.getByText('Calendario operativo')).toBeVisible()
  })

  test('ejecuta el cambio de prioridad de cola con validación de motivo', async ({ page }) => {
    await page.route(/\/api\/logistics\/inbound\/dock-queue\/queue-entry-1\/priority/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'queue-entry-1',
          position: 1,
          priority: 'HIGH',
          status: 'WAITING',
          cpv_code: 'CPV-2026-001',
          vehicle_plate: 'ABC-123',
          waiting_seconds: 300,
        }),
      }),
    )

    await page.goto('/logistics/inbound/docks')
    await expect(page.getByRole('heading', { name: 'Muelles de entrada' })).toBeVisible({ timeout: 15000 })

    await page.getByRole('button', { name: 'Prioridad' }).first().click()
    await expect(page.getByRole('heading', { name: 'Cambiar prioridad de cola' })).toBeVisible()

    await page.getByLabel(/Motivo/i).fill('Descarga de producto perecible urgente')
    await page.getByText('Alta').click()

    await page.getByRole('button', { name: 'Confirmar cambio' }).click()
    await expect(page.getByRole('heading', { name: 'Cambiar prioridad de cola' })).toBeHidden()
  })

  test('visualiza la vista de muelles y estados de ocupación', async ({ page }) => {
    await page.goto('/logistics/inbound/docks')

    await expect(page.getByText('M-01')).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('M-02')).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('Disponible')).toBeVisible()
    await expect(page.getByText('Ocupado')).toBeVisible()
  })
})
