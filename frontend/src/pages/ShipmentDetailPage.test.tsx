import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { operationsApi } from '../api/operations-api'
import {
  createAuthValue,
  renderWithAuth,
  testSession,
  testUser,
} from '../test/test-utils'
import { ApiRequestError } from '../types/api'
import type { Shipment } from '../types/operations'
import type { UserRole } from '../types/user'
import { LoginPage } from './LoginPage'
import { ShipmentDetailPage } from './ShipmentDetailPage'

const pendingPickupShipment: Shipment = {
  id: 'cfd8998c-e47f-4c04-b9f7-22419fa67e61',
  tracking_code: 'SHP-0001',
  client_id: 'client-1',
  origin_address: 'Av. Origen 123',
  destination_address: 'Av. Destino 456',
  origin_district: 'Lima',
  destination_district: 'Callao',
  package_description: 'Caja de prueba',
  package_count: 1,
  total_weight: '5.50',
  declared_value: null,
  priority: 'normal',
  priority_label: 'Normal',
  status: 'pending_pickup',
  status_label: 'Pendiente de recojo',
  expected_delivery_at: null,
  assigned_route_id: null,
  delivered_at: null,
  created_by: 'user-1',
  created_at: '2026-07-25T10:00:00Z',
  updated_at: '2026-07-25T10:00:00Z',
}

const deliveredShipment: Shipment = {
  ...pendingPickupShipment,
  status: 'delivered',
  status_label: 'Entregado',
}

const cancelledShipment: Shipment = {
  ...pendingPickupShipment,
  status: 'cancelled',
  status_label: 'Cancelado',
}

function renderShipmentDetail(role: UserRole = 'admin', shipment: Shipment = pendingPickupShipment) {
  return renderWithAuth(
    <Routes>
      <Route path="/shipments/:shipmentId" element={<ShipmentDetailPage />} />
      <Route path="/login" element={<LoginPage />} />
    </Routes>,
    {
      auth: createAuthValue({
        user: { ...testUser, role },
        session: testSession,
        currentSession: testSession,
        isAuthenticated: true,
      }),
      initialEntries: [`/shipments/${shipment.id}`],
    },
  )
}

async function openStatusDialog() {
  await screen.findByRole('heading', { name: 'SHP-0001' })
  await userEvent.click(screen.getByRole('button', { name: 'Cambiar estado' }))
}

describe('ShipmentDetailPage - Transiciones de estado y permisos', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(operationsApi.shipments, 'get').mockResolvedValue(pendingPickupShipment)
    vi.spyOn(operationsApi.shipments, 'timeline').mockResolvedValue([])
    vi.spyOn(operationsApi.shipments, 'status').mockResolvedValue(pendingPickupShipment)
  })

  it('1. pending_pickup muestra los diez estados', async () => {
    renderShipmentDetail()
    await openStatusDialog()

    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()

    const { getByText } = within(dialog)
    expect(getByText('Registrado')).toBeInTheDocument()
    expect(getByText('Pendiente de recojo')).toBeInTheDocument()
    expect(getByText('Recogido')).toBeInTheDocument()
    expect(getByText('Recibido en almacén')).toBeInTheDocument()
    expect(getByText('En tránsito')).toBeInTheDocument()
    expect(getByText('En reparto')).toBeInTheDocument()
    expect(getByText('Entregado')).toBeInTheDocument()
    expect(getByText('Retrasado')).toBeInTheDocument()
    expect(getByText('Cancelado')).toBeInTheDocument()
    expect(getByText('Devuelto')).toBeInTheDocument()
  })

  it('2. solo picked_up, delayed y cancelled están habilitados para pending_pickup', async () => {
    renderShipmentDetail()
    await openStatusDialog()

    expect(screen.getByRole('button', { name: /Recogido/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /Retrasado/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /Cancelado/i })).toBeEnabled()

    expect(screen.getByRole('button', { name: /Entregado/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /En tránsito/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Recibido en almacén/i })).toBeDisabled()
  })

  it('3. el estado actual aparece marcado', async () => {
    renderShipmentDetail()
    await openStatusDialog()

    expect(screen.getByText('Actual')).toBeInTheDocument()
  })

  it('4. cancelled y returned no permiten cambios (estado final)', async () => {
    vi.spyOn(operationsApi.shipments, 'get').mockResolvedValue(cancelledShipment)
    renderShipmentDetail('admin', cancelledShipment)
    await openStatusDialog()

    expect(screen.getByText(/no admite más cambios/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Confirmar cambio' })).not.toBeInTheDocument()
  })

  it('5. delivered solo permite returned', async () => {
    vi.spyOn(operationsApi.shipments, 'get').mockResolvedValue(deliveredShipment)
    renderShipmentDetail('admin', deliveredShipment)
    await openStatusDialog()

    expect(screen.getByRole('button', { name: /Devuelto/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /Cancelado/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /En tránsito/i })).toBeDisabled()
  })

  it('6. un estado deshabilitado no genera petición HTTP', async () => {
    const statusSpy = vi.spyOn(operationsApi.shipments, 'status')
    renderShipmentDetail()
    await openStatusDialog()

    const disabledBtn = screen.getByRole('button', { name: /Entregado/i })
    await userEvent.click(disabledBtn)

    expect(statusSpy).not.toHaveBeenCalled()
  })

  it('7. el POST envía status, description y location con cookies y CSRF', async () => {
    const user = userEvent.setup({ delay: null })
    const statusSpy = vi.spyOn(operationsApi.shipments, 'status')
    renderShipmentDetail()
    await screen.findByRole('heading', { name: 'SHP-0001' })
    await user.click(screen.getByRole('button', { name: 'Cambiar estado' }))

    await user.click(screen.getByRole('button', { name: /Recogido/i }))
    await user.type(screen.getByLabelText(/Ubicación/i), 'Almacén Central Ate')
    await user.type(screen.getByLabelText(/Descripción/i), 'Recogido sin observaciones')

    await user.click(screen.getByRole('button', { name: 'Confirmar cambio' }))

    expect(statusSpy).toHaveBeenCalledWith('cfd8998c-e47f-4c04-b9f7-22419fa67e61', {
      status: 'picked_up',
      location: 'Almacén Central Ate',
      description: 'Recogido sin observaciones',
    })
  }, 10_000)

  it('9. un HTTP 409 recarga detalle y timeline', async () => {
    vi.spyOn(operationsApi.shipments, 'status').mockRejectedValue(
      new ApiRequestError('Transición inválida', { code: 'INVALID_SHIPMENT_STATUS_TRANSITION', status: 409 }),
    )
    const getSpy = vi.spyOn(operationsApi.shipments, 'get')
    const timelineSpy = vi.spyOn(operationsApi.shipments, 'timeline')

    renderShipmentDetail()
    await openStatusDialog()
    await userEvent.click(screen.getByRole('button', { name: /Recogido/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar cambio' }))

    expect(await screen.findByText(/El estado del envío cambió o la transición ya no está permitida/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(getSpy).toHaveBeenCalledTimes(2)
      expect(timelineSpy).toHaveBeenCalledTimes(2)
    })
  })

  it('11. los roles sin permiso (warehouse_operator) no pueden abrir el modal', async () => {
    renderShipmentDetail('warehouse_operator')
    await screen.findByRole('heading', { name: 'SHP-0001' })

    expect(screen.queryByRole('button', { name: 'Cambiar estado' })).not.toBeInTheDocument()
  })
})
