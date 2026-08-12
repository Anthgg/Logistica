import { test, expect } from '@playwright/test'
import { installApiMocks } from './fixtures/api-mocks'

test.describe('Rutas protegidas por permisos', () => {
  test('ruta permitida muestra la página de almacenes', async ({ page }) => {
    await installApiMocks(page, {
      permissions: ['logistics.warehouses.read'],
    })
    await page.goto('/warehouses')
    await expect(page.getByRole('heading', { name: 'Almacenes' })).toBeVisible()
  })

  test('ruta denegada muestra 403', async ({ page }) => {
    await installApiMocks(page, {
      permissions: [],
      sensitivePermissions: [],
      stepUpPermissions: [],
      roles: [],
    })
    await page.goto('/warehouses')
    await expect(page.getByText('403')).toBeVisible()
    await expect(
      page.getByText(/no tienes permisos|No tienes permisos/i),
    ).toBeVisible()
  })

  test('403 no redirige a login', async ({ page }) => {
    await installApiMocks(page, {
      permissions: [],
      sensitivePermissions: [],
      stepUpPermissions: [],
      roles: [],
    })
    await page.goto('/warehouses')
    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.getByText('403')).toBeVisible()
  })
})