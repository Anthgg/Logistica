import { useCallback, useRef } from 'react'

type FeedbackType = 'success' | 'warning' | 'error'

const FREQUENCIES: Record<FeedbackType, number> = {
  success: 880,
  warning: 440,
  error: 220,
}

const DURATIONS: Record<FeedbackType, number> = {
  success: 120,
  warning: 200,
  error: 350,
}

const VIBRATION_PATTERNS: Record<FeedbackType, number[]> = {
  success: [50],
  warning: [100, 50, 100],
  error: [200, 100, 200],
}

export interface ScanFeedbackOptions {
  soundEnabled?: boolean
  vibrationEnabled?: boolean
}

export function useScanFeedback(options: ScanFeedbackOptions = {}) {
  const { soundEnabled = true, vibrationEnabled = true } = options
  const audioCtxRef = useRef<AudioContext | null>(null)
  const lastPlayRef = useRef(0)

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext()
    }
    return audioCtxRef.current
  }, [])

  const playTone = useCallback((type: FeedbackType) => {
    if (!soundEnabled) return
    const now = Date.now()
    if (now - lastPlayRef.current < 150) return
    lastPlayRef.current = now

    try {
      const ctx = getAudioContext()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = FREQUENCIES[type]
      osc.type = type === 'error' ? 'square' : 'sine'
      gain.gain.value = 0.15
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + DURATIONS[type] / 1000)
      osc.start(ctx.currentTime)
      osc.stop(ctx.currentTime + DURATIONS[type] / 1000)
    } catch {
      // AudioContext may not be available
    }
  }, [soundEnabled, getAudioContext])

  const vibrate = useCallback((type: FeedbackType) => {
    if (!vibrationEnabled) return
    try {
      navigator.vibrate?.(VIBRATION_PATTERNS[type])
    } catch {
      // Vibration may not be supported
    }
  }, [vibrationEnabled])

  const feedback = useCallback((type: FeedbackType) => {
    playTone(type)
    vibrate(type)
  }, [playTone, vibrate])

  return { feedback, playTone, vibrate }
}
