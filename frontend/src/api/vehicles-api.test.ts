import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest, getCsrfToken } from './api-client'
import { vehiclesApi } from './vehicles-api'

vi.mock('./api-client', () => ({
  apiRequest: vi.fn(),
  getCsrfToken: vi.fn(),
}))

const mockedRequest = vi.mocked(apiRequest)
const mockedCsrf = vi.mocked(getCsrfToken)

const backendVehicle = {
  id: 'vehicle-1',
  vehicle_code: 'VH-001',
  display_plate: 'ABC-123',
  normalized_plate: 'ABC123',
  masked_vin: '***********123456',
  make_id: 'make-1',
  model_id: 'model-1',
  manufacturing_year: 2024,
  vehicle_type: 'TRUCK',
  body_type: 'CLOSED',
  lifecycle_status: 'ACTIVE',
  operational_status: 'AVAILABLE',
  compliance_status: 'COMPLIANT',
  created_at: '2026-07-28T12:00:00Z',
  updated_at: '2026-07-28T12:00:00Z',
}

describe('vehiclesApi', () => {
  beforeEach(() => {
    mockedRequest.mockReset()
    mockedCsrf.mockReset()
    mockedCsrf.mockResolvedValue('csrf-token')
  })

  it('no llama al GET de listado que el backend no expone', async () => {
    const result = await vehiclesApi.list({ page: 2, page_size: 10 })

    expect(mockedRequest).not.toHaveBeenCalled()
    expect(result).toEqual({
      items: [],
      page: 2,
      page_size: 10,
      total: 0,
      total_pages: 0,
    })
  })

  it('normaliza el detalle real para la vista del frontend', async () => {
    mockedRequest.mockResolvedValue(backendVehicle)

    const result = await vehiclesApi.get('vehicle-1')

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/vehicles/vehicle-1',
    })
    expect(result).toMatchObject({
      id: 'vehicle-1',
      internal_code: 'VH-001',
      plate_number: 'ABC-123',
      year_of_manufacture: 2024,
      capabilities: {
        can_update: false,
        can_change_plate: true,
      },
    })
  })

  it('mapea el formulario de creación al DTO del backend', async () => {
    mockedRequest.mockResolvedValue(backendVehicle)

    await vehiclesApi.create({
      plate_number: 'ABC-123',
      make_id: 'make-1',
      model_id: 'model-1',
      year_of_manufacture: 2024,
      vehicle_type: 'TRUCK',
      body_type: 'CLOSED',
    })

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/vehicles',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'csrf-token' },
      body: {
        display_plate: 'ABC-123',
        make_id: 'make-1',
        model_id: 'model-1',
        vehicle_code: undefined,
        vin: undefined,
        chassis_number: undefined,
        engine_number: undefined,
        manufacturing_year: 2024,
        vehicle_type: 'TRUCK',
        body_type: 'CLOSED',
        notes: undefined,
      },
    })
  })

  it('usa la ruta y el campo reales para cambiar la placa', async () => {
    mockedRequest.mockResolvedValue(backendVehicle)

    await vehiclesApi.changePlate('vehicle-1', 'XYZ-999', 'Renovación registral')

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/vehicles/vehicle-1/plate-change',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'csrf-token' },
      body: {
        new_display_plate: 'XYZ-999',
        reason: 'Renovación registral',
      },
    })
  })

  it('lista modelos desde la marca y acepta la respuesta como arreglo', async () => {
    mockedRequest.mockResolvedValue([
      {
        id: 'model-1',
        make_id: 'make-1',
        code: 'M1',
        name: 'Modelo 1',
        vehicle_type: 'TRUCK',
        body_type: 'CLOSED',
        status: 'ACTIVE',
        system_defined: false,
      },
    ])

    const result = await vehiclesApi.listModels('make-1')

    expect(mockedRequest).toHaveBeenCalledWith({
      path: '/logistics/vehicle-makes/make-1/models',
    })
    expect(result[0]).toMatchObject({
      id: 'model-1',
      suggested_vehicle_type: 'TRUCK',
      is_active: true,
    })
  })
})
