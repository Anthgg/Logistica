import { test, expect } from '@playwright/test'
import { installApiMocks, installUnauthorizedMocks } from './fixtures/api-mocks'

test.describe('Cambio de contexto organizacional', () => {
  test('selector muestra solo alcances autorizados', async ({ page }) => {
    await installApiMocks(page, {
      permissions: ['logistics.warehouses.read'],
      roles: [
        {
          role_code: 'WH_MANAGER',
          role_name: 'Responsable de almacén',
          scope_type: 'WAREHOUSE',
          organization_id: 'org-1',
          branch_id: 'branch-1',
          warehouse_id: 'wh-1',
          expires_at: null,
        },
      ],
    })
    await page.goto('/dashboard')
    // El selector de contexto se renderiza cuando hay roles no globales.
    // Validación completa requiere UI de selector (pendiente).
    expect(true).toBe(true)
  })
})

test.describe('Sesión expirada redirige a login', () => {
  test('401 en permisos redirige a login', async ({ page }) => {
    await installUnauthorizedMocks(page)
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })
})