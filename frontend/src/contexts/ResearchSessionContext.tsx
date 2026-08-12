import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { researchApi } from '../api/research-api'
import { CaptureBar } from '../components/research/CaptureBar'
import {
  KeyboardTimingCollector,
  makeBatch,
  mouseBehaviorEvent,
  retryWithBackoff,
  type PointerSample,
} from '../research/telemetry'
import type {
  BehavioralEvent,
  CollectorConfiguration,
  MouseBehaviorEventName,
  ResearchScenario,
} from '../types/research'
import {
  ResearchSessionContext,
  type ResearchCounters,
} from './research-session-context'

const initialCounters: ResearchCounters = {
  keyboard: 0,
  mouse: 0,
  captures: 0,
  batches: 0,
  errors: 0,
}

function clientDeviceType(): 'desktop' | 'tablet' | 'mobile' {
  const agent = navigator.userAgent
  const isTablet = /iPad|Tablet|Android(?!.*Mobile)/i.test(agent)
  const isMobile = /Android.*Mobile|iPhone|iPod/i.test(agent)
  return isTablet ? 'tablet' : isMobile ? 'mobile' : 'desktop'
}

export function ResearchSessionProvider({ children }: { children: ReactNode }) {
  const [configuration, setConfiguration] = useState<CollectorConfiguration | null>(null)
  const [participantId, setParticipantId] = useState<string | null>(null)
  const [startedAtEpoch, setStartedAtEpoch] = useState<number | null>(null)
  const [latestAcceptedFacialCaptureId, setLatestAcceptedFacialCaptureId] =
    useState<string | null>(null)
  const [latestBehavioralWindowId, setLatestBehavioralWindowId] =
    useState<string | null>(null)
  const [lastCaptureConfirmedAt, setLastCaptureConfirmedAt] =
    useState<string | null>(null)
  const [lastBehaviorBatchConfirmedAt, setLastBehaviorBatchConfirmedAt] =
    useState<string | null>(null)
  const [counters, setCounters] = useState(initialCounters)
  const streamRef = useRef<MediaStream | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const eventBufferRef = useRef<BehavioralEvent[]>([])
  const batchSequenceRef = useRef(1)
  const captureSequenceRef = useRef(1)
  const eventSequenceRef = useRef(1)
  const keyboardCollectorRef = useRef<KeyboardTimingCollector | null>(null)
  if (!keyboardCollectorRef.current) {
    keyboardCollectorRef.current = new KeyboardTimingCollector(
      () => eventSequenceRef.current++,
    )
  }
  const pointerSampleRef = useRef<PointerSample | null>(null)
  const lastPointerAtRef = useRef(0)
  const lastWheelAtRef = useRef(0)
  const pendingBatchesRef = useRef<Set<Promise<void>>>(new Set())

  const recordError = useCallback(() => {
    setCounters((current) => ({ ...current, errors: current.errors + 1 }))
  }, [])

  const flush = useCallback(async () => {
    if (!configuration || eventBufferRef.current.length === 0) return
    const events = eventBufferRef.current.splice(0, configuration.max_batch_events)
    const batch = makeBatch(events, batchSequenceRef.current++)
    const promise = retryWithBackoff(() => researchApi.sendBatch(configuration.id, batch))
      .then((response) => {
        setCounters((current) => ({
          ...current,
          batches: current.batches + 1,
        }))
        setLastBehaviorBatchConfirmedAt(new Date().toISOString())
        if (response.behavioral_window_id) {
          setLatestBehavioralWindowId(response.behavioral_window_id)
        }
      })
      .catch(() => recordError())
      .finally(() => pendingBatchesRef.current.delete(promise))
    pendingBatchesRef.current.add(promise)
    await promise
  }, [configuration, recordError])

  useEffect(() => {
    if (!configuration || startedAtEpoch === null) return undefined
    const append = (event: BehavioralEvent) => {
      eventBufferRef.current.push(event)
      if (eventBufferRef.current.length >= configuration.max_batch_events) void flush()
    }
    const onKeyboard = (event: KeyboardEvent) => {
      const sanitized = keyboardCollectorRef.current?.handle(event) ?? null
      if (!sanitized) return
      append(sanitized)
      setCounters((current) => ({ ...current, keyboard: current.keyboard + 1 }))
    }
    const appendMouse = (
      event: MouseEvent | PointerEvent | WheelEvent,
      kind: MouseBehaviorEventName,
    ) => {
      const result = mouseBehaviorEvent(
        event,
        kind,
        eventSequenceRef.current++,
        pointerSampleRef.current,
      )
      pointerSampleRef.current = result.sample
      append(result.behavior)
      setCounters((current) => ({ ...current, mouse: current.mouse + 1 }))
    }
    const onPointerMove = (event: PointerEvent) => {
      const now = performance.now()
      if (now - lastPointerAtRef.current < 50) return
      lastPointerAtRef.current = now
      appendMouse(event, 'move')
    }
    const onClick = (event: MouseEvent) => appendMouse(event, 'click')
    const onPointerDown = (event: PointerEvent) => {
      appendMouse(event, 'pointerdown')
    }
    const onPointerUp = (event: PointerEvent) => {
      appendMouse(event, 'pointerup')
    }
    const onWheel = (event: WheelEvent) => {
      const now = performance.now()
      if (now - lastWheelAtRef.current < 100) return
      lastWheelAtRef.current = now
      appendMouse(event, 'scroll')
    }
    document.addEventListener('keydown', onKeyboard, true)
    document.addEventListener('keyup', onKeyboard, true)
    document.addEventListener('pointermove', onPointerMove, true)
    document.addEventListener('pointerdown', onPointerDown, true)
    document.addEventListener('pointerup', onPointerUp, true)
    document.addEventListener('click', onClick, true)
    document.addEventListener('wheel', onWheel, { capture: true, passive: true })
    const interval = window.setInterval(() => void flush(), configuration.batch_interval_seconds * 1000)
    return () => {
      document.removeEventListener('keydown', onKeyboard, true)
      document.removeEventListener('keyup', onKeyboard, true)
      document.removeEventListener('pointermove', onPointerMove, true)
      document.removeEventListener('pointerdown', onPointerDown, true)
      document.removeEventListener('pointerup', onPointerUp, true)
      document.removeEventListener('click', onClick, true)
      document.removeEventListener('wheel', onWheel, true)
      window.clearInterval(interval)
    }
  }, [configuration, flush, startedAtEpoch])

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => {
      track.onended = null
      track.stop()
    })
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
  }, [])

  useEffect(() => () => {
    stopCamera()
    eventBufferRef.current = []
    pendingBatchesRef.current.clear()
    keyboardCollectorRef.current?.reset()
  }, [stopCamera])

  const clear = useCallback(() => {
    stopCamera()
    setConfiguration(null)
    setParticipantId(null)
    setStartedAtEpoch(null)
    setLatestAcceptedFacialCaptureId(null)
    setLatestBehavioralWindowId(null)
    setLastCaptureConfirmedAt(null)
    setLastBehaviorBatchConfirmedAt(null)
    eventBufferRef.current = []
    pendingBatchesRef.current.clear()
    keyboardCollectorRef.current?.reset()
    pointerSampleRef.current = null
    setCounters(initialCounters)
  }, [stopCamera])

  const stopForSecurity = useCallback(() => {
    clear()
  }, [clear])

  const cancelSession = useCallback(async (reason: string) => {
    if (!configuration) return
    try {
      await researchApi.cancel(configuration.id, reason)
    } finally {
      clear()
    }
  }, [clear, configuration])

  const captureFrame = useCallback(async () => {
    const video = videoRef.current
    const activeStream = streamRef.current
    const hasLiveTrack = activeStream?.getVideoTracks().some((track) => track.readyState === 'live')

    if (configuration && activeStream && !hasLiveTrack) {
      recordError()
      void cancelSession('camera_permission_lost')
      return
    }

    if (!configuration || !video || !activeStream || video.readyState < 2 || document.visibilityState !== 'visible') return
    const ratio = Math.min(640 / Math.max(video.videoWidth, 1), 1)
    const width = Math.max(64, Math.round(video.videoWidth * ratio))
    const height = Math.max(64, Math.round(video.videoHeight * ratio))
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) { recordError(); return }
    context.drawImage(video, 0, 0, width, height)
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/webp', 0.72))
    if (!blob || blob.size > configuration.max_image_size_bytes) { recordError(); return }
    const sequenceNumber = captureSequenceRef.current++
    try {
      const response = await retryWithBackoff(() => researchApi.sendCapture(configuration.id, {
        image: blob,
        capturedAt: new Date().toISOString(),
        sequenceNumber,
        width,
        height,
      }))
      setLatestAcceptedFacialCaptureId(response.id)
      setLastCaptureConfirmedAt(response.captured_at)
      setCounters((current) => ({ ...current, captures: current.captures + 1 }))
    } catch {
      recordError()
    }
  }, [cancelSession, configuration, recordError])

  useEffect(() => {
    if (!configuration || !streamRef.current) return undefined
    const timer = window.setInterval(() => void captureFrame(), configuration.capture_interval_seconds * 1000)
    return () => window.clearInterval(timer)
  }, [captureFrame, configuration])

  const startSession = useCallback(async ({
    participantId: nextParticipantId,
    scenario,
    expectedDurationMinutes,
  }: {
    participantId: string
    scenario: ResearchScenario
    expectedDurationMinutes: number
  }) => {
    if (configuration) throw new Error('Ya existe una sesión experimental activa.')
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    })
    streamRef.current = stream
    stream.getVideoTracks().forEach((track) => {
      track.onended = () => {
        if (streamRef.current) {
          void cancelSession('camera_permission_lost')
        }
      }
    })
    try {
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      const response = await researchApi.start({
        participant_id: nextParticipantId,
        scenario,
        expected_duration_minutes: expectedDurationMinutes,
        screen_width: window.screen.width,
        screen_height: window.screen.height,
        client_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        browser: navigator.userAgent,
        operating_system: navigator.platform,
        device_type: clientDeviceType(),
      })
      setConfiguration(response.session)
      setParticipantId(nextParticipantId)
      setStartedAtEpoch(Date.now())
      setLatestAcceptedFacialCaptureId(null)
      setLatestBehavioralWindowId(null)
      setLastCaptureConfirmedAt(null)
      setLastBehaviorBatchConfirmedAt(null)
      setCounters(initialCounters)
      batchSequenceRef.current = 1
      captureSequenceRef.current = 1
      eventSequenceRef.current = 1
      keyboardCollectorRef.current?.reset()
      pointerSampleRef.current = null
    } catch (error: unknown) {
      stopCamera()
      throw error
    }
  }, [cancelSession, configuration, stopCamera])

  const finishSession = useCallback(async () => {
    if (!configuration) return
    while (eventBufferRef.current.length > 0) await flush()
    await Promise.allSettled([...pendingBatchesRef.current])
    await researchApi.finish(configuration.id, counters.errors)
    clear()
  }, [clear, configuration, counters.errors, flush])

  const value = useMemo(() => ({
    configuration,
    participantId,
    isActive: configuration !== null,
    hasCamera: streamRef.current !== null,
    startedAtEpoch,
    experimentalSessionId: configuration?.id ?? null,
    latestAcceptedFacialCaptureId,
    latestBehavioralWindowId,
    lastCaptureConfirmedAt,
    lastBehaviorBatchConfirmedAt,
    counters,
    startSession,
    finishSession,
    cancelSession,
    stopForSecurity,
  }), [
    cancelSession,
    configuration,
    counters,
    finishSession,
    lastBehaviorBatchConfirmedAt,
    lastCaptureConfirmedAt,
    latestAcceptedFacialCaptureId,
    latestBehavioralWindowId,
    participantId,
    startSession,
    startedAtEpoch,
    stopForSecurity,
  ])

  return (
    <ResearchSessionContext.Provider value={value}>
      {children}
      <video ref={videoRef} className="capture-video" muted playsInline aria-hidden="true" />
      {configuration && <CaptureBar />}
    </ResearchSessionContext.Provider>
  )
}
