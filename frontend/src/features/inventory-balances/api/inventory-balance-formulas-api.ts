import { apiRequest } from '../../../api/api-client'
import type { InventoryBalanceFormula } from '../types/inventory-balances'

export const inventoryBalanceFormulasApi = {
  async listFormulas(): Promise<InventoryBalanceFormula[]> {
    return apiRequest<InventoryBalanceFormula[]>({
      path: '/logistics/inventory/balances/formulas',
      method: 'GET',
    })
  },

  async getFormula(formulaId: string): Promise<InventoryBalanceFormula> {
    return apiRequest<InventoryBalanceFormula>({
      path: `/logistics/inventory/balances/formulas/${formulaId}`,
      method: 'GET',
    })
  },
}
