import type {
  BehavioralBatch,
  BehavioralEvent,
  KeyboardBehaviorEvent,
  KeyboardCategory,
  MouseBehaviorEvent,
  MouseBehaviorEventName,
  MouseButtonCategory,
} from '../types/research'

export const SENSITIVE_EVENT_FIELDS = new Set([
  'key',
  'code',
  'text',
  'value',
  'input',
  'password',
  'clipboard',
  'html',
  'selector',
  'target',
])

interface PendingKeyTiming {
  category: KeyboardCategory
  downAt: number
  flightTime: number
  intervalFromPrevious: number
  isBackspace: boolean
  isModifier: boolean
}

export interface PointerSample {
  x: number
  y: number
  at: number
}

function isSensitiveTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  if (
    target instanceof HTMLInputElement &&
    ['password', 'email'].includes(target.type)
  ) {
    return true
  }
  return target.closest('[data-private-input="true"]') !== null
}

export function categorizeKeyboardEvent(
  event: KeyboardEvent,
): KeyboardCategory {
  const key = event.key
  if (['Shift', 'Control', 'Alt', 'Meta', 'AltGraph'].includes(key)) {
    return 'modifier'
  }
  if (['Backspace', 'Delete'].includes(key)) return 'correction'
  if (
    key.startsWith('Arrow') ||
    ['Tab', 'Enter', 'Home', 'End', 'PageUp', 'PageDown', 'Escape'].includes(
      key,
    )
  ) {
    return 'navigation'
  }
  if (/^F(?:[1-9]|1[0-2])$/.test(key)) return 'function'
  if (/^[\p{L}\p{N}]$/u.test(key)) return 'alphanumeric'
  return 'other'
}

export class KeyboardTimingCollector {
  private readonly pending = new Map<KeyboardCategory, PendingKeyTiming[]>()
  private previousDownAt: number | null = null
  private previousUpAt: number | null = null
  private readonly nextSequence: () => number

  constructor(nextSequence: () => number) {
    this.nextSequence = nextSequence
  }

  handle(event: KeyboardEvent, now = Date.now()): KeyboardBehaviorEvent | null {
    if (
      isSensitiveTarget(event.target) ||
      event.isComposing ||
      (event.type === 'keydown' && event.repeat)
    ) {
      return null
    }

    const category = categorizeKeyboardEvent(event)
    if (event.type === 'keydown') {
      const queue = this.pending.get(category) ?? []
      queue.push({
        category,
        downAt: now,
        flightTime:
          this.previousUpAt === null ? 0 : Math.max(0, now - this.previousUpAt),
        intervalFromPrevious:
          this.previousDownAt === null
            ? 0
            : Math.max(0, now - this.previousDownAt),
        isBackspace: event.key === 'Backspace',
        isModifier: category === 'modifier',
      })
      this.pending.set(
        category,
        queue.filter((item) => now - item.downAt <= 10_000),
      )
      this.previousDownAt = now
      return null
    }

    if (event.type !== 'keyup') return null
    const queue = this.pending.get(category)
    const timing = queue?.shift()
    if (!timing) return null
    this.previousUpAt = now

    return {
      type: 'keyboard',
      event: 'timing',
      timestamp: new Date(now).toISOString(),
      sequence_index: this.nextSequence(),
      category: timing.category,
      dwell_time_ms: Math.max(0, now - timing.downAt),
      flight_time_ms: timing.flightTime,
      interval_from_previous_ms: timing.intervalFromPrevious,
      is_backspace: timing.isBackspace,
      is_modifier: timing.isModifier,
    }
  }

  reset(): void {
    this.pending.clear()
    this.previousDownAt = null
    this.previousUpAt = null
  }
}

function buttonCategory(button: number): MouseButtonCategory {
  if (button === 0) return 'primary'
  if (button === 1) return 'middle'
  if (button === 2) return 'secondary'
  if (button < 0) return 'none'
  return 'other'
}

export function mouseBehaviorEvent(
  event: MouseEvent | PointerEvent | WheelEvent,
  kind: MouseBehaviorEventName,
  sequenceIndex: number,
  previous: PointerSample | null,
  now = Date.now(),
): { behavior: MouseBehaviorEvent; sample: PointerSample } {
  const x = event.clientX
  const y = event.clientY
  const deltaX = previous ? x - previous.x : 0
  const deltaY = previous ? y - previous.y : 0
  const distance = Math.hypot(deltaX, deltaY)
  const elapsed = previous ? Math.max(now - previous.at, 1) : 0
  const velocity = elapsed > 0 ? (distance / elapsed) * 1000 : 0
  const scrollDelta = event instanceof WheelEvent ? event.deltaY : 0
  const rawButton = kind === 'click' || kind.startsWith('pointer')
    ? event.button
    : -1

  return {
    behavior: {
      type: 'mouse',
      event: kind,
      timestamp: new Date(now).toISOString(),
      sequence_index: sequenceIndex,
      normalized_x: Number(
        Math.min(Math.max(x / Math.max(window.innerWidth, 1), 0), 1).toFixed(4),
      ),
      normalized_y: Number(
        Math.min(Math.max(y / Math.max(window.innerHeight, 1), 0), 1).toFixed(4),
      ),
      delta_x: Number(deltaX.toFixed(2)),
      delta_y: Number(deltaY.toFixed(2)),
      distance: Number(distance.toFixed(2)),
      velocity: Number(velocity.toFixed(2)),
      button_category: buttonCategory(rawButton),
      scroll_delta: Number(scrollDelta.toFixed(2)),
    },
    sample: { x, y, at: now },
  }
}

export function makeBatch(
  events: BehavioralEvent[],
  sequenceNumber: number,
  options?: {
    batchId?: string
    visibilityState?: string
    timezoneOffsetMinutes?: number
    droppedEventCount?: number
    collectorErrorCount?: number
  },
): BehavioralBatch {
  const now = new Date().toISOString()
  return {
    batch_id: options?.batchId ?? crypto.randomUUID(),
    sequence_number: sequenceNumber,
    started_at: events[0]?.timestamp ?? now,
    ended_at: events.at(-1)?.timestamp ?? now,
    visibility_state: options?.visibilityState ?? document.visibilityState,
    client_timezone_offset_minutes:
      options?.timezoneOffsetMinutes ?? -new Date().getTimezoneOffset(),
    dropped_event_count: options?.droppedEventCount ?? 0,
    collector_error_count: options?.collectorErrorCount ?? 0,
    events,
  }
}

export async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  retries = 3,
  waits = [250, 750, 1500],
): Promise<T> {
  let lastError: unknown
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await operation()
    } catch (error: unknown) {
      lastError = error
      if (attempt === retries) break
      await new Promise<void>((resolve) => {
        window.setTimeout(resolve, waits[attempt] ?? waits.at(-1) ?? 1500)
      })
    }
  }
  throw lastError
}

export function containsSensitiveField(value: unknown): boolean {
  if (Array.isArray(value)) return value.some(containsSensitiveField)
  if (typeof value !== 'object' || value === null) return false
  return Object.entries(value).some(
    ([key, nested]) =>
      SENSITIVE_EVENT_FIELDS.has(key.toLowerCase()) ||
      containsSensitiveField(nested),
  )
}
