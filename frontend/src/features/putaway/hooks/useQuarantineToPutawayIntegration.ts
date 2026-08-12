import { useCallback } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { putawayOrdersApi } from '../api/putawayOrdersApi'
import type { CreatePutawayOrderRequest } from '../types/putaway'

interface QuarantineReleaseData {
  release_id: string
  allocation_id: string
  warehouse_id: string
  product_id: string
  product_name: string
  quantity: string
  unit_id: string
  lot_id?: string
  serial_id?: string
}

export function useQuarantineToPutawayIntegration() {
  const createOrder = useMutation(
    (data: CreatePutawayOrderRequest) => putawayOrdersApi.createOrder(data),
  )

  const createFromRelease = useCallback(
    async (release: QuarantineReleaseData) => {
      const orderData: CreatePutawayOrderRequest = {
        warehouse_id: release.warehouse_id,
        source_type: 'quality_release',
        source_id: release.release_id,
        priority: 'normal',
        notes: `Generada desde liberación de cuarentena ${release.release_id}`,
        lines: [
          {
            product_id: release.product_id,
            quantity: { value: release.quantity, scale: 3 },
            unit_id: release.unit_id,
            lot_id: release.lot_id,
            serial_id: release.serial_id,
          },
        ],
      }
      return createOrder.mutate(orderData)
    },
    [createOrder],
  )

  return {
    createFromRelease,
    isPending: createOrder.isPending,
    error: createOrder.error,
  }
}
