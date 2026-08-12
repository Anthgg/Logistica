import { test, expect } from '@playwright/test'
import { installApiMocks } from './fixtures/api-mocks'

test.describe('Crear organización — autorizado y denegado', () => {
  test('usuario con permiso de creación ve el botón de crear almacén', async ({
    page,
  }) => {
    await installApiMocks(page, {
      permissions: ['logistics.warehouses.read', 'logistics.warehouses.create'],
    })
    await page.goto('/warehouses')
    await expect(page.getByRole('button', { name: /Nuevo almacén/i })).toBeVisible()
  })

  test('usuario sin permiso de creación no ve el botón de crear', async ({
    page,
  }) => {
    await installApiMocks(page, {
      permissions: ['logistics.warehouses.read'],
    })
    await page.goto('/warehouses')
    await expect(
      page.getByRole('button', { name: /Nuevo almacén/i }),
    ).toBeHidden()
  })
})