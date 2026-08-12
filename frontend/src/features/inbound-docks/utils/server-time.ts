/**
 * Helpers de tiempo basados en la hora del servidor.
 *
 * Reglas:
 * - El backend es la única fuente autoritativa de tiempo.
 * - React puede interpolar visualmente.
 * - No se envía el valor calculado.
 * - Sincronizar periódicamente.
 * - Manejar pestaña suspendida y desfase de hora local.
 */
import { useEffect, useMemo, useRef, useState } from 'react'

const SYNC_INTERVAL_MS = 30_000

interface BaseTimeProvider {
  serverTimeIso: string | null
  timezone: string | null
  lastSyncedAt: Date | null
  driftMs: number
}

interface TimeProviderOptions {
  pollIntervalMs?: number
}

export interface ServerTimeHook extends BaseTimeProvider {
  /** Hora actual estimada (ms epoch) según interpolación local desde la última sincronización. */
  estimatedNowMs: () => number
  /** Diferencia estimada entre el reloj del navegador y la hora del servidor. */
  estimatedDriftMs: number
  forceResync: () => void
}

export function useServerTime(
  serverTimeIso: string | null,
  timezone: string | null,
  options: TimeProviderOptions = {},
): ServerTimeHook {
  const pollIntervalMs = options.pollIntervalMs ?? SYNC_INTERVAL_MS
  const lastSyncMsRef = useRef<number | null>(null)
  const [tick, setTick] = useState(0)
  const [resyncNonce, setResyncNonce] = useState(0)

  useEffect(() => {
    if (!serverTimeIso) {
      lastSyncMsRef.current = null
      return
    }
    const parsed = Date.parse(serverTimeIso)
    if (Number.isNaN(parsed)) {
      lastSyncMsRef.current = null
      return
    }
    lastSyncMsRef.current = parsed - Date.now()
  }, [serverTimeIso, resyncNonce])

  useEffect(() => {
    if (!serverTimeIso) return
    const interval = window.setInterval(() => setTick((t) => t + 1), 1000)
    return () => window.clearInterval(interval)
  }, [serverTimeIso, resyncNonce])

  useEffect(() => {
    if (!serverTimeIso) return
    const interval = window.setInterval(
      () => setResyncNonce((n) => n + 1),
      pollIntervalMs,
    )
    return () => window.clearInterval(interval)
  }, [serverTimeIso, pollIntervalMs])

  const driftMs = useMemo(() => {
    if (!serverTimeIso) return 0
    const parsed = Date.parse(serverTimeIso)
    if (Number.isNaN(parsed)) return 0
    return parsed - Date.now()
  }, [serverTimeIso, resyncNonce, tick])

  const lastSyncedAt = useMemo(() => {
    if (!serverTimeIso) return null
    const parsed = Date.parse(serverTimeIso)
    if (Number.isNaN(parsed)) return null
    return new Date(parsed)
  }, [serverTimeIso, resyncNonce])

  return {
    serverTimeIso,
    timezone,
    lastSyncedAt,
    driftMs,
    estimatedDriftMs: driftMs,
    estimatedNowMs: () => Date.now() + driftMs,
    forceResync: () => setResyncNonce((n) => n + 1),
  }
}

export function formatApproxSeconds(
  serverTimeIso: string | null,
  startedAt: string | null,
  activePauseStartedAt: string | null,
  accumulatedPauseSeconds: number,
  status: string,
): {
  grossSeconds: number | null
  pausedSeconds: number | null
  netSeconds: number | null
  isApproximate: boolean
} {
  if (!serverTimeIso || !startedAt) {
    return { grossSeconds: null, pausedSeconds: null, netSeconds: null, isApproximate: true }
  }
  const start = Date.parse(startedAt)
  const serverNow = Date.parse(serverTimeIso)
  if (Number.isNaN(start) || Number.isNaN(serverNow)) {
    return { grossSeconds: null, pausedSeconds: null, netSeconds: null, isApproximate: true }
  }
  const gross = Math.max(0, Math.floor((serverNow - start) / 1000))
  let paused = Math.max(0, accumulatedPauseSeconds)
  if (activePauseStartedAt && (status === 'PAUSED' || status === 'UNLOADING_PAUSED')) {
    const pauseStart = Date.parse(activePauseStartedAt)
    if (!Number.isNaN(pauseStart)) {
      paused += Math.max(0, Math.floor((serverNow - pauseStart) / 1000))
    }
  }
  const net = Math.max(0, gross - paused)
  return { grossSeconds: gross, pausedSeconds: paused, netSeconds: net, isApproximate: true }
}
