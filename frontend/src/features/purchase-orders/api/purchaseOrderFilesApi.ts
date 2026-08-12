import type {
  PurchaseOrderFile,
  PurchaseOrderFileAttach,
  PurchaseOrderFileVisibility,
} from '../types/purchase-orders-v2'

function unavailable(feature: string): never {
  throw new Error(
    `${feature} todavía no está publicado como endpoint independiente por el backend 0.9.3.`,
  )
}

export const purchaseOrderFilesApi = {
  async list(_purchaseOrderId: string): Promise<PurchaseOrderFile[]> {
    return []
  },

  async attach(
    _purchaseOrderId: string,
    _payload: PurchaseOrderFileAttach,
  ): Promise<PurchaseOrderFile> {
    return unavailable('El adjunto de archivos a la OC')
  },

  async updateVisibility(
    _purchaseOrderId: string,
    _fileId: string,
    _visibility: PurchaseOrderFileVisibility,
  ): Promise<PurchaseOrderFile> {
    return unavailable('La modificación de visibilidad de archivos de OC')
  },

  async detach(_purchaseOrderId: string, _fileId: string): Promise<void> {
    return unavailable('La desvinculación de archivos de OC')
  },
}