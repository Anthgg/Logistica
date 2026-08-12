import { useCallback } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { putawayOrdersApi } from '../api/putawayOrdersApi'
import type { CreatePutawayOrderRequest } from '../types/putaway'

interface ReceptionCompleteData {
  reception_id: string
  warehouse_id: string
  items: {
    product_id: string
    product_name: string
    quantity: string
    unit_id: string
    lot_id?: string
    serial_id?: string
    pallet_id?: string
  }[]
}

export function useReceptionToPutawayIntegration() {
  const createOrder = useMutation(
    (data: CreatePutawayOrderRequest) => putawayOrdersApi.createOrder(data),
  )

  const createFromReception = useCallback(
    async (reception: ReceptionCompleteData) => {
      if (reception.items.length === 0) return null

      const orderData: CreatePutawayOrderRequest = {
        warehouse_id: reception.warehouse_id,
        source_type: 'reception',
        source_id: reception.reception_id,
        priority: 'normal',
        notes: `Generada desde recepción ${reception.reception_id}`,
        lines: reception.items.map((item) => ({
          product_id: item.product_id,
          quantity: { value: item.quantity, scale: 3 },
          unit_id: item.unit_id,
          lot_id: item.lot_id,
          serial_id: item.serial_id,
          pallet_id: item.pallet_id,
        })),
      }
      return createOrder.mutate(orderData)
    },
    [createOrder],
  )

  return {
    createFromReception,
    isPending: createOrder.isPending,
    error: createOrder.error,
  }
}
