import type { ApiRequestError } from '../types/api'

type UnauthorizedListener = (error: ApiRequestError) => void

const listeners = new Set<UnauthorizedListener>()
let hasNotifiedSessionLoss = false

export function subscribeToUnauthorized(
  listener: UnauthorizedListener,
): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function notifyUnauthorized(error: ApiRequestError): void {
  if (hasNotifiedSessionLoss) {
    return
  }

  hasNotifiedSessionLoss = true
  listeners.forEach((listener) => listener(error))
}

export function resetUnauthorizedNotification(): void {
  hasNotifiedSessionLoss = false
}
