import { test, expect } from '@playwright/test'
import { installApiMocks, installUnauthorizedMocks } from './fixtures/api-mocks'

test.describe('Login y acceso al módulo logístico', () => {
  test('usuario con permisos logísticos accede al dashboard', async ({ page }) => {
    const pageErrors: string[] = []
    const invalidScriptResponses: string[] = []
    page.on('pageerror', (error) => pageErrors.push(error.message))
    page.on('response', (response) => {
      if (
        response.request().resourceType() === 'script' &&
        !response.headers()['content-type']?.includes('javascript')
      ) {
        invalidScriptResponses.push(
          `${response.status()} ${response.url()}: ${response.headers()['content-type'] ?? 'sin content-type'}`,
        )
      }
    })

    await installApiMocks(page)
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 20000 })
    await page.waitForTimeout(500)
    expect(pageErrors, pageErrors.join('\n')).toEqual([])
    expect(invalidScriptResponses, invalidScriptResponses.join('\n')).toEqual([])
    expect(await page.locator('#root').innerHTML()).not.toBe('')
    await expect(
      page.getByRole('heading', { name: 'Pulso logístico' }),
    ).toBeVisible()
  })

  test('usuario sin sesión es redirigido a login', async ({ page }) => {
    await installUnauthorizedMocks(page)
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })
})

test.describe('Menú según permisos', () => {
  test('oculta módulo de almacenes cuando no tiene permiso', async ({ page }) => {
    await installApiMocks(page, {
      permissions: [],
      sensitivePermissions: [],
      stepUpPermissions: [],
      roles: [],
    })
    await page.goto('/dashboard')
    await expect(page.getByRole('link', { name: 'Almacenes' })).toBeHidden({ timeout: 15000 })
  })

  test.fixme('muestra módulo de almacenes cuando tiene permiso', async ({ page }) => {
    test.setTimeout(30000)
    await installApiMocks(page, {
      permissions: ['logistics.warehouses.read'],
    })
    await page.goto('/login')
    await page.waitForLoadState('networkidle')
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('link', { name: 'Almacenes' })).toBeVisible({ timeout: 25000 })
  })
})
