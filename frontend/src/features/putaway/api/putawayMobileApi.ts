import { apiRequest } from '../../../api/api-client'

export const putawayMobileApi = {
  async getWorkspace(userId: string): Promise<unknown> {
    return apiRequest({ path: `/logistics/putaway/users/${userId}/workspace`, method: 'GET' })
  },

  async scanCode(code: string, context?: Record<string, unknown>): Promise<unknown> {
    return apiRequest({
      path: '/logistics/putaway/scan',
      method: 'POST',
      body: { code, ...context },
    })
  },

  async getActiveTask(userId: string): Promise<unknown> {
    return apiRequest({ path: `/logistics/putaway/users/${userId}/active-task`, method: 'GET' })
  },
}
